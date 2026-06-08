import subprocess
import tkinter as tk

from config.config import PAGE_W, WINDOW_TITLE
from accessory import run_applescript, render_pdf


if __name__ == "__main__":
    # Entry point: create Tk root and run the preview overlay
    from window import PreviewOverlay

    root = tk.Tk()
    overlay = PreviewOverlay(root)
    root.mainloop()