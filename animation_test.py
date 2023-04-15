import sys
import time
import io
from PyQt5.QtWidgets import QApplication
from main import MainWindow


class AnimationTest(io.IOBase):
    def __init__(self):
        self._start_time = time.time()
        self._data = bytearray()
        self._data.extend(bytes('\x1b[5;33;44m\x1b[4;20HHello\x1b[s\x1b[25m', 'ascii'))
        self._data.extend(bytes('\x1b/S\x02\x10\x00\x00', 'ascii'))
        self._x = 20
        sprite = bytearray(4096)
        for i in range(4096):
            sprite[i] = i & 255
        self._data.extend(sprite)
        self._data.extend(bytes('\x1b/A\x00\x00', 'ascii'))

    def read(self, length):
        actual = min(length, len(self._data))
        res = bytes(self._data[0:actual])
        self._data = self._data[actual:]
        now = time.time()
        if (now - self._start_time) > 0.01 and self._x < 255:
            self._start_time = now
            frame = bytearray(b'\x1b/B\x00\x00\x1b/H\x04\x00')
            frame.extend(bytes([self._x, 0, 0, 1]))
            frame.extend(bytes('\x1b/D\x02\x00\x00\x00', 'ascii'))
            self._data.extend(frame)
            self._x += 1
            if self._x >= 255:
                # Restore cursor
                self._data.extend(b'\x1b[u\x1b[5m')
        return res


def unit_test():
    app = QApplication(sys.argv)
    stream = AnimationTest()
    window = MainWindow(stream)
    window.show()
    app.exec_()


if __name__ == '__main__':
    unit_test()
