import os, json, threading
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QSlider
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl
from src.ui.widgets.SVGLabel import SVGLabel
from src.ui.widgets.SVGButton import SVGButton
import src.caching.albumCovers
import src.caching.playlistCovers
import src.caching.tracks
import src.utils as utils


class Player(QWidget):
    def __init__(self, parent, session):
        super().__init__()
        self.parent = parent
        self.session = session

        self.player = QMediaPlayer(self)
        self.player.setVolume(75)

        self.play_currentlist = []
        self.play_currenttrack = None
        self.play_looping: int = 0

        self.play_layout = QHBoxLayout()
        self.setLayout(self.play_layout)

        self.play_nowplaying = QLabel("Select a song to start playing!")
        self.play_seeker = QSlider(1)
        self.play_seeker.setMinimumWidth(400)
        self.play_pauseb = SVGButton("play")
        self.play_pauseb.setFixedSize(30, 30)
        self.play_forb = SVGButton("next")
        self.play_preb = SVGButton("prev")
        self.play_forb.setFixedSize(30, 30)
        self.play_preb.setFixedSize(30, 30)
        self.play_loopb = SVGButton("repeat")
        self.play_loopb.setFixedSize(30, 30)
        self.play_state = QLabel()
        self.play_volume_indicator = SVGLabel("volume")
        self.play_volume = QSlider(1)
        self.play_volume.setRange(10, 100)
        self.play_volume.setValue(75)
        self.play_volume.setMinimumWidth(50)
        self.play_volume.setMaximumWidth(150)

        self.hideable_widgets = (self.play_seeker, self.play_pauseb, self.play_forb, self.play_preb, self.play_loopb, self.play_state, self.play_volume, self.play_volume_indicator)

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

        self.update_message_state()

    def update_message_state(self):
        hide = not bool(self.play_currenttrack)
        for widget in self.hideable_widgets:
            widget.setHidden(hide)

    def read_playstate(self):
        if os.path.exists(self.parent.session_path + "/lastplay"):
            try:
                with open(self.parent.session_path + "/lastplay", "r") as f:
                    ldata = f.read()
                data = json.loads(ldata)
                self.play_currentlist = data["current_play"]
                self.streamtrackid(data["current_id"], start=False)
                self.play_looping = data["looping"]
                self.update_loopbutton()
                self.player.setPosition(data["position"])
                self.player.setVolume(data["volume"])
                self.play_volume.setValue(data["volume"])
                self.play_seeker.setRange(0, data["length"])
                self.play_seeker.setValue(data["position"])
            except KeyError:
                print("[E> Invalid State removed")
                os.remove(self.parent.session_path + "/lastplay")

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
            self.play_loopb.set_icon("repeat")
        elif self.play_looping == 1:
            self.play_loopb.set_icon("repeat_on")
        elif self.play_looping == 2:
            self.play_loopb.set_icon("repeat_one")

    def skip_forward(self, by=1):
        if not by:
            by = 1
        currenti = self.play_currentlist.index(int(self.play_currenttrack))
        self.streamtrackid(
            self.play_currentlist[(currenti + by) % len(self.play_currentlist)]
        )

    def skip_backward(self, by=1):
        if not by:
            by = 1
        currenti = self.play_currentlist.index(int(self.play_currenttrack))
        self.streamtrackid(self.play_currentlist[currenti - by])

    def playback(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()
            calbum = self.session.deezer.get_track(self.play_currenttrack).album.id
            self.parent.insert_history(calbum)

    def update_player(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_pauseb.set_icon("pause")
        else:
            self.play_pauseb.set_icon("play")
        index = self.play_currentlist.index(self.play_currenttrack)
        self.play_preb.setDisabled(index == 0)
        self.play_forb.setDisabled(
            (index == len(self.play_currentlist)) or (self.play_looping == 2)
        )
        if self.play_currenttrack:
            track = self.session.deezer.get_track(self.play_currenttrack)
            self.play_nowplaying.setText(f"<b>{track.title}</b> - {track.artist.name}")

    def set_seeker(self, lenght):
        def buffer():
            src.caching.tracks.download(self.session.deezer, nxtid)

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
        self.play_state.setText(
            utils.ms_to_str(duration) + "/" + utils.ms_to_str(self.player.duration())
        )

    def set_position(self, position):
        self.player.setPosition(position)

    def streamtrackid(self, tid, start=True, historize=True):
        self.play_currenttrack = tid
        path = src.caching.tracks.download(self.session.deezloader, tid)
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
        if start:
            self.player.play()
        self.update_player(self.player.state())
        bg = utils.calc_background_color(
            src.caching.albumCovers.download_medium(
                self.session.deezer, self.session.deezer.get_track(tid).album.id
            )
        )
        fg = utils.calc_foreground_color(bg)
        self.setStyleSheet(f"background-color: {bg}; color: {fg}")
        if historize:
            albumid = self.session.deezer.get_track(tid).album.id
            self.parent.insert_history(albumid)
        self.update_message_state()

    def dump_state(self):
        return json.dumps(
            {
                "current_id": self.play_currenttrack,
                "current_play": self.play_currentlist,
                "looping": self.play_looping,
                "position": self.player.position(),
                "volume": self.player.volume(),
                "length": self.player.duration(),
            }
        )