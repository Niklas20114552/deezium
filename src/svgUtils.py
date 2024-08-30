from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer


def create_colored_svg(svg_filename: str, text_color):
    renderer = QSvgRenderer(svg_filename)
    image_size = renderer.defaultSize()
    image = QPixmap(image_size)
    image.fill(Qt.transparent)  # Ensure transparency

    painter = QPainter(image)
    renderer.render(painter)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(image.rect(), text_color)
    painter.end()

    return image
