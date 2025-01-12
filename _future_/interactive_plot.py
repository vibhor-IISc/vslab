#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 21:53:52 2025

@author: vibhor
"""

# from vslab._future_.data import Data2D
# import matplotlib.pyplot as plt

# d = Data2D('/Users/vibhor/Downloads/vslabtest')

# x = d.X
# y = d.Y

# z = d.read_column(2)

# plt.imshow(z)

# plt.show()



from vslab._future_.data import Data2D
from bokeh.plotting import figure, curdoc
from bokeh.models import Slider, ColumnDataSource
from bokeh.layouts import row, column
import numpy as np

# Load data (you can ignore this section as it's specific to your setup)
d = Data2D('/Users/vibhor/Downloads/vslabtest')
x = d.X
z = d.read_column(2)  # Assuming z is a 2D array (matrix)

# Initial setup: Select the first row of z to display
initial_row = 0
data_row = z[initial_row]

# Create a ColumnDataSource for dynamic updates
image_source = ColumnDataSource(data={"image": [z]})
line_source = ColumnDataSource(data={"x": x, "y": data_row})

# Create an image figure
image_figure = figure(title="Image Plot", width=300, height=300)
image_figure.image(image='image', x=0, y=0, dw=10, dh=10, palette="Spectral11", source=image_source)

# Create a line figure
line_figure = figure(title="Line Plot", width=600, height=300)
line_figure.line('x', 'y', source=line_source, line_width=2)

# Define a callback function for the slider
def update_plot(attr, old, new):
    selected_row = slider.value
    line_source.data = {"x": x, "y": z[selected_row]}  # Update line data
    # Update image source (if modifying row-specific changes to images as well)
    # image_source.data = {"image": [z]}  # Uncomment if the slider controls images
    
# Create a slider
slider = Slider(start=0, end=z.shape[0]-1, value=0, step=1, title="Row Selector")
slider.on_change("value", update_plot)

# Combine layout
layout = column(slider, row(image_figure, line_figure))

# Add the layout to the current document
curdoc().add_root(layout)