import tkinter as tk

from PIL import Image, ImageChops, ImageDraw

from util.win32 import user32, apply_layered_image
from .coords import point_to_pixels, point_to_percent

MARKER_DIAMETER = 40
MARKER_RING_WIDTH = 4
MARKER_DOT = 6
SUPERSAMPLE = 8

_marker_images = {}

def hex_to_rgb(color):
	color = color.lstrip('#')
	return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))

def render_marker(ring_color, fill_color, alpha):
	cache_key = (ring_color, fill_color, alpha)
	if cache_key in _marker_images:
		return _marker_images[cache_key]

	size = MARKER_DIAMETER * SUPERSAMPLE
	img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
	draw = ImageDraw.Draw(img)

	center = size / 2
	outer = center - 1
	ring = hex_to_rgb(ring_color) + (alpha,)
	fill = hex_to_rgb(fill_color) + (alpha,)
	draw.ellipse((center - outer, center - outer, center + outer, center + outer), fill=fill, outline=ring, width=MARKER_RING_WIDTH * SUPERSAMPLE)

	inner = MARKER_DOT * SUPERSAMPLE / 2
	draw.ellipse((center - inner, center - inner, center + inner, center + inner), fill=ring)

	img = img.resize((MARKER_DIAMETER, MARKER_DIAMETER), Image.LANCZOS)
	r, g, b, a = img.split()
	premultiplied = Image.merge('RGBA', (ImageChops.multiply(b, a), ImageChops.multiply(g, a), ImageChops.multiply(r, a), a))
	_marker_images[cache_key] = premultiplied.tobytes()
	return _marker_images[cache_key]

class MarkerOverlay:
	def __init__(self, root, point, get_bounds, label, ring='#008000', fill='#00ff00', alpha=153):
		self.point = dict(point)
		self.get_bounds = get_bounds
		self.drag = None

		self.window = tk.Toplevel(root)
		self.window.overrideredirect(True)
		self.window.attributes('-topmost', True)
		self.window.config(cursor='fleur')
		self.follow()
		self.window.update_idletasks()

		hwnd = user32.GetParent(self.window.winfo_id()) or self.window.winfo_id()
		apply_layered_image(hwnd, MARKER_DIAMETER, MARKER_DIAMETER, render_marker(ring, fill, alpha))

		self.window.bind('<ButtonPress-1>', self.on_press)
		self.window.bind('<B1-Motion>', self.on_drag)
		self.window.bind('<ButtonRelease-1>', self.on_release)

	def follow(self):
		cx, cy = point_to_pixels(self.point, self.get_bounds())
		self.place(cx, cy)

	def place(self, cx, cy):
		half = MARKER_DIAMETER // 2
		self.window.geometry(f"{MARKER_DIAMETER}x{MARKER_DIAMETER}+{cx - half}+{cy - half}")

	def show(self):
		self.window.deiconify()
		self.follow()

	def hide(self):
		self.window.withdraw()

	def on_press(self, event):
		self.drag = (event.x_root, event.y_root) + point_to_pixels(self.point, self.get_bounds())

	def on_drag(self, event):
		if not self.drag:
			return
		start_x, start_y, cx, cy = self.drag
		bounds = self.get_bounds()
		bx, by, bw, bh = bounds
		cx = max(bx, min(cx + event.x_root - start_x, bx + bw - 1))
		cy = max(by, min(cy + event.y_root - start_y, by + bh - 1))
		self.point = point_to_percent(cx, cy, bounds)
		self.place(cx, cy)

	def on_release(self, event):
		self.drag = None

	def close(self):
		self.window.destroy()
		return self.point
