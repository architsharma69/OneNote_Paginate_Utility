from pathlib import Path
from pynput import keyboard

CONFIG_PATH = Path(__file__).parent
ROOT_PATH = CONFIG_PATH.parent

TEMP_DIR     = ROOT_PATH / "temp_files"
TEMP_PDF     = TEMP_DIR / "preview.pdf"

APPLESCRIPT  = CONFIG_PATH / "applescripts" / "Save_temp_pdf_text.txt"

WINDOW_W     = 360          # overlay window width in pixels
PAGE_W       = 300          # rendered page width inside the window
WINDOW_TITLE = "PDF Preview"

# Hotkey: Cmd+Shift+R  (use Key.ctrl instead of Key.cmd on Windows)
HOTKEY_MODS  = {keyboard.Key.cmd, keyboard.Key.shift}
HOTKEY_KEY   = keyboard.KeyCode.from_char('r')
