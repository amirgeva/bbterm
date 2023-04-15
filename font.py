import numpy as np
from PyQt5.QtCore import QRect
from PyQt5.QtGui import QImage
from inline_font import SIZE, load_font


# from .canvas import Canvas


class Font:
    def __init__(self, image, canvas):
        self._width = SIZE
        self._height = SIZE
        self._canvas = canvas
        self._canvas_rect = canvas.rect()
        if isinstance(image, np.ndarray):
            if len(image.shape) == 2:
                hh, ww = image.shape
                c = 3
                # convert to rgb
                rgb = np.ndarray((hh, ww, 3), dtype=np.uint8)
                for y in range(hh):
                    for x in range(ww):
                        rgb[y, x, :] = image[y, x]
                image = rgb
            else:
                hh, ww, c = image.shape
            data = image.data
            if not isinstance(data, bytes):
                data = data.tobytes()
            image = QImage(data, ww, hh, ww * c, QImage.Format_RGB888)
        self._image: QImage = image.convertToFormat(QImage.Format.Format_Indexed8)
        self._colors = self._image.colorTable()
        self._rects = []
        self._image_rect = QRect(0, 0, image.width(), image.height())
        # row_width = (self._image.width() // w)
        for y in range(0, self._image.height(), self._height):
            for x in range(0, self._image.width(), self._width):
                self._rects.append(QRect(x, y, self._width, self._height))

    def get_canvas(self):
        return self._canvas

    def right_most(self):
        return self._canvas_rect.width() - SIZE

    def bottom_most(self):
        return self._canvas_rect.height() - SIZE

    def scroll(self):
        self._canvas.scroll(0, SIZE)

    def set_back_color(self, r: int, g: int, b: int):
        if 255 >= r >= 0 and 255 >= g >= 0 and 255 >= b >= 0:
            self._colors[0] = 0xFF000000 | (r << 16) | (g << 8) | b
            self._image.setColorTable(self._colors)

    def set_fore_color(self, r: int, g: int, b: int):
        if 255 >= r >= 0 and 255 >= g >= 0 and 255 >= b >= 0:
            self._colors[1] = 0xFF000000 | (r << 16) | (g << 8) | b
            self._image.setColorTable(self._colors)

    def draw_char(self, x: int, y: int, index: int):
        if index >= len(self._rects):
            return
        target = QRect(x, y, self._width, self._height)
        if not self._canvas_rect.contains(target, False):
            return
        source = self._rects[index]
        self._canvas.draw_sub_image(target, self._image, source)

    def draw_text(self, x: int, y: int, text: str):
        for c in text:
            self.draw_char(x, y, ord(c))
            x += self._width


def create_font(target_canvas):
    return Font(load_font(), target_canvas)
