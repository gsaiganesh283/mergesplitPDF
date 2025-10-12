import tkinter as tk
from tkinter import filedialog, messagebox
from pypdf import PdfMerger


def run_merger(parent=None):
    """Create and run the Merge PDF GUI. If parent is provided it will create a Toplevel window; otherwise a new Tk root is used.

    Returns the main window object (Tk or Toplevel).
    """
    is_root = parent is None
    root = tk.Tk() if is_root else tk.Toplevel(parent)
    root.title("PDF Merger")
    root.geometry("500x400")

    listbox = tk.Listbox(root, width=70, height=15)
    listbox.pack(pady=20)

    def select_files():
        files = filedialog.askopenfilenames(
            title="Select PDF files",
            filetypes=[("PDF Files", "*.pdf")],
            defaultextension=".pdf"
        )
        listbox.delete(0, tk.END)
        for file in files:
            listbox.insert(tk.END, file)

    def merge_pdfs():
        files = listbox.get(0, tk.END)
        if not files:
            messagebox.showwarning("No Files", "Please select PDF files to merge.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save Merged PDF",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if not output_path:
            return

        try:
            merger = PdfMerger()
            for pdf in files:
                merger.append(pdf)
            merger.write(output_path)
            merger.close()
            messagebox.showinfo("Success", f"Merged PDF saved to:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to merge PDFs:\n{e}")

    def clear_list():
        listbox.delete(0, tk.END)

    frame = tk.Frame(root)
    frame.pack(pady=10)

    btn_select = tk.Button(frame, text="Select PDF Files", command=select_files)
    btn_select.pack(side=tk.LEFT, padx=10)

    btn_merge = tk.Button(frame, text="Merge PDFs", command=merge_pdfs)
    btn_merge.pack(side=tk.LEFT, padx=10)

    bottom_frame = tk.Frame(root)
    bottom_frame.pack(side=tk.BOTTOM, pady=10)

    btn_clear = tk.Button(bottom_frame, text="Clear", command=clear_list)
    btn_clear.pack()

    if is_root:
        root.mainloop()

    return root


if __name__ == "__main__":
    run_merger()