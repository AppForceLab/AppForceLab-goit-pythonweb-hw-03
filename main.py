import mimetypes
import pathlib
import os
import json
import urllib.parse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from jinja2 import Environment, FileSystemLoader


class HttpHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.env = Environment(loader=FileSystemLoader("templates"))
        super().__init__(*args, **kwargs)

    def do_POST(self):
        try:
            data = self.rfile.read(int(self.headers["Content-Length"])).decode()
            data_dict = dict(urllib.parse.parse_qsl(urllib.parse.unquote_plus(data)))
        except Exception as e:
            self.send_error(400, f"Error processing request: {e}")
            return

        os.makedirs("storage", exist_ok=True)
        messages = self.load_messages()

        messages[str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))] = {
            "username": data_dict.get("username", "Anonymous"),
            "message": data_dict.get("message", ""),
        }

        self.save_messages(messages)
        self.redirect("/read")

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        routes = {
            "/": "templates/index.html",
            "/message": "templates/message.html",
        }

        if parsed_url.path in routes:
            self.send_html_file(routes[parsed_url.path])
        elif parsed_url.path == "/read":
            messages = self.load_messages()
            self.send_template("read.jinja", {"messages": messages})
        elif pathlib.Path(parsed_url.path[1:]).exists():
            self.send_static()
        else:
            self.send_html_file("templates/error.html", 404)

    def send_html_file(self, filename, status=200):
        try:
            with open(filename, "rb") as fd:
                self.respond_with_content(fd.read(), "text/html", status)
        except FileNotFoundError:
            self.send_error(404, "File not found")

    def send_template(self, template_name, data=None, status=200):
        try:
            template = self.env.get_template(template_name)
            html = template.render(data or {})
            self.respond_with_content(html.encode(), "text/html", status)
        except Exception as e:
            self.send_error(500, f"Template rendering error: {e}")

    def send_static(self):
        try:
            file_path = f".{self.path}"
            content_type = (
                mimetypes.guess_type(self.path)[0] or "application/octet-stream"
            )
            with open(file_path, "rb") as file:
                self.respond_with_content(file.read(), content_type, 200, file_path)
        except FileNotFoundError:
            self.send_error(404, "Static file not found")
        except Exception as e:
            self.send_error(500, f"Error sending static file: {e}")

    def respond_with_content(self, content, content_type, status, file_path=None):
        self.send_response(status)
        self.send_header("Content-type", content_type)
        if file_path:
            self.send_header("Content-Length", str(os.path.getsize(file_path)))
        self.end_headers()
        self.wfile.write(content)

    def redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    @staticmethod
    def load_messages():
        try:
            with open("storage/data.json", "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def save_messages(messages):
        with open("storage/data.json", "w", encoding="utf-8") as file:
            json.dump(messages, file, indent=2)


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("127.0.0.1", 3000)
    http = server_class(server_address, handler_class)
    try:
        print("Server started! http://127.0.0.1:3000")
        http.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped.")
        http.server_close()


if __name__ == "__main__":
    run()
