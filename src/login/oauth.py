import http.server, re, socketserver, sys, os, requests


def _pathval(path, name):
    pattern = re.compile(rf'[\&|\?]{name}=([^\&\#]+)')
    match = re.search(pattern, path)
    if match:
        return match.groups()[0]


class _RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        er = _pathval(self.path, 'error_reason')
        if er:
            self.wfile.write(b'Error: ' + er.encode('utf-8') + b'. You may close this tab now')
            print('[E> OAuth - Error ' + er.encode('utf-8'))
            return
        cd = _pathval(self.path, 'code')
        if cd:
            self.wfile.write(b'Valid. You may close this tab now')
            print('[D> OAuth - Valid')
            _returnval(cd)
            return
        self.wfile.write(b'Something went wrong. You may close this tab now')
        print('[E> OAuth - Something went wrong')
    
    def log_message(self, format: str, *args) -> None:
        pass


def _returnval(rturnval):
    response = requests.get(f'https://connect.deezer.com/oauth/access_token.php?app_id=663691&secret=e133f3d457427cc05b0dffbeadbae890&code={rturnval}')
    if response.status_code == 200:
        match = re.search(re.compile(r'access_token=([^&]*)'), response.text)
        if match:
            with open(os.path.expanduser(f'~/.config/deezium/{sys.argv[1]}/aro.dat'), 'w') as f:
                f.write(match.groups()[0])
            sys.exit()
    sys.exit()


hserver = socketserver.TCPServer(('localhost', 3875), _RequestHandler)
print('[D> OAuth - Serving')
hserver.handle_request()
hserver.server_close()
