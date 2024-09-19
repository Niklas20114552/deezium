import threading, platform, requests, os, re, pickle
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QGroupBox, QPushButton, QDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtNetwork import QNetworkCookie
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import QUrl

if platform.system() == "Windows":
    APP_DATA_PATH: str = "C:\\Program Files\\Deezium\\"
elif platform.system() == "Linux":
    APP_DATA_PATH: str = "/usr/share/deezium/"


class LoginPage(QWidget):
    def login(self):
        """Prepares and runs the background job for the oauth server"""
        self.parent.closeLocked = True
        login_thread = threading.Thread(target=self.parent.run_oauth, daemon=True)
        login_thread.start()
        self.parent.createWebLoginPage()

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        login_mlayout = QHBoxLayout()
        login_layout = QVBoxLayout()
        login2_layout = QVBoxLayout()

        self.setLayout(login_mlayout)
        login_mlayout.addStretch()
        login_mlayout.addLayout(login_layout)
        login_mlayout.addLayout(login2_layout)
        login_mlayout.addStretch()

        group_box = QGroupBox("Login")
        group_layout = QVBoxLayout()
        group_box.setLayout(group_layout)

        login_layout.addStretch()
        login2_layout.addStretch()

        title_layout = QHBoxLayout()
        title_layout.addStretch()

        logo_layout = QHBoxLayout()
        logo = QLabel()
        logop = QPixmap(APP_DATA_PATH + "deezium256.png")
        logo.setPixmap(logop)
        login_title = QLabel("Deezium")
        login_title.setFont(QFont(login_title.font().family(), 20))
        title_layout.addWidget(login_title)
        title_layout.addStretch()
        logo_layout.addStretch()
        logo_layout.addWidget(logo)
        logo_layout.addStretch()
        group_layout.addLayout(logo_layout)
        group_layout.addLayout(title_layout)

        login_button = QPushButton("Login with Deezer")
        login_button.setIcon(QIcon(APP_DATA_PATH + "deezer_logo.png"))
        group_layout.addWidget(login_button)

        disclaimer = QGroupBox("Disclaimer")
        dis_layout = QVBoxLayout()
        dis_layout.addWidget(QLabel("<b>NOT AFFILIATED WITH DEEZER</b>"))
        dis_layout.addWidget(QLabel("The Author of this program is"))
        dis_layout.addWidget(QLabel("not responsible for the usage"))
        dis_layout.addWidget(QLabel("of this program by other people."))
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

        login_button.clicked.connect(self.login)


class WebLoginPage(QWidget):
    def __init__(self, parent):
        super().__init__()

        def process_return(html):
            """Runs when the html was fully loaded. Processes the html to find the success or error message."""
            if not html:
                return
            html = str(html)
            match = re.match("Error: ([a-zA-Z]*). You may close this tab now", html)
            if html == "Valid. You may close this tab now":
                print('[D> Login success')
                parent.closeLocked = False
                parent.update_config()
                parent.login()
            elif html == "Something went wrong. You may close this tab now":
                parent.closeLocked = False
                parent.createLoginFailedPage()
            elif match:
                parent.closeLocked = False
                parent.createLoginFailedPage(match.groups()[0])

        def process_added_cookie(cookie):
            """Processes a cookie of the cookie store to find a deezer arl cookie to store and use for login later"""
            cookie = QNetworkCookie(cookie)
            name = bytearray(cookie.name()).decode()
            domain = cookie.domain()
            value = bytearray(cookie.value()).decode()
            if name == "arl" and domain == ".deezer.com" and len(value) == 192:
                print("[D> Arl found and imported.")
                with open(parent.session_path + "/arl.dat", "w") as f:
                    f.write(value)

        def load_finished():
            """Runs when the html was fully loaded and calls the parser with parts out of the html"""
            login_webengine.page().runJavaScript(
                "document.querySelector('pre').innerHTML;", process_return
            )

        def abort():
            """Aborts the login process by sending one request to the oauth server to shut it down"""
            try:
                requests.get("http://localhost:3875")
            except requests.exceptions.ConnectionError:
                pass
            parent.closeLocked = False
            parent.createLoginPage()

        main_layout = QVBoxLayout(self)

        abort_button = QPushButton("Abort login")
        abort_button.clicked.connect(abort)

        login_webengine = QWebEngineView()
        login_webengine.load(
            QUrl(
                "https://connect.deezer.com/oauth/auth.php?app_id=663691&redirect_uri=http://localhost:3875/&perms=basic_access,email,offline_access,manage_library,manage_community,delete_library,listening_history"
            )
        )
        login_webengine.loadFinished.connect(load_finished)
        login_webengine.page().profile().cookieStore().cookieAdded.connect(
            process_added_cookie
        )

        main_layout.addWidget(abort_button)
        main_layout.addWidget(login_webengine)


class LoginFailedPage(QWidget):
    def __init__(self, parent, errcode):
        super().__init__()
        main_layout = QHBoxLayout(self)
        v_layout = QVBoxLayout()
        main_layout.addStretch()
        main_layout.addLayout(v_layout)
        main_layout.addStretch()

        title = QLabel("Something went wrong")
        title.setFont(QFont(title.font().family(), 15))
        subtitle = QLabel()
        if errcode:
            subtitle.setText("Error Code: " + errcode)
        else:
            subtitle.setText("An unknown Error occurred.")

        backbutton = QPushButton("Back")
        backbutton.clicked.connect(parent.createLoginPage)

        v_layout.addStretch()
        v_layout.addWidget(title)
        v_layout.addWidget(subtitle)
        v_layout.addWidget(backbutton)
        v_layout.addStretch()
