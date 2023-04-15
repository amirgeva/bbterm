from typing import Optional, Dict
from PyQt5.QtCore import QRect
from PyQt5.QtGui import QPixmap, QPainter, QImage, QColor
from font import Font, create_font
from inline_font import SIZE


class Canvas:
    def __init__(self, w: int, h: int):
        self._pixmap = QPixmap(w, h)
        self._pixmap.fill(QColor(0, 0x80, 0))
        self._painter = QPainter(self._pixmap)
        self._saved_blink_cursor = (0, 0)
        self._saved_blink: Optional[QPixmap] = None
        self._cursor = (0, 0)
        self._fonts: Dict[int, Font] = {0: create_font(self)}
        self._cur_font = 0
        self._blink_count = 0
        self._blink = False

    def get_font(self) -> Font:
        return self._fonts[self._cur_font]

    def set_blink(self, state: bool):
        self._blink = state

    def process_blink_counter(self):
        if self._blink:
            self._blink_count += 1
            if self._blink_count >= 50:
                self._blink_count = 0
                self.blink(self._cursor[0], self._cursor[1])
                return True
        return False

    def set_cursor(self, cursor):
        if self.valid_cursor(cursor):
            self._cursor = cursor

    def valid_cursor(self, cursor):
        font = self._fonts[self._cur_font]
        return 0 <= cursor[1] < font.bottom_most() and 0 <= cursor[0] < font.right_most()

    def get_cursor(self):
        return self._cursor

    def get_pixmap(self):
        return self._pixmap

    def width(self):
        return self._pixmap.width()

    def height(self):
        return self._pixmap.height()

    def rect(self):
        return self._pixmap.rect()

    def fill(self, color: QColor):
        self._clear_blink()
        self._pixmap.fill(color)

    def draw_image(self, x: int, y: int, image: QImage):
        self._clear_blink()
        self._painter.drawImage(x, y, image)

    def draw_sub_image(self, target: QRect, image: QImage, source: QRect):
        self._clear_blink()
        self._painter.drawImage(target, image, source)

    def copy_from(self, other: QPixmap):
        self._clear_blink()
        self._painter.drawPixmap(0, 0, other)

    def scroll(self, x, y):
        self._clear_blink()
        self._pixmap.scroll(x, y, self._pixmap.rect())

    def _clear_blink(self):
        if self._saved_blink is not None:
            rect = QRect(self._saved_blink_cursor[0], self._saved_blink_cursor[1], SIZE, SIZE)
            self._painter.drawPixmap(rect, self._saved_blink)
            self._saved_blink = None

    def blink(self, x, y):
        if self._saved_blink is not None:
            rect = QRect(self._saved_blink_cursor[0], self._saved_blink_cursor[1], SIZE, SIZE)
            self._painter.drawPixmap(rect, self._saved_blink)
            self._saved_blink = None
        else:
            self._saved_blink = self._pixmap.copy(QRect(x, y, SIZE, SIZE))
            self._saved_blink_cursor = x, y
            image = self._saved_blink.toImage()
            for i in range(SIZE):
                for j in range(SIZE):
                    p = 0xFF000000 | (~image.pixel(i, j) & 0xFFFFFF)
                    image.setPixel(i, j, p)
            self._painter.drawImage(x, y, image)
