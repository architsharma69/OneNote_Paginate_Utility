import subprocess
import threading
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import fitz  # pymupdf
from PIL import Image, ImageTk

from config.config import APPLESCRIPT, TEMP_DIR, TEMP_PDF, PAGE_W

# Control Applescript Execution ---------------------------------------------------------------------

def run_applescript(output_folder, output_file):
    """
    We want to run the applescript file which saves to temporary PDF
    Here we also inject the output directory and filename into the applescript
    """
    # Create output_folder if necessary
    Path.mkdir(output_folder, exist_ok=True)

    result = subprocess.run(
        ["osascript", str(APPLESCRIPT), output_folder, output_file],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"AppleScript failed:\n{result.stderr}")
    

# Render temp PDF into PIL images -------------------------------------------------------------------

def render_pdf(pdf_path: Path, width: int) -> list[Image.Image]:
    """Convert PDF pages to PIL images scaled to the given width."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(str(pdf_path))
    resized = []
    for page in doc:
        mat = fitz.Matrix(150/72, 150/72)   # 150 DPI
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        ratio  = width / img.width
        height = int(img.height * ratio)
        resized.append(img.resize((width, height), Image.LANCZOS))

    return resized


# All Component Tests -------------------------------------------------------------------------------
def render_pdf_test(pdf_path: Path, width: int):
    images = render_pdf(pdf_path, width)
    for i, img in enumerate(images):
        img.save(f"page_{i+1}.png")



if __name__ == "__main__":
   render_pdf_test(TEMP_PDF, PAGE_W)