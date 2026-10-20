import tkinter as tk

from app.theme import ROW_HOVER_BG, ITEM_FG, ITEM_FONT, SUBHEADER_FG, SIDEBAR_BG, ENTRY_BG, ENTRY_FG, ENTRY_BORDER
from .rows import HoverRow

ENTRY_PAD = 6

class Dropdown:
	instances = []

	def __init__(self, parent, options, value, on_select):
		self.options = options
		self.value = value
		self.on_select = on_select
		self.opened = False
		self.enabled = True

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
		self.build_rows()

		Dropdown.instances.append(self)

	def build_rows(self):
		for option in self.options:
			row = HoverRow(self.list, option, lambda option=option: self.select(option), SIDEBAR_BG, ROW_HOVER_BG, bullet="")
			row.widget.pack(fill='x')
			row.set_selected(option == self.value)
			self.rows[option] = row

	def set_options(self, options):
		if tuple(options) == tuple(self.options):
			return
		for row in self.rows.values():
			row.widget.destroy()
		self.rows = {}
		self.options = options
		self.build_rows()

	def set_value(self, value):
		if value in self.rows:
			for option, row in self.rows.items():
				row.set_selected(option == value)
		self.value = value
		if self.enabled:
			self.label.config(text=value)

	def set_enabled(self, enabled, placeholder=""):
		if not enabled:
			self.close()
		self.enabled = enabled
		cursor = 'hand2' if enabled else 'arrow'
		self.label.config(text=self.value if enabled else placeholder, fg=ENTRY_FG if enabled else SUBHEADER_FG, cursor=cursor)
		self.arrow.config(text="▾" if enabled else "", cursor=cursor)
		self.box.config(cursor=cursor)

	def destroy(self):
		if self in Dropdown.instances:
			Dropdown.instances.remove(self)
		self.frame.destroy()

	def toggle(self):
		if not self.enabled:
			return
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
		if self.value in self.rows:
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