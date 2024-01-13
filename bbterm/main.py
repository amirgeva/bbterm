import socket
import sys
import time
import argh
import threading
from typing import Optional
from PyQt5.QtCore import QTimer, QSize, Qt
from PyQt5.QtGui import QPaintEvent, QPainter, QResizeEvent, QKeyEvent
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from .canvas import Canvas
from .font import SIZE
from .protocol import ClientProtocol
from .telnet_client import TelnetClient
from server import Server

key_map = {
    Qt.Key_Return: b'\r\x00',
    Qt.Key_Backspace: b'\x08',
    Qt.Key_Tab: b'\x09',
    Qt.Key_Up: b'\x1b[A',
    Qt.Key_Down: b'\x1b[B',
    Qt.Key_Right: b'\x1b[C',
    Qt.Key_Left: b'\x1b[D',
    Qt.Key_PageUp: b'\x1b[5~',
    Qt.Key_PageDown: b'\x1b[6~',
    Qt.Key_Insert: b'\x1b[2~',
    Qt.Key_Delete: b'\x1b[3~',
    Qt.Key_Home: b'\x1b[H',
    Qt.Key_End: b'\x1b[F'
}

terminating = False


def run_server(server: Server, port: int):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', port))
    server_socket.listen()
    sock, addr = server_socket.accept()
    sock.settimeout(0.1)
    while not terminating:
        try:
            incoming = sock.recv(256)
            server.handle_incoming(incoming)
        except socket.timeout:
            pass
        server.process(sock)
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()
    server_socket.close()


class CanvasWidget(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._canvas = Canvas(SIZE * 40, SIZE * 25)
        self._text_line_width = self._canvas.width() // SIZE
        self._scaling = 1
        self.set_window_size(parent.size())

    def get_canvas(self):
        return self._canvas

    def set_window_size(self, size: QSize):
        width_scaling = size.width() / self.width()
        height_scaling = size.height() / self.height()
        self._scaling = min(width_scaling, height_scaling)
        self.update()

    def width(self):
        return self._canvas.width()

    def height(self):
        return self._canvas.height()

    def paintEvent(self, e: QPaintEvent):
        qp = QPainter(self)
        qp.scale(self._scaling, self._scaling)
        qp.drawPixmap(0, 0, self._canvas.get_pixmap())


class MainWindow(QMainWindow):
    def __init__(self, io):
        super().__init__()
        self._main_widget = CanvasWidget(self)
        self._io = io
        self._protocol: Optional[ClientProtocol] = ClientProtocol(io, self._main_widget.get_canvas())
        self.setMinimumSize(1280, 800)
        self.setCentralWidget(self._main_widget)
        self._read_timer = QTimer(self)
        self._read_timer.timeout.connect(self._on_read_timer)
        self._read_timer.start(10)

    def _on_read_timer(self):
        if self._protocol is not None:
            if self._protocol.process():
                self._main_widget.update()

    def resizeEvent(self, e: QResizeEvent) -> None:
        super().resizeEvent(e)
        self._main_widget.set_window_size(self.size())

    def keyPressEvent(self, e: QKeyEvent) -> None:
        super().keyPressEvent(e)
        text = e.text()
        key = e.key()
        if not text and key in key_map:
            text = key_map[key]
        if text:
            if isinstance(text, str):
                if text == '\r':
                    text = b'\r\x00'
                else:
                    text = bytes(text, 'ascii')
            self._io.write(text)


def run_terminal(host: str, port: str, local_server: Optional[Server] = None):
    try:
        server_thread: Optional[threading.Thread] = None
        if local_server is not None:
            host = 'localhost'
            server_thread = threading.Thread(target=run_server, args=[local_server, int(port)])
            server_thread.start()
            time.sleep(1.0)
        client = TelnetClient(host, int(port))
        if client.connect():
            app = QApplication(sys.argv)
            window = MainWindow(client)
            window.show()
            app.exec_()
        else:
            print("Failed to connect")
        if server_thread:
            global terminating
            terminating = True
            server_thread.join()
    except ValueError:
        print("Invalid port number")


def main():
    argh.dispatch_command(run_terminal)


if __name__ == '__main__':
    main()
