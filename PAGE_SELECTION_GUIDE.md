# 📑 Page Selection Feature

## Overview

The PDF Tools now include advanced page selection functionality for both **Merge** and **Split** operations, allowing users to have fine-grained control over which pages are processed.

---

## 🔀 Merge with Page Selection

### How It Works

1. **Upload PDFs**
   - Drag & drop or click to select multiple PDF files
   - Files appear in upload list with their order

2. **Click "📑 Select Pages"**
   - Modal opens showing all uploaded files
   - For each file, users can see page preview

3. **Select Pages from Each PDF**
   - View which pages from each PDF will be included
   - Option to select all pages or specific pages
   - Clear visual indication of selected pages

4. **Click "Continue with Selection"**
   - Proceeds with merge using only selected pages
   - Order is preserved from the merge order

5. **Review & Download**
   - Preview shows merged result
   - Download the merged PDF

### Example Flow

```
Step 1: Upload 3 PDFs
├── Document1.pdf (10 pages)
├── Document2.pdf (15 pages)
└── Document3.pdf (8 pages)

Step 2: Click "Select Pages"
├── Document1.pdf → Select pages 1-5
├── Document2.pdf → Select pages 1,3,5,7-9
└── Document3.pdf → Select pages 1-3

Step 3: Merge
└── Output: Merged PDF with selected pages in order

Result: merged.pdf with 15 selected pages
```

---

## ✂️ Split with Page Selection

### How It Works

1. **Upload PDF**
   - Drag & drop or click to select a single PDF file
   - File preview shows file size

2. **Click "📑 Select Pages"**
   - Modal opens with page grid
   - Shows all pages in the PDF

3. **Select Pages Using Two Methods:**

   **Method A: Grid Selection**
   - Visual grid of checkboxes (one per page)
   - Click to select/deselect individual pages
   - "Select All" and "Deselect All" buttons
   - Real-time count of selected pages

   **Method B: Page Range**
   - Enter page ranges in text format
   - Examples:
     - `1-5` → Pages 1 to 5
     - `1,5,10` → Pages 1, 5, and 10
     - `1-5, 10, 15-20` → Combined ranges
   - More efficient for large PDFs

4. **Click "Apply Selection"**
   - Splits PDF using only selected pages
   - Creates individual PDF for each selected page

5. **Review & Download**
   - Preview shows how many pages will be extracted
   - Download ZIP file with all selected pages as separate PDFs

### Example Flows

**Grid Method:**
```
PDF with 30 pages
│
├─ [☑] Page 1
├─ [☑] Page 2
├─ [☐] Page 3
├─ [☑] Page 4
├─ [☐] Page 5
...

Result: 3 PDFs (pages 1, 2, 4)
```

**Range Method:**
```
Input: "1-3, 5, 10-12"
       
Pages selected:
- Pages 1, 2, 3 (from range 1-3)
- Page 5 (individual)
- Pages 10, 11, 12 (from range 10-12)

Result: 7 PDFs (one per page)
```

---

## 🎯 Key Features

### Merge Page Selection
✅ **File-by-file selection** - Select specific pages from each PDF
✅ **Order preservation** - Merge order remains intact
✅ **Visual preview** - See which pages are being merged
✅ **Select all option** - Quick selection for entire files
✅ **Flexible workflow** - Change selections before final merge

### Split Page Selection
✅ **Grid interface** - Visual checkbox grid for easy selection
✅ **Range input** - Efficient text-based page range entry
✅ **Dual modes** - Switch between grid and range views
✅ **Real-time count** - See selected pages as you check
✅ **Smart parsing** - Supports complex page ranges

---

## 💡 Use Cases

### Merge Scenario 1: Combine Specific Chapters
```
Document: Report.pdf (30 pages)
Want: Chapter 1 (pages 1-5) + Chapter 3 (pages 15-20)

Solution:
1. Upload Report.pdf
2. Click "Select Pages"
3. Enter range: "1-5, 15-20"
4. Merge creates PDF with chapters 1 and 3
```

### Merge Scenario 2: Combine Multiple Documents
```
Files: A.pdf (10 pages), B.pdf (20 pages), C.pdf (15 pages)
Want: First 5 pages of each

Solution:
1. Upload all three files
2. Click "Select Pages"
3. For each file: Select pages 1-5
4. Merge creates 15-page combined document
```

### Split Scenario 1: Extract Specific Pages
```
Document: Report.pdf (50 pages)
Want: Pages 1, 5, 10-15, 20, 25

Solution:
1. Upload Report.pdf
2. Click "Select Pages"
3. Enter: "1, 5, 10-15, 20, 25"
4. Get 8 individual PDFs
```

### Split Scenario 2: Split Every Nth Page
```
Document: Book.pdf (200 pages)
Want: Pages 1, 25, 50, 75, 100, 125, 150, 175, 200

Solution:
1. Upload Book.pdf
2. Click "Select Pages" → Range tab
3. Enter: "1, 25, 50, 75, 100, 125, 150, 175, 200"
4. Get 9 PDFs at intervals
```

---

## 🚀 Technical Details

### Page Selection Storage
- Selections stored in JavaScript variables
- `mergePageSelections` - For merge operations
- `splitPageSelections` - For split operations
- Passed to backend for processing

### Range Parsing
Page ranges are parsed with the `parsePageRange()` function:
- Supports individual pages: `5`
- Supports ranges: `1-10`
- Supports combinations: `1-5, 10, 15-20`
- Automatically sorts and deduplicates

### Modal Management
- Page selector opens in modal dialog
- Can be closed with X button or apply selection
- Selection state persists until operation completes

---

## 🎨 UI Components

### Merge Page Selector Modal
```
┌─────────────────────────────────────┐
│ 📄 Select Pages to Merge         ✕  │
├─────────────────────────────────────┤
│ Select pages from each PDF          │
│                                     │
│ Document1.pdf                       │
│ [Select All Pages]                  │
│                                     │
│ Document2.pdf                       │
│ [Select All Pages]                  │
│                                     │
│ [Deselect All] [Continue with...]  │
└─────────────────────────────────────┘
```

### Split Page Selector Modal
```
┌─────────────────────────────────────┐
│ ✂️ Select Pages to Split         ✕  │
├─────────────────────────────────────┤
│ [Page Grid] [Page Range]            │
│                                     │
│ [☑] Page 1   [☑] Page 2            │
│ [☑] Page 3   [☐] Page 4            │
│ [☑] Page 5   ...                   │
│                                     │
│ [Select All] [Deselect All]         │
│ [Apply Selection]                   │
└─────────────────────────────────────┘
```

---

## 📱 Responsive Design

- **Desktop**: Full grid layout with all controls visible
- **Tablet**: Optimized grid with adjusted sizing
- **Mobile**: Single column, scrollable interface
- Modal is centered and responsive
- Touch-friendly checkbox sizes

---

## ⚙️ Backend Integration (Future)

Current implementation is frontend with UI ready for backend:

```python
# Future backend endpoint
POST /merge
{
    "files": [...],
    "selections": {
        "file1": [1, 2, 3],
        "file2": [1, 5, 10-15],
        "file3": [1-5]
    }
}

POST /split
{
    "file": "...",
    "pages": [1, 5, 10-15, 20]
}
```

---

## 🔄 Workflow Summary

### Merge Flow
```
Upload PDFs
    ↓
[Optional] Click "Select Pages"
    ↓
Click "Merge PDFs"
    ↓
Review Preview
    ↓
Download merged.pdf
```

### Split Flow
```
Upload PDF
    ↓
[Optional] Click "Select Pages"
    ├─ Grid Method: Check individual pages
    └─ Range Method: Enter page ranges
    ↓
Click "Split PDF"
    ↓
Review Preview
    ↓
Download split_pages.zip
```

---

## ✨ Benefits

✅ **Precision Control** - Process exactly the pages you need
✅ **Time Saving** - No need to manually extract/edit before processing
✅ **Flexibility** - Works with files of any size
✅ **User Friendly** - Intuitive modal interface
✅ **Error Reduction** - Visual feedback prevents mistakes
✅ **Professional** - Advanced feature for power users

---

## 🎓 Tips & Tricks

1. **For Grid Selection**: Use "Select All" button for quick full-page selection
2. **For Range Entry**: Order doesn't matter - they'll be sorted automatically
3. **Deduplication**: Entering "1-5, 3, 4" will only include pages 1-5 once
4. **Large PDFs**: Use range input instead of grid for faster selection
5. **Copy-Paste**: You can copy page ranges from documents and paste directly

---

**Version**: 1.0
**Status**: ✅ Live and Ready
**Last Updated**: January 9, 2026
