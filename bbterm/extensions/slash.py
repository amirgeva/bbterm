from typing import Optional, Callable, Dict

from PyQt5.QtGui import QPixmap

from bbterm.debug_utils import diag

from ..inline_font import SIZE
from ..sprites import set_sprite, get_sprite
from ..canvas import Canvas

_saved_background: Optional[QPixmap] = None
protocol_version: int = 1
terminal_width: int = 1280
terminal_height: int = 800

"""
This is an extension protocol for the BBS.
It is intended for graphical clients

The protocol is similar to ANSI:
ESC / <command> <size> <payload>

<command> is a single character indicating the command type.
currently supported commands are:
- 'V': capability negotiation
- 'H': set cursor
- 'A': store background
- 'B': load background
- 'S': set sprite image
- 'D': draw sprite

<size> is a 2-byte little-endian unsigned integer indicating the size of the payload in bytes.

<payload> is the binary data for the command, of length <size>.

For capability negotiation, the payload is a 16 bit version number, 
	followed by terminal width and height in pixels (each 16 bits). 
	The server sends this command first to check if the client supports 
	the protocol, and the client responds with the same command if it does.
	The client can ignore the server width,height, and use its own dimensions in the response.
For set cursor, the payload is: x (2 bytes), y (2 bytes)   (in pixels, not character cells)
For store/load background, the payload is empty
For set sprite image, the payload is: sprite_id (2 bytes), image data (32*32*4 bytes, RGBA image)
For draw sprite, the payload is: sprite_id (2 bytes) (drawn at current cursor position)
"""


def set_cursor(canvas: Canvas, data: bytes):
	if len(data) == 4:
		x = data[0] | (data[1] << 8)
		y = data[2] | (data[3] << 8)
		canvas.set_cursor((x, y))


def set_sprite_pixels(_: Canvas, data: bytes):
	if len(data) == (2 + SIZE * SIZE * 4):
		index = (data[1] << 8) | data[0]
		diag(f"Setting sprite {index}")
		set_sprite(index, data[2:])
	else:
		diag(f"Sprite data size incorrect {len(data)}")


def draw_sprite(canvas: Canvas, data: bytes):
	if len(data) == 2:
		index = (data[1] << 8) | data[0]
		sprite = get_sprite(index)
		if sprite:
			cursor = canvas.get_cursor()
			canvas.draw_image(cursor[0], cursor[1], sprite.get_image())


def version_negotiation(_: Canvas, data: bytes, io):
	if len(data) == 6 and io is not None:
		# Respond with our client protocol version
		response = bytearray(11)
		response[0:5] = b'\x1b/V\x06\x00'
		response[5:7] = protocol_version.to_bytes(2, 'little')
		response[7:9] = terminal_width.to_bytes(2, 'little')
		response[9:11] = terminal_height.to_bytes(2, 'little')
		io.write(response)


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
		"""
		Process a single command, if enough data is available. 
		Returns the new index after processing, or the same index if not enough data.
		"""
		n = len(data)-i
		if n >= 5:
			code = chr(data[i + 2])
			payload_size = (data[i + 4] << 8) | data[i + 3]
			if n < (5 + payload_size):
				return i
			payload = data[(i + 5):(i + 5 + payload_size)]
			if code in self._codes:
				function = self._codes[code]
				function(canvas, payload)
			elif code == 'V':
				version_negotiation(canvas, payload, io)
			else:
				# Ignore unknown command, but skip it to avoid desync
				diag(f"Unknown slash command: {code}")
			i += payload_size + 5
		return i
