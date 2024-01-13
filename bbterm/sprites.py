from typing import Dict
from PyQt5.QtGui import QImage
from .errors import ProtocolError
from .font import SIZE


def rgb_to_argb(data: bytes) -> bytes:
    argb_data = bytearray(SIZE * SIZE * 4)
    source = 0
    destination = 0
    for i in range(SIZE * SIZE):
        argb_data[destination + 0] = data[source]
        argb_data[destination + 1] = data[source + 1]
        argb_data[destination + 2] = data[source + 2]
        argb_data[destination + 3] = 255
        if data[source] == 0 and data[source + 1] == 0 and data[source + 2] == 0:
            argb_data[destination + 3] = 0
        destination += 4
        source += 3
    return bytes(argb_data)


class Sprite:
    def __init__(self, data: bytes):
        if len(data) == (SIZE * SIZE * 3):
            data = rgb_to_argb(data)
        if len(data) != (SIZE * SIZE * 4):
            raise ProtocolError("Invalid sprite data")
        # Data should be ARGB 32bpp row scan of 32x32 image, 4096 bytes total
        image = QImage(data, SIZE, SIZE, 4 * SIZE, QImage.Format_ARGB32_Premultiplied)
        self._image = image

    def get_image(self):
        return self._image


_sprites: Dict[int, Sprite] = {}


def set_sprite(index: int, data: bytes):
    _sprites[index] = Sprite(data)


def get_sprite(index: int):
    if index in _sprites:
        return _sprites[index]
    return None
