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
from image_crop import ImageCropper, crop_uploaded_images

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB limit for multiple images

# Error handlers to return JSON instead of HTML
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "File(s) too large. Maximum total upload size is 500 MB."}), 413

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"error": "Internal server error. Please try with fewer or smaller images."}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request. Please check your input."}), 400

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

@app.route('/cropImages', methods=['POST'])
def crop_images():
    """Upload multiple images and get them cropped and zipped"""
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    try:
        # Validate that files are images
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'}
        for f in files:
            ext = Path(f.filename).suffix.lower()
            if ext not in valid_extensions:
                return jsonify({"error": f"Invalid file format: {f.filename}. Supported: {', '.join(valid_extensions)}"}), 400
        
        # Process images
        zip_bytes, filename = crop_uploaded_images(files)
        
        # Return ZIP file
        return send_file(
            BytesIO(zip_bytes),
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/getCropImagePreviews', methods=['POST'])
def get_crop_image_previews():
    """Generate previews for images with auto-crop detection - shows BEFORE and AFTER"""
    try:
        files = request.files.getlist('files')
        
        # Filter out empty files
        files = [f for f in files if f and f.filename]
        
        if not files:
            return jsonify({"error": "No files uploaded"}), 400

        from PIL import Image as PILImage
        
        file_previews = []
        cropper = ImageCropper(auto_detect=True, margin=5)
        
        for file_idx, f in enumerate(files):
            try:
                # Read image
                img_bytes = f.read()
                original_image = PILImage.open(BytesIO(img_bytes))
                
                # Get original image info
                orig_width, orig_height = original_image.size
                
                # Auto-detect crop bounds
                x, y, w, h = cropper.detect_content_bounds(original_image.copy())
                
                # Convert numpy int64 to Python int for JSON serialization
                x, y, w, h = int(x), int(y), int(w), int(h)
                
                # Crop the image
                crop_area = (x, y, x + w, y + h)
                cropped_image = original_image.crop(crop_area)
                cropped_width, cropped_height = cropped_image.size
                
                # Create original thumbnail preview
                orig_thumb = original_image.copy()
                orig_thumb.thumbnail((200, 200), PILImage.Resampling.LANCZOS)
                orig_buffer = BytesIO()
                if orig_thumb.mode in ('RGBA', 'LA', 'P'):
                    orig_thumb = orig_thumb.convert('RGB')
                orig_thumb.save(orig_buffer, format='JPEG', quality=70)
                orig_buffer.seek(0)
                orig_base64 = base64.b64encode(orig_buffer.getvalue()).decode('utf-8')
                
                # Create cropped thumbnail preview
                cropped_thumb = cropped_image.copy()
                cropped_thumb.thumbnail((200, 200), PILImage.Resampling.LANCZOS)
                cropped_buffer = BytesIO()
                if cropped_thumb.mode in ('RGBA', 'LA', 'P'):
                    cropped_thumb = cropped_thumb.convert('RGB')
                cropped_thumb.save(cropped_buffer, format='JPEG', quality=70)
                cropped_buffer.seek(0)
                cropped_base64 = base64.b64encode(cropped_buffer.getvalue()).decode('utf-8')
                
                file_previews.append({
                    'fileIndex': file_idx,
                    'fileName': f.filename,
                    'originalWidth': int(orig_width),
                    'originalHeight': int(orig_height),
                    'croppedWidth': int(cropped_width),
                    'croppedHeight': int(cropped_height),
                    'cropBounds': {'x': x, 'y': y, 'w': w, 'h': h},
                    'originalPreview': f'data:image/jpeg;base64,{orig_base64}',
                    'croppedPreview': f'data:image/jpeg;base64,{cropped_base64}'
                })
            except Exception as e:
                return jsonify({"error": f"Error reading {f.filename}: {str(e)}"}), 400
        
        return jsonify({
            'success': True,
            'files': file_previews
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/cropSingleImage', methods=['POST'])
def crop_single_image():
    """Crop a single image and return it for download"""
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        from PIL import Image as PILImage
        
        # Read image
        img_bytes = file.read()
        original_image = PILImage.open(BytesIO(img_bytes))
        
        # Auto-detect crop bounds
        cropper = ImageCropper(auto_detect=True, margin=2)
        x, y, w, h = cropper.detect_content_bounds(original_image.copy())
        
        # Crop the image
        crop_area = (x, y, x + w, y + h)
        cropped_image = original_image.crop(crop_area)
        
        # Convert to RGB if needed for JPEG
        if cropped_image.mode in ('RGBA', 'LA', 'P'):
            background = PILImage.new('RGB', cropped_image.size, (255, 255, 255))
            if cropped_image.mode == 'RGBA':
                background.paste(cropped_image, mask=cropped_image.split()[-1])
            else:
                background.paste(cropped_image)
            cropped_image = background
        elif cropped_image.mode != 'RGB':
            cropped_image = cropped_image.convert('RGB')
        
        # Save to buffer
        img_buffer = BytesIO()
        
        # Determine format from filename
        ext = Path(file.filename).suffix.lower()
        if ext in ['.png']:
            cropped_image.save(img_buffer, format='PNG')
            mimetype = 'image/png'
        else:
            cropped_image.save(img_buffer, format='JPEG', quality=95)
            mimetype = 'image/jpeg'
        
        img_buffer.seek(0)
        
        # Generate output filename
        base_name = Path(file.filename).stem
        out_ext = '.png' if ext == '.png' else '.jpg'
        output_filename = f"cropped_{base_name}{out_ext}"
        
        return send_file(
            img_buffer,
            mimetype=mimetype,
            as_attachment=True,
            download_name=output_filename
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/cropImageWithBounds', methods=['POST'])
def crop_image_with_bounds():
    """Crop a single image with custom bounds"""
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        # Get crop coordinates from request
        data = request.form
        x = int(data.get('x', 0))
        y = int(data.get('y', 0))
        width = int(data.get('width', 0))
        height = int(data.get('height', 0))

        # Save uploaded file temporarily
        temp_input = os.path.join(tempfile.gettempdir(), secure_filename(file.filename))
        file.save(temp_input)

        try:
            # Crop the image
            cropper = ImageCropper(auto_detect=False)
            output_path = cropper.crop_image(
                temp_input,
                crop_box=(x, y, width, height)
            )

            # Read and return the cropped image
            with open(output_path, 'rb') as f:
                img_data = f.read()

            # Cleanup
            os.remove(temp_input)
            os.remove(output_path)

            return send_file(
                BytesIO(img_data),
                mimetype='image/jpeg',
                as_attachment=True,
                download_name=f"cropped_{file.filename}"
            )
        finally:
            if os.path.exists(temp_input):
                os.remove(temp_input)

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)