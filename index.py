import tkinter as tk
from tkinter import messagebox

from mpdf import run_merger
from split import run_split_ui


def launch_merger():
    try:
        run_merger(parent=root)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open merger:\n{e}")


def open_split_ui():
    try:
        run_split_ui(parent=root)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open split UI:\n{e}")


root = tk.Tk()
root.title("PDF Tools")
root.geometry("300x150")

frame = tk.Frame(root)
frame.pack(expand=True)

btn_merge = tk.Button(frame, text="Merge PDF", width=20, command=launch_merger)
btn_merge.pack(pady=10)

btn_split = tk.Button(frame, text="Split PDF", width=20, command=open_split_ui)
btn_split.pack(pady=5)

root.mainloop()
