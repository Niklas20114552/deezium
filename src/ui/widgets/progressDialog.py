from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar

from main import APP_DATA_PATH, APP_NAME


class ProgressDialog(QDialog):
    def __init__(self, text):
        super().__init__()
        self.setWindowIcon(QIcon(APP_DATA_PATH + "deezium.png"))
        self.setWindowTitle(APP_NAME)
        self.setFixedHeight(55)
        layout = QVBoxLayout()
        self.label = QLabel(text)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)
