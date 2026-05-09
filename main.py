import subprocess
import threading
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import fitz  # pymupdf
from PIL import Image, ImageTk

from config.config import APPLESCRIPT

# Control Applescript Execution

def run_applescript():
    """
    We want to run the applescript file which saves to temporary PDF
    """
    result = subprocess.run(
        ["osascript", str(APPLESCRIPT)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"AppleScript failed:\n{result.stderr}")
