import deezer
import requests
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel


class QPlayList(QWidget):
    playlist_clicked = pyqtSignal(int)

    def __init__(self, listids: list[int], deezerclient: deezer.Client):
        super().__init__()
        self.listids = listids
        self.cli = deezerclient
        self.data = []
        self.construct_items()
        self.main_layout = QVBoxLayout(self)
        self.construct_list()

    def construct_items(self):
        for playlist in self.listids:
            dt = {}
            playlist = self.cli.get_playlist(playlist)
            dt["name"] = playlist.title
            dt["length"] = playlist.duration
            dt["author"] = playlist.creator
            pix = QPixmap()
            pix.loadFromData(requests.get(playlist.picture_small).content)
            dt["icon-pixmap"] = pix
            dt["dpy-track"] = playlist
            self.data.append(dt)

    def construct_list(self):
        for playlist in self.data:
            row = QHBoxLayout()
            icon_label = QLabel()
            icon_label.setPixmap(playlist["icon-pixmap"])
            icon_label.mousePressEvent = lambda event, artist_id=playlist[
                "author"
            ].id: (self.playlist_clicked.emit(artist_id))
            text_label = QLabel(f"<b>{playlist['name']}</b> -")
            text_label.mousePressEvent = lambda event, artist_id=playlist[
                "author"
            ].id: (self.playlist_clicked.emit(artist_id))
            artist_label = QLabel(playlist["author"].name)
            duration = QLabel(f" (<i>{round(playlist['length'] / 60)} min long</i>)")
            row.addWidget(icon_label)
            row.addWidget(text_label)
            row.addWidget(artist_label)
            row.addWidget(duration)
            row.addStretch()
            self.main_layout.addLayout(row)
