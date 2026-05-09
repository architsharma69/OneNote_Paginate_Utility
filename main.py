import subprocess
import threading
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import fitz  # pymupdf
from PIL import Image, ImageTk

from config.config import APPLESCRIPT, TEMP_DIR, TEMP_PDF

# Control Applescript Execution

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
    

if __name__ == "__main__":
    run_applescript(TEMP_DIR, TEMP_PDF)