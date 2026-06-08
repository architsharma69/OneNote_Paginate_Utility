import subprocess
from pathlib import Path
import fitz  # pymupdf
from PIL import Image

from config.config import APPLESCRIPT, TEMP_DIR, TEMP_PDF


# Control Applescript Execution ---------------------------------------------------------------------

def run_applescript():
    """Run the AppleScript to export the current OneNote page as TEMP_PDF."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        ["osascript", str(APPLESCRIPT), str(TEMP_DIR), str(TEMP_PDF)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"AppleScript failed:\n{result.stderr}")


# Render temp PDF into PIL images -------------------------------------------------------------------

def render_pdf(pdf_path: Path, width: int) -> list[Image.Image]:
    """Convert PDF pages to PIL images scaled to the given width (200 DPI)."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(str(pdf_path))
    resized = []
    for page in doc:
        mat = fitz.Matrix(400 / 72, 400 / 72)   # 400 DPI
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        ratio = width / img.width
        height = int(img.height * ratio)
        resized.append(img.resize((width, height), Image.LANCZOS))

    return resized
