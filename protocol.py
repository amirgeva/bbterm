from io import IOBase
from typing import List, Callable, Tuple, Optional
from PyQt5.QtGui import QPixmap
from canvas import Canvas
from errors import ProtocolError
from font import SIZE
from extensions import extensions


class ClientProtocol:
    def __init__(self, io: IOBase, canvas: Canvas):
        self._data = bytearray()
        self._io = io
        self._cur_font = 0
        self._canvas = canvas
        self._cursor_stack: List[Tuple[int, int]] = []
        self._csi_terminators = ''
        self._saved_background: Optional[QPixmap] = None
        self._extensions = [Class() for Class in extensions]
        self._processors = {ord(e.get_escape_pattern()): e.process for e in self._extensions}

    def process(self):
        res = False
        if self._canvas.process_blink_counter():
            res = True
        data = self._io.read(65536)
        if data is not None and len(data) > 0:
            self._data.extend(data)
            res |= self._parse()
        return res

    def _parse(self):
        n = len(self._data)
        i = 0
        res = False
        while i < n:
            try:
                c = self._data[i]
                if c == 27:
                    escape_character = self._data[i + 1]
                    if escape_character in self._processors:
                        processor: Callable[[Canvas, bytearray, int], int] = self._processors[escape_character]
                        j = processor(self._canvas, self._data, i)
                        if j > i:
                            i = j
                            res = True
                        else:
                            break
                    else:
                        raise RuntimeError("Unsupported code")
                else:
                    self._handle_char(c)
                    res = True
                    i += 1
            except IndexError:
                self._data = self._data[i:]
                return res
            except ProtocolError:
                self._data = self._data[i:]
                return res
        self._data.clear()
        return res

    def _handle_char(self, ch: int):
        if ch == 13:
            self._canvas.set_cursor((0, self._canvas.get_cursor()[1] + SIZE))
        elif ch >= 32:
            self._draw_char(ch)

    def _draw_char(self, ch: int):
        if ch > 0:
            font = self._canvas.get_font()
            cursor = self._canvas.get_cursor()
            font.draw_char(cursor[0], cursor[1], ch)
            x = cursor[0] + SIZE
            y = cursor[1]
            if x > font.right_most():
                x = 0
                y += SIZE
                if y > font.bottom_most():
                    font.scroll()
                    y -= SIZE
            self._canvas.set_cursor((x, y))
