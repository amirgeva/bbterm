from typing import Optional, Callable, Dict

from PyQt5.QtGui import QPixmap

from ..inline_font import SIZE
from ..sprites import set_sprite, get_sprite
from ..canvas import Canvas

_saved_background: Optional[QPixmap] = None


def set_cursor(canvas: Canvas, data: bytes):
    if len(data) == 4:
        x = data[0] | (data[1] << 8)
        y = data[2] | (data[3] << 8)
        canvas.set_cursor((x, y))


def set_sprite_pixels(_: Canvas, data: bytes):
    if len(data) == (2 + SIZE * SIZE * 4):
        index = (data[1] << 8) | data[0]
        set_sprite(index, data[2:])


def draw_sprite(canvas: Canvas, data: bytes):
    if len(data) == 2:
        index = (data[1] << 8) | data[0]
        sprite = get_sprite(index)
        if sprite:
            cursor = canvas.get_cursor()
            canvas.draw_image(cursor[0], cursor[1], sprite.get_image())


# Store background
def store_background(canvas: Canvas, _: bytes):
    global _saved_background
    _saved_background = canvas.get_pixmap().copy()


# Load background
def load_background(canvas: Canvas, _: bytes):
    if _saved_background is not None:
        canvas.copy_from(_saved_background)


class SlashExtension:
    def __init__(self):
        self._codes: Dict[str, Callable[[Canvas, bytes], None]] \
            = {'H': set_cursor, 'A': store_background,
               'B': load_background, 'D': draw_sprite, 'S': set_sprite_pixels}

    @staticmethod
    def get_escape_pattern():
        return '/'

    def process(self, canvas: Canvas, data: bytearray, i: int, io=None):
        n = len(data)
        if i < (n - 4):
            code = chr(data[i + 2])
            packet_size = (data[i + 4] << 8) | data[i + 3]
            if code in self._codes:
                function = self._codes[code]
                packet = bytes(data[(i + 5):(i + 5 + packet_size)])
                function(canvas, packet)
            i += packet_size + 5
        return i
