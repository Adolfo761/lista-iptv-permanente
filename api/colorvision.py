from http.server import BaseHTTPRequestHandler
import yt_dlp

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Canal oficial de Color Visión 9
                info = ydl.extract_info("https://www.youtube.com/channel/UCiDATmLMS6XfkB7mh8pmeHg/live", download=False)
                stream_url = info.get("url")
                if stream_url:
                    self.send_response(302)
                    self.send_header("Location", stream_url)
                    self.end_headers()
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"No YouTube Live stream URL found for Color Vision.")
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode('utf-8'))
