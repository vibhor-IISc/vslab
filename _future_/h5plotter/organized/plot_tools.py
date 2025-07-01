# hdf_viewer/plot_tools.py
import matplotlib.pyplot as plt

plt.ion()  # Enable interactive mode

def plot_heatmap(data, title="Heatmap", cmap="viridis"):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    img = ax.imshow(data, aspect='auto', origin='lower', cmap=cmap)
    fig.colorbar(img, label='Value')
    ax.set_title(f"Heatmap of {title}")
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    fig.tight_layout()
    plt.show(block=False)
    return fig

def plot_cross_sections(data, x, y, fig=None):
    if fig is None or not plt.fignum_exists(fig.number):
        fig, axs = plt.subplots(2, 1, figsize=(8, 6), constrained_layout=True)
    else:
        fig.clf()
        axs = fig.subplots(2, 1)

    axs[0].plot(data[y, :], label=f"Row y={y}")
    # axs[0].axvline(x, color='r', linestyle='--')
    axs[0].set_title(f"Horizontal Cross-section at y={y}")
    axs[0].set_xlabel("X")
    axs[0].set_ylabel("Value")
    axs[0].legend()

    axs[1].plot(data[:, x], label=f"Column x={x}")
    # axs[1].axhline(y, color='r', linestyle='--')
    axs[1].set_title(f"Vertical Cross-section at x={x}")
    axs[1].set_xlabel("Y")
    axs[1].set_ylabel("Value")
    axs[1].legend()

    fig.suptitle(f"Cross-sections at (x={x}, y={y})")
    fig.canvas.draw()
    plt.show(block=False)
    return fig
