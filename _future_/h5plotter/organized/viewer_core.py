# hdf_viewer/viewer_core.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import h5py
from plot_tools import plot_heatmap
from interactivity import enable_click_interaction

class HDF2DViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HDF Viewer (2D)")
        self.geometry("300x200")
        self.filename = None
        self.datasets = []
        self.current_figure = None
        self.cross_section_figure = None
        self.colormap = tk.StringVar(value="seismic")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        ttk.Button(self, text="Open HDF File", command=self.open_file).pack(pady=10)

        self.dataset_label = ttk.Label(self, text="Select 2D Dataset:")
        self.dataset_combo = ttk.Combobox(self, state="readonly")

        ttk.Label(self, text="Select Colormap:").pack()
        self.colormap_combo = ttk.Combobox(self, textvariable=self.colormap, state="readonly")
        self.colormap_combo['values'] = [
            'seismic', 'plasma', 'inferno', 'magma', 'cividis',
            'Greys', 'viridis', 'jet', 'rainbow', 'coolwarm'
        ]
        self.colormap_combo.current(0)
        self.colormap_combo.pack()

        self.plot_button = ttk.Button(self, text="Plot Heatmap", command=self.plot_data)

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

    def plot_data(self):
        dataset_name = self.dataset_combo.get()
        if not dataset_name:
            return

        try:
            with h5py.File(self.filename, 'r') as f:
                data = f[dataset_name][:]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load dataset: {e}")
            return

        if self.current_figure:
            from matplotlib import pyplot as plt
            plt.close(self.current_figure)

        cmap = self.colormap.get()
        self.current_figure = plot_heatmap(data, dataset_name, cmap=cmap)
        enable_click_interaction(self.current_figure, data, self)

    def on_close(self):
        from matplotlib import pyplot as plt
        if self.current_figure:
            plt.close(self.current_figure)
        if self.cross_section_figure:
            plt.close(self.cross_section_figure)
        self.destroy()
