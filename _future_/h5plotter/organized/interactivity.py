# hdf_viewer/interactivity.py
from plot_tools import plot_cross_sections

def enable_click_interaction(fig, data, app):
    ax = fig.axes[0]

    def onclick(event):
        if event.inaxes != ax:
            return
        x, y = int(event.xdata + 0.5), int(event.ydata + 0.5)
        if 0 <= y < data.shape[0] and 0 <= x < data.shape[1]:
            value = data[y, x]
            print(f"Clicked at (x={x}, y={y}) → value: {value:.4f}")
            ax.set_title(f"Value at (x={x}, y={y}): {value:.4f}")
            fig.canvas.draw()
            app.cross_section_figure = plot_cross_sections(data, x, y, app.cross_section_figure)

    fig.canvas.mpl_connect('button_press_event', onclick)