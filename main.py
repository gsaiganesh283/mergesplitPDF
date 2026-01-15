from flask import Flask, request, send_file, render_template, redirect, url_for, jsonify
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from docx import Document
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from copy import deepcopy
import tempfile
import os
from werkzeug.utils import secure_filename
from pathlib import Path
from pdf2image import convert_from_bytes
import base64
from io import BytesIO

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB limit (adjust)

@app.route('/')
def index():
    return render_template('index.html')  # optional simple form

@app.route('/getPagePreviews', methods=['POST'])
def get_page_previews():
    """Generate thumbnail previews for all pages in a PDF"""
    f = request.files.get('file')
    if not f:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        # Read PDF and get page count
        pdf_bytes = f.read()
        reader = PdfReader(BytesIO(pdf_bytes))
        page_count = len(reader.pages)
        
        # Convert PDF pages to images (limit to first 50 pages for performance)
        max_pages = min(page_count, 50)
        images = convert_from_bytes(pdf_bytes, first_page=1, last_page=max_pages, dpi=100)
        
        # Convert images to base64
        previews = []
        for i, image in enumerate(images, start=1):
            # Resize image for faster loading
            image.thumbnail((200, 280), image.Resampling.LANCZOS)
            
            # Convert to base64
            img_buffer = BytesIO()
            image.save(img_buffer, format='JPEG', quality=70)
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            
            previews.append({
                'page': i,
                'image': f'data:image/jpeg;base64,{img_base64}'
            })
        
        return jsonify({
            'success': True,
            'pageCount': page_count,
            'previews': previews
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/getMergePagePreviews', methods=['POST'])
def get_merge_page_previews():
    """Generate preview thumbnails for each file in merge operation"""
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    try:
        file_previews = []
        
        for file_idx, f in enumerate(files):
            pdf_bytes = f.read()
            reader = PdfReader(BytesIO(pdf_bytes))
            page_count = len(reader.pages)
            
            # Get first page as preview
            if page_count > 0:
                images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1, dpi=100)
                image = images[0]
                image.thumbnail((150, 200), image.Resampling.LANCZOS)
                
                img_buffer = BytesIO()
                image.save(img_buffer, format='JPEG', quality=70)
                img_buffer.seek(0)
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                
                file_previews.append({
                    'fileIndex': file_idx,
                    'fileName': f.filename,
                    'pageCount': page_count,
                    'firstPageImage': f'data:image/jpeg;base64,{img_base64}'
                })
        
        return jsonify({
            'success': True,
            'files': file_previews
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

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

@app.route('/mergeWord', methods=['POST'])
def merge_word():
    """Merge multiple Word documents into a single document, preserving exact formatting and styles"""
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    try:
        # Read the first document as the base to preserve all styles and settings
        first_doc_bytes = files[0].read()
        merged_doc = Document(BytesIO(first_doc_bytes))

        # Append remaining documents
        for file_idx, f in enumerate(files[1:], start=1):
            try:
                # Read the Word document
                doc_bytes = f.read()
                doc = Document(BytesIO(doc_bytes))
                
                # Add page break before appending next document
                last_paragraph = merged_doc.add_page_break()
                
                # Copy all body elements from the source document
                # Use XML cloning to preserve exact formatting
                for element in doc.element.body:
                    # Use deepcopy to properly clone XML elements with all attributes and formatting
                    try:
                        # Clone the element with all its properties
                        cloned_element = deepcopy(element)
                        merged_doc.element.body.append(cloned_element)
                    except Exception as clone_err:
                        # If cloning fails, try alternative method
                        # Convert to string and parse to ensure clean copy
                        element_xml = OxmlElement(element.tag)
                        element_xml._element = deepcopy(element)
                        merged_doc.element.body.append(element)
                
                # Add page break after each merged document
                merged_doc.add_page_break()
                    
            except Exception as e:
                return jsonify({"error": f"Error processing {f.filename}: {str(e)}"}), 400

        # Save the merged document to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as out_tmp:
            merged_doc.save(out_tmp.name)
            out_tmp.close()
            return send_file(out_tmp.name, as_attachment=True, download_name="merged.docx")

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/getMergeWordPagePreviews', methods=['POST'])
def get_merge_word_page_previews():
    """Generate preview info for each Word document in merge operation"""
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    try:
        file_previews = []
        
        for file_idx, f in enumerate(files):
            try:
                doc = Document(f.stream)
                
                # Extract preview text (first 100 characters or first few lines)
                preview_text = ""
                char_count = 0
                max_chars = 100
                
                for paragraph in doc.paragraphs:
                    if char_count >= max_chars:
                        break
                    para_text = paragraph.text
                    if para_text:
                        preview_text += para_text + " "
                        char_count += len(para_text)
                
                # Count paragraphs and tables
                paragraph_count = len(doc.paragraphs)
                table_count = len(doc.tables)
                
                file_previews.append({
                    'fileIndex': file_idx,
                    'fileName': f.filename,
                    'paragraphs': paragraph_count,
                    'tables': table_count,
                    'preview': preview_text.strip()[:100] + ("..." if len(preview_text) > 100 else "")
                })
            except Exception as e:
                return jsonify({"error": f"Error reading {f.filename}: {str(e)}"}), 400
        
        return jsonify({
            'success': True,
            'files': file_previews
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)