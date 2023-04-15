import socket
import time


class TelnetClient:
    def __init__(self, host: str, port: int):
        self._address = host, port
        self._terminating = False
        self._connected = False
        self._buffer = bytearray()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(5.0)  # for connection

    def connect(self):
        try:
            self._socket.connect(self._address)
            self._socket.setblocking(False)
            return True
        except TimeoutError:
            return False
        except ConnectionRefusedError:
            return False

    def write(self, data: bytes):
        i = 0
        n = len(data)
        while i < n:  # socket is non-blocking. Loop until everything is sent
            i += self._socket.send(data[i:n])
            if i < n:
                time.sleep(0.01)  # For low volume data, this should never happen

    def read(self, size: int) -> bytes:
        # Return what's available
        try:
            return self._socket.recv(size)
        except BlockingIOError:
            return bytes()
