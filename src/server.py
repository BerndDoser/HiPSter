from http.server import HTTPServer, SimpleHTTPRequestHandler


class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Allow your local server to handle external assets smoothly
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type")
        super().end_headers()


print("Starting server on http://localhost:8083 with CORS enabled...")
httpd = HTTPServer(("localhost", 8083), CORSRequestHandler)
httpd.serve_forever()
