#!/usr/bin/env python3
import http.server
import socketserver
import os

PORT = 8000
os.chdir('.')

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    print("http://localhost:8000")
    httpd.serve_forever()
