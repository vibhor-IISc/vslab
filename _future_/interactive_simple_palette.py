from bokeh.io import curdoc
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, FileInput, Div, Select
from bokeh.plotting import figure
from base64 import b64decode
import numpy as np
import io
from bokeh.palettes import Spectral11, Viridis256, Inferno256, Plasma256

# Initial palette list
palette_options = {
    "Spectral11": Spectral11,
    "Viridis256": Viridis256,
    "Inferno256": Inferno256,
    "Plasma256": Plasma256,
}

# Create widgets
file_input = FileInput(accept=".npy")
message = Div(text="Upload a NumPy (.npy) file")
palette_select = Select(title="Select Palette:", value="Spectral11", options=list(palette_options.keys()))

# Data source for the image
image_source = ColumnDataSource(data={"image": [np.zeros((10, 10))]})  # Initial empty image

# Create an image figure
image_figure = figure(title="Image Plot", width=300, height=300)

# Add initial glyph for image
image_renderer = image_figure.image(
    image="image", x=0, y=0, dw=10, dh=10, palette=Spectral11, source=image_source
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

# Callback to change the palette
def palette_change_callback(attr, old, new):
    # Remove and re-add the glyph with a new palette
    global image_renderer
    image_figure.renderers.remove(image_renderer)  # Remove old renderer
    image_renderer = image_figure.image(
        image="image", x=0, y=0, dw=10, dh=10, palette=palette_options[new], source=image_source
    )  # Add new renderer

# Link the callbacks
file_input.on_change("value", file_input_callback)
palette_select.on_change("value", palette_change_callback)

# Layout for Bokeh server app
layout = column(message, file_input, palette_select, image_figure)
curdoc().add_root(layout)
