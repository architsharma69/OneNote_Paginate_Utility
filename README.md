# OneNote Paginate Utility

## The Problem
* OneNote is designed as an endless page - it does not offer a pagebreak feature.
    * It also doesn't display guidelines to indicate where the page will be split when the document is printed
    * For someone that uses OneNote to write assignments, they need to know how the pages will be split when they are converting their document to a PDF.
* As such, this is an important feature which is currently lacking.

## Solution
* Currently, one way to view page splits is to navigate to the print preview on OneNote. 
    * However, this is obviously impractical - the preview is a tiny window, and doesnt update in real time. It also doesn't show up to the viewer in real time.

### Solution Version 1:
* Export current page to temp PDF using `applescript` macro
* Convert PDF to image using `pdf2image`
* Create overlay on the side using `tkinter`
* Refresh the overlay
    * Using hotkeys with `keyboard`
    * On a timer