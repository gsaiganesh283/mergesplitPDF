from flask import Flask, request, send_file, render_template, redirect, url_for
from pypdf import PdfMerger, PdfReader, PdfWriter
import tempfile
import os
import sys
from werkzeug.utils import secure_filename
from pathlib import Path

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

app = Flask(__name__, 
            static_folder=resource_path('static'), 
            template_folder=resource_path('templates'))
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB limit (adjust)

@app.route('/')
def index():
    return render_template('index.html')  # optional simple form

@app.route('/merge', methods=['POST'])
def merge():
    files = request.files.getlist('files')
    if not files:
        return "No files uploaded", 400

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as out_tmp:
        merger = PdfMerger()
        for f in files:
            # read file stream directly
            merger.append(f.stream)
        merger.write(out_tmp.name)
        merger.close()
        out_tmp.close()
        return send_file(out_tmp.name, as_attachment=True, download_name="merged.pdf")

@app.route('/split', methods=['POST'])
def split():
    f = request.files.get('file')
    if not f:
        return "No file uploaded", 400

    # create temp folder for pages
    tmpdir = tempfile.mkdtemp()
    reader = PdfReader(f.stream)
    paths = []
    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        out_path = Path(tmpdir) / f"page_{i}.pdf"
        with open(out_path, "wb") as out_f:
            writer.write(out_f)
        paths.append(out_path)

    # For simplicity, return first page or zip them. Here we return zip:
    import zipfile
    zip_path = Path(tempfile.gettempdir()) / (secure_filename(f.filename) + "_pages.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        for p in paths:
            zf.write(p, arcname=p.name)

    # cleanup split files (optional) - careful with errors
    for p in paths:
        try:
            os.remove(p)
        except Exception:
            pass

    return send_file(zip_path, as_attachment=True, download_name="pages.zip")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)