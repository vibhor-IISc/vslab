from vslab._future_.data import Data2D
from bokeh.plotting import figure, curdoc
from bokeh.models import Slider, ColumnDataSource, FileInput, Div
from bokeh.layouts import row, column
import io
import base64
import numpy as np

# Initial path setup (placeholder for default or uploaded file)
path = '/Users/vibhor/Downloads/vslabtest'

# Load data from the path
def load_data(file_path):
    d = Data2D(file_path)
    x = d.X
    z = d.read_column(2)  # Assuming z is a 2D array (matrix)
    return x, z

# Initialize data
x, z = load_data(path)

# Initial setup: Select the first row of z to display
initial_row = 0
data_row = z[initial_row]

# Create ColumnDataSource for dynamic updates
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

# Slider to select a row
slider = Slider(start=0, end=z.shape[0] - 1, value=0, step=1, title="Row Selector")
slider.on_change("value", update_plot)

# FileInput widget for browsing and uploading files
file_input = FileInput(accept=".dat")  # Modify this as per accepted extensions

# Info div for feedback
info = Div(text="<b>Upload a file to update the plot.</b>")

# Callback for file upload
def upload_file_callback(attr, old, new):
    global x, z  # Use global variables to update the data
    try:
        # Decode the uploaded file content
        file_contents = io.BytesIO(base64.b64decode(file_input.value))
        # Process the uploaded file through Data2D
        temp_path = file_contents  # Placeholder, adjust for your Data2D setup
        d = Data2D(temp_path)  # Replace this with your actual Data2D handling logic
        x = d.X
        z = d.read_column(2)  # Reload data
        
        # Update data sources
        slider.end = z.shape[0] - 1
        slider.value = 0  # Reset slider to initial value
        line_source.data = {"x": x, "y": z[0]}
        image_source.data = {"image": [z]}

        info.text = "<b>Success:</b> File uploaded and plot updated."
    except Exception as e:
        info.text = f"<b>Error:</b> Unable to process file. Details: {e}"

# Link the callback to the FileInput widget
file_input.on_change("value", upload_file_callback)

# Combine layout
layout = column(file_input, info, slider, row(image_figure, line_figure))

# Add the layout to the current document
curdoc().add_root(layout)
