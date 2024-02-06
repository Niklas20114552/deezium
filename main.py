#!/usr/bin/python3
import sys, os, platform, api, deezloader.exceptions, json, threading
from PyQt5.QtCore import QUrl, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QSlider, QProgressBar, QDialog, QGroupBox, QScrollArea, QFrame
from configparser import ConfigParser

config = ConfigParser()

APP_NAME: str = "Deezium"
if platform.system() == 'Windows':
    APP_DATA_PATH: str = "C:\\Program Files\\Deezium\\"
elif platform.system() == 'Linux':
    APP_DATA_PATH: str = '/usr/share/deezium/'
else:
    print('Sorry, but your Operating System is not supported.')
    sys.exit()
    
    
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
            pix.loadFromData(api.download_albumcover(self.cli, album.id))
            dt['icon-pixmap'] = pix
            dt['dpy-album'] = album
            self.data.append(dt)
            
    def construct_list(self):
        for album in self.data:
            row = QHBoxLayout()
            icon_label = QLabel()
            icon_label.setPixmap(album['icon-pixmap'])
            icon_label.mousePressEvent = lambda event, album_id=album['dpy-album'].id: self.album_clicked.emit(album_id)
            text_label = QLabel(f"<b>{album['name']}</b> -")
            text_label.mousePressEvent = lambda event, album_id=album['dpy-album'].id: self.album_clicked.emit(album_id)
            artist_label = QLabel(album['artist'].name)
            artist_label.mousePressEvent = lambda event, artist_id=album['artist'].id: self.artist_clicked.emit(artist_id)
            duration = QLabel(f" (<i>{round(album['length'] / 60)} min long</i>)")
            row.addWidget(icon_label)
            row.addWidget(text_label)
            row.addWidget(artist_label)
            row.addWidget(duration)
            row.addStretch()
            self.main_layout.addLayout(row)
            
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
            icon_label.mousePressEvent = lambda event, artist_id=artist['dpy-artist'].id: self.artist_clicked.emit(artist_id)
            text_label = QLabel(f"<b>{artist['name']}</b>")
            text_label.mousePressEvent = lambda event, artist_id=artist['dpy-artist'].id: self.artist_clicked.emit(artist_id)
            row.addWidget(icon_label)
            row.addWidget(text_label)
            row.addStretch()
            self.main_layout.addLayout(row)
            
class QTrackList(QWidget):
    artist_clicked = pyqtSignal(int)
    album_clicked = pyqtSignal(int)
    track_clicked = pyqtSignal(int)

    def __init__(self, trackids: list[int], deezerclient: api.deezer.Client, show_album: bool = True,
                 show_icons: bool = True, show_artist: bool = True):
        super().__init__()
        self.trackids = trackids
        self.cli = deezerclient
        self.data = []
        self.show_album = show_album
        self.show_icons = show_icons
        self.show_artist = show_artist
        self.construct_items()
        self.main_layout = QVBoxLayout(self)
        self.construct_list()

    def construct_items(self):
        for track in self.trackids:
            dt = {}
            track = self.cli.get_track(track)
            dt['name'] = track.title
            dt['artist'] = track.artist
            dt['length'] = track.duration
            dt['album'] = track.album
            if self.show_icons:
                pix = QPixmap()
                pix.loadFromData(api.download_albumcover(self.cli, track.album.id))
                dt['icon-pixmap'] = pix
            dt['dpy-track'] = track
            self.data.append(dt)

    def construct_list(self):
        for track in self.data:
            row = QHBoxLayout()
            if self.show_icons:
                icon_label = QLabel()
                icon_label.setPixmap(track['icon-pixmap'])
                icon_label.mousePressEvent = lambda event, track_id=track['dpy-track'].id: self.track_clicked.emit(track_id)
            text_label = QLabel(f"<b>{track['name']}</b> -")
            text_label.mousePressEvent = lambda event, track_id=track['dpy-track'].id: self.track_clicked.emit(track_id)
            if self.show_artist:
                artist_label = QLabel(track['artist'].name)
                artist_label.mousePressEvent = lambda event, artist_id=track['artist'].id: self.artist_clicked.emit(artist_id)
            duration = QLabel(f" (<i>{round(track['length'] / 60)} min long</i>)")
            if self.show_album:
                album_label = QLabel(f"in <b>{track['album'].title}</b> by <i>{track['album'].artist.name}</i>")
                album_label.mousePressEvent = lambda event, album_id=track['album'].id: self.album_clicked.emit(album_id)
            if self.show_icons:
                row.addWidget(icon_label)
            row.addWidget(text_label)
            if self.show_artist:
                row.addWidget(artist_label)
            row.addWidget(duration)
            row.addStretch()
            if self.show_album:
                row.addWidget(album_label)
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
            icon_label.mousePressEvent = lambda event, artist_id=playlist['author'].id: self.playlist_clicked.emit(artist_id)
            text_label = QLabel(f"<b>{playlist['name']}</b> -")
            text_label.mousePressEvent = lambda event, artist_id=playlist['author'].id: self.playlist_clicked.emit(artist_id)
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
        self.logged_in = False
        self.play_currenttrack = None
        self.play_looping: int = 0
        
        self.player = QMediaPlayer(self)
        self.player.setVolume(50)
        
        self.play_currentlist = []
        
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
        self.play_volume.setRange(0, 150)
        self.play_volume.setValue(75)
        self.play_volume.setMinimumWidth(75)
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
                data = json.loads(open(os.path.expanduser('~/.config/deezium/lastplay'), 'r').read())
                self.streamtrackid(data['current_id'], start=False)
                self.play_currentlist = data['current_play']
                self.play_looping = data['looping']
                self.update_loopbutton()
                self.player.setPosition(data['position'])
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
        if not by: by = 1
        currenti = self.play_currentlist.index(int(self.play_currenttrack))
        self.streamtrackid(self.play_currentlist[(currenti + by) % len(self.play_currentlist)])
        
    def skip_backward(self, by=1):
        if not by: by = 1
        currenti = self.play_currentlist.index(int(self.play_currenttrack))
        self.streamtrackid(self.play_currentlist[currenti - by])
            
    def streamtrackid(self, id, start=True):
        def stream():
            path = api.download_track(self.deezdw_session, id)
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
            if start: self.player.play()
            self.play_currenttrack = id
            self.update_player(self.player.state())
            bg = api.calc_background_color(self.deezpy_session.get_track(id).album.cover_big)
            fg = api.calc_foreground_color(bg)
            self.play_widget.setStyleSheet(f'background-color: {bg}; color: {fg}')
            # waitdialog.accept()
            
        # waitdialog = ProgressDialog('Buffering')
        # dthread = threading.Thread(target=stream)
        # dthread.start()
        # waitdialog.exec_()
        stream()
        
    def playtrack(self, id):
        self.streamtrackid(id, start=True)
        self.play_currentlist = [id]
        
    def playalbums(self, ids, first=None):
        if not first:
            self.streamtrackid(ids[0], start=True)
        else:
            self.streamtrackid(first, start=True)
        self.play_currentlist = ids
        
    def status_switch_b(self):
        self.play_widget.setLayout(self.playb_layout)
        
    def update_player(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_pauseb.setText('')
        else:
            self.play_pauseb.setText('')
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
            buffer_thread = threading.Thread(target=buffer)
            buffer_thread.start()
        
    def set_volume(self, vol):
        self.player.setVolume(vol)
        
    def update_seeker(self, duration):
        self.play_seeker.setValue(duration)
        self.play_state.setText(api.ms_to_str(duration) + '/' + api.ms_to_str(self.player.duration()))
            
    def playback(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def set_position(self, position):
        self.player.setPosition(position)
        
    def login(self):
        print('[D> Initing Sessions')
        self.init_sessions()
        print('[D> Creating Main Page')
        self.createMainPage()
        self.logged_in = True
        print('[D> Restoring state')
        self.read_playstate()
    
    def init_sessions(self):
        if not self.deezdw_session:
            try:
                self.deezdw_session = api.DWLogin(self.config_arl)
            except deezloader.exceptions.BadCredentials:
                os.remove(os.path.expanduser('~/.config/deezium/arl.dat'))
                self.update_config()
                self.createLoginPage()
        if not self.deezpy_session:
            try:
                self.deezpy_session = api.deezer.Client(access_token=self.config_aro)
            except api.deezer.exceptions.DeezerErrorResponse:
                os.remove(os.path.expanduser('~/.config/deezium/aro.dat'))
                self.update_config()
                self.createLoginPage()
        
    def update_config(self):
        print('[D> Config read')
        self.config_aro = api.get_oauth_token()
        self.config_arl = api.get_login_token()
    
    def createLoginPage(self):
        def login():
            api.gen_oauth_token()
            self.update_config()
            update_buttons()
            
        def update_buttons():
            login_button.setDisabled(bool(self.config_aro))
            arl_input.setDisabled(bool(self.config_arl))
            arl_label.setDisabled(bool(self.config_arl))
            continue_button.setDisabled(not ((bool(self.config_arl) or len(arl_input.text()) == 192) and bool(self.config_aro)))
            
        def continuelogin():
            if arl_input.isEnabled():
                open(os.path.expanduser('~/.config/deezium/arl.dat'), 'w').write(arl_input.text())
            self.update_config()
            if bool(self.config_arl) and bool(self.config_aro):
                self.login()
        
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
        
        note_label = QLabel('To get Deezium working properly,')
        note2_label = QLabel('you have to complete 2 steps:')
        group_layout.addWidget(note_label)
        group_layout.addWidget(note2_label)
        
        login_button = QPushButton('1. Login with Deezer')
        login_button.setIcon(QIcon(APP_DATA_PATH + 'deezer_logo.png'))
        group_layout.addWidget(login_button)
        arl_label = QLabel('2. Enter your Deezer ARL:')
        arl_input = QLineEdit()
        group_layout.addWidget(arl_label)
        group_layout.addWidget(arl_input)
        
        continue_button = QPushButton('Continue')
        group_layout.addWidget(continue_button)
        
        disclaimer = QGroupBox('Disclaimer')
        dis_layout = QVBoxLayout()
        text = []
        text.append(QLabel('<b>NOT AFFILIATED WITH DEEZER</b>'))
        text.append(QLabel('The Author of this program is'))
        text.append(QLabel('not responsible for the usage'))
        text.append(QLabel('of this program by other people.'))
        text.append(QLabel())
        text.append(QLabel("The Author does not recommend"))
        text.append(QLabel("you doing this illegally or"))
        text.append(QLabel("against Deezer's terms of service."))
        text.append(QLabel())
        text.append(QLabel("Seriously please buy an abo when you"))
        text.append(QLabel("this program. The artists also want"))
        text.append(QLabel("money for their work. Thank you."))
        for t in text:
            dis_layout.addWidget(t)
        
        disclaimer.setLayout(dis_layout)
        
        login_layout.addWidget(group_box)
        login2_layout.addWidget(disclaimer)
        
        login_layout.addStretch()
        login2_layout.addStretch()
        
        login_button.clicked.connect(login)
        arl_input.textChanged.connect(update_buttons)
        continue_button.clicked.connect(continuelogin)

        self.setCentralWidget(login_widget)
        update_buttons()
        
    def createMainPage(self):
        def stream():
            self.streamtrackid(id_input.text())
        
        def search():
            query = searchbar.text()
            self.createSearchresultPage(query)
            
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
        title_layout.addWidget(searchbar)
        title_layout.addWidget(searchbutton)
        
        searchbar.returnPressed.connect(search)
        searchbutton.clicked.connect(search)
        
        main_layout.addLayout(title_layout)
        
        id_input = QLineEdit()
        id_input.returnPressed.connect(stream)
        
        main_layout.addWidget(id_input)
        
        main_layout.addStretch()
        main_layout.addWidget(self.play_widget)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
    def createSearchresultPage(self, query):
        def search():
            query = searchbar.text()
            self.createSearchresultPage(query)
            
        def album_clicked(id):
            self.createAlbumoverviewPage(id)
            
        def artist_clicked(id):
            print(id)
            
        def track_clicked(id):
            self.playtrack(id)
            
        def playlist_clicked(id):
            print(id)
            
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
            track_widget = QLabel("No results found. Here's a banana for you: 🍌")
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
            
        def playitem(id):
            self.playalbums(trackids, first=id)
            
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        album = self.deezpy_session.get_album(albumid)
        tracks = album.get_tracks()
        trackids = []
        for track in tracks:
            trackids.append(track.id)
        
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
        cover_pixmap.loadFromData(api.requests.get(album.cover_medium).content)
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
        sidepanel_layout.addWidget(tit_label)
        sidepanel_layout.addWidget(len_label)
        sidepanel_layout.addWidget(rel_label)
        sidepanel_layout.addWidget(play_button)
        sidepanel_layout.addWidget(author_button)
        
        search_layout.addLayout(header_layout)
        
        track_widget = QTrackList(trackids, deezerclient=self.deezpy_session, show_album=False)
        track_widget.track_clicked.connect(playitem)
        search_layout.addWidget(track_widget)
        search_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        main_layout.addWidget(search_area)
        main_layout.addWidget(self.play_widget)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
    def closeEvent(self, event):
        if self.logged_in and self.play_currentlist != [] and self.play_currenttrack:
            print('[D> State saved')
            os.makedirs(os.path.expanduser('~/.config/deezium/'), exist_ok=True)
            json_data = json.dumps({'current_id': self.play_currenttrack, 'current_play': self.play_currentlist, 'looping': self.play_looping, 'position': self.player.position()})
            open(os.path.expanduser('~/.config/deezium/lastplay'), 'w').write(json_data)
        super().closeEvent(event)

       
       
def main(argv):
    app = QApplication(sys.argv)
    app.setDesktopFileName('deezium')

    deezium = MainWindow()
    deezium.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
