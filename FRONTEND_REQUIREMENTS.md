# Frontend Application - Extensions & Requirements

## ✅ Backend Extensions (Python)

All required Python packages are installed and verified:

| Package | Version | Purpose |
|---------|---------|---------|
| **Flask** | 3.1.2 | Web framework for serving the application |
| **pypdf** | 6.6.0 | PDF manipulation library |
| **PyPDF2** | 3.0.1 | Alternative PDF library (compatible) |
| **Werkzeug** | 3.1.5 | WSGI utilities for Flask |
| **gunicorn** | 23.0.0 | Production WSGI server |

## 🎨 Frontend Technologies

### Browser Requirements
- **Modern Web Browser** (Chrome, Firefox, Safari, Edge)
  - ES6 JavaScript support
  - HTML5 support
  - CSS3 Flexbox and Grid

### Frontend Features (No External Dependencies Needed)
- ✅ Pure HTML5
- ✅ Vanilla CSS3 (No CSS framework required)
- ✅ Vanilla JavaScript (No jQuery or other frameworks)
- ✅ Drag & Drop API (HTML5 native)
- ✅ File API (HTML5 native)
- ✅ Fetch API (modern browsers)

## 🚀 How to Run

### 1. Install Backend Dependencies
```bash
cd /workspaces/mergesplitPDF
pip install -r requirements.txt
```

### 2. Start the Flask Server
```bash
python main.py
```

### 3. Open in Browser
Navigate to: `http://127.0.0.1:8000`

## 📋 Frontend Features

### Merge Tab
- ✅ Drag & drop multiple PDFs
- ✅ Click to browse and select files
- ✅ Reorder PDFs (drag to reorder in merge order)
- ✅ Remove individual files
- ✅ Progress tracking during merge
- ✅ Automatic download of merged PDF

### Split Tab
- ✅ Drag & drop single PDF
- ✅ Split modes:
  - All pages (one PDF per page)
  - By page range
  - Even/Odd pages
- ✅ Progress tracking during split
- ✅ Automatic download as ZIP file

## 🎯 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Python** | 3.7+ | 3.10+ |
| **RAM** | 512 MB | 2 GB |
| **Disk** | 100 MB | 500 MB |
| **Browser** | Chrome 60+ | Chrome 90+, Firefox 88+, Safari 14+, Edge 90+ |

## ✨ Advanced Features Implemented

- **Responsive Design** - Works on mobile, tablet, desktop
- **Real-time Stats** - File count and total size display
- **Drag & Drop** - Intuitive file handling
- **Progress Bars** - Visual feedback during processing
- **Error Handling** - User-friendly error messages
- **Animations** - Smooth transitions and visual feedback
- **Status Notifications** - Success/error/info messages
- **Drag to Reorder** - Reorder PDFs before merging

## 🔧 Server Configuration

- **Host**: 0.0.0.0 (all interfaces)
- **Port**: 8000
- **Max File Size**: 200 MB per request
- **Debug Mode**: OFF (secure for production)

## 📦 Production Deployment

For production use, replace Flask's development server with gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

Options:
- `-w 4`: 4 worker processes
- `-b 0.0.0.0:8000`: Bind to all interfaces on port 8000
- `main:app`: Flask app instance

## ✅ Status: READY TO USE

All extensions and dependencies are installed. The frontend application is fully functional and ready to process PDFs!
