import os
import deezloader.exceptions
import src.deezloader2
import deezer


class LoginManager:
    def __init__(self, session_id, datapath):
        self.logged_in = False
        self.login_arl = ""
        self.login_aro = ""

        self.deezer = ""
        self.deezloader = ""

        self.session_id = session_id
        self.session_path = os.path.expanduser(f'~/.config/deezium/{session_id}')
        self.datapath = datapath
        
        os.makedirs(self.session_path, exist_ok=True)
        self.login()

    def login(self):
        if os.path.exists(f"{self.session_path}/aro.dat") and os.path.exists(f"{self.session_path}/arl.dat"):
            with open(f"{self.session_path}/arl.dat", "r") as f:
                self.login_arl = f.read()
            with open(f"{self.session_path}/aro.dat", "r") as f:
                self.login_aro = f.read()

            try:
                self.deezloader = src.deezloader2.Login2(self.login_arl)
            except ValueError:
                os.remove(f"{self.session_path}/arl.dat")
                return self.session_logout()
            except deezloader.exceptions.BadCredentials:
                os.remove(f"{self.session_path}/arl.dat")
                return self.session_logout()

            try:
                self.deezer = deezer.Client(access_token=self.login_aro)
            except deezer.exceptions.DeezerErrorResponse:
                os.remove(f"{self.session_path}/aro.dat")
                return self.session_logout()

            self.logged_in = True
        else:
            self.logged_in = False
            print('[W> Not every needed file to login is present')

    def session_logout(self):
        self.login_aro = ""
        self.login_arl = ""
        self.logged_in = False

    def full_logout(self):
        self.session_logout()
        if os.path.exists(f"{self.session_path}/arl.dat"):
            os.remove(f"{self.session_path}/arl.dat")
        if os.path.exists(f"{self.session_path}/aro.dat"):
            os.remove(f"{self.session_path}/aro.dat")

    def host_oauth_server(self, forced: bool = False):
        if (not os.path.exists(os.path.expanduser(f"{self.session_path}/aro.dat"))) or forced:
            os.system(
                f'python "{self.datapath}oauth.py" {self.session_id}'
            )
