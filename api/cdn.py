from http.server import BaseHTTPRequestHandler
import urllib.request
import json
import ssl

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        ctx = ssl._create_unverified_context()
        url = "https://www.dailymotion.com/player/metadata/video/x1b7bk"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://cdn.com.do/",
            "Origin": "https://cdn.com.do"
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=6) as response:
                data = json.loads(response.read().decode('utf-8'))
                qualities = data.get("qualities", {})
                stream_url = None
                
                # Intentar buscar la calidad óptima
                for q_key in ["auto", "1080", "720", "480", "360"]:
                    if q_key in qualities:
                        for item in qualities[q_key]:
                            if item.get("type") == "application/x-mpegURL":
                                stream_url = item.get("url")
                                break
                        if stream_url:
                            break
                            
                # Fallback a cualquier m3u8
                if not stream_url:
                    for q_list in qualities.values():
                        for item in q_list:
                            if item.get("type") == "application/x-mpegURL":
                                stream_url = item.get("url")
                                break
                        if stream_url:
                            break
                            
                if stream_url:
                    self.send_response(302)
                    self.send_header("Location", stream_url)
                    self.end_headers()
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"No HLS stream found for CDN.")
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode('utf-8'))
