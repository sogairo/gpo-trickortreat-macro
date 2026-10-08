import tkinter as tk

from .coords import to_pixels, to_percent

GRAB = 10
HANDLE = 6
MIN_SIZE = 10

CURSORS = {
	"n": "sb_v_double_arrow",
	"s": "sb_v_double_arrow",
	"e": "sb_h_double_arrow",
	"w": "sb_h_double_arrow",
	"nw": "size_nw_se",
	"se": "size_nw_se",
	"ne": "size_ne_sw",
	"sw": "size_ne_sw",
	"move": "fleur",
}

class RegionOverlay:
	def __init__(self, root, box, get_bounds, label, fill='green', border='lime', label_fg='#ffffff', alpha=0.6, font=("Arial", 9, "bold")):
		self.label = label
		self.border = border
		self.label_fg = label_fg
		self.font = font
		self.box = dict(box)
		self.get_bounds = get_bounds
		self.mode = None
		self.start = None

		self.window = tk.Toplevel(root)
		self.window.overrideredirect(True)
		self.window.attributes('-topmost', True)
		self.window.attributes('-alpha', alpha)

		self.canvas = tk.Canvas(self.window, bg=fill, highlightthickness=0, bd=0)
		self.canvas.pack(fill='both', expand=True)
		self.canvas.bind('<Configure>', lambda event: self.redraw())
		self.canvas.bind('<Motion>', self.on_motion)
		self.canvas.bind('<ButtonPress-1>', self.on_press)
		self.canvas.bind('<B1-Motion>', self.on_drag)
		self.canvas.bind('<ButtonRelease-1>', self.on_release)

		self.follow()

	def follow(self):
		x1, y1, x2, y2 = to_pixels(self.box, self.get_bounds())
		self.place(x1, y1, x2, y2)

	def place(self, x1, y1, x2, y2):
		self.window.geometry(f"{x2 - x1}x{y2 - y1}+{x1}+{y1}")

	def show(self):
		self.window.deiconify()
		self.follow()

	def hide(self):
		self.window.withdraw()

	def redraw(self):
		self.canvas.delete('all')
		w = self.canvas.winfo_width()
		h = self.canvas.winfo_height()
		self.canvas.create_rectangle(1, 1, w - 2, h - 2, outline=self.border, width=2)
		self.canvas.create_text(6, 5, anchor='nw', text=self.label.upper(), fill=self.label_fg, font=self.font)
		half = HANDLE // 2
		for x in (0, w // 2, w - 1):
			for y in (0, h // 2, h - 1):
				if x == w // 2 and y == h // 2:
					continue
				self.canvas.create_rectangle(x - half, y - half, x + half, y + half, fill=self.border, outline='')

	def mode_at(self, x, y):
		w = self.canvas.winfo_width()
		h = self.canvas.winfo_height()
		mode = ""
		if y < GRAB:
			mode += "n"
		elif y >= h - GRAB:
			mode += "s"
		if x < GRAB:
			mode += "w"
		elif x >= w - GRAB:
			mode += "e"
		return mode or "move"

	def on_motion(self, event):
		if self.mode:
			return
		self.canvas.config(cursor=CURSORS[self.mode_at(event.x, event.y)])

	def on_press(self, event):
		self.mode = self.mode_at(event.x, event.y)
		self.start = (event.x_root, event.y_root) + to_pixels(self.box, self.get_bounds())

	def on_drag(self, event):
		if not self.mode:
			return
		start_x, start_y, x1, y1, x2, y2 = self.start
		dx = event.x_root - start_x
		dy = event.y_root - start_y
		bounds = self.get_bounds()
		bx, by, bw, bh = bounds
		left = bx
		top = by
		right = bx + bw
		bottom = by + bh

		if self.mode == "move":
			w = x2 - x1
			h = y2 - y1
			x1 = max(left, min(x1 + dx, right - w))
			y1 = max(top, min(y1 + dy, bottom - h))
			x2 = x1 + w
			y2 = y1 + h
		else:
			if "w" in self.mode:
				x1 = max(left, min(x1 + dx, x2 - MIN_SIZE))
			if "e" in self.mode:
				x2 = min(right, max(x2 + dx, x1 + MIN_SIZE))
			if "n" in self.mode:
				y1 = max(top, min(y1 + dy, y2 - MIN_SIZE))
			if "s" in self.mode:
				y2 = min(bottom, max(y2 + dy, y1 + MIN_SIZE))

		self.box = to_percent(x1, y1, x2, y2, bounds)
		self.place(x1, y1, x2, y2)

	def on_release(self, event):
		self.mode = None
		self.start = None

	def close(self):
		self.window.destroy()
		return self.box
