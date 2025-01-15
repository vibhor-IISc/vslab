from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Select, Div, Slider, Spacer, LinearColorMapper, ColorBar, FileInput
from bokeh.plotting import figure
import xarray as xr
import numpy as np
import io
from base64 import b64decode

# Create placeholder dataset
dataset = None
initial_array = None

# Widgets
file_input = FileInput(accept=".h5")
layer_select = Select(title="Select Layer:", value="", options=[])
palette_options = ["Viridis256", "Inferno256", "Plasma256"]
palette_select = Select(title="Select Palette:", value="Viridis256", options=palette_options)
row_slider = Slider(start=0, end=1, value=0, step=1, title="Row Index")
col_slider = Slider(start=0, end=1, value=0, step=1, title="Column Index")
message = Div(text="Upload a dataset to get started.")

# Data Sources
image_source = ColumnDataSource(data={"image": [np.zeros((1, 1))]})
row_cut_source = ColumnDataSource(data={"x": [], "y": []})
col_cut_source = ColumnDataSource(data={"x": [], "y": []})

# Figures
color_mapper = LinearColorMapper(palette=palette_select.value)
image_figure = figure(title="2D Image Plot", width=500, height=400)
image_figure.image(
    image="image", x=0, y=0, dw=1, dh=1, color_mapper=color_mapper, source=image_source
)
color_bar = ColorBar(color_mapper=color_mapper, location=(0, 0))
image_figure.add_layout(color_bar, 'right')

row_cut_figure = figure(title="Row Linecut", width=600, height=250)
row_cut_figure.line("x", "y", source=row_cut_source, line_width=2, color="blue")

col_cut_figure = figure(title="Column Linecut", width=600, height=250)
col_cut_figure.line("x", "y", source=col_cut_source, line_width=2, color="green")

# Callbacks
def file_input_callback(attr, old, new):
    global dataset, initial_array, xcoord, ycoord
    try:
        # Decode the uploaded file content
        file_content = io.BytesIO(b64decode(file_input.value))
        file_content.seek(0)  # Ensure the stream is at the beginning
        dataset = xr.open_dataset(file_content)
        
        xcoord = dataset.X.values
        ycoord = dataset.Y.values
        

        # Update initial layer
        layer_names = list(dataset.data_vars.keys())
        layer_select.options = layer_names
        layer_select.value = layer_names[0] if layer_names else ""

        if layer_names:
            initial_array = dataset[layer_names[0]].values
            update_layer(None, None, None)
            message.text = f"Dataset loaded. Shape: {initial_array.shape}"
        else:
            message.text = "No valid layers found in the dataset."
    except Exception as e:
        message.text = f"Failed to load dataset: {e}"


def update_layer(attr, old, new):
    global initial_array
    if not dataset:
        return

    selected_layer = layer_select.value
    if selected_layer in dataset:
        new_array = dataset[selected_layer].values
        image_source.data = {"image": [new_array]}
        row_slider.end = new_array.shape[0] - 1
        col_slider.end = new_array.shape[1] - 1
        row_slider.value = 0
        col_slider.value = 0
        initial_array = new_array
        update_linecuts(None, None, None)

def update_linecuts(attr, old, new):
    if initial_array is None:
        return

    row_index = row_slider.value
    col_index = col_slider.value
    row_cut_source.data = {"x": xcoord, "y": initial_array[row_index, :]}
    col_cut_source.data = {"x": ycoord, "y": initial_array[:, col_index]}

def update_palette(attr, old, new):
    color_mapper.palette = palette_select.value

# Link callbacks
file_input.on_change("value", file_input_callback)
layer_select.on_change("value", update_layer)
row_slider.on_change("value", update_linecuts)
col_slider.on_change("value", update_linecuts)
palette_select.on_change("value", update_palette)

# Layout
left = column(message, file_input, layer_select, palette_select, image_figure)
gap = Spacer(width=50)
right = column(row_slider, row_cut_figure, col_slider, col_cut_figure)
layout = row(left, gap, right)

curdoc().add_root(layout)
