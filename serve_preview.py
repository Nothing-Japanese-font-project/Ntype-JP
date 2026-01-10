import http.server
import socketserver
import json
import os
import shutil
from pathlib import Path
from fontTools.ttLib import TTFont

PORT = 8080
DIST_DIR = Path("dist")
CACHE_DIR = DIST_DIR / ".cache"
PREVIEW_DIR = Path("preview")

class PreviewRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/fonts":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            fonts = []
            if DIST_DIR.exists():
                for f in DIST_DIR.glob("*.otf"):
                    target_url = f"/dist/{f.name}"
                    # WOFF化の試行
                    woff_path = self.get_woff_version(f)
                    if woff_path:
                        target_url = f"/dist/.cache/{woff_path.name}"
                        size = woff_path.stat().st_size
                    else:
                        size = f.stat().st_size

                    fonts.append({
                        "name": f.name,
                        "url": target_url,
                        "size": size,
                        "original_size": f.stat().st_size
                    })
            fonts.sort(key=lambda x: x["name"])
            
            self.wfile.write(json.dumps(fonts).encode())
            return
            
        if self.path.startswith("/dist/"):
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
            
        original_path = self.path
        if self.path == "/" or not Path(PREVIEW_DIR / self.path.lstrip("/")).exists():
            self.path = "/preview/index.html"
        else:
            self.path = f"/preview{original_path}"
            
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def get_woff_version(self, otf_path):
        """OTFをWOFFに変換してパスを返す。既存ならそれを返す。"""
        if not CACHE_DIR.exists():
            CACHE_DIR.mkdir(parents=True)
        
        # WOFF2を優先、なければWOFF
        try:
            import brotli
            ext = ".woff2"
            flavor = "woff2"
        except ImportError:
            ext = ".woff"
            flavor = "woff"
        
        target_path = CACHE_DIR / (otf_path.stem + ext)
        
        # 既に存在し、元ファイルより新しければスキップ
        if target_path.exists() and target_path.stat().st_mtime > otf_path.stat().st_mtime:
            return target_path
            
        print(f"Converting {otf_path.name} to {flavor}...")
        try:
            font = TTFont(otf_path)
            font.flavor = flavor
            font.save(target_path)
            return target_path
        except Exception as e:
            print(f"Conversion failed: {e}")
            return None

class ThreadingSimpleServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def run():
    os.chdir(Path(__file__).parent)
    port = PORT
    while port < PORT + 10:
        try:
            with ThreadingSimpleServer(("", port), PreviewRequestHandler) as httpd:
                print(f"Serving preview at http://localhost:{port}")
                print("Press Ctrl+C to stop.")
                httpd.serve_forever()
                break
        except OSError:
            print(f"Port {port} is in use, trying next one...")
            port += 1
        except KeyboardInterrupt:
            print("\nShutting down server.")
            break

if __name__ == "__main__":
    run()
