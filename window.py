import threading
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from PIL import Image, ImageTk
from pynput import keyboard

from config.config import *
from accessory import run_applescript, render_pdf


# ── Overlay window ────────────────────────────────────────────────────────────

class PreviewOverlay:

    def __init__(self, root: tk.Tk):
        self.root = root

        self.pages: list[ImageTk.PhotoImage] = []  # PhotoImage objects for display
        self.pages_pil: list[Image.Image] = []  # Original PIL images for rescaling
        self.current = 0          # 0-indexed
        self._hotkeys: set = set()
        self._stop_refresh_event = threading.Event()
        self.collapsed_mode = False
        self.pdf_aspect_ratio = None  # Width/Height ratio of PDF pages
        self._resizing = False  # Flag to prevent recursive Configure events

        self._build_ui()

        # On first launch, trigger a refresh to get the current OneNote page
        self._trigger_refresh()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        r = self.root
        r.title(WINDOW_TITLE)
        r.resizable(True, True)  # Enable window resizing
        r.attributes("-topmost", True)          # always on top
        r.attributes("-type", "utility")       # macOS: utility window stays above fullscreen apps
        r.configure(bg="#F0F0F0")

        # Position: top-right corner of screen
        r.update_idletasks()   # ensure tkinter is initialised before querying screen size
        sw = r.winfo_screenwidth()
        x  = max(0, sw - WINDOW_W - 20)
        r.geometry(f"{WINDOW_W}x600")   # set size first
        r.geometry(f"+{x}+40")          # then position separately

        # ── Title bar ────────────────────────────────────────────────────────
        titlebar = tk.Frame(r, bg="#E8E8E8", height=36)
        titlebar.pack(fill="x")
        titlebar.pack_propagate(False)

        tk.Label(
            titlebar, text="PDF Preview",
            bg="#E8E8E8", fg="#555555",
            font=("SF Pro Text", 12)
        ).pack(side="left", padx=12)

        # Close button (⊗)
        self.close_btn = tk.Button(
            titlebar, text="⊗",
            bg="#E8E8E8", fg="#FF5F57",
            relief="flat", bd=0,
            font=("SF Pro Text", 12),
            activebackground="#D8D8D8",
            cursor="hand2",
            command=self._close_window
        )
        self.close_btn.pack(side="right", padx=4, pady=6)

        # Minimize button (–)
        self.minimize_btn = tk.Button(
            titlebar, text="–",
            bg="#E8E8E8", fg="#333333",
            relief="flat", bd=0,
            font=("SF Pro Text", 14),
            activebackground="#D8D8D8",
            cursor="hand2",
            command=self._toggle_collapse
        )
        self.minimize_btn.pack(side="right", padx=4, pady=6)

        self.refresh_btn = tk.Button(
            titlebar, text="↻  Refresh",
            bg="#E8E8E8", fg="#333333",
            relief="flat", bd=0,
            font=("SF Pro Text", 11),
            activebackground="#D8D8D8",
            cursor="hand2",
            command=self._trigger_refresh
        )
        self.refresh_btn.pack(side="right", padx=8, pady=6)

        # Drag-to-move on titlebar
        titlebar.bind("<ButtonPress-1>",   self._drag_start)
        titlebar.bind("<B1-Motion>",       self._drag_move)

        # ── Page canvas ──────────────────────────────────────────────────────
        self.canvas_bg = tk.Frame(r, bg="#C8C8C8", padx=16, pady=16)
        self.canvas_bg.pack(fill="both", expand=True)

        self.canvas = tk.Label(self.canvas_bg, bg="#FFFFFF", cursor="arrow")
        self.canvas.pack()

        # ── Navigation bar ───────────────────────────────────────────────────
        self.nav = tk.Frame(r, bg="#F0F0F0", height=40)
        self.nav.pack(fill="x")
        self.nav.pack_propagate(False)

        self.prev_btn = tk.Button(
            self.nav, text="← Prev",
            bg="#F0F0F0", fg="#333333",
            relief="flat", bd=0,
            font=("SF Pro Text", 11),
            activebackground="#E0E0E0",
            cursor="hand2",
            state="disabled",
            command=self._prev_page
        )
        self.prev_btn.pack(side="left", padx=12)

        # Stop button (⏹)
        self.stop_btn = tk.Button(
            self.nav, text="⏹  Stop",
            bg="#F0F0F0", fg="#FF5F57",
            relief="flat", bd=0,
            font=("SF Pro Text", 11),
            activebackground="#E0E0E0",
            cursor="hand2",
            state="disabled",
            command=self._on_stop_refresh
        )
        self.stop_btn.pack(side="left", padx=4)

        self.page_label = tk.Label(
            self.nav, text="— / —",
            bg="#F0F0F0", fg="#555555",
            font=("SF Pro Text", 11)
        )
        self.page_label.pack(side="left", expand=True)

        self.next_btn = tk.Button(
            self.nav, text="Next →",
            bg="#F0F0F0", fg="#333333",
            relief="flat", bd=0,
            font=("SF Pro Text", 11),
            activebackground="#E0E0E0",
            cursor="hand2",
            state="disabled",
            command=self._next_page
        )
        self.next_btn.pack(side="right", padx=12)

        # ── Status bar ───────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Starting up…")
        status_bar = tk.Frame(r, bg="#E8E8E8", height=24)
        status_bar.pack(fill="x")
        status_bar.pack_propagate(False)

        self.status_dot = tk.Label(status_bar, text="●", bg="#E8E8E8", fg="#28C840", font=("SF Pro Text", 9))
        self.status_dot.pack(side="left", padx=(8, 2), pady=4)

        tk.Label(
            status_bar, textvariable=self.status_var,
            bg="#E8E8E8", fg="#777777",
            font=("SF Pro Text", 10)
        ).pack(side="left")

        # In _build_ui(), add this line at the end:
        r.bind("<Command-Shift-R>", lambda e: self._trigger_refresh())
        r.bind("<Configure>", self._on_window_configure)

    # ── Drag to move ──────────────────────────────────────────────────────────

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _drag_move(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    # ── Window resizing with aspect ratio ──────────────────────────────────────

    def _on_window_configure(self, event):
        """Enforce PDF aspect ratio when window is resized."""
        if self._resizing or self.pdf_aspect_ratio is None or self.collapsed_mode:
            return
        
        self._resizing = True
        try:
            # Get current window geometry
            w = self.root.winfo_width()
            h = self.root.winfo_height()
            
            # Calculate title bar height (36px), nav bar height (40px), status bar height (24px)
            # and padding (32px for canvas_bg padding)
            overhead = 36 + 40 + 24 + 32
            available_height = h - overhead
            available_width = w - 32  # 16px padding on each side of canvas_bg
            
            # Calculate what height should be to maintain aspect ratio
            expected_height = int(available_width / self.pdf_aspect_ratio) + overhead
            
            # If aspect ratio is off, correct it
            if abs(h - expected_height) > 5:  # 5px tolerance to avoid constant adjustments
                self.root.geometry(f"{w}x{expected_height}")
            else:
                # Redraw the current page at the new width
                if self.pages_pil and self.current < len(self.pages_pil):
                    self._show_page(self.current)
        finally:
            self._resizing = False

    # ── Page navigation ───────────────────────────────────────────────────────

    def _show_page(self, index: int):
        if not self.pages_pil or not self.pages:
            return
        self.current = index
        
        # Get the available canvas width (minus padding)
        canvas_width = self.canvas_bg.winfo_width() - 32  # 16px padding on each side
        if canvas_width < 50:  # Fallback if widget not yet rendered
            canvas_width = PAGE_W
        
        # Get original PIL image and rescale if needed
        pil_img = self.pages_pil[index]
        if canvas_width != PAGE_W:
            scale_ratio = canvas_width / PAGE_W
            new_width = int(pil_img.width * scale_ratio)
            new_height = int(pil_img.height * scale_ratio)
            scaled_pil = pil_img.resize((new_width, new_height), Image.LANCZOS)
            scaled_photo = ImageTk.PhotoImage(scaled_pil)
        else:
            scaled_photo = self.pages[index]
        
        self.canvas.configure(image=scaled_photo, width=scaled_photo.width(), height=scaled_photo.height())
        self.canvas.image = scaled_photo  # keep reference alive

        total = len(self.pages)
        self.page_label.configure(text=f"{index + 1} / {total}")
        self.prev_btn.configure(state="normal" if index > 0          else "disabled")
        self.next_btn.configure(state="normal" if index < total - 1  else "disabled")

    def _prev_page(self):
        if self.current > 0:
            self._show_page(self.current - 1)

    def _next_page(self):
        if self.current < len(self.pages) - 1:
            self._show_page(self.current + 1)

    # ── Status helpers ────────────────────────────────────────────────────────

    def _set_status(self, text: str, idle=False, error=False):
        self.status_var.set(text)
        if error:
            self.status_dot.configure(fg="#FF5F57")
        elif idle:
            self.status_dot.configure(fg="#28C840")
        else:
            self.status_dot.configure(fg="#FFBD2E")   # yellow = busy

    # ── Refresh flow ──────────────────────────────────────────────────────────

    def _trigger_refresh(self):
        """Called by button or hotkey. Runs export in a background thread."""
        self.refresh_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._set_status("Exporting from OneNote…")
        self._stop_refresh_event.clear()

        # Hide the window so it doesn't interfere with AppleScript
        self.root.withdraw()

        thread = threading.Thread(target=self._refresh_worker, daemon=True)
        thread.start()

    def _refresh_worker(self):
        """Background thread: run AppleScript, then render PDF."""
        try:
            TEMP_DIR.mkdir(parents=True, exist_ok=True)
            run_applescript()

            # Check if stop was requested
            if self._stop_refresh_event.is_set():
                self.root.after(0, lambda: self._set_status("Refresh cancelled", idle=True))
                self.root.after(0, lambda: self.stop_btn.configure(state="disabled"))
                self.root.after(0, lambda: self.refresh_btn.configure(state="normal"))
                self.root.after(0, self.root.deiconify)
                return

            # Back on main thread: render and show
            self.root.after(0, self._load_pages_from_pdf)

        except Exception as e:
            self.root.after(0, lambda: self._on_error(str(e)))

    def _load_pages_from_pdf(self):
        """Render the PDF and update the UI. Must run on main thread."""
        try:
            self._set_status("Rendering pages…")
            pil_images = render_pdf(TEMP_PDF, PAGE_W)

            # Store both original PIL images and PhotoImage objects
            self.pages_pil = pil_images  # Keep originals for rescaling
            self.pages = [ImageTk.PhotoImage(img) for img in pil_images]
            self.current = 0

            # Calculate PDF aspect ratio from first page
            if self.pages_pil:
                first_img = self.pages_pil[0]
                self.pdf_aspect_ratio = first_img.width / first_img.height

            self._show_page(0)
            self._set_status(f"Ready — {len(self.pages)} page(s)", idle=True)

        except Exception as e:
            self._on_error(str(e))

        finally:
            self.refresh_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.root.deiconify()        # bring overlay back
            self.root.attributes("-topmost", True)
            self.root.lift()             # Bring to front after rendering

    def _on_error(self, message: str):
        self._set_status("Error — see terminal for details", error=True)
        self.refresh_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.root.deiconify()
        print(f"[ERROR] {message}")

    # ── Window controls ───────────────────────────────────────────────────────

    def _toggle_collapse(self):
        """Toggle collapse/expand state: hide canvas and nav, show only title bar."""
        if self.collapsed_mode:
            # Expand: show canvas and nav
            self.canvas_bg.pack(fill="both", expand=True)
            self.nav.pack(fill="x")
            self.minimize_btn.configure(text="–")
            self.collapsed_mode = False
        else:
            # Collapse: hide canvas and nav
            self.canvas_bg.pack_forget()
            self.nav.pack_forget()
            self.minimize_btn.configure(text="+")
            self.collapsed_mode = True

    def _close_window(self):
        """Close the application."""
        self.root.quit()

    def _on_stop_refresh(self):
        """Stop the current refresh operation."""
        self._stop_refresh_event.set()
        self.stop_btn.configure(state="disabled")