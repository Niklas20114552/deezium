import deezer
import src.caching.albumCovers
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMenu, QHBoxLayout, QLabel

from src import utils
from src.ui.widgets.SVGButton import SVGButton


class QTrackList(QWidget):
    artist_clicked = pyqtSignal(int)
    album_clicked = pyqtSignal(int)
    track_clicked = pyqtSignal(int)
    toggle_fav = pyqtSignal(int)
    add_queue = pyqtSignal(int)
    add_playlist = pyqtSignal(int)

    def __init__(
        self,
        trackids: list[int],
        deezerclient: deezer.Client,
        show_album: bool = True,
        show_icons: bool = True,
        show_artist: bool = True,
    ):
        super().__init__()
        self.trackids = trackids
        self.cli = deezerclient
        self.data = []
        self.show_album = show_album
        self.show_icons = show_icons
        self.show_artist = show_artist
        self.favorites: list[int] = utils.conv_paginated_ids(
            deezerclient.get_user_tracks()
        )
        self.construct_items()
        self.main_layout = QVBoxLayout(self)
        self.construct_list()

    def construct_items(self):
        for trackid in self.trackids:
            dt = {}
            track = self.cli.get_track(trackid)
            if trackid > 0 and track.album.id != 0:
                try:
                    dt["name"] = track.title
                    dt["artist"] = track.artist
                    dt["length"] = track.duration
                    dt["album"] = track.album
                    dt["album-art"] = track.album.artist
                    if self.show_icons:
                        pix = QPixmap()
                        pix.loadFromData(
                            src.caching.albumCovers.download_small(self.cli, track.album.id)
                        )
                        dt["icon-pixmap"] = pix
                    dt["dpy-track"] = track
                    self.data.append(dt)
                except deezer.exceptions.DeezerErrorResponse:
                    print("[E> Failed processing " + str(trackid) + " on deezers end")
                    print(f"[TRB> AlbumId: {track.album.id} ArtistId {track.artist.id}")

    def update_fav(self):
        self.favorites = utils.conv_paginated_ids(self.cli.get_user_tracks())

    def construct_list(self):
        for track in self.data:

            def openmenu():
                self.update_fav()
                menu = QMenu(self)
                if track["dpy-track"].id in self.favorites:
                    fav = menu.addAction("Remove from &favorites")
                else:
                    fav = menu.addAction("Add to &favorites")
                queue = menu.addAction("Add to &queue")
                playlist = menu.addAction("Add to &playlist")

                fav.triggered.connect(
                    lambda event, tid=track["dpy-track"].id: self.toggle_fav.emit(tid)
                )
                queue.triggered.connect(
                    lambda event, tid=track["dpy-track"].id: self.add_queue.emit(tid)
                )
                playlist.triggered.connect(
                    lambda event, tid=track["dpy-track"].id: self.add_playlist.emit(tid)
                )

                buttonpos = QCursor.pos()
                menu.exec_(buttonpos)

            row = QHBoxLayout()
            text_label = QLabel(f"<b>{track['name']}</b> -")
            text_label.mousePressEvent = lambda event, track_id=track["dpy-track"].id: (
                self.track_clicked.emit(track_id)
            )
            duration = QLabel(f" (<i>{round(track['length'] / 60)} min long</i>)")
            show_menu_button = SVGButton("more")
            show_menu_button.setFixedSize(30, 30)
            show_menu_button.clicked.connect(openmenu)

            if self.show_icons:
                icon_label = QLabel()
                icon_label.setPixmap(track["icon-pixmap"])
                icon_label.mousePressEvent = lambda event, track_id=track[
                    "dpy-track"
                ].id: (self.track_clicked.emit(track_id))
                row.addWidget(icon_label)

            row.addWidget(text_label)

            if self.show_artist:
                artist_label = QLabel(track["artist"].name)
                artist_label.mousePressEvent = lambda event, artist_id=track[
                    "artist"
                ].id: (self.artist_clicked.emit(artist_id))
                row.addWidget(artist_label)

            row.addWidget(duration)
            row.addStretch()

            if self.show_album:
                album_label = QLabel(
                    f"in <b>{track['album'].title}</b> by <i>{track['album-art'].name}</i>"
                )
                album_label.mousePressEvent = lambda event, album_id=track[
                    "album"
                ].id: (self.album_clicked.emit(album_id))
                row.addWidget(album_label)

            row.addWidget(show_menu_button)
            self.main_layout.addLayout(row)
