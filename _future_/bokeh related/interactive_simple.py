from bokeh.io import curdoc
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, FileInput, Div
from bokeh.plotting import figure
from base64 import b64decode
import numpy as np
import io

# Create widgets
file_input = FileInput(accept=".npy")  # Accept only .npy files
message = Div(text="Upload a NumPy (.npy) file")

# Data source for the image
image_source = ColumnDataSource(data={"image": [np.zeros((10, 10))]})  # Initial empty image

# Create an image figure
image_figure = figure(title="Image Plot", width=300, height=300)
image_figure.image(
    image="image", x=0, y=0, dw=10, dh=10, palette="Spectral11", source=image_source
)

# Callback function to handle file input
def file_input_callback(attr, old, new):
    if file_input.value:
        # Decode base64 file data
        file_content = io.BytesIO(b64decode(file_input.value))
        
        try:
            # Load NumPy array
            array = np.load(file_content)
            message.text = f"Array loaded successfully! Shape: {array.shape}, Data type: {array.dtype}"
            
            # Update image source data
            image_source.data = {"image": [array]}
        except Exception as e:
            message.text = f"Failed to load file: {e}"

# Link the callback to the FileInput widget
file_input.on_change("value", file_input_callback)

# Layout for Bokeh server app
layout = column(message, file_input, image_figure)
curdoc().add_root(layout)

