import tkinter as tk
from tkinter import filedialog, messagebox
import os
from pypdf import PdfReader, PdfWriter


def run_split_ui(parent=None):
    """Create and run the Split PDF UI. If parent is None, a standalone window is created.

    Returns the window object.
    """
    is_root = parent is None
    win = tk.Tk() if is_root else tk.Toplevel(parent)
    win.title("Split PDF")
    win.geometry("420x200")

    def select_and_split():
        pdf_path = filedialog.askopenfilename(title="Select PDF to split", filetypes=[("PDF Files", "*.pdf")])
        if not pdf_path:
            return

        # Determine user's Downloads folder
        downloads = None
        if os.name == 'nt':
            userprofile = os.environ.get('USERPROFILE')
            if userprofile:
                downloads = os.path.join(userprofile, 'Downloads')
        if not downloads:
            home = os.path.expanduser('~')
            downloads = os.path.join(home, 'Downloads')

        # Create a folder inside Downloads with the PDF base name
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        target_dir = os.path.join(downloads, base_name)
        os.makedirs(target_dir, exist_ok=True)

        try:
            reader = PdfReader(pdf_path)
            for i, page in enumerate(reader.pages, start=1):
                writer = PdfWriter()
                writer.add_page(page)
                out_path = os.path.join(target_dir, f"page_{i}.pdf")
                with open(out_path, "wb") as f:
                    writer.write(f)
            messagebox.showinfo("Success", f"Split into {len(reader.pages)} files.\nFiles saved to:\n{target_dir}\nFolder Create with File Name and saved in Downloads")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to split PDF:\n{e}")

    lbl = tk.Label(win, text="Select a PDF and an output folder to split each page into separate files.")
    lbl.pack(pady=10, padx=10)

    btn_select_split = tk.Button(win, text="Select & Split", command=select_and_split)
    btn_select_split.pack(pady=10)

    if is_root:
        win.mainloop()

    return win


if __name__ == "__main__":
    run_split_ui()
