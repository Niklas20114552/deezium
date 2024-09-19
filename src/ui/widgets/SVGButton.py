from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QPushButton
import platform
from src import svgUtils

if platform.system() == "Windows":
    APP_DATA_PATH: str = "C:\\Program Files\\Deezium\\"
elif platform.system() == "Linux":
    APP_DATA_PATH: str = "/usr/share/deezium/"


class SVGButton(QPushButton):
    def __init__(self, svg_filename):
        super().__init__()
        self.text_color = self.palette().color(self.foregroundRole())
        self.svg_filename = ""
        self.icon = QIcon()
        self.set_icon(svg_filename)

    def set_icon(self, svg_filename):
        self.svg_filename = f"{APP_DATA_PATH}svgs/{svg_filename}.svg"
        self.icon = QIcon(
            svgUtils.create_colored_svg(self.svg_filename, self.text_color)
        )
        self.setIcon(self.icon)
