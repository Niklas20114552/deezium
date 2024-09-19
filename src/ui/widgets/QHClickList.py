from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel


class QHClickList(QWidget):
    action = pyqtSignal()

    def __init__(self, title: str, pixmap: QPixmap, lasttext: str, hovertext: str):
        super().__init__()
        self.main_layout = QHBoxLayout(self)
        self.pixmap = pixmap
        self.title = title
        self.lasttext = "(" + lasttext + ")"
        self.hovertext = hovertext
        self.construct_list()

    def construct_list(self):
        title = QLabel("<b>" + self.title + "</b")
        title.mousePressEvent = lambda event: self.action.emit()
        icon_label = QLabel()
        icon_label.setPixmap(self.pixmap)
        icon_label.setToolTip(self.hovertext)
        icon_label.mousePressEvent = lambda event: self.action.emit()
        last_label = QLabel(self.lasttext)
        last_label.mousePressEvent = lambda event: self.action.emit()
        self.main_layout.addWidget(icon_label)
        self.main_layout.addWidget(title)
        self.main_layout.addWidget(last_label)
        self.main_layout.addStretch()
