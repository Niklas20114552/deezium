#!/usr/bin/python3
import os
import sys, json, subprocess, inspect, random, traceback, deezer
from PyQt5.QtWidgets import QApplication, QMainWindow, QLineEdit, QScrollArea, QCheckBox
from configparser import ConfigParser
import src.caching.albumCovers
import src.utils as utils
from src.login.loginManager import LoginManager
from src.ui.widgets.QAlbumHList import QAlbumHList
from src.ui.widgets.QAlbumList import QAlbumList
from src.ui.widgets.QArtistList import QArtistList
from src.ui.widgets.QHClickList import QHClickList
from src.ui.widgets.QPlayList import QPlayList
from src.ui.widgets.QTrackList import QTrackList
from src.ui.widgets.SVGButton import SVGButton
from src.ui.widgets.errorDialog import ErrorDialog
from src.ui.loginPages import *
from src.ui.player import Player

config = ConfigParser()
APP_DEVMODE: bool = False

APP_NAME: str = "Deezium"
if platform.system() == "Windows":
    APP_DATA_PATH: str = "C:\\Program Files\\Deezium\\"
elif platform.system() == "Linux":
    APP_DATA_PATH: str = "/usr/share/deezium/"
else:
    print("Sorry, but your Operating System is not supported.")
    sys.exit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(APP_DATA_PATH + "deezium.png"))
        self.setMinimumSize(800, 600)

        # TODO: Implement session system
        self.session = LoginManager('default', APP_DATA_PATH)
        self.session_path = os.path.expanduser('~/.config/deezium/default')
        
        self.history = []
        self.closeLocked: bool = False
        
        self.player = Player(self, self.session)

        print("[D> Main loading")
        self.update_config()
        if self.session.logged_in:
            self.login()
        else:
            self.createLoginPage()

    def insert_history(self, tid):
        if tid in self.history:
            self.history.remove(tid)
        self.history.insert(0, tid)
        self.history = self.history[:10]
        self.save_history()

    def playtrack(self, tid):
        self.player.play_currentlist = [tid]
        self.player.streamtrackid(tid, start=True)
        self.player.update_loopbutton()

    def playalbums(self, ids, first=None):
        self.player.play_currentlist = ids
        if not first:
            self.player.streamtrackid(ids[0], start=True)
        else:
            self.player.streamtrackid(first, start=True)
        self.player.play_looping = 0
        self.player.update_loopbutton()

    def playlist(self, ids, first=None):
        self.player.play_currentlist = ids
        if not first:
            self.player.streamtrackid(ids[0], start=True)
        else:
            self.player.streamtrackid(first, start=True)
        self.player.play_looping = 1
        self.player.update_loopbutton()

    def toggle_favorite_track(self, tid):
        def toggle():
            ids = utils.conv_paginated_ids(self.session.deezer.get_user_tracks())
            if tid in ids:
                self.session.deezer.remove_user_track(tid)
            else:
                self.session.deezer.add_user_track(tid)

        thread = threading.Thread(target=toggle, daemon=True)
        thread.start()

    def login(self):
        """Prepares the player to load the main page and loads old playing state"""
        print("[D> Initializing Sessions")
        self.init_sessions()
        print("[D> Creating Main Page")
        self.createMainPage()
        print("[D> Restoring state")
        self.player.read_playstate()

    def init_sessions(self):
        """Initializes the two online api sessions and if necessary kick back to log in"""
        os.makedirs(os.path.expanduser("~/.cache/deezium/"), exist_ok=True)
        os.chdir(os.path.expanduser("~/.cache/deezium/"))
        self.session.login()

    def update_config(self):
        """READs the config and updates the two token variables accordingly"""
        if os.path.exists(self.session_path + "/history"):
            with open(os.path.expanduser(self.session_path + "/history"), "r") as f:
                self.history = json.loads(f.read())
        print("[D> Config read")

    def logout(self) -> None:
        """Logs out and clears the stored authentication data"""
        self.session.full_logout()
        subprocess.Popen(os.path.abspath(inspect.getsourcefile(lambda: 0)))
        sys.exit()

    def run_oauth(self) -> None:
        """Runs the web oauth server for deezer login"""
        self.session.host_oauth_server()
        self.update_config()

    def createLoginFailedPage(self, errcode: str = ""):
        """Creates the error page for the login"""
        self.setCentralWidget(LoginFailedPage(self, errcode))

    def createWebLoginPage(self):
        """Creates the web-based login page"""

        self.setCentralWidget(WebLoginPage(self))

    def createLoginPage(self):
        """Creates the login page"""
        self.setCentralWidget(LoginPage(self))

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
        title_text = QLabel("Your Favorites")
        title_text.setFont(QFont(title_text.font().family(), 16))
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        searchbar = QLineEdit()
        searchbar.setPlaceholderText("Search for music and audiobooks")
        searchbutton = QPushButton("Search")
        settings_button = SVGButton("settings")
        settings_button.setFixedSize(30, 30)
        settings_button.clicked.connect(self.createSettingsPage)
        title_layout.addWidget(searchbar)
        title_layout.addWidget(searchbutton)
        title_layout.addWidget(settings_button)

        searchbar.returnPressed.connect(search)
        searchbutton.clicked.connect(search)

        main_layout.addLayout(title_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)

        history_label = QLabel("History")
        history_label.setFont(QFont(history_label.font().family(), 14))

        if self.history:
            history_widget = QScrollArea()
            history_widget.setWidgetResizable(True)
            history_swidget = QAlbumHList(
                self.history, deezerclient=self.session.deezer
            )
            history_swidget.album_clicked.connect(album_clicked)
            history_widget.setWidget(history_swidget)

        else:
            history_widget = QLabel(
                "There's no history here. So you have to write history now, then."
            )

        f_title = QLabel("Favorites")
        f_title.setFont(QFont(history_label.font().family(), 14))

        f_albums = self.session.deezer.get_user_albums()
        f_album_p = QPixmap()
        if f_albums:
            f_album_p.loadFromData(
                src.caching.albumCovers.download_small(self.session.deezer, f_albums[0].id)
            )
        f_album_w = QHClickList(
            "Albums",
            f_album_p,
            f"{f_albums.total} albums total",
            f"{f_albums[0].title} - {f_albums[0].artist.name}",
        )

        f_tracks = self.session.deezer.get_user_tracks()
        f_track_p = QPixmap()
        r_track = random.choice(f_tracks)
        if f_tracks:
            try:
                f_track_p.loadFromData(
                    src.caching.albumCovers.download_small(
                        self.session.deezer, r_track.album.id
                    )
                )
            except deezer.exceptions.DeezerErrorResponse:
                print("[W> Loading of f_track_p failed")

        f_track_w = QHClickList(
            "Tracks",
            f_track_p,
            f"{f_tracks.total} tracks total",
            f"{r_track.title} - {r_track.artist.name}",
        )
        f_track_w.action.connect(show_ftracks)

        scroll_layout.addWidget(history_label)
        scroll_layout.addWidget(history_widget)
        scroll_layout.addWidget(f_title)
        scroll_layout.addWidget(f_album_w)
        scroll_layout.addWidget(f_track_w)
        scroll_layout.addStretch()

        main_layout.addWidget(scroll_area)
        main_layout.addWidget(self.player)

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
        back_button = SVGButton("back")
        back_button.clicked.connect(self.createMainPage)
        back_button.setFixedSize(30, 30)
        title_layout.addWidget(back_button)
        title_text = QLabel("Search - Results for " + query)
        title_text.setFont(QFont(title_text.font().family(), 16))
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        searchbar = QLineEdit()
        searchbar.setPlaceholderText("Search for music and audiobooks")
        searchbutton = QPushButton("Search")
        searchbar.setText(query)
        title_layout.addWidget(searchbar)
        title_layout.addWidget(searchbutton)

        searchbar.returnPressed.connect(search)
        searchbutton.clicked.connect(search)

        main_layout.addLayout(title_layout)

        search_area = QScrollArea()
        search_area.setWidgetResizable(True)
        search_widget = QWidget()
        search_layout = QVBoxLayout()
        search_widget.setLayout(search_layout)
        search_area.setWidget(search_widget)

        alb_title = QLabel("Albums")
        alb_title.setFont(QFont(title_text.font().family(), 14))
        album_search = []
        for s in self.session.deezer.search_albums(query):
            album_search.append(s.id)
        if len(album_search) == 0:
            album_widget = QLabel("No results found. Here's a note for you: 🎵")
        else:
            album_widget = QAlbumList(
                album_search[:5], deezerclient=self.session.deezer
            )
            album_widget.album_clicked.connect(album_clicked)
            album_widget.artist_clicked.connect(artist_clicked)

        track_title = QLabel("Tracks")
        track_title.setFont(QFont(title_text.font().family(), 14))
        track_search = []
        for s in self.session.deezer.search(query):
            track_search.append(s.id)
        if len(track_search) == 0:
            track_widget = QLabel(
                "No results found. Here's a banana for you: 🍌"
            )  # as the creator of this program,
            #                                                                        i dont like bananas. accept it!
        else:
            track_widget = QTrackList(
                track_search[:5], deezerclient=self.session.deezer
            )
            track_widget.album_clicked.connect(album_clicked)
            track_widget.artist_clicked.connect(artist_clicked)
            track_widget.track_clicked.connect(track_clicked)

        art_title = QLabel("Artists")
        art_title.setFont(QFont(title_text.font().family(), 14))
        artist_search = []
        for s in self.session.deezer.search_artists(query):
            artist_search.append(s.id)
        if len(artist_search) == 0:
            artist_widget = QLabel("No results found. Here's a tree for you: 🌲")
        else:
            artist_widget = QArtistList(
                artist_search[:5], deezerclient=self.session.deezer
            )
            artist_widget.artist_clicked.connect(artist_clicked)

        pl_title = QLabel("Playlists")
        pl_title.setFont(QFont(title_text.font().family(), 14))
        playlist_search = []
        for s in self.session.deezer.search_playlists(query):
            playlist_search.append(s.id)
        if len(playlist_search) == 0:
            playlist_widget = QLabel("No results found. Here's a cat for you: 🐱")
        else:
            playlist_widget = QPlayList(
                playlist_search[:5], deezerclient=self.session.deezer
            )
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
        main_layout.addWidget(self.player)

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
        album = self.session.deezer.get_album(albumid)
        tracks = album.get_tracks()
        trackids = utils.conv_paginated_ids(tracks)

        title_layout = QHBoxLayout()
        back_button = SVGButton("back")
        back_button.clicked.connect(self.createMainPage)
        back_button.setFixedSize(30, 30)
        title_layout.addWidget(back_button)
        title_text = QLabel(album.title + " - " + album.artist.name)
        title_text.setFont(QFont(title_text.font().family(), 16))
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        searchbar = QLineEdit()
        searchbar.setPlaceholderText("Search for music and audiobooks")
        searchbutton = QPushButton("Search")
        title_layout.addWidget(searchbar)
        title_layout.addWidget(searchbutton)

        searchbar.returnPressed.connect(search)
        searchbutton.clicked.connect(search)

        search_area = QScrollArea()
        search_area.setWidgetResizable(True)
        search_widget = QWidget()
        search_layout = QVBoxLayout()
        search_widget.setLayout(search_layout)
        search_area.setWidget(search_widget)

        header_layout = QHBoxLayout()

        cover = QLabel()
        cover_pixmap = QPixmap()
        cover_pixmap.loadFromData(
            src.caching.albumCovers.download_medium(self.session.deezer, album.id)
        )
        cover.setPixmap(cover_pixmap)
        header_layout.addWidget(cover)

        sidepanel_layout = QVBoxLayout()
        header_layout.addLayout(sidepanel_layout)
        header_layout.addStretch()

        tit_label = QLabel(f"<b>Number of titles:</b> {tracks.total}")
        len_label = QLabel(f"<b>Length:</b> {utils.convert_sec_to_min(album.duration)}")
        rel_label = QLabel(
            f'<b>Release date:</b> {album.release_date.strftime("%Y-%m-%d")}'
        )
        play_button = QPushButton("Play album")
        play_button.clicked.connect(play)
        author_button = QPushButton("Visit " + album.artist.name)
        clean_button = QPushButton("Clean cached tracks")
        sidepanel_layout.addWidget(tit_label)
        sidepanel_layout.addWidget(len_label)
        sidepanel_layout.addWidget(rel_label)
        sidepanel_layout.addWidget(play_button)
        sidepanel_layout.addWidget(author_button)
        sidepanel_layout.addWidget(clean_button)

        search_layout.addLayout(header_layout)

        track_widget = QTrackList(
            trackids, deezerclient=self.session.deezer, show_album=False
        )
        track_widget.track_clicked.connect(playitem)
        # track_widget.add_playlist.
        # track_widget.add_queue.
        track_widget.toggle_fav.connect(self.toggle_favorite_track)

        search_layout.addWidget(track_widget)
        search_layout.addStretch()

        main_layout.addLayout(title_layout)
        main_layout.addWidget(search_area)
        main_layout.addWidget(self.player)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def createSettingsPage(self):
        def update_cbutton():
            cleanc_button.setDisabled(
                not (
                    cleanc_i1.isChecked()
                    or cleanc_i2.isChecked()
                    or cleanc_i3.isChecked()
                )
            )
            if cleanc_i1.isChecked() or cleanc_i2.isChecked() or cleanc_i3.isChecked():
                cleanc_button.setStyleSheet("color: white; background-color: #a50003")
            else:
                cleanc_button.setStyleSheet("")

        def cbutton_clicked():
            cleanc_i1.setChecked(False)
            cleanc_i2.setChecked(False)
            cleanc_i3.setChecked(False)
            print("[D> Cleanup: Cleanup started")
            if cleanc_i1.isChecked():
                print("[D> Cleanup: Cleaning Album covers (medium)")
                src.caching.albumCovers.clear_ids(
                    src.caching.albumCovers.get_cached(size="m"), size="m"
                )
            if cleanc_i2.isChecked():
                print("[D> Cleanup: Cleaning Album covers (medium)")
                src.caching.albumCovers.clear_ids(
                    src.caching.albumCovers.get_cached(size="s"), size="s"
                )
            if cleanc_i3.isChecked():
                print("[D> Cleanup: Cleaning Tracks (cached)")
                src.caching.tracks.clear_ids(src.caching.tracks.get_cached())
            print("[D> Cleanup: Finished")
            sys.exit()

        def chbutton_clicked():
            print("[D> Cleanup: Cleaning History")
            os.remove(self.session_path + "/history")
            os.remove(self.session_path + "/lastplay")
            sys.exit()

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        title_layout = QHBoxLayout()
        back_button = SVGButton("back")
        back_button.clicked.connect(self.createMainPage)
        back_button.setFixedSize(30, 30)
        title_layout.addWidget(back_button)
        title_text = QLabel("Settings")
        title_text.setFont(QFont(title_text.font().family(), 16))
        title_layout.addWidget(title_text)

        search_area = QScrollArea()
        search_area.setWidgetResizable(True)
        search_widget = QWidget()
        search_layout = QVBoxLayout()
        search_widget.setLayout(search_layout)
        search_area.setWidget(search_widget)

        account_box = QGroupBox("Account")
        account_layout = QVBoxLayout(account_box)
        account_name = QLabel(
            "Currently logged in as " + self.session.deezer.get_user().name
        )
        logout_button = QPushButton("Log out")
        logout_button.setStyleSheet("color: white; background-color: #a50003")
        logout_button.clicked.connect(self.logout)
        account_layout.addWidget(account_name)
        account_layout.addWidget(logout_button)

        data_box = QGroupBox("Data managment")
        data_layout = QVBoxLayout(data_box)
        cleanc_title = QLabel("Clean cached data:")
        cleanc_subtitle = QLabel("Anything below can't be reverted!")
        cleanc_i1 = QCheckBox("Album covers (medium)")
        cleanc_i2 = QCheckBox("Album covers (small)")
        cleanc_i3 = QCheckBox("Tracks (cached)")
        cleanc_i1.toggled.connect(update_cbutton)
        cleanc_i2.toggled.connect(update_cbutton)
        cleanc_i3.toggled.connect(update_cbutton)
        cleanc_button = QPushButton("Clear data and close")
        cleanc_button.setStyleSheet("")
        cleanc_button.setDisabled(True)
        cleanc_button.clicked.connect(cbutton_clicked)
        cleanc_label = QLabel("Cleaning can take a while")
        data_layout.addWidget(cleanc_subtitle)
        data_layout.addWidget(cleanc_title)
        data_layout.addWidget(cleanc_i1)
        data_layout.addWidget(cleanc_i2)
        data_layout.addWidget(cleanc_i3)
        data_layout.addWidget(cleanc_button)
        data_layout.addWidget(cleanc_label)

        cleanh_button = QPushButton("Clear history and close")
        cleanh_button.clicked.connect(chbutton_clicked)
        data_layout.addWidget(cleanh_button)

        search_layout.addWidget(account_box)
        search_layout.addWidget(data_box)
        search_layout.addStretch()

        main_layout.addLayout(title_layout)
        main_layout.addWidget(search_area)
        main_layout.addWidget(self.player)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def createPlaylistPage(
        self, tracks: deezer.PaginatedList[deezer.Track], ptype: str = "fa"
    ):
        def playitem(tid):
            self.playlist(pl_trackids, first=tid)

        def play():
            self.playlist(pl_trackids)

        def search():
            query = searchbar.text()
            self.createSearchresultPage(query)

        pl_coverpix = QPixmap()
        if ptype == "fa":
            pl_title = "Favorite Tracks"
            pl_author = self.session.deezer.get_user().name
            with open(APP_DATA_PATH + "favorite.png", "rb") as f:
                pl_coverpix.loadFromData(f.read())
        else:
            pl = self.session.deezer.get_playlist(ptype)
            pl_title = pl.title
            pl_author = pl.creator.name
            pl_coverpix.loadFromData(
                src.caching.playlistCovers.download_medium(self.session.deezer, pl.id)
            )

        pl_trackids = []
        pl_length = 0
        for track in tracks:
            pl_trackids.append(track.id)
            pl_length += track.duration
        pl_totalt = tracks.total

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        title_layout = QHBoxLayout()
        back_button = SVGButton("back")
        back_button.clicked.connect(self.createMainPage)
        back_button.setFixedSize(30, 30)
        title_layout.addWidget(back_button)
        title_text = QLabel(pl_title + " - " + pl_author)
        title_text.setFont(QFont(title_text.font().family(), 16))
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        searchbar = QLineEdit()
        searchbar.setPlaceholderText("Search for music and audiobooks")
        searchbutton = QPushButton("Search")
        title_layout.addWidget(searchbar)
        title_layout.addWidget(searchbutton)

        searchbar.returnPressed.connect(search)
        searchbutton.clicked.connect(search)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
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

        tit_label = QLabel(f"<b>Number of titles:</b> {pl_totalt}")
        len_label = QLabel(f"<b>Length:</b> {utils.convert_sec_to_min(pl_length)}")
        play_button = QPushButton("Play playlist")
        play_button.clicked.connect(play)
        author_button = QPushButton("Visit " + pl_author)
        clean_button = QPushButton("Clean cached tracks")
        sidepanel_layout.addWidget(tit_label)
        sidepanel_layout.addWidget(len_label)
        sidepanel_layout.addWidget(play_button)
        sidepanel_layout.addWidget(author_button)
        sidepanel_layout.addWidget(clean_button)

        scroll_layout.addLayout(header_layout)

        if pl_totalt:
            track_widget = QTrackList(pl_trackids, deezerclient=self.session.deezer)
            track_widget.track_clicked.connect(playitem)
            track_widget.toggle_fav.connect(self.toggle_favorite_track)
        else:
            track_widget = QLabel("This playlist is empty.")
        scroll_layout.addWidget(track_widget)

        main_layout.addLayout(title_layout)
        main_layout.addWidget(scroll_area)
        main_layout.addWidget(self.player)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def save_history(self):
        if self.session.logged_in and self.player.play_currentlist != [] and self.player.play_currenttrack:
            print("[D> State saved")
            os.makedirs(self.session_path, exist_ok=True)
            json_data = self.player.dump_state()
            with open(self.session_path + "/lastplay", "w") as f:
                f.write(json_data)
            with open(self.session_path + "/history", "w") as f:
                f.write(json.dumps(self.history))

    def closeEvent(self, event):
        if not self.closeLocked:
            if os.path.exists(os.path.expanduser("~/.cache/deezium/.cache")):
                os.remove(os.path.expanduser("~/.cache/deezium/.cache"))
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
    old_dir = os.getenv("PWD")
    os.chdir(os.path.expanduser('~/.cache/deezium'))
    app = QApplication(sys.argv)
    app.setDesktopFileName("deezium")

    try:
        deezium = MainWindow()
        deezium.show()

    except Exception:
        trb = traceback.format_exc()
        format_traceback(trb)

    app_exec = app.exec_()
    os.chdir(old_dir)
    return app_exec


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
