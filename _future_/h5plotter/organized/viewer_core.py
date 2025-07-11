# hdf_viewer/viewer_core.py   - STABLE
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import h5py
import numpy as np
from matplotlib import pyplot as plt
from plot_tools import plot_heatmap
from interactivity import enable_click_interaction

class HDF2DViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HDview")
        self.geometry("250x400")
        self.filename = None
        self.datasets = []
        self.original_data = None
        self.processed_data = None
        self.colormap = tk.StringVar(value="seismic")
        self.reverse_cmap = tk.BooleanVar(value=False)
        self.processing_window = None
        self.operation_history = []

        self.available_operations = {
            "Abs": (tk.BooleanVar(), lambda d: np.abs(d)),
            "Scale20": (tk.BooleanVar(), lambda d: d*20),
            "Log10": (tk.BooleanVar(), lambda d: np.log(np.where(d > 0, d, np.nan))),
            "Sqrt": (tk.BooleanVar(), lambda d: np.sqrt(np.clip(d, a_min=0, a_max=None))),
        }

        self.fig = None
        self.ax = None
        self.im = None
        self.cross_section_figure = None
        self.cross_section_axes = None
        self.last_click = None

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        ttk.Button(self, text="Open HDF File", command=self.open_file).pack(pady=10)

        self.dataset_label = ttk.Label(self, text="Select 2D Dataset:")
        self.dataset_combo = ttk.Combobox(self, state="readonly")

        ttk.Label(self, text="Select Colormap:").pack()
        self.colormap_combo = ttk.Combobox(self, textvariable=self.colormap, state="readonly")
        self.colormap_combo['values'] = [
            'viridis', 'plasma', 'inferno', 'magma', 'cividis',
            'Greys', 'seismic', 'jet', 'rainbow', 'coolwarm'
        ]
        self.colormap_combo.current(0)
        self.colormap_combo.pack()

        self.reverse_check = ttk.Checkbutton(self, text="Reverse Colormap", variable=self.reverse_cmap)
        self.reverse_check.pack()

        self.plot_button = ttk.Button(self, text="Plot Heatmap", command=self.plot_data)
        self.image_processing_button = ttk.Button(self, text="Image Processing", command=self.open_processing_window)
        self.reset_button = ttk.Button(self, text="Reset Data", command=self.reset_data)

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
        self.image_processing_button.pack(pady=5)
        self.reset_button.pack(pady=5)

    def apply_math_operations(self):
        data = self.original_data.copy()
        for op in self.operation_history:
            _, func = self.available_operations[op]
            try:
                with np.errstate(divide='ignore', invalid='ignore'):
                    data = func(data)
            except Exception as e:
                print(f"Error applying {op}: {e}")
        self.processed_data = data

    def plot_data(self):
        dataset_name = self.dataset_combo.get()
        if not dataset_name:
            return

        try:
            with h5py.File(self.filename, 'r') as f:
                self.original_data = f[dataset_name][:]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load dataset: {e}")
            return

        self.show_heatmap(dataset_name)

    def show_heatmap(self, title):
        self.apply_math_operations()

        cmap = self.colormap.get()
        if self.reverse_cmap.get():
            cmap += "_r"

        if self.fig is None or self.ax is None or self.im is None:
            self.fig, self.ax = plt.subplots()
            self.im = self.ax.imshow(self.processed_data, aspect='auto', origin='lower', cmap=cmap)
            self.ax.set_title(title)
            self.fig.colorbar(self.im, ax=self.ax)
            self.fig.canvas.mpl_connect('close_event', lambda e: setattr(self, 'fig', None))
            enable_click_interaction(self.fig, self.processed_data, self)
            self.fig.show()
        else:
            self.im.set_data(self.processed_data)
            self.im.set_cmap(cmap)
            self.im.set_clim(vmin=np.nanmin(self.processed_data), vmax=np.nanmax(self.processed_data))
            self.fig.canvas.draw_idle()
            enable_click_interaction(self.fig, self.processed_data, self)

        if self.last_click is not None:
            self.update_cross_section(*self.last_click)

    def open_processing_window(self):
        if self.processing_window and tk.Toplevel.winfo_exists(self.processing_window):
            self.processing_window.lift()
            return

        self.processing_window = tk.Toplevel(self)
        self.processing_window.title("Image Processing Options")

        for name, (var, _) in self.available_operations.items():
            def make_callback(op=name):
                def callback(*args):
                    if self.available_operations[op][0].get():
                        if op not in self.operation_history:
                            self.operation_history.append(op)
                    else:
                        if op in self.operation_history:
                            self.operation_history.remove(op)
                    self.show_heatmap(self.dataset_combo.get())
                return callback

            var.trace_add("write", make_callback(name))
            ttk.Checkbutton(self.processing_window, text=name, variable=var).pack(anchor='w')

    def reset_data(self):
        for var, _ in self.available_operations.values():
            var.set(False)
        self.operation_history = []
        self.show_heatmap(self.dataset_combo.get())

    def update_cross_section(self, x, y):
        self.last_click = (x, y)
        data = self.processed_data

        if self.cross_section_figure is None or self.cross_section_axes is None:
            self.cross_section_figure, self.cross_section_axes = plt.subplots(2, 1, figsize=(6, 4))
            self.cross_section_figure.suptitle(f"Cross-sections at (x={x}, y={y})")
            self.cross_section_axes[0].plot(data[y, :], label="Row")
            self.cross_section_axes[0].set_ylabel("Value")
            self.cross_section_axes[1].plot(data[:, x], label="Column")
            self.cross_section_axes[1].set_ylabel("Value")
            self.cross_section_figure.tight_layout()
            self.cross_section_figure.canvas.mpl_connect('close_event', lambda e: setattr(self, 'cross_section_figure', None))
            self.cross_section_figure.show()
        else:
            self.cross_section_axes[0].clear()
            self.cross_section_axes[1].clear()
            self.cross_section_axes[0].plot(data[y, :], label="Row")
            self.cross_section_axes[1].plot(data[:, x], label="Column")
            self.cross_section_axes[0].set_ylabel("Value")
            self.cross_section_axes[1].set_ylabel("Value")
            self.cross_section_figure.suptitle(f"Cross-sections at (x={x}, y={y})")
            self.cross_section_figure.canvas.draw_idle()

    def on_close(self):
        if self.fig:
            plt.close(self.fig)
        if self.cross_section_figure:
            plt.close(self.cross_section_figure)
        self.destroy()
