import http.server
import socketserver
import os

os.chdir(r"C:\Users\eyal\עדכון עמודים מיוחדים מאני")

PORT = 8080
Handler = http.server.SimpleHTTPRequestHandler

print(f"Starting server at http://localhost:{PORT}")
print(f"Open: http://localhost:{PORT}")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()




