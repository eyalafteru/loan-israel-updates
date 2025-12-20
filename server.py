import http.server
import socketserver
import os

os.chdir(r"C:\Users\eyal\loan-israel-updaets\loan-israel-updates")

PORT = 8080
Handler = http.server.SimpleHTTPRequestHandler

print(f"Starting server at http://localhost:{PORT}")
print(f"Open: http://localhost:{PORT}/דפים%20לשינוי/הלוואה%20חוץ%20בנקאית.html")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()




