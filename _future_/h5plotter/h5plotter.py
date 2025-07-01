# -*- coding: utf-8 -*-
"""
Created on Tue Jul  1 16:07:12 2025

@author: user
"""

import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import h5py
import numpy as np
import matplotlib.pyplot as plt

class HDF2DViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("2D HDF Viewer")
        self.geometry("400x200")
        self.filename = None
        self.datasets = []
        self.current_figure = None  # Track the heatmap window

        self.protocol("WM_DELETE_WINDOW", self.on_close)  # Handle window close

        ttk.Button(self, text="Open HDF File", command=self.open_file).pack(pady=10)
        self.dataset_label = ttk.Label(self, text="Select 2D Dataset:")
        self.dataset_combo = ttk.Combobox(self, state="readonly")
        self.plot_button = ttk.Button(self, text="Plot Heatmap", command=self.plot_heatmap)

    def open_file(self):
        self.filename = filedialog.askopenfilename(
            title="Select HDF5 file", filetypes=[("HDF5 files", "*.hdf *.h5")]
        )
        if not self.filename:
            return

        try:
            with h5py.File(self.filename, 'r') as f:
                self.datasets = [key for key in f.keys() if f[key].ndim == 2]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {e}")
            return

        if not self.datasets:
            messagebox.showwarning("No 2D Data", "No 2D datasets found in the file.")
            return

        self.dataset_label.pack()
        self.dataset_combo['values'] = self.datasets
        self.dataset_combo.current(0)
        self.dataset_combo.pack()
        self.plot_button.pack(pady=10)

    def plot_heatmap(self):
        dataset_name = self.dataset_combo.get()
        if not dataset_name:
            return

        try:
            with h5py.File(self.filename, 'r') as f:
                data = f[dataset_name][:]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load dataset: {e}")
            return

        # Close old figure if still open
        if self.current_figure:
            plt.close(self.current_figure)

        # Create and store new figure
        self.current_figure = plt.figure()
        ax = self.current_figure.add_subplot(111)
        img = ax.imshow(data, aspect='auto', origin='lower', cmap='viridis')
        self.current_figure.colorbar(img, label='Value')
        ax.set_title(f"Heatmap of {dataset_name}")
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        self.current_figure.tight_layout()
        self.current_figure.show()

    def on_close(self):
        if self.current_figure:
            plt.close(self.current_figure)
        self.destroy()


if __name__ == "__main__":
    app = HDF2DViewer()
    app.mainloop()