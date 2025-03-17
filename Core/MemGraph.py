import textual_plot
from textual.app import ComposeResult
from textual_plot import PlotWidget


class Memgraph(PlotWidget):
    memory: dict
    swap: dict

    def __init__(self):
        self.memory = {"x": [], "y": []}
        self.swap = {"x": [], "y": []}
        super().__init__()

    def compose(self) -> ComposeResult:
        yield PlotWidget(allow_pan_and_zoom=False)

    def on_mount(self) -> None:
        plot = self.query_one(PlotWidget)
        plot.set_xlabel("")
        plot.set_ylabel("GB")
        plot.set_xticks([])
        #self.set_yticks([])
        plot.set_yticks([0, 2, 4, 6, 8, 10, 12, 14, 16])
        self.set_ylimits(ymin=0.0, ymax=16.0)

    def allow_focus(self) -> bool:
        return False

    def plot_data(self, data, line_style):
        x = data["x"]
        y = data["y"]
        plot = self.query_one(PlotWidget)
        plot.plot(x=x, y=y, line_style=line_style,hires_mode=textual_plot.HiResMode.BRAILLE)

    def append_data_point(self, time, mem_y, swap_y):
        self.memory["x"].append(time)
        self.memory["y"].append(mem_y)
        self.swap["x"].append(time)
        self.swap["y"].append(swap_y)
        #self.plot_data(self.memory, "bright_yellow")
        #self.plot_data(self.swap, "bright_red")