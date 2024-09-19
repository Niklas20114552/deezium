from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton


class ErrorDialog(QDialog):
    def __init__(self, trb: str):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.title = QLabel("Sorry! Deezium crashed.")
        self.title.setFont(QFont(self.title.font().family(), 18))
        self.log = QTextEdit()
        self.log.setFont(QFont("Monospace"))
        self.log.setReadOnly(True)
        self.log.setPlainText(trb)
        self.okay_button = QPushButton("Close")
        self.okay_button.clicked.connect(self.accept)
        self.main_layout.addWidget(self.title)
        self.main_layout.addWidget(self.log)
        self.main_layout.addWidget(self.okay_button)
