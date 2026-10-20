import tkinter as tk

from app.theme import TITLE_BG, TITLE_FG, TITLE_ACTIVE_FG, ROW_HOVER_BG

def icon_box(w, h):
	size = max(8, int(h * 0.42))
	return (w - size) // 2, (h - size) // 2, size

def draw_close_icon(canvas, w, h, color):
	x0, y0, size = icon_box(w, h)
	canvas.create_line(x0, y0, x0 + size, y0 + size, fill=color, width=2, tags='icon')
	canvas.create_line(x0, y0 + size, x0 + size, y0, fill=color, width=2, tags='icon')

class IconButton:
	def __init__(self, parent, width, height, draw, command):
		self.draw = draw
		self.command = command
		self.color = TITLE_FG
		self.canvas = tk.Canvas(parent, width=width, height=height, bg=TITLE_BG, highlightthickness=0, bd=0, cursor='hand2')
		self.canvas.bind('<Configure>', lambda event: self.redraw())
		self.canvas.bind('<Enter>', lambda event: self.set_colors(TITLE_FG, ROW_HOVER_BG))
		self.canvas.bind('<Leave>', lambda event: self.set_colors(TITLE_FG, TITLE_BG))
		self.canvas.bind('<ButtonPress-1>', lambda event: self.set_colors(TITLE_ACTIVE_FG, ROW_HOVER_BG))
		self.canvas.bind('<ButtonRelease-1>', self.on_release)

	def set_colors(self, color, bg):
		self.color = color
		self.canvas.config(bg=bg)
		self.redraw()

	def redraw(self):
		self.canvas.delete('icon')
		self.draw(self.canvas, self.canvas.winfo_width(), self.canvas.winfo_height(), self.color)

	def on_release(self, event):
		self.set_colors(TITLE_FG, ROW_HOVER_BG)
		if 0 <= event.x < self.canvas.winfo_width() and 0 <= event.y < self.canvas.winfo_height():
			self.command()