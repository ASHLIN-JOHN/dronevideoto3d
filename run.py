import sys
import os

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--allow-file-access-from-files --disable-web-security"
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

from PyQt5.QtWidgets import QApplication
from app.main_window import MainWindow
from app.theme import get_stylesheet


class CORSHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        super().end_headers()

    def log_message(self, format, *args):
        pass


def start_file_server():
    server = HTTPServer(('127.0.0.1', 8765), CORSHandler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def main():
    file_server = start_file_server()

    app = QApplication(sys.argv)
    app.setApplicationName("Drone 3D Studio")
    app.setStyle("Fusion")
    app.setStyleSheet(get_stylesheet())

    window = MainWindow()
    window.file_server_port = 8765
    window.showMaximized()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
