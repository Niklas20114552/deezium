#!/usr/bin/python3
import sys, os, platform, deezloader.exceptions, json, threading, subprocess, inspect, random, traceback, re
from PyQt5.QtCore import QUrl, pyqtSignal, Qt
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QIcon, QFont, QPixmap, QCursor
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QLineEdit, QSlider, QProgressBar, QGroupBox, QScrollArea, QFrame, QCheckBox, QDialog, QTextEdit, QMenu
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtNetwork import QNetworkCookie
from configparser import ConfigParser
from importlib.util import module_from_spec, spec_from_file_location

config = ConfigParser()
APP_DEVMODE: bool = False

APP_NAME: str = "Deezium"
if platform.system() == 'Windows':
    APP_DATA_PATH: str = "C:\\Program Files\\Deezium\\"
elif platform.system() == 'Linux':
    APP_DATA_PATH: str = '/usr/share/deezium/'
else:
    print('Sorry, but your Operating System is not supported.')
    sys.exit()

if len(sys.argv) > 1:
    if sys.argv[1] == '--dev':
        print('[D> Devmode enabled!')
        APP_DEVMODE = True

if not APP_DEVMODE:
    import_spec = spec_from_file_location('api', APP_DATA_PATH + 'deezium_api.py')
    api = module_from_spec(import_spec)
    sys.modules['api'] = api
    import_spec.loader.exec_module(api)
else:
    import deezium_api as api

class NoArlDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        title = QLabel('No ARL could be imported')
        title.setFont(QFont(title.font().family(), 12))
        text1 = QLabel('While logging in no access token could be imported from your Deezer Account.')
        text2 = QLabel('To properly use Deezium you must enter your access token:')
        self.input = QLineEdit()
        self.input.setMaxLength(192)
        self.input.setPlaceholderText('Enter your access token here')
        self.confirm_button = QPushButton('Continue')
        self.confirm_button.setDisabled(True)

        self.main_layout.addWidget(title)
        self.main_layout.addWidget(text1)
        self.main_layout.addWidget(text2)
        self.main_layout.addWidget(self.input)
        self.main_layout.addWidget(self.confirm_button)

        self.input.textChanged(self.update_button)
        self.confirm_button.clicked.connect(self.confirm)

    def update_button(self):
        self.confirm_button.setDisabled(not len(self.input.text()) == 192)

    def confirm(self):
        with open(os.path.expanduser('~/.config/deezium/arl.dat'), 'w') as f:
            f.write(self.input.text())

    def closeEvent(self, event) -> None:
        self.reject()
        super().closeEvent(event)


class ErrorDialog(QDialog):
    def __init__(self, trb: str):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.title = QLabel('Shit happens...')
        self.title.setFont(QFont(self.title.font().family(), 18))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setHtml("<pre>{}</pre>".format(trb))
        self.okay_button = QPushButton('Okay')
        self.okay_button.clicked.connect(self.accept)
        self.main_layout.addWidget(self.title)
        self.main_layout.addWidget(self.log)
        self.main_layout.addWidget(self.okay_button)


class QAlbumList(QWidget):
    album_clicked = pyqtSignal(int)
    artist_clicked = pyqtSignal(int)

    def __init__(self, albumids: list[int], deezerclient: api.deezer.Client):
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
            dt['name'] = album.title
            dt['artist'] = album.artist
            dt['length'] = album.duration
            pix = QPixmap()
            pix.loadFromData(api.download_albumcover_s(self.cli, album.id))
            dt['icon-pixmap'] = pix
            dt['dpy-album'] = album
            self.data.append(dt)

    def construct_list(self):
        for album in self.data:
            row = QHBoxLayout()
            icon_label = QLabel()
            icon_label.setPixmap(album['icon-pixmap'])
            icon_label.mousePressEvent = lambda event, album_id=album['dpy-album'].id: (
                self.album_clicked.emit(album_id))
            text_label = QLabel(f"<b>{album['name']}</b> -")
            text_label.mousePressEvent = lambda event, album_id=album['dpy-album'].id: (
                self.album_clicked.emit(album_id))
            artist_label = QLabel(album['artist'].name)
            artist_label.mousePressEvent = lambda event, artist_id=album['artist'].id: (
                self.artist_clicked.emit(artist_id))
            duration = QLabel(f" (<i>{round(album['length'] / 60)} min long</i>)")
            row.addWidget(icon_label)
            row.addWidget(text_label)
            row.addWidget(artist_label)
            row.addWidget(duration)
            row.addStretch()
            self.main_layout.addLayout(row)


class QAlbumHList(QWidget):
    album_clicked = pyqtSignal(int)

    def __init__(self, albumids: list[int], deezerclient: api.deezer.Client):
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
            dt['name'] = album.title
            dt['artist'] = album.artist
            dt['id'] = album.id
            pix = QPixmap()
            pix.loadFromData(api.download_albumcover_m(self.cli, album.id))
            dt['icon-pixmap'] = pix
            self.data.append(dt)

    def construct_list(self):
        for album in self.data:
            icon_label = QLabel()
            icon_label.setPixmap(album['icon-pixmap'])
            icon_label.mousePressEvent = lambda event, album_id=album['id']: self.album_clicked.emit(album_id)
            icon_label.setToolTip(f"{album['name']} - {album['artist'].name}")
            self.main_layout.addWidget(icon_label)


class QHClickList(QWidget):
    action = pyqtSignal()

    def __init__(self, title: str, pixmap: QPixmap, lasttext: str, hovertext: str):
        super().__init__()
        self.main_layout = QHBoxLayout(self)
        self.pixmap = pixmap
        self.title = title
        self.lasttext = '(' + lasttext + ')'
        self.hovertext = hovertext
        self.construct_list()

    def construct_list(self):
        title = QLabel('<b>' + self.title + '</b')
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


class QArtistList(QWidget):
    artist_clicked = pyqtSignal(int)

    def __init__(self, artistids: list[int], deezerclient: api.deezer.Client):
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
            dt['name'] = artist.name
            pix = QPixmap()
            pix.loadFromData(api.requests.get(artist.picture_small).content)
            dt['icon-pixmap'] = pix
            dt['dpy-artist'] = artist
            self.data.append(dt)

    def construct_list(self):
        for artist in self.data:
            row = QHBoxLayout()
            icon_label = QLabel()
            icon_label.setPixmap(artist['icon-pixmap'])
            icon_label.mousePressEvent = lambda event, artist_id=artist['dpy-artist'].id: (
                self.artist_clicked.emit(artist_id))
            text_label = QLabel(f"<b>{artist['name']}</b>")
            text_label.mousePressEvent = lambda event, artist_id=artist['dpy-artist'].id: (
                self.artist_clicked.emit(artist_id))
            row.addWidget(icon_label)
            row.addWidget(text_label)
            row.addStretch()
            self.main_layout.addLayout(row)


class QTrackList(QWidget):
    artist_clicked = pyqtSignal(int)
    album_clicked = pyqtSignal(int)
    track_clicked = pyqtSignal(int)
    toggle_fav = pyqtSignal(int)
    add_queue = pyqtSignal(int)
    add_playlist = pyqtSignal(int)

    def __init__(self, trackids: list[int], deezerclient: api.deezer.Client, show_album: bool = True,
                 show_icons: bool = True, show_artist: bool = True):
        super().__init__()
        self.trackids = trackids
        self.cli = deezerclient
        self.data = []
        self.show_album = show_album
        self.show_icons = show_icons
        self.show_artist = show_artist
        self.favorites: list[int] = api.conv_paginated_ids(deezerclient.get_user_tracks())
        self.construct_items()
        self.main_layout = QVBoxLayout(self)
        self.construct_list()

    def construct_items(self):
        for trackid in self.trackids:
            dt = {}
            track = self.cli.get_track(trackid)
            if trackid > 0 and track.album.id != 0:
                try:
                    dt['name'] = track.title
                    dt['artist'] = track.artist
                    dt['length'] = track.duration
                    dt['album'] = track.album
                    dt['album-art'] = track.album.artist
                    if self.show_icons:
                        pix = QPixmap()
                        pix.loadFromData(api.download_albumcover_s(self.cli, track.album.id))
                        dt['icon-pixmap'] = pix
                    dt['dpy-track'] = track
                    self.data.append(dt)
                except api.deezer.exceptions.DeezerErrorResponse:
                    print('[E> Failed processing ' + str(trackid) + ' on deezers end')
                    print(f'[TRB> AlbumId: {track.album.id} ArtistId {track.artist.id}')

    def update_fav(self):
        self.favorites = api.conv_paginated_ids(self.cli.get_user_tracks())

    def construct_list(self):
        for track in self.data:
            def openmenu():
                self.update_fav()
                menu = QMenu(self)
                if track['dpy-track'].id in self.favorites:
                    fav = menu.addAction('Remove from &favorites')
                else:
                    fav = menu.addAction('Add to &favorites')
                queue = menu.addAction('Add to &queue')
                playlist = menu.addAction('Add to &playlist')

                fav.triggered.connect(lambda event, tid=track['dpy-track'].id: self.toggle_fav.emit(tid))
                queue.triggered.connect(lambda event, tid=track['dpy-track'].id: self.add_queue.emit(tid))
                playlist.triggered.connect(lambda event, tid=track['dpy-track'].id: self.add_playlist.emit(tid))

                buttonpos = QCursor.pos()
                menu.exec_(buttonpos)

            row = QHBoxLayout()
            text_label = QLabel(f"<b>{track['name']}</b> -")
            text_label.mousePressEvent = lambda event, track_id=track['dpy-track'].id: (
                self.track_clicked.emit(track_id))
            duration = QLabel(f" (<i>{round(track['length'] / 60)} min long</i>)")
            show_menu_button = QPushButton('')
            show_menu_button.setFixedSize(30, 30)
            show_menu_button.setFont(QFont('Material Icons', 12))
            show_menu_button.clicked.connect(openmenu)

            if self.show_icons:
                icon_label = QLabel()
                icon_label.setPixmap(track['icon-pixmap'])
                icon_label.mousePressEvent = lambda event, track_id=track['dpy-track'].id: (
                    self.track_clicked.emit(track_id))
                row.addWidget(icon_label)

            row.addWidget(text_label)

            if self.show_artist:
                artist_label = QLabel(track['artist'].name)
                artist_label.mousePressEvent = lambda event, artist_id=track['artist'].id: (
                    self.artist_clicked.emit(artist_id))
                row.addWidget(artist_label)

            row.addWidget(duration)
            row.addStretch()

            if self.show_album:
                album_label = QLabel(f"in <b>{track['album'].title}</b> by <i>{track['album-art'].name}</i>")
                album_label.mousePressEvent = lambda event, album_id=track['album'].id: (
                    self.album_clicked.emit(album_id))
                row.addWidget(album_label)

            row.addWidget(show_menu_button)
            self.main_layout.addLayout(row)


class QPlayList(QWidget):
    playlist_clicked = pyqtSignal(int)

    def __init__(self, listids: list[int], deezerclient: api.deezer.Client):
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
            dt['name'] = playlist.title
            dt['length'] = playlist.duration
            dt['author'] = playlist.creator
            pix = QPixmap()
            pix.loadFromData(api.requests.get(playlist.picture_small).content)
            dt['icon-pixmap'] = pix
            dt['dpy-track'] = playlist
            self.data.append(dt)

    def construct_list(self):
        for playlist in self.data:
            row = QHBoxLayout()
            icon_label = QLabel()
            icon_label.setPixmap(playlist['icon-pixmap'])
            icon_label.mousePressEvent = lambda event, artist_id=playlist['author'].id: (
                self.playlist_clicked.emit(artist_id))
            text_label = QLabel(f"<b>{playlist['name']}</b> -")
            text_label.mousePressEvent = lambda event, artist_id=playlist['author'].id: (
                self.playlist_clicked.emit(artist_id))
            artist_label = QLabel(playlist['author'].name)
            duration = QLabel(f" (<i>{round(playlist['length'] / 60)} min long</i>)")
            row.addWidget(icon_label)
            row.addWidget(text_label)
            row.addWidget(artist_label)
            row.addWidget(duration)
            row.addStretch()
            self.main_layout.addLayout(row)


class ProgressDialog(QDialog):
    def __init__(self, text):
        super().__init__()
        self.setWindowIcon(QIcon(APP_DATA_PATH + 'deezium.png'))
        self.setWindowTitle(APP_NAME)
        self.setFixedHeight(55)
        layout = QVBoxLayout()
        self.label = QLabel(text)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(APP_DATA_PATH + 'deezium.png'))
        self.setMinimumSize(800, 600)
        self.deezpy_session = None
        self.deezdw_session = None
        self.logged_in: bool = False
        self.play_currenttrack = None
        self.play_looping: int = 0
        self.closeLocked: bool = False

        self.player = QMediaPlayer(self)

        self.player.setVolume(75)

        self.play_currentlist = []
        self.history = []

        self.play_widget = QWidget()
        self.play_layout = QHBoxLayout()
        self.play_widget.setLayout(self.play_layout)

        self.play_nowplaying = QLabel()
        self.play_seeker = QSlider(1)
        self.play_seeker.setMinimumWidth(400)
        self.play_pauseb = QPushButton('')
        self.play_pauseb.setFixedSize(30, 30)
        self.play_pauseb.setFont(QFont('Material Icons', 12))
        self.play_forb = QPushButton('')
        self.play_preb = QPushButton('')
        self.play_forb.setFixedSize(30, 30)
        self.play_preb.setFixedSize(30, 30)
        self.play_forb.setFont(QFont('Material Icons', 12))
        self.play_preb.setFont(QFont('Material Icons', 12))
        self.play_loopb = QPushButton('')
        self.play_loopb.setFixedSize(30, 30)
        self.play_state = QLabel()
        self.play_volume_indicator = QLabel('')
        self.play_volume_indicator.setFont(QFont('Material Icons', 12))
        self.play_volume = QSlider(1)
        self.play_volume.setRange(10, 100)
        self.play_volume.setValue(75)
        self.play_volume.setMinimumWidth(50)
        self.play_volume.setMaximumWidth(150)

        self.play_pauseb.clicked.connect(self.playback)
        self.player.stateChanged.connect(self.update_player)
        self.player.positionChanged.connect(self.update_seeker)
        self.player.durationChanged.connect(self.set_seeker)
        self.player.mediaStatusChanged.connect(self.update_mediastate)
        self.play_seeker.sliderMoved.connect(self.set_position)
        self.play_volume.sliderMoved.connect(self.set_volume)
        self.play_forb.clicked.connect(self.skip_forward)
        self.play_preb.clicked.connect(self.skip_backward)
        self.play_loopb.clicked.connect(self.toggle_loop)

        self.play_layout.addWidget(self.play_seeker)
        self.play_layout.addWidget(self.play_state)
        self.play_layout.addStretch()
        self.play_layout.addWidget(self.play_nowplaying)
        self.play_layout.addWidget(self.play_preb)
        self.play_layout.addWidget(self.play_pauseb)
        self.play_layout.addWidget(self.play_forb)
        self.play_layout.addStretch()
        self.play_layout.addWidget(self.play_volume_indicator)
        self.play_layout.addWidget(self.play_volume)
        self.play_layout.addWidget(self.play_loopb)

        print('[D> Main loading')
        self.update_config()
        if bool(self.config_arl) and bool(self.config_aro):
            self.login()
        else:
            self.createLoginPage()

    def read_playstate(self):
        if os.path.exists(os.path.expanduser('~/.config/deezium/lastplay')):
            try:
                with open(os.path.expanduser('~/.config/deezium/lastplay'), 'r') as f:
                    ldata = f.read()
                data = json.loads(ldata)
                self.play_currentlist = data['current_play']
                self.streamtrackid(data['current_id'], start=False)
                self.play_looping = data['looping']
                self.update_loopbutton()
                self.player.setPosition(data['position'])
                self.player.setVolume(data['volume'])
                self.play_volume.setValue(data['volume'])
                # self.play_seeker.setValue(data['position'])
            except KeyError:
                print('[E> Invalid State removed')
                os.remove(os.path.expanduser('~/.config/deezium/lastplay'))

    def update_mediastate(self, mstate):
        if mstate == QMediaPlayer.EndOfMedia:
            if self.play_looping == 2:
                self.player.setPosition(0)
                self.player.play()
            elif self.play_currenttrack == self.play_currentlist[-1]:
                if self.play_looping == 1:
                    self.skip_forward()
                else:
                    self.streamtrackid(self.play_currentlist[0], start=False)
            else:
                self.skip_forward()

    def toggle_loop(self):
        self.play_looping = (self.play_looping + 1) % 3
        self.update_loopbutton()

    def update_loopbutton(self):
        if self.play_looping == 0:
            self.play_loopb.setText('')
        elif self.play_looping == 1:
            self.play_loopb.setText('')
        elif self.play_looping == 2:
            self.play_loopb.setText('')

    def skip_forward(self, by=1):
        if not by:
            by = 1
        currenti = self.play_currentlist.index(int(self.play_currenttrack))
        self.streamtrackid(self.play_currentlist[(currenti + by) % len(self.play_currentlist)])

    def skip_backward(self, by=1):
        if not by:
            by = 1
        currenti = self.play_currentlist.index(int(self.play_currenttrack))
        self.streamtrackid(self.play_currentlist[currenti - by])

    def streamtrackid(self, tid, start=True, historize=True):
        self.play_currenttrack = tid
        path = api.download_track(self.deezdw_session, tid)
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
        if start:
            self.player.play()
        self.update_player(self.player.state())
        bg = api.calc_background_color(api.download_albumcover_m(self.deezpy_session, self.deezpy_session.get_track(tid).album.id))
        fg = api.calc_foreground_color(bg)
        self.play_widget.setStyleSheet(f'background-color: {bg}; color: {fg}')
        if historize:
            albumid = self.deezpy_session.get_track(tid).album.id
            self.insert_history(albumid)
        # self.update_metadata()

    def insert_history(self, tid):
        if tid in self.history:
            self.history.remove(tid)
        self.history.insert(0, tid)
        self.history = self.history[:10]
        self.save_history()

    def playtrack(self, tid):
        self.play_currentlist = [tid]
        self.streamtrackid(tid, start=True)
        self.play_looping = 0
        self.update_loopbutton()

    def playalbums(self, ids, first=None):
        self.play_currentlist = ids
        if not first:
            self.streamtrackid(ids[0], start=True)
        else:
            self.streamtrackid(first, start=True)
        self.play_looping = 0
        self.update_loopbutton()

    def playlist(self, ids, first=None):
        self.play_currentlist = ids
        if not first:
            self.streamtrackid(ids[0], start=True)
        else:
            self.streamtrackid(first, start=True)
        self.play_looping = 1
        self.update_loopbutton()

    def toggle_favorite_track(self, tid):
        def toggle():
            ids = api.conv_paginated_ids(self.deezpy_session.get_user_tracks())
            if tid in ids:
                self.deezpy_session.remove_user_track(tid)
            else:
                self.deezpy_session.add_user_track(tid)

        # deepcode ignore MissingAPI: it is required to keep the application running, while the list is converted,
        # as this takes a little moment
        thread = threading.Thread(target=toggle)
        thread.start()

    def update_player(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_pauseb.setText('')
        else:
            self.play_pauseb.setText('')
        index = self.play_currentlist.index(self.play_currenttrack)
        self.play_preb.setDisabled(index == 0)
        self.play_forb.setDisabled((index == len(self.play_currentlist)) or (self.play_looping == 2))
        if self.play_currenttrack:
            track = self.deezpy_session.get_track(self.play_currenttrack)
            self.play_nowplaying.setText(f'<b>{track.title}</b> - {track.artist.name}')

    def set_seeker(self, lenght):
        def buffer():
            api.download_track(self.deezdw_session, nxtid)

        self.play_seeker.setRange(0, lenght)

        index = self.play_currentlist.index(self.play_currenttrack) + 1
        if self.play_looping != 2 and index != len(self.play_currentlist):
            nxtid = self.play_currentlist[index]
            # file deepcode ignore MissingAPI: it is required to keep the application running, while the next song is buffering
            buffer_thread = threading.Thread(target=buffer)
            buffer_thread.start()

    def set_volume(self, vol):
        self.player.setVolume(vol)

    def update_seeker(self, duration):
        """Updates the Timestamp next to the seeker to the correct time."""
        self.play_seeker.setValue(duration)
        self.play_state.setText(api.ms_to_str(duration) + '/' + api.ms_to_str(self.player.duration()))

    def playback(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()
            calbum = self.deezpy_session.get_track(self.play_currenttrack).album.id
            self.insert_history(calbum)

    def set_position(self, position):
        self.player.setPosition(position)

    def login(self):
        """Prepares the player to load the main page and loads old playing state"""
        print('[D> Initializing Sessions')
        self.init_sessions()
        print('[D> Creating Main Page')
        try:
            self.createMainPage()
        except api.deezer.exceptions.DeezerErrorResponse:
            os.remove(os.path.expanduser('~/.config/deezium/aro.dat'))
            self.update_config()
            self.createLoginFailedPage()
        self.logged_in = True
        print('[D> Restoring state')
        self.read_playstate()

    def init_sessions(self):
        """Initializes the two online api sessions and if necessary kick back to log in"""
        os.chdir(os.path.expanduser('~/.cache/deezium/'))
        logout = False
        if not self.deezdw_session:
            try:
                self.deezdw_session = api.deezloader2.Login2(self.config_arl)
            except ValueError:
                os.remove(os.path.expanduser('~/.config/deezium/arl.dat'))
                logout = True
            except deezloader.exceptions.BadCredentials:
                os.remove(os.path.expanduser('~/.config/deezium/arl.dat'))
                logout = True
        if not self.deezpy_session:
            try:
                self.deezpy_session = api.deezer.Client(access_token=self.config_aro)
            except api.deezer.exceptions.DeezerErrorResponse:
                os.remove(os.path.expanduser('~/.config/deezium/aro.dat'))
                logout = True
        if logout:
            self.update_config()
            self.createLoginFailedPage()

    def update_config(self):
        """READs the config and updates the two token variables accordingly"""
        self.config_aro = api.get_oauth_token()
        self.config_arl = api.get_login_token()
        if os.path.exists(os.path.expanduser('~/.config/deezium/history')):
            with open(os.path.expanduser('~/.config/deezium/history'), 'r') as f:
                self.history = json.loads(f.read())
        print('[D> Config read')

    @staticmethod
    def logout() -> None:
        """Logs out and clears the stored authentication data"""
        api.logout()
        subprocess.Popen(os.path.abspath(inspect.getsourcefile(lambda: 0)))
        sys.exit()

    def run_oauth(self) -> None:
        """Runs the web oauth server for deezer login"""
        api.gen_oauth_token(APP_DATA_PATH)
        self.update_config()

    def createLoginFailedPage(self, errcode: str = ''):
        """Creates the error page for the login"""
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        v_layout = QVBoxLayout()
        main_layout.addStretch()
        main_layout.addLayout(v_layout)
        main_layout.addStretch()

        title = QLabel("Something wen't wrong")
        title.setFont(QFont(title.font().family(), 15))
        subtitle = QLabel()
        if errcode:
            subtitle.setText('Error Code: ' + errcode)
        else:
            subtitle.setText('An unknown Error occured.')

        backbutton = QPushButton('Back')
        backbutton.clicked.connect(self.createLoginPage)

        v_layout.addStretch()
        v_layout.addWidget(title)
        v_layout.addWidget(subtitle)
        v_layout.addWidget(backbutton)
        v_layout.addStretch()

        self.setCentralWidget(main_widget)

    def createWebLoginPage(self):
        """Creates the web-based login page"""
        def process_return(html):
            """Runs when the html was fully loaded. Processes the html to find the success or error message."""
            if html is None:
                self.closeLocked = False
                return
            match = re.match('Error: ([a-zA-Z]*)\. You may close this tab now', html)
            if html == 'Valid. You may close this tab now':
                self.closeLocked = False
                self.update_config()
                if not bool(self.config_arl):
                    dialog = NoArlDialog()
                    if dialog.exec_() == QDialog.Accepted:
                        self.update_config()
                    else:
                        self.close()
                self.login()
            elif html == 'Something went wrong. You may close this tab now':
                self.closeLocked = False
                self.createLoginFailedPage()
            elif match:
                self.closeLocked = False
                self.createLoginFailedPage(match.groups()[0])

        def process_added_cookie(cookie):
            """Processes a cookie of the cookie store to find an deezer arl cookie to store and use for login later"""
            cookie = QNetworkCookie(cookie)
            jsonarr = {"name": bytearray(cookie.name()).decode(), "domain": cookie.domain(),
                       "value": bytearray(cookie.value()).decode(),
                       "path": cookie.path(), "expirationDate": cookie.expirationDate().toString(Qt.ISODate),
                       "secure": cookie.isSecure(),
                       "httponly": cookie.isHttpOnly()}
            if jsonarr['name'] == 'arl' and jsonarr['domain'] == '.deezer.com' and len(jsonarr['value']) == 192:
                print('[D> Arl found and imported.')
                with open(os.path.expanduser('~/.config/deezium/arl.dat'), 'w') as f:
                    f.write(jsonarr['value'])

        def load_finished():
            """Runs when the html was fully loaded and calls the parser with parts out of the html"""
            login_webengine.page().runJavaScript("document.getElementsByTagName('pre')[0].innerHTML;", process_return)

        def abort():
            """Aborts the login process by sending one request to the oauth server to shut it down"""
            try:
                api.requests.get('http://localhost:3875')
            except api.requests.exceptions.ConnectionError:
                pass
            self.createLoginPage()

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        abort_button = QPushButton('Abort login')
        abort_button.clicked.connect(abort)

        login_webengine = QWebEngineView()
        login_webengine.load(QUrl(
            'https://connect.deezer.com/oauth/auth.php?app_id=663691&redirect_uri=http://localhost:3875/&perms=basic_access,email,offline_access,manage_library,manage_community,delete_library,listening_history'))
        login_webengine.loadFinished.connect(load_finished)
        login_webengine.page().profile().cookieStore().cookieAdded.connect(process_added_cookie)

        main_layout.addWidget(abort_button)
        main_layout.addWidget(login_webengine)

        self.setCentralWidget(main_widget)

    def createLoginPage(self):
        """Creates the login page"""
        def login():
            """Prepares and runs the background job for the oauth server"""
            self.closeLocked = True
            # file deepcode ignore MissingAPI: this is required, because the application has to run the login server in the background, to not freeze the gui.
            login_thread = threading.Thread(target=self.run_oauth)
            login_thread.start()
            self.createWebLoginPage()

        login_widget = QWidget()
        login_mlayout = QHBoxLayout()
        login_layout = QVBoxLayout()
        login2_layout = QVBoxLayout()

        login_widget.setLayout(login_mlayout)
        login_mlayout.addStretch()
        login_mlayout.addLayout(login_layout)
        login_mlayout.addLayout(login2_layout)
        login_mlayout.addStretch()

        group_box = QGroupBox('Login')
        group_layout = QVBoxLayout()
        group_box.setLayout(group_layout)

        login_layout.addStretch()
        login2_layout.addStretch()

        title_layout = QHBoxLayout()
        title_layout.addStretch()

        logo_layout = QHBoxLayout()
        logo = QLabel()
        logop = QPixmap(APP_DATA_PATH + 'deezium256.png')
        logo.setPixmap(logop)
        login_title = QLabel(APP_NAME)
        login_title.setFont(QFont(login_title.font().family(), 20))
        title_layout.addWidget(login_title)
        title_layout.addStretch()
        logo_layout.addStretch()
        logo_layout.addWidget(logo)
        logo_layout.addStretch()
        group_layout.addLayout(logo_layout)
        group_layout.addLayout(title_layout)

        login_button = QPushButton('Login with Deezer')
        login_button.setIcon(QIcon(APP_DATA_PATH + 'deezer_logo.png'))
        group_layout.addWidget(login_button)

        disclaimer = QGroupBox('Disclaimer')
        dis_layout = QVBoxLayout()
        dis_layout.addWidget(QLabel('<b>NOT AFFILIATED WITH DEEZER</b>'))
        dis_layout.addWidget(QLabel('The Author of this program is'))
        dis_layout.addWidget(QLabel('not responsible for the usage'))
        dis_layout.addWidget(QLabel('of this program by other people.'))
        dis_layout.addWidget(QLabel())
        dis_layout.addWidget(QLabel("The Author does not recommend"))
        dis_layout.addWidget(QLabel("you doing this illegally or"))
        dis_layout.addWidget(QLabel("against Deezer's terms of service."))
        dis_layout.addWidget(QLabel())
        dis_layout.addWidget(QLabel("Seriously please buy an subscription"))
        dis_layout.addWidget(QLabel("when you use this program. The artists also"))
        dis_layout.addWidget(QLabel("want money for their work. Thank you."))

        disclaimer.setLayout(dis_layout)

        login_layout.addWidget(group_box)
        login2_layout.addWidget(disclaimer)

        login_layout.addStretch()
        login2_layout.addStretch()

        login_button.clicked.connect(login)

        self.setCentralWidget(login_widget)

    def createMainPage(self):
        """Creates the main page or "home" page or "favorites" page"""
        def search():
            query = searchbar.text()
            self.createSearchresultPage(query)

        def album_clicked(aid):
            self.createAlbumoverviewPage(aid)

        def show_ftracks():
            self.createPlaylistPage(f_tracks)

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        title_layout = QHBoxLayout()
        title_text = QLabel('Your Favorites')
        title_text.setFont(QFont(title_text.font().family(), 16))
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        searchbar = QLineEdit()
        searchbar.setPlaceholderText('Search for music and audiobooks')
        searchbutton = QPushButton('Search')
        settings_button = QPushButton("")
        settings_button.setFixedSize(30, 30)
        settings_button.setFont(QFont('Material Icons', 12))
        settings_button.clicked.connect(self.createSettingsPage)
        title_layout.addWidget(searchbar)
        title_layout.addWidget(searchbutton)
        title_layout.addWidget(settings_button)

        searchbar.returnPressed.connect(search)
        searchbutton.clicked.connect(search)

        main_layout.addLayout(title_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)

        history_label = QLabel('History')
        history_label.setFont(QFont(history_label.font().family(), 14))

        if self.history:
            history_widget = QScrollArea()
            history_widget.setWidgetResizable(True)
            history_swidget = QAlbumHList(self.history, deezerclient=self.deezpy_session)
            history_swidget.album_clicked.connect(album_clicked)
            history_widget.setWidget(history_swidget)

        else:
            history_widget = QLabel("There's no history here. So you have to write history now, then.")

        f_title = QLabel('Favorites')
        f_title.setFont(QFont(history_label.font().family(), 14))

        f_albums = self.deezpy_session.get_user_albums()
        f_album_p = QPixmap()
        if f_albums:
            f_album_p.loadFromData(api.download_albumcover_s(self.deezpy_session, f_albums[0].id))
        f_album_w = QHClickList('Albums', f_album_p, f'{f_albums.total} albums total',
                                f'{f_albums[0].title} - {f_albums[0].artist.name}')

        f_tracks = self.deezpy_session.get_user_tracks()
        f_track_p = QPixmap()
        r_track = random.choice(f_tracks)
        if f_tracks:
            try:
                f_track_p.loadFromData(api.download_albumcover_s(self.deezpy_session, r_track.album.id))
            except api.deezer.exceptions.DeezerErrorResponse:
                print('[W> Loading of f_track_p failed')

        f_track_w = QHClickList('Tracks', f_track_p, f'{f_tracks.total} tracks total',
                                f'{r_track.title} - {r_track.artist.name}')
        f_track_w.action.connect(show_ftracks)

        scroll_layout.addWidget(history_label)
        scroll_layout.addWidget(history_widget)
        scroll_layout.addWidget(f_title)
        scroll_layout.addWidget(f_album_w)
        scroll_layout.addWidget(f_track_w)
        scroll_layout.addStretch()

        main_layout.addWidget(scroll_area)
        main_layout.addWidget(self.play_widget)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def createSearchresultPage(self, query):
        """Searches deezer and creates the search results page"""
        def search():
            query = searchbar.text()
            self.createSearchresultPage(query)

        def album_clicked(aid):
            self.createAlbumoverviewPage(aid)

        def artist_clicked(aid):
            print(aid)

        def track_clicked(tid):
            self.playtrack(tid)

        def playlist_clicked(pid):
            print(pid)

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        title_layout = QHBoxLayout()
        back_button = QPushButton('')
        back_button.setFont(QFont('Material Icons', 12))
        back_button.clicked.connect(self.createMainPage)
        back_button.setFixedSize(30, 30)
        title_layout.addWidget(back_button)
        title_text = QLabel('Search - Results for ' + query)
        title_text.setFont(QFont(title_text.font().family(), 16))
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        searchbar = QLineEdit()
        searchbar.setPlaceholderText('Search for music and audiobooks')
        searchbutton = QPushButton('Search')
        searchbar.setText(query)
        title_layout.addWidget(searchbar)
        title_layout.addWidget(searchbutton)

        searchbar.returnPressed.connect(search)
        searchbutton.clicked.connect(search)

        main_layout.addLayout(title_layout)

        search_area = QScrollArea()
        search_area.setWidgetResizable(True)
        search_area.setFrameShape(QFrame.NoFrame)
        search_widget = QWidget()
        search_layout = QVBoxLayout()
        search_widget.setLayout(search_layout)
        search_area.setWidget(search_widget)

        alb_title = QLabel('Albums')
        alb_title.setFont(QFont(title_text.font().family(), 14))
        album_search = []
        for s in self.deezpy_session.search_albums(query):
            album_search.append(s.id)
        if len(album_search) == 0:
            album_widget = QLabel("No results found. Here's a note for you: 🎵")
        else:
            album_widget = QAlbumList(album_search[:5], deezerclient=self.deezpy_session)
            album_widget.album_clicked.connect(album_clicked)
            album_widget.artist_clicked.connect(artist_clicked)

        track_title = QLabel('Tracks')
        track_title.setFont(QFont(title_text.font().family(), 14))
        track_search = []
        for s in self.deezpy_session.search(query):
            track_search.append(s.id)
        if len(track_search) == 0:
            track_widget = QLabel("No results found. Here's a banana for you: 🍌") # as the creator of this program,
            #                                                                        i dont like bananas. accept it!
        else:
            track_widget = QTrackList(track_search[:5], deezerclient=self.deezpy_session)
            track_widget.album_clicked.connect(album_clicked)
            track_widget.artist_clicked.connect(artist_clicked)
            track_widget.track_clicked.connect(track_clicked)

        art_title = QLabel('Artists')
        art_title.setFont(QFont(title_text.font().family(), 14))
        artist_search = []
        for s in self.deezpy_session.search_artists(query):
            artist_search.append(s.id)
        if len(artist_search) == 0:
            artist_widget = QLabel("No results found. Here's a tree for you: 🌲")
        else:
            artist_widget = QArtistList(artist_search[:5], deezerclient=self.deezpy_session)
            artist_widget.artist_clicked.connect(artist_clicked)

        pl_title = QLabel('Playlists')
        pl_title.setFont(QFont(title_text.font().family(), 14))
        playlist_search = []
        for s in self.deezpy_session.search_playlists(query):
            playlist_search.append(s.id)
        if len(playlist_search) == 0:
            playlist_widget = QLabel("No results found. Here's a cat for you: 🐱")
        else:
            playlist_widget = QPlayList(playlist_search[:5], deezerclient=self.deezpy_session)
            playlist_widget.playlist_clicked.connect(playlist_clicked)

        search_layout.addWidget(alb_title)
        search_layout.addWidget(album_widget)
        search_layout.addWidget(track_title)
        search_layout.addWidget(track_widget)
        search_layout.addWidget(art_title)
        search_layout.addWidget(artist_widget)
        search_layout.addWidget(pl_title)
        search_layout.addWidget(playlist_widget)
        search_layout.addStretch()

        # main_layout.addStretch()
        main_layout.addWidget(search_area)
        main_layout.addWidget(self.play_widget)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def createAlbumoverviewPage(self, albumid):
        def search():
            query = searchbar.text()
            self.createSearchresultPage(query)

        def play():
            self.playalbums(trackids)

        def playitem(tid):
            self.playalbums(trackids, first=tid)

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        album = self.deezpy_session.get_album(albumid)
        tracks = album.get_tracks()
        trackids = api.conv_paginated_ids(tracks)

        title_layout = QHBoxLayout()
        back_button = QPushButton('')
        back_button.setFont(QFont('Material Icons', 12))
        back_button.clicked.connect(self.createMainPage)
        back_button.setFixedSize(30, 30)
        title_layout.addWidget(back_button)
        title_text = QLabel(album.title + ' - ' + album.artist.name)
        title_text.setFont(QFont(title_text.font().family(), 16))
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        searchbar = QLineEdit()
        searchbar.setPlaceholderText('Search for music and audiobooks')
        searchbutton = QPushButton('Search')
        title_layout.addWidget(searchbar)
        title_layout.addWidget(searchbutton)

        searchbar.returnPressed.connect(search)
        searchbutton.clicked.connect(search)

        search_area = QScrollArea()
        search_area.setWidgetResizable(True)
        search_area.setFrameShape(QFrame.NoFrame)
        search_widget = QWidget()
        search_layout = QVBoxLayout()
        search_widget.setLayout(search_layout)
        search_area.setWidget(search_widget)

        header_layout = QHBoxLayout()

        cover = QLabel()
        cover_pixmap = QPixmap()
        cover_pixmap.loadFromData(api.download_albumcover_m(self.deezpy_session, album.id))
        cover.setPixmap(cover_pixmap)
        header_layout.addWidget(cover)

        sidepanel_layout = QVBoxLayout()
        header_layout.addLayout(sidepanel_layout)
        header_layout.addStretch()

        tit_label = QLabel(f'<b>Number of titles:</b> {tracks.total}')
        len_label = QLabel(f'<b>Length:</b> {api.convert_sec_to_min(album.duration)}')
        rel_label = QLabel(f'<b>Release date:</b> {album.release_date.strftime("%Y-%m-%d")}')
        play_button = QPushButton('Play album')
        play_button.clicked.connect(play)
        author_button = QPushButton('Visit ' + album.artist.name)
        clean_button = QPushButton('Clean cached tracks')
        sidepanel_layout.addWidget(tit_label)
        sidepanel_layout.addWidget(len_label)
        sidepanel_layout.addWidget(rel_label)
        sidepanel_layout.addWidget(play_button)
        sidepanel_layout.addWidget(author_button)
        sidepanel_layout.addWidget(clean_button)

        search_layout.addLayout(header_layout)

        track_widget = QTrackList(trackids, deezerclient=self.deezpy_session, show_album=False)
        track_widget.track_clicked.connect(playitem)
        #track_widget.add_playlist.
        #track_widget.add_queue.
        track_widget.toggle_fav.connect(self.toggle_favorite_track)

        search_layout.addWidget(track_widget)
        search_layout.addStretch()

        main_layout.addLayout(title_layout)
        main_layout.addWidget(search_area)
        main_layout.addWidget(self.play_widget)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def createSettingsPage(self):
        def update_cbutton():
            cleanc_button.setDisabled(not (cleanc_i1.isChecked() or cleanc_i2.isChecked() or cleanc_i3.isChecked()))
            if cleanc_i1.isChecked() or cleanc_i2.isChecked() or cleanc_i3.isChecked():
                cleanc_button.setStyleSheet('color: white; background-color: #a50003')
            else:
                cleanc_button.setStyleSheet('')

        def cbutton_clicked():
            cleanc_i1.setChecked(False)
            cleanc_i2.setChecked(False)
            cleanc_i3.setChecked(False)
            print('[D> Cleanup: Cleanup started')
            if cleanc_i1.isChecked():
                print('[D> Cleanup: Cleaning Album covers (medium)')
                api.clean_albumcovers(api.get_cached_albumcovers(size='m'), size='m')
            if cleanc_i2.isChecked():
                print('[D> Cleanup: Cleaning Album covers (medium)')
                api.clean_albumcovers(api.get_cached_albumcovers(size='s'), size='s')
            if cleanc_i3.isChecked():
                print('[D> Cleanup: Cleaning Tracks (cached)')
                api.clean_trackids(api.get_cached_tracks())
            print('[D> Cleanup: Finished')
            sys.exit()

        def chbutton_clicked():
            print('[D> Cleanup: Cleaning History')
            os.remove(os.path.expanduser('~/.config/deezium/history'))
            os.remove(os.path.expanduser('~/.config/deezium/lastplay'))
            sys.exit()

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        title_layout = QHBoxLayout()
        back_button = QPushButton('')
        back_button.setFont(QFont('Material Icons', 12))
        back_button.clicked.connect(self.createMainPage)
        back_button.setFixedSize(30, 30)
        title_layout.addWidget(back_button)
        title_text = QLabel('Settings')
        title_text.setFont(QFont(title_text.font().family(), 16))
        title_layout.addWidget(title_text)

        search_area = QScrollArea()
        search_area.setWidgetResizable(True)
        search_area.setFrameShape(QFrame.NoFrame)
        search_widget = QWidget()
        search_layout = QVBoxLayout()
        search_widget.setLayout(search_layout)
        search_area.setWidget(search_widget)

        account_box = QGroupBox('Account')
        account_layout = QVBoxLayout(account_box)
        account_name = QLabel('Currently logged in as ' + self.deezpy_session.get_user().name)
        logout_button = QPushButton('Log out')
        logout_button.setStyleSheet('color: white; background-color: #a50003')
        logout_button.clicked.connect(self.logout)
        account_layout.addWidget(account_name)
        account_layout.addWidget(logout_button)

        data_box = QGroupBox('Data managment')
        data_layout = QVBoxLayout(data_box)
        cleanc_title = QLabel('Clean cached data:')
        cleanc_subtitle = QLabel("Anything below can't be reverted!")
        cleanc_i1 = QCheckBox('Album covers (medium)')
        cleanc_i2 = QCheckBox('Album covers (small)')
        cleanc_i3 = QCheckBox('Tracks (cached)')
        cleanc_i1.toggled.connect(update_cbutton)
        cleanc_i2.toggled.connect(update_cbutton)
        cleanc_i3.toggled.connect(update_cbutton)
        cleanc_button = QPushButton('Clear data and close')
        cleanc_button.setStyleSheet('')
        cleanc_button.setDisabled(True)
        cleanc_button.clicked.connect(cbutton_clicked)
        cleanc_label = QLabel('Cleaning can take a while')
        data_layout.addWidget(cleanc_subtitle)
        data_layout.addWidget(cleanc_title)
        data_layout.addWidget(cleanc_i1)
        data_layout.addWidget(cleanc_i2)
        data_layout.addWidget(cleanc_i3)
        data_layout.addWidget(cleanc_button)
        data_layout.addWidget(cleanc_label)

        cleanh_button = QPushButton('Clear history and close')
        cleanh_button.clicked.connect(chbutton_clicked)
        data_layout.addWidget(cleanh_button)

        search_layout.addWidget(account_box)
        search_layout.addWidget(data_box)
        search_layout.addStretch()

        main_layout.addLayout(title_layout)
        main_layout.addWidget(search_area)
        main_layout.addWidget(self.play_widget)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def createPlaylistPage(self, tracks: api.deezer.PaginatedList[api.deezer.Track], ptype: str = 'fa'):
        def playitem(tid):
            self.playlist(pl_trackids, first=tid)

        def play():
            self.playlist(pl_trackids)

        def search():
            query = searchbar.text()
            self.createSearchresultPage(query)

        pl_coverpix = QPixmap()
        if ptype == 'fa':
            pl_title = 'Favorite Tracks'
            pl_author = self.deezpy_session.get_user().name
            with open(APP_DATA_PATH + 'favorite.png', 'rb') as f:
                pl_coverpix.loadFromData(f.read())
        else:
            pl = self.deezpy_session.get_playlist(ptype)
            pl_title = pl.title
            pl_author = pl.creator.name
            pl_coverpix.loadFromData(api.download_playlcover_m(self.deezpy_session, pl.id))

        pl_trackids = []
        pl_length = 0
        for track in tracks:
            pl_trackids.append(track.id)
            pl_length += track.duration
        pl_totalt = tracks.total

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        title_layout = QHBoxLayout()
        back_button = QPushButton('')
        back_button.setFont(QFont('Material Icons', 12))
        back_button.clicked.connect(self.createMainPage)
        back_button.setFixedSize(30, 30)
        title_layout.addWidget(back_button)
        title_text = QLabel(pl_title + ' - ' + pl_author)
        title_text.setFont(QFont(title_text.font().family(), 16))
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        searchbar = QLineEdit()
        searchbar.setPlaceholderText('Search for music and audiobooks')
        searchbutton = QPushButton('Search')
        title_layout.addWidget(searchbar)
        title_layout.addWidget(searchbutton)

        searchbar.returnPressed.connect(search)
        searchbutton.clicked.connect(search)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)

        header_layout = QHBoxLayout()

        cover = QLabel()
        cover.setPixmap(pl_coverpix)
        header_layout.addWidget(cover)

        sidepanel_layout = QVBoxLayout()
        header_layout.addLayout(sidepanel_layout)
        header_layout.addStretch()

        tit_label = QLabel(f'<b>Number of titles:</b> {pl_totalt}')
        len_label = QLabel(f'<b>Length:</b> {api.convert_sec_to_min(pl_length)}')
        play_button = QPushButton('Play playlist')
        play_button.clicked.connect(play)
        author_button = QPushButton('Visit ' + pl_author)
        clean_button = QPushButton('Clean cached tracks')
        sidepanel_layout.addWidget(tit_label)
        sidepanel_layout.addWidget(len_label)
        sidepanel_layout.addWidget(play_button)
        sidepanel_layout.addWidget(author_button)
        sidepanel_layout.addWidget(clean_button)

        scroll_layout.addLayout(header_layout)

        if pl_totalt:
            track_widget = QTrackList(pl_trackids, deezerclient=self.deezpy_session)
            track_widget.track_clicked.connect(playitem)
            track_widget.toggle_fav.connect(self.toggle_favorite_track)
        else:
            track_widget = QLabel('This playlist is empty.')
        scroll_layout.addWidget(track_widget)

        main_layout.addLayout(title_layout)
        main_layout.addWidget(scroll_area)
        main_layout.addWidget(self.play_widget)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def save_history(self):
        if self.logged_in and self.play_currentlist != [] and self.play_currenttrack:
            print('[D> State saved')
            os.makedirs(os.path.expanduser('~/.config/deezium/'), exist_ok=True)
            json_data = json.dumps({'current_id': self.play_currenttrack, 'current_play': self.play_currentlist,
                                    'looping': self.play_looping, 'position': self.player.position(),
                                    'volume': self.player.volume()})
            with open(os.path.expanduser('~/.config/deezium/lastplay'), 'w') as f:
                f.write(json_data)
            with open(os.path.expanduser('~/.config/deezium/history'), 'w') as f:
                f.write(json.dumps(self.history))

    def closeEvent(self, event):
        if not self.closeLocked:
            os.remove(os.path.expanduser('~/.cache/deezium/.cache'))
            self.save_history()
            super().closeEvent(event)
        else:
            return event.ignore()


def format_traceback(trb: str):
    print(trb)
    dialog = ErrorDialog(trb)
    dialog.exec_()
    sys.exit()


def main(argv):
    app = QApplication(sys.argv)
    app.setDesktopFileName('deezium')

    try:
        deezium = MainWindow()
        deezium.show()
    except Exception:
        trb = traceback.format_exc()
        format_traceback(trb)

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
