import deezer
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

import src.caching.albumCovers


class QAlbumList(QWidget):
    album_clicked = pyqtSignal(int)
    artist_clicked = pyqtSignal(int)

    def __init__(self, albumids: list[int], deezerclient: deezer.Client):
        super().__init__()
        self.albumids = albumids
        self.cli = deezerclient
        self.data = []
        self.construct_items()
        self.main_layout = QVBoxLayout(self)
        self.construct_list()

    def construct_items(self):
        for album in self.albumids:
            dt = {}
            album = self.cli.get_album(album)
            dt["name"] = album.title
            dt["artist"] = album.artist
            dt["length"] = album.duration
            pix = QPixmap()
            pix.loadFromData(src.caching.albumCovers.download_small(self.cli, album.id))
            dt["icon-pixmap"] = pix
            dt["dpy-album"] = album
            self.data.append(dt)

    def construct_list(self):
        for album in self.data:
            row = QHBoxLayout()
            icon_label = QLabel()
            icon_label.setPixmap(album["icon-pixmap"])
            icon_label.mousePressEvent = lambda event, album_id=album["dpy-album"].id: (
                self.album_clicked.emit(album_id)
            )
            text_label = QLabel(f"<b>{album['name']}</b> -")
            text_label.mousePressEvent = lambda event, album_id=album["dpy-album"].id: (
                self.album_clicked.emit(album_id)
            )
            artist_label = QLabel(album["artist"].name)
            artist_label.mousePressEvent = lambda event, artist_id=album["artist"].id: (
                self.artist_clicked.emit(artist_id)
            )
            duration = QLabel(f" (<i>{round(album['length'] / 60)} min long</i>)")
            row.addWidget(icon_label)
            row.addWidget(text_label)
            row.addWidget(artist_label)
            row.addWidget(duration)
            row.addStretch()
            self.main_layout.addLayout(row)
