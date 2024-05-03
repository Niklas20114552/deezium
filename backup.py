#!/usr/bin/python3
import sys, os, platform, api, deezloader.exceptions, math
from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QSlider, QProgressBar, QDialog, QGroupBox
from configparser import ConfigParser

config = ConfigParser()

APP_NAME: str = "Deezium"
if platform.system() == 'Windows':
    APP_DATA_PATH: str = "C:\\Program Files\\Deezium\\"
elif platform.system() == 'Linux':
    APP_DATA_PATH: str = '/usr/share/deezium/'
else:
    print('Sorry, but your Operation System is not supported.')
    sys.exit()
    
    
class QTiledAlbum(QWidget):
    def __init__(self, images: list[str]):
        super().__init__()
        self.images = images
        self.create_ui()
        
    def create_ui(self):
        self.main_layout = QVBoxLayout()
        lenght = len(self.images) - 1
        items_pr = math.floor(self.frameGeometry().width() / 200)
        rows = [self.images[i:i+items_pr] for i in range(0, len(self.images), items_pr)]
        for row_d in rows:
            row = QHBoxLayout()
            for index, item in enumerate(row_d):
                pixmap = QPixmap(item)
                label = QLabel()
                label.setPixmap(pixmap)
                row.addWidget(label)
                if lenght != index:
                    row.addStretch()
            self.main_layout.addLayout(row)
        self.setLayout(self.main_layout)
        
    def resizeEvent(self, a0):
        self.create_ui()

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
        self.play_looping: bool = False
        
        self.player = QMediaPlayer(self)
        self.player.setVolume(50)
        
        self.play_currentlist = [1041883582, 1733705837, 68473089, 747588442, 78917814]
        
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
        self.play_state = QLabel()
        self.play_volume_indicator = QLabel('')
        self.play_volume_indicator.setFont(QFont('Material Icons', 12))
        self.play_volume = QSlider(1)
        self.play_volume.setRange(0, 100)
        self.play_volume.setValue(50)
        self.play_volume.setMinimumWidth(75)
        self.play_volume.setMaximumWidth(150)
        
        self.play_navbutton = QPushButton()
        self.play_navbutton.clicked.connect(self.nav_clicked)
        
        self.play_pauseb.clicked.connect(self.playback)
        self.player.stateChanged.connect(self.update_player)
        self.player.positionChanged.connect(self.update_seeker)
        self.player.durationChanged.connect(self.set_seaker)
        self.player.mediaStatusChanged.connect(self.update_mediastate)
        self.play_seeker.sliderMoved.connect(self.set_position)
        self.play_volume.sliderMoved.connect(self.set_volume)
        self.play_forb.clicked.connect(self.skip_forward)
        self.play_preb.clicked.connect(self.skip_backward)
        
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
        self.play_layout.addWidget(self.play_navbutton)
        
        print('[D> Main loading')
        self.update_config()
        if bool(self.config_arl) and bool(self.config_aro):
            self.login()
        else:
            self.createLoginPage()
            
    def update_mediastate(self, mstate):
        if mstate == QMediaPlayer.EndOfMedia:
            if self.play_currenttrack == self.play_currentlist[-1]:
                if self.play_looping:
                    self.skip_forward()
                else:
                    self.streamtrackid(self.play_currentlist[0], start=False)
            else:
                self.skip_forward()
                
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
        
        
    def nav_clicked(self):
        if self.play_navbutton.text() == 'Search':
            self.createSearchPage()
        elif self.play_navbutton.text() == 'Back':
            self.createMainPage()
            
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
            
    def set_seaker(self, lenght):
        self.play_seeker.setRange(0, lenght)
        
    def set_volume(self, vol):
        self.player.setVolume(vol)
        
    def update_seeker(self, duration):
        self.play_seeker.setValue(duration)
        self.play_state.setText(api.ms_to_str(self.player.position()) + '/' + api.ms_to_str(self.player.duration()))
            
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
                with open(os.path.expanduser('~/.config/deezium/arl.dat'), 'w') as f:
                    f.write(arl_input.text())
            self.update_config()
            if bool(self.config_arl) and bool(self.config_aro):
                self.login()
        
        login_widget = QWidget()
        login_mlayout = QHBoxLayout()
        login_layout = QVBoxLayout()
        
        login_widget.setLayout(login_mlayout)
        login_mlayout.addStretch()
        login_mlayout.addLayout(login_layout)
        login_mlayout.addStretch()
        
        group_box = QGroupBox('Login')
        group_layout = QVBoxLayout()
        group_box.setLayout(group_layout)
        
        login_layout.addStretch()
        
        title_layout = QHBoxLayout()
        title_layout.addStretch()
        
        logo = QLabel()
        logop = QPixmap(APP_DATA_PATH + 'deezium256.png')
        logo.setPixmap(logop)
        login_title = QLabel(APP_NAME)
        login_title.setFont(QFont(login_title.font().family(), 20))
        title_layout.addWidget(login_title)
        title_layout.addStretch()
        group_layout.addWidget(logo)
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
        
        login_layout.addWidget(group_box)
        
        login_layout.addStretch()
        
        login_button.clicked.connect(login)
        arl_input.textChanged.connect(update_buttons)
        continue_button.clicked.connect(continuelogin)

        self.setCentralWidget(login_widget)
        update_buttons()
        
    def createMainPage(self):
        def stream():
            self.streamtrackid(id_input.text())
            
        self.play_navbutton.setText('Search')
        
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        title_text = QLabel('Your Favorites')
        title_text.setFont(QFont(title_text.font().family(), 16))
        main_layout.addWidget(title_text)
        
        id_input = QLineEdit()
        id_input.returnPressed.connect(stream)
        
        main_layout.addWidget(id_input)
        
        test = QTiledAlbum(['/home/niklas/200.jpg', '/home/niklas/200.jpg', '/home/niklas/200.jpg', '/home/niklas/200.jpg', '/home/niklas/200.jpg', '/home/niklas/200.jpg'])
        main_layout.addWidget(test)

        main_layout.addStretch()
        main_layout.addWidget(self.play_widget)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
    def createSearchPage(self):
        self.play_navbutton.setText('Back')
        
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        title_text = QLabel('Search')
        title_text.setFont(QFont(title_text.font().family(), 16))
        main_layout.addWidget(title_text)
        
        main_layout.addStretch()
        main_layout.addWidget(self.play_widget)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
       
       
def main(argv):
    app = QApplication(sys.argv)
    app.setDesktopFileName('deezium')

    deezium = MainWindow()
    deezium.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
