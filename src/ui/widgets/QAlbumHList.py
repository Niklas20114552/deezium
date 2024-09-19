import deezer
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel

import src.caching.albumCovers


class QAlbumHList(QWidget):
    album_clicked = pyqtSignal(int)

    def __init__(self, albumids: list[int], deezerclient: deezer.Client):
        super().__init__()
        self.albumids = albumids
        self.cli = deezerclient
        self.data = []
        self.construct_items()
        self.main_layout = QHBoxLayout(self)
        self.construct_list()

    def construct_items(self):
        for album in self.albumids:
            dt = {}
            album = self.cli.get_album(album)
            dt["name"] = album.title
            dt["artist"] = album.artist
            dt["id"] = album.id
            pix = QPixmap()
            pix.loadFromData(src.caching.albumCovers.download_medium(self.cli, album.id))
            dt["icon-pixmap"] = pix
            self.data.append(dt)

    def construct_list(self):
        for album in self.data:
            icon_label = QLabel()
            icon_label.setPixmap(album["icon-pixmap"])
            icon_label.mousePressEvent = lambda event, album_id=album[
                "id"
            ]: self.album_clicked.emit(album_id)
            icon_label.setToolTip(f"{album['name']} - {album['artist'].name}")
            self.main_layout.addWidget(icon_label)
