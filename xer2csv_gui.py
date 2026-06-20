"""
XER to CSV Converter - Desktop App

A simple window-based front-end for the xer2csv package.
No command line needed: pick your .xer files, pick an output folder, click Convert.

Run it by double-clicking this file, or with:  python xer2csv_gui.py
"""

import os
import sys
import queue
import threading

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Make sure the bundled xer2csv package can be imported no matter where the
# app is launched from (double-click, terminal, PyInstaller bundle, etc.).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from xer2csv import XerToCsvConverter


class ConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("XER to CSV Converter")
        self.root.geometry("680x540")
        self.root.minsize(560, 460)

        # State
        self.xer_files = []          # list of full paths to .xer files
        self.output_dir = tk.StringVar()
        self.clean_csv = tk.BooleanVar(value=True)  # drop the extra row-number column
        self.log_queue = queue.Queue()
        self.is_running = False

        self._build_ui()
        self._poll_log_queue()

    # ----------------------------------------------------------------- UI build
    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # --- Title ---
        header = ttk.Label(
            self.root,
            text="XER to CSV Converter",
            font=("Segoe UI", 16, "bold"),
        )
        header.pack(anchor="w", padx=12, pady=(12, 0))

        subtitle = ttk.Label(
            self.root,
            text="Add your .xer files, choose where to save, then click Convert.",
            foreground="#555555",
        )
        subtitle.pack(anchor="w", padx=12, pady=(0, 8))

        # --- File selection area ---
        files_frame = ttk.LabelFrame(self.root, text="1. XER files to convert")
        files_frame.pack(fill="both", expand=True, **pad)

        list_container = ttk.Frame(files_frame)
        list_container.pack(fill="both", expand=True, padx=8, pady=8)

        self.file_list = tk.Listbox(list_container, selectmode=tk.EXTENDED, height=8)
        self.file_list.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            list_container, orient="vertical", command=self.file_list.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.file_list.config(yscrollcommand=scrollbar.set)

        btn_row = ttk.Frame(files_frame)
        btn_row.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(btn_row, text="Add files...", command=self.add_files).pack(side="left")
        ttk.Button(btn_row, text="Add folder...", command=self.add_folder).pack(
            side="left", padx=6
        )
        ttk.Button(btn_row, text="Remove selected", command=self.remove_selected).pack(
            side="left"
        )
        ttk.Button(btn_row, text="Clear all", command=self.clear_files).pack(
            side="left", padx=6
        )

        # --- Output folder ---
        out_frame = ttk.LabelFrame(self.root, text="2. Save CSV files to")
        out_frame.pack(fill="x", **pad)

        out_row = ttk.Frame(out_frame)
        out_row.pack(fill="x", padx=8, pady=8)
        self.out_entry = ttk.Entry(out_row, textvariable=self.output_dir)
        self.out_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(out_row, text="Browse...", command=self.choose_output).pack(
            side="left", padx=(6, 0)
        )

        ttk.Checkbutton(
            out_frame,
            text="Clean output (leave off the extra row-number column)",
            variable=self.clean_csv,
        ).pack(anchor="w", padx=8, pady=(0, 8))

        # --- Convert button + progress ---
        action_row = ttk.Frame(self.root)
        action_row.pack(fill="x", **pad)
        self.convert_btn = ttk.Button(
            action_row, text="Convert", command=self.start_conversion
        )
        self.convert_btn.pack(side="left")
        self.progress = ttk.Progressbar(action_row, mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True, padx=(10, 0))

        # --- Status log ---
        log_frame = ttk.LabelFrame(self.root, text="Status")
        log_frame.pack(fill="both", expand=True, **pad)
        self.log_text = tk.Text(log_frame, height=7, wrap="word", state="disabled")
        self.log_text.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        log_scroll = ttk.Scrollbar(
            log_frame, orient="vertical", command=self.log_text.yview
        )
        log_scroll.pack(side="right", fill="y", pady=8, padx=(0, 8))
        self.log_text.config(yscrollcommand=log_scroll.set)

        self.log("Ready. Add one or more .xer files to begin.")

    # ----------------------------------------------------------- file selection
    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select XER files",
            filetypes=[("XER files", "*.xer"), ("All files", "*.*")],
        )
        self._add_paths(paths)

    def add_folder(self):
        folder = filedialog.askdirectory(title="Select a folder containing .xer files")
        if not folder:
            return
        found = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith(".xer")
        ]
        if not found:
            messagebox.showinfo(
                "No XER files", "That folder doesn't contain any .xer files."
            )
            return
        self._add_paths(found)
        # Helpfully default the output folder if it's still empty.
        if not self.output_dir.get():
            self.output_dir.set(os.path.join(folder, "csv_output"))

    def _add_paths(self, paths):
        added = 0
        for p in paths:
            if p not in self.xer_files:
                self.xer_files.append(p)
                self.file_list.insert(tk.END, p)
                added += 1
        if added:
            self.log(f"Added {added} file(s). Total queued: {len(self.xer_files)}.")

    def remove_selected(self):
        for index in reversed(self.file_list.curselection()):
            self.file_list.delete(index)
            del self.xer_files[index]

    def clear_files(self):
        self.file_list.delete(0, tk.END)
        self.xer_files.clear()

    def choose_output(self):
        folder = filedialog.askdirectory(title="Choose where to save the CSV files")
        if folder:
            self.output_dir.set(folder)

    # --------------------------------------------------------------- conversion
    def start_conversion(self):
        if self.is_running:
            return
        if not self.xer_files:
            messagebox.showwarning("No files", "Add at least one .xer file first.")
            return
        out = self.output_dir.get().strip()
        if not out:
            messagebox.showwarning(
                "No output folder", "Choose a folder to save the CSV files."
            )
            return

        self.is_running = True
        self.convert_btn.config(state="disabled")
        self.progress.config(maximum=len(self.xer_files), value=0)
        self.log("")
        self.log("Starting conversion.")

        # Run the work off the UI thread so the window stays responsive.
        worker = threading.Thread(
            target=self._convert_worker,
            args=(list(self.xer_files), out, self.clean_csv.get()),
            daemon=True,
        )
        worker.start()

    def _convert_worker(self, files, output_root, clean):
        succeeded, failed = 0, 0
        for path in files:
            name = os.path.basename(path)
            try:
                self.log(f"Converting {name}.")
                converter = XerToCsvConverter()
                converter.read_xer(path)

                stem = os.path.splitext(name)[0]
                subdir = os.path.join(output_root, stem)
                converter.convert_to_csv(subdir, include_index=not clean)

                table_count = len(converter.tables)
                self.log(f"Saved {table_count} CSV file(s) to {subdir}.")
                succeeded += 1
            except Exception as exc:  # Keep going even if one file is malformed.
                failed += 1
                self.log(f"Could not convert {name}. Reason: {exc}")
            finally:
                self.log_queue.put(("progress", 1))

        self.log("Conversion finished.")
        self.log(f"{succeeded} file(s) converted, {failed} failed.")
        self.log_queue.put(("finished", (succeeded, failed, output_root)))

    # --------------------------------------------------------- thread-safe log
    def log(self, message):
        self.log_queue.put(("log", message))

    def _poll_log_queue(self):
        try:
            while True:
                kind, payload = self.log_queue.get_nowait()
                if kind == "log":
                    self._append_log(payload)
                elif kind == "progress":
                    self.progress["value"] += payload
                elif kind == "finished":
                    self._on_finished(*payload)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_log_queue)

    def _append_log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def _on_finished(self, succeeded, failed, output_root):
        self.is_running = False
        self.convert_btn.config(state="normal")
        if failed == 0:
            if messagebox.askyesno(
                "Conversion complete",
                f"Converted {succeeded} file(s) successfully.\n\nOpen the output folder?",
            ):
                self._open_folder(output_root)
        else:
            messagebox.showwarning(
                "Finished with errors",
                f"Succeeded: {succeeded}\nFailed: {failed}\n\nSee the Status box for details.",
            )

    @staticmethod
    def _open_folder(path):
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception:
            pass


def main():
    root = tk.Tk()
    try:
        # Slightly nicer native look where available.
        ttk.Style().theme_use("vista" if sys.platform.startswith("win") else "clam")
    except tk.TclError:
        pass
    ConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
