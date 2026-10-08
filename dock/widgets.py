import tkinter as tk

from app.theme import TITLE_BG, TITLE_FG, TITLE_ACTIVE_FG, ROW_HOVER_BG, ITEM_FG, ITEM_HOVER_FG, ITEM_FONT, ITEM_HOVER_FONT, SUBHEADER_FG, SUBHEADER_FONT, SCROLLBAR_THUMB, SCROLLBAR_THUMB_HOVER, ITEM_SELECTED_FG, ITEM_SELECTED_FONT, SIDEBAR_BG, ENTRY_BG, ENTRY_FG, ENTRY_BORDER

ENTRY_PAD = 6
ROW_PAD = 4

SCROLLBAR_WIDTH = 6
SCROLLBAR_MIN_THUMB = 20

def icon_box(w, h):
	size = max(8, int(h * 0.42))
	return (w - size) // 2, (h - size) // 2, size

def draw_close_icon(canvas, w, h, color):
	x0, y0, size = icon_box(w, h)
	canvas.create_line(x0, y0, x0 + size, y0 + size, fill=color, width=2, tags='icon')
	canvas.create_line(x0, y0 + size, x0 + size, y0, fill=color, width=2, tags='icon')

def draw_maximize_icon(canvas, w, h, color, maximized):
	x0, y0, size = icon_box(w, h)
	if maximized:
		offset = max(2, size // 4)
		small = size - offset
		canvas.create_line(x0 + offset, y0 + offset, x0 + offset, y0, x0 + size, y0, x0 + size, y0 + small, x0 + small, y0 + small, fill=color, width=2, tags='icon')
		canvas.create_rectangle(x0, y0 + offset, x0 + small, y0 + size, outline=color, width=2, tags='icon')
	else:
		canvas.create_rectangle(x0, y0, x0 + size, y0 + size, outline=color, width=2, tags='icon')

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

class HoverRow:
	def __init__(self, parent, text, command, bg, hover_bg, hint=None, bullet="• ", wrap=True):
		self.text = text
		self.wrap = wrap
		self.bullet = bullet
		self.bg = bg
		self.hover_bg = hover_bg
		self.hovered = False
		self.selected = False
		self.widget = tk.Frame(parent, cursor='hand2')
		self.marker = tk.Label(self.widget, anchor='nw', cursor='hand2', padx=0, pady=2)
		self.label = tk.Label(self.widget, anchor='w', justify='left', cursor='hand2', padx=0, pady=2)
		self.hint = None
		if hint:
			self.hint = tk.Label(self.widget, text=hint, fg=SUBHEADER_FG, font=SUBHEADER_FONT, anchor='e', cursor='hand2', padx=4)
			self.hint.pack(side='right', anchor='n')
		self.marker.pack(side='left', anchor='n', padx=(ROW_PAD, 0))
		self.label.pack(side='left', fill='x', expand=True, padx=(0, ROW_PAD))
		if wrap:
			self.widget.bind('<Configure>', self.on_resize)
		for part in self.parts():
			part.bind('<Enter>', self.on_enter)
			part.bind('<Leave>', self.on_leave)
			part.bind('<Button-1>', lambda event: command())
		self.render()

	def on_resize(self, event=None):
		width = event.width if event is not None else self.widget.winfo_width()
		width -= self.marker.winfo_reqwidth() + 2 * ROW_PAD
		if self.hint is not None:
			width -= self.hint.winfo_reqwidth()
		self.label.config(wraplength=max(1, width))

	def parts(self):
		return [part for part in (self.widget, self.marker, self.label, self.hint) if part is not None]

	def render(self):
		bg = self.hover_bg if self.hovered else self.bg
		if self.selected:
			marker, fg, font = "> ", ITEM_SELECTED_FG, ITEM_SELECTED_FONT
		elif self.hovered:
			marker, fg, font = "> ", ITEM_HOVER_FG, ITEM_HOVER_FONT
		else:
			marker, fg, font = self.bullet, ITEM_FG, ITEM_FONT
		self.marker.config(text=marker, fg=fg, bg=bg, font=font)
		self.label.config(text=self.text, fg=fg, bg=bg, font=font)
		self.widget.config(bg=bg)
		if self.wrap and self.widget.winfo_width() > 1:
			self.on_resize()
		if self.hint is not None:
			self.hint.config(bg=bg)

	def set_selected(self, selected):
		self.selected = selected
		self.render()

	def set_text(self, text):
		self.text = text
		self.render()

	def reset(self):
		self.hovered = False
		self.render()

	def on_enter(self, event):
		self.hovered = True
		self.render()

	def on_leave(self, event):
		if self.widget.winfo_containing(event.x_root, event.y_root) in self.parts():
			return
		self.hovered = False
		self.render()

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

class Dropdown:
	instances = []

	def __init__(self, parent, options, value, on_select):
		self.options = options
		self.value = value
		self.on_select = on_select
		self.opened = False

		self.frame = tk.Frame(parent, bg=SIDEBAR_BG)
		self.box = tk.Frame(self.frame, bg=ENTRY_BG, highlightthickness=1, highlightbackground=ENTRY_BORDER, highlightcolor=ENTRY_BORDER, cursor='hand2')
		self.box.pack(fill='x')
		self.label = tk.Label(self.box, text=value, bg=ENTRY_BG, fg=ENTRY_FG, font=ITEM_FONT, anchor='w', cursor='hand2')
		self.label.pack(side='left', fill='x', expand=True, padx=(ENTRY_PAD, 0), pady=3)
		self.arrow = tk.Label(self.box, text="▾", bg=ENTRY_BG, fg=ITEM_FG, font=ITEM_FONT, cursor='hand2')
		self.arrow.pack(side='right', padx=(0, ENTRY_PAD))
		for part in (self.box, self.label, self.arrow):
			part.bind('<Button-1>', lambda event: self.toggle())

		self.list = tk.Frame(self.frame, bg=SIDEBAR_BG, highlightthickness=1, highlightbackground=ENTRY_BORDER, highlightcolor=ENTRY_BORDER)
		self.rows = {}
		for option in options:
			row = HoverRow(self.list, option, lambda option=option: self.select(option), SIDEBAR_BG, ROW_HOVER_BG, bullet="")
			row.widget.pack(fill='x')
			row.set_selected(option == value)
			self.rows[option] = row

		Dropdown.instances.append(self)

	def toggle(self):
		if self.opened:
			self.close()
		else:
			self.open()

	def open(self):
		self.list.pack(fill='x')
		self.arrow.config(text="▴")
		self.opened = True

	def close(self):
		if not self.opened:
			return
		self.list.pack_forget()
		self.arrow.config(text="▾")
		self.opened = False
		for row in self.rows.values():
			row.hovered = False
			row.render()

	def select(self, option):
		self.close()
		if option == self.value:
			return
		self.rows[self.value].set_selected(False)
		self.value = option
		self.rows[option].set_selected(True)
		self.label.config(text=option)
		self.on_select(option)

	def contains(self, widget):
		while widget is not None:
			if widget is self.frame:
				return True
			widget = getattr(widget, "master", None)
		return False

	@classmethod
	def close_others(cls, widget):
		for dropdown in cls.instances:
			if dropdown.opened and not dropdown.contains(widget):
				dropdown.close()