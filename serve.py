#!/usr/bin/env python3
"""
Local dev server that mimics GitHub Pages 404 behaviour.
Usage: python3 serve.py [port]   (default port: 8001)
"""
import http.server
import socketserver
import sys
import os

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
ROOT = os.path.dirname(os.path.abspath(__file__))


class GHPagesHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            page = os.path.join(ROOT, "404.html")
            try:
                with open(page, "rb") as f:
                    body = f.read()
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            except FileNotFoundError:
                pass
        super().send_error(code, message, explain)

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} — {fmt % args}")


with socketserver.TCPServer(("", PORT), GHPagesHandler) as httpd:
    httpd.allow_reuse_address = True
    print(f"Serving at http://0.0.0.0:{PORT}  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
