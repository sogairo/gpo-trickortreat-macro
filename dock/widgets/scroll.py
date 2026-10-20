import tkinter as tk

from app.theme import SCROLLBAR_THUMB, SCROLLBAR_THUMB_HOVER

SCROLLBAR_WIDTH = 6
SCROLLBAR_MIN_THUMB = 20

class ThinScrollbar:
	def __init__(self, parent, bg, target):
		self.target = target
		self.first = 0.0
		self.last = 1.0
		self.hovered = False
		self.drag = None
		self.canvas = tk.Canvas(parent, width=SCROLLBAR_WIDTH, bg=bg, highlightthickness=0, bd=0)
		self.canvas.bind('<Configure>', lambda event: self.draw())
		self.canvas.bind('<Enter>', lambda event: self.set_hovered(True))
		self.canvas.bind('<Leave>', lambda event: self.set_hovered(False))
		self.canvas.bind('<ButtonPress-1>', self.on_press)
		self.canvas.bind('<B1-Motion>', self.on_drag)
		self.canvas.bind('<ButtonRelease-1>', self.on_release)
		self.canvas.bind('<MouseWheel>', lambda event: self.target.yview_scroll(int(-event.delta / 120), 'units'))

	def set(self, first, last):
		self.first = float(first)
		self.last = float(last)
		self.draw()

	def set_hovered(self, hovered):
		self.hovered = hovered
		self.draw()

	def visible(self):
		return self.first > 0 or self.last < 1

	def draw(self):
		self.canvas.delete('thumb')
		if not self.visible():
			return
		w = self.canvas.winfo_width()
		h = self.canvas.winfo_height()
		y1 = self.first * h
		y2 = min(h, max(y1 + SCROLLBAR_MIN_THUMB, self.last * h))
		color = SCROLLBAR_THUMB_HOVER if self.hovered or self.drag else SCROLLBAR_THUMB
		self.canvas.create_rectangle(1, y1, w - 1, y2, fill=color, outline='', tags='thumb')

	def on_press(self, event):
		if not self.visible():
			return
		h = max(1, self.canvas.winfo_height())
		span = self.last - self.first
		if not self.first * h <= event.y <= self.last * h:
			self.target.yview_moveto(event.y / h - span / 2)
		self.drag = (event.y, self.first)
		self.draw()

	def on_drag(self, event):
		if not self.drag:
			return
		h = max(1, self.canvas.winfo_height())
		start_y, start_first = self.drag
		self.target.yview_moveto(start_first + (event.y - start_y) / h)

	def on_release(self, event):
		self.drag = None
		self.draw()