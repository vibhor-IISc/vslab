#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 11 10:53:17 2025

@author: vibhor
"""

from bokeh.plotting import figure, curdoc
from bokeh.models import FileInput, ColumnDataSource, Div
from bokeh.layouts import column
import pandas as pd
import io
import numpy as np


# Create a Bokeh document
doc = curdoc()

# Data source for the plot
source = ColumnDataSource(data={'x': [], 'y': []})

# Create a simple figure
plot = figure(title="Uploaded Data Plot", width=600, height=400)
plot.line('x', 'y', source=source, line_width=2)

# FileInput widget
file_input = FileInput(accept=".dat")  # Accepts only CSV files

# Info div
info = Div(text="<b>Instructions:</b> Upload a CSV file with two columns: 'x' and 'y'.")

# Callback function to handle file upload
def file_upload_callback(attr, old, new):
    try:
        # Decode the file contents
        xx, yy = np.loadtxt('col_data.dat', usecols=(0,1), skiprows = 1, unpack=True, delimiter = ',')
        source.data = {'x': xx, 'y': yy}
        
        # file_contents = io.BytesIO(file_input.value)
        # Parse the file into a DataFrame
        # df = pd.read_csv(file_contents)
        
        # Validate if the CSV has 'x' and 'y' columns
        # if 'x' in df.columns and 'y' in df.columns:
        #     source.data = {'x': df['x'], 'y': df['y']}
        #     info.text = "<b>Success:</b> Plot updated from uploaded file."
        # else:
        #     info.text = "<b>Error:</b> The uploaded CSV must contain 'x' and 'y' columns."
    except Exception as e:
        info.text = f"<b>Error:</b> Failed to process file. Details: {e}"

# Link the callback to the FileInput widget
file_input.on_change('value', file_upload_callback)

# Arrange in a layout
layout = column(info, file_input, plot)

# Add the layout to the document
doc.add_root(layout)
