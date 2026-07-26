from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(302)
        self.send_header("Location", "https://cdn3.wind.do/streams/telesistema/telesistema_master.m3u8")
        self.end_headers()
