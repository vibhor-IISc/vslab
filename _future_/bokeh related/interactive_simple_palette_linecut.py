#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 11 22:39:05 2025

@author: vibhor
"""

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, FileInput, Div, Slider
from bokeh.plotting import figure
from base64 import b64decode
import numpy as np
import io

# Global variable to store the uploaded array
uploaded_array = np.zeros((10, 10))  # Initial dummy array

# Create widgets
file_input = FileInput(accept=".npy")
message = Div(text="Upload a NumPy (.npy) file")
row_slider = Slider(start=0, end=uploaded_array.shape[0] - 1, value=0, step=1, title="Row Index")
col_slider = Slider(start=0, end=uploaded_array.shape[1] - 1, value=0, step=1, title="Column Index")

# Linecut sources
row_cut_source = ColumnDataSource(data={"x": [], "y": []})
col_cut_source = ColumnDataSource(data={"x": [], "y": []})

# Figures for row and column cuts
row_cut_figure = figure(title="Row Linecut", width=400, height=200)
row_cut_figure.line("x", "y", source=row_cut_source, line_width=2, color="blue")

col_cut_figure = figure(title="Column Linecut", width=400, height=200)
col_cut_figure.line("x", "y", source=col_cut_source, line_width=2, color="green")

# Callback to update linecuts
def update_linecuts(attr, old, new):
    # Get row and column indices
    row_index = row_slider.value
    col_index = col_slider.value

    # Update data for linecuts
    row_cut_source.data = {"x": list(range(uploaded_array.shape[1])), "y": uploaded_array[row_index, :]}
    col_cut_source.data = {"x": list(range(uploaded_array.shape[0])), "y": uploaded_array[:, col_index]}

# Callback to handle file upload
def file_input_callback(attr, old, new):
    global uploaded_array

    if file_input.value:
        # Decode and load NumPy array
        file_content = io.BytesIO(b64decode(file_input.value))
        try:
            uploaded_array = np.load(file_content)
            message.text = f"Array uploaded successfully! Shape: {uploaded_array.shape}"

            # Update slider ranges
            row_slider.end = uploaded_array.shape[0] - 1
            col_slider.end = uploaded_array.shape[1] - 1
            row_slider.value = 0
            col_slider.value = 0

            # Initialize linecuts
            update_linecuts(None, None, None)

        except Exception as e:
            message.text = f"Failed to load array: {e}"

# Link the callbacks
file_input.on_change("value", file_input_callback)
row_slider.on_change("value", update_linecuts)
col_slider.on_change("value", update_linecuts)

# Layout for the app
layout = column(
    message,
    file_input,
    row(row_slider, col_slider),
    row(row_cut_figure, col_cut_figure),
)
curdoc().add_root(layout)
