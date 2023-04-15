import re
from typing import Callable, Dict

from ..inline_font import SIZE
from PyQt5.QtGui import QColor

from ..canvas import Canvas

_cursor_pattern = r'(\d+);(\d+)'
_color_pattern = r'(\d+)(?:;(\d+))*'
_cursor_stack = []
_colors = [(0, 0, 0), (170, 0, 0), (0, 170, 0), (170, 85, 0),
           (0, 0, 170), (170, 0, 170), (0, 170, 170), (170, 170, 170)]


def clear(canvas: Canvas, _: str):
    # support only full screen clearing
    canvas.fill(QColor(0, 0, 0))


def set_cursor(canvas: Canvas, param: str):
    m = re.match(_cursor_pattern, param)
    if m:
        g = m.groups()
        y = (int(g[0]) - 1) * SIZE
        x = (int(g[1]) - 1) * SIZE
        canvas.set_cursor((x, y))


def move_up(canvas: Canvas, param: str):
    n = int(param) if param else 1
    cursor = canvas.get_cursor()
    canvas.set_cursor((cursor[0], cursor[1] - n * SIZE))


def move_down(canvas: Canvas, param: str):
    n = int(param) if param else 1
    cursor = canvas.get_cursor()
    canvas.set_cursor((cursor[0], cursor[1] + n * SIZE))


def move_right(canvas: Canvas, param: str):
    n = int(param) if param else 1
    cursor = canvas.get_cursor()
    canvas.set_cursor((cursor[0] + n * SIZE, cursor[1]))


def move_left(canvas: Canvas, param: str):
    n = int(param) if param else 1
    cursor = canvas.get_cursor()
    canvas.set_cursor((cursor[0] - n * SIZE, cursor[1]))


def push_cursor(canvas: Canvas, _: str):
    _cursor_stack.append(canvas.get_cursor())


def pop_cursor(canvas: Canvas, _: str):
    if len(_cursor_stack) > 0:
        canvas.set_cursor(_cursor_stack.pop())


def set_attributes(canvas: Canvas, param: str):
    font = canvas.get_font()
    m = re.match(_color_pattern, param)
    values = [int(c) for c in m.groups() if c is not None]
    if len(values) == 0:
        values = [0]
    color_mod = 0
    for value in values:
        if value == 0:
            font.set_back_color(0, 0, 0)
            font.set_fore_color(255, 255, 255)
            color_mod = 0
        if value == 5:
            canvas.set_blink(True)
        if value == 25:
            canvas.set_blink(False)
        if value == 1:
            color_mod = 85
        if 30 <= value <= 37:
            color = _colors[value - 30]
            font.set_fore_color(color[0] + color_mod, color[1] + color_mod, color[2] + color_mod)
        if 40 <= value <= 47:
            color = _colors[value - 40]
            font.set_back_color(color[0] + color_mod, color[1] + color_mod, color[2] + color_mod)
        if 90 <= value <= 97:
            color = _colors[value - 90]
            font.set_fore_color(color[0] + 85, color[1] + 85, color[2] + 85)
        if 100 <= value <= 107:
            color = _colors[value - 100]
            font.set_back_color(color[0] + 85, color[1] + 85, color[2] + 85)


class AnsiExtension:
    def __init__(self):
        self._codes: Dict[str, Callable[[Canvas, str], None]] = \
            {'J': clear, 'H': set_cursor, 'A': move_up, 'B': move_down, 'C': move_right,
             'D': move_left, 's': push_cursor, 'u': pop_cursor, 'm': set_attributes}

    @staticmethod
    def get_escape_pattern():
        return '['

    def process(self, canvas: Canvas, data: bytearray, i: int):
        n = len(data)
        for j in range(i + 2, n):
            code = chr(data[j])
            if code.isalpha():
                if code in self._codes:
                    function = self._codes[code]
                    sub = data[(i + 2):j]
                    text = sub.decode('ascii')
                    function(canvas, text)
                    return j + 1
                raise RuntimeError("Invalid ANSI code")
        return i
