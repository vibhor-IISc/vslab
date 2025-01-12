from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, FileInput, Div, Slider, Select, Spacer
from bokeh.plotting import figure
from base64 import b64decode
from bokeh.palettes import Spectral11, Viridis256, Inferno256, Plasma256
import numpy as np
import io

# Global variable to store the uploaded array
uploaded_array = np.zeros((10, 10))  # Initial dummy array

# Palette options for dropdown
palette_options = {
    "Spectral11": Spectral11,
    "Viridis256": Viridis256,
    "Inferno256": Inferno256,
    "Plasma256": Plasma256,
}

# Create widgets
file_input = FileInput(accept=".npy")
message = Div(text="Upload a NumPy (.npy) file")
row_slider = Slider(start=0, end=uploaded_array.shape[0] - 1, value=0, step=1, title="Row Index")
col_slider = Slider(start=0, end=uploaded_array.shape[1] - 1, value=0, step=1, title="Column Index")
palette_select = Select(title="Select Palette:", value="Spectral11", options=list(palette_options.keys()))

# ColumnDataSources for plots
image_source = ColumnDataSource(data={"image": [uploaded_array]})
row_cut_source = ColumnDataSource(data={"x": [], "y": []})
col_cut_source = ColumnDataSource(data={"x": [], "y": []})

# 2D Image Plot
image_figure = figure(title="2D Image Plot", width=500, height=500)
image_renderer = image_figure.image(
    image="image", x=0, y=0, dw=10, dh=10, palette=Spectral11, source=image_source
)

# Row and Column Linecut Plots
row_cut_figure = figure(title="Row Linecut", width=600, height=250)
row_cut_figure.line("x", "y", source=row_cut_source, line_width=2, color="blue")

col_cut_figure = figure(title="Column Linecut", width=600, height=250)
col_cut_figure.line("x", "y", source=col_cut_source, line_width=2, color="green")

# Callback to handle file upload
def file_input_callback(attr, old, new):
    global uploaded_array

    if file_input.value:
        # Decode and load NumPy array
        file_content = io.BytesIO(b64decode(file_input.value))
        try:
            uploaded_array = np.load(file_content)
            message.text = f"Array uploaded successfully! Shape: {uploaded_array.shape}"

            # Update 2D plot source
            image_source.data = {"image": [uploaded_array]}

            # Update slider ranges
            row_slider.end = uploaded_array.shape[0] - 1
            col_slider.end = uploaded_array.shape[1] - 1
            row_slider.value = 0
            col_slider.value = 0

            # Update linecuts
            update_linecuts(None, None, None)

        except Exception as e:
            message.text = f"Failed to load array: {e}"

# Callback to update linecuts
def update_linecuts(attr, old, new):
    row_index = row_slider.value
    col_index = col_slider.value

    # Update row and column linecuts
    row_cut_source.data = {"x": list(range(uploaded_array.shape[1])), "y": uploaded_array[row_index, :]}
    col_cut_source.data = {"x": list(range(uploaded_array.shape[0])), "y": uploaded_array[:, col_index]}

# Callback to change the palette
def palette_change_callback(attr, old, new):
    global image_renderer
    # Remove and re-add the glyph with the new palette
    image_figure.renderers.remove(image_renderer)
    image_renderer = image_figure.image(
        image="image", x=0, y=0, dw=10, dh=10, palette=palette_options[new], source=image_source
    )

# Link the callbacks
file_input.on_change("value", file_input_callback)
row_slider.on_change("value", update_linecuts)
col_slider.on_change("value", update_linecuts)
palette_select.on_change("value", palette_change_callback)

# Layout for the app
# Working
# layout = column(
#     message,
#     file_input,
#     palette_select,
#     image_figure,
#     row(row_slider, col_slider),
#     row(row_cut_figure, col_cut_figure),
# )



left = column(message, file_input, palette_select, image_figure)

gap = Spacer(width = 100)

right = column(row_slider, row_cut_figure,col_slider, col_cut_figure)

layout = row(left, gap, right)


curdoc().add_root(layout)









