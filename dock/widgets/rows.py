import tkinter as tk
import tkinter.font as tkfont

from app.theme import ITEM_FG, ITEM_HOVER_FG, ITEM_FONT, ITEM_HOVER_FONT, SUBHEADER_FG, SUBHEADER_FONT, ITEM_SELECTED_FG, ITEM_SELECTED_FONT

ROW_PAD = 4
ROW_FONTS = (ITEM_FONT, ITEM_HOVER_FONT, ITEM_SELECTED_FONT)
HOVER_MARKER = "> "
WRAP_SLACK = 4

_fonts = {}

def font_for(spec):
	if spec not in _fonts:
		_fonts[spec] = tkfont.Font(font=spec)
	return _fonts[spec]

def widest(text):
	return max(font_for(spec).measure(text) for spec in ROW_FONTS)

def wrap_text(text, width):
	lines = []
	for paragraph in text.split("\n"):
		line = ""
		for word in paragraph.split(" "):
			candidate = f"{line} {word}" if line else word
			if not line or widest(candidate) <= width:
				line = candidate
			else:
				lines.append(line)
				line = word
		lines.append(line)
	return "\n".join(lines)

class HoverRow:
	def __init__(self, parent, text, command, bg, hover_bg, hint=None, bullet="• ", wrap=True):
		self.text = text
		self.wrapped = text
		self.wrap_width = None
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

	def marker_width(self):
		return max(widest(self.bullet), widest(HOVER_MARKER))

	def on_resize(self, event=None):
		width = event.width if event is not None else self.widget.winfo_width()
		width -= self.marker_width() + 2 * ROW_PAD + WRAP_SLACK
		if self.hint is not None:
			width -= self.hint.winfo_reqwidth()
		width = max(1, width)
		if width == self.wrap_width:
			return
		self.wrap_width = width
		self.rewrap()

	def rewrap(self):
		if self.wrap and self.wrap_width:
			self.wrapped = wrap_text(self.text, self.wrap_width)
		else:
			self.wrapped = self.text
		self.label.config(text=self.wrapped)

	def parts(self):
		return [part for part in (self.widget, self.marker, self.label, self.hint) if part is not None]

	def render(self):
		bg = self.hover_bg if self.hovered else self.bg
		if self.selected:
			marker, fg, font = HOVER_MARKER, ITEM_SELECTED_FG, ITEM_SELECTED_FONT
		elif self.hovered:
			marker, fg, font = HOVER_MARKER, ITEM_HOVER_FG, ITEM_HOVER_FONT
		else:
			marker, fg, font = self.bullet, ITEM_FG, ITEM_FONT
		self.marker.config(text=marker, fg=fg, bg=bg, font=font)
		self.label.config(text=self.wrapped, fg=fg, bg=bg, font=font)
		self.widget.config(bg=bg)
		if self.hint is not None:
			self.hint.config(bg=bg)

	def set_selected(self, selected):
		self.selected = selected
		self.render()

	def set_text(self, text):
		self.text = text
		self.rewrap()
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