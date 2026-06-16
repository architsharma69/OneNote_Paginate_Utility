# OneNote Paginate Utility

## The Problem
* OneNote is designed as an endless page - it does not offer a pagebreak feature.
    * It also doesn't display guidelines to indicate where the page will be split when the document is printed
    * For someone that uses OneNote to write assignments, they need to know how the pages will be split when they are converting their document to a PDF.
* As such, this is an important feature which is currently lacking.

## Solution
* Currently, one way to view page splits is to navigate to the print preview on OneNote. 
    * However, this is obviously impractical - the preview is a tiny window, and doesnt update in real time. It also doesn't show up to the viewer in real time.

### Solution Template:
* Export current page to temp PDF using `applescript` macro
* Convert PDF to image using `pymupdf`
* Create overlay on the side using `tkinter`
* Refresh the overlay
    * Using hotkeys with `keyboard`
    * On a timer

### Version 1:
Workflow & Functionalities:
* Controlled by the orchestrator, `main.py`
    * `Save_temp_pdf_text.txt` applescript saves as temp PDF
    * Convert to PIL images
    * Create resizable overlay using `tkinter`
        * Has `navigation`, `refresh`, `stop` functionalities
* Currently triggered by a macbook `shortcut`, which runs a simple shell script to trigger `main.py` based on keystroke

Problems to work on:
* PIL images still have terrible quality, changing DPI does not change image quality. Consider changing rendering method