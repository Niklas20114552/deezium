import deezer
import requests
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel


class QArtistList(QWidget):
    artist_clicked = pyqtSignal(int)

    def __init__(self, artistids: list[int], deezerclient: deezer.Client):
        super().__init__()
        self.artistids = artistids
        self.cli = deezerclient
        self.data = []
        self.construct_items()
        self.main_layout = QVBoxLayout(self)
        self.construct_list()

    def construct_items(self):
        for artist in self.artistids:
            dt = {}
            artist = self.cli.get_artist(artist)
            dt["name"] = artist.name
            pix = QPixmap()
            pix.loadFromData(requests.get(artist.picture_small).content)
            dt["icon-pixmap"] = pix
            dt["dpy-artist"] = artist
            self.data.append(dt)

    def construct_list(self):
        for artist in self.data:
            row = QHBoxLayout()
            icon_label = QLabel()
            icon_label.setPixmap(artist["icon-pixmap"])
            icon_label.mousePressEvent = lambda event, artist_id=artist[
                "dpy-artist"
            ].id: (self.artist_clicked.emit(artist_id))
            text_label = QLabel(f"<b>{artist['name']}</b>")
            text_label.mousePressEvent = lambda event, artist_id=artist[
                "dpy-artist"
            ].id: (self.artist_clicked.emit(artist_id))
            row.addWidget(icon_label)
            row.addWidget(text_label)
            row.addStretch()
            self.main_layout.addLayout(row)
