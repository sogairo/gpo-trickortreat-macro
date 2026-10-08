import tkinter as tk

from app.settings import LAYOUT
from app.theme import SIDEBAR_BG, SLOT_HEADER_BG, SLOT_BORDER, ROW_HOVER_BG, SUBHEADER_FG, SUBHEADER_FONT, ITEM_FG, ITEM_FONT, ENTRY_BG, ENTRY_FG, ENTRY_BORDER, ENTRY_FOCUS_BORDER
from .log import LogPanel
from .widgets import HoverRow, Dropdown, ENTRY_PAD

SECTION_GAP = 10
MASK_CHAR = "X"

def make_entry(parent, value, on_save, max_length=None, secret=False):
	if max_length:
		value = value[:max_length]
	var = tk.StringVar(value=value)
	box = tk.Frame(parent, bg=ENTRY_BG, highlightthickness=1, highlightbackground=ENTRY_BORDER, highlightcolor=ENTRY_BORDER)
	box.pack(fill='x')
	entry = tk.Entry(box, textvariable=var, bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG, font=ITEM_FONT, relief='flat', bd=0, highlightthickness=0)
	entry.pack(fill='x', padx=ENTRY_PAD, ipady=3)
	if secret:
		entry.config(show=MASK_CHAR)
	if max_length:
		check = entry.register(lambda proposed: len(proposed) <= max_length)
		entry.config(validate='key', validatecommand=(check, '%P'))
	saved = [value]

	def save(event):
		box.config(highlightbackground=ENTRY_BORDER)
		if secret:
			entry.config(show=MASK_CHAR)
		text = var.get().strip()
		var.set(text)
		if text != saved[0]:
			saved[0] = text
			on_save(text)

	def focus_entry(event):
		entry.focus_set()
		return "break"

	box.bind('<Button-1>', focus_entry)
	def focus_in(event):
		box.config(highlightbackground=ENTRY_FOCUS_BORDER)
		if secret:
			entry.config(show="")

	entry.bind('<FocusIn>', focus_in)
	entry.bind('<Return>', lambda event: entry.winfo_toplevel().focus_set())
	entry.bind('<FocusOut>', save)
	return entry

class Section:
	def __init__(self, panel, title):
		self.panel = panel
		self.visible = True
		self.frame = tk.Frame(panel.body, bg=SIDEBAR_BG)
		tk.Label(self.frame, text=title.upper(), bg=SIDEBAR_BG, fg=SUBHEADER_FG, font=SUBHEADER_FONT, anchor='w').pack(fill='x', pady=(0, 3))

	def entry(self, value, on_save, max_length=None, secret=False):
		return make_entry(self.frame, value, on_save, max_length, secret)

	def dropdown(self, options, value, on_select):
		dropdown = Dropdown(self.frame, options, value, on_select)
		dropdown.frame.pack(fill='x')
		return dropdown

	def set_visible(self, visible):
		if visible != self.visible:
			self.visible = visible
			self.panel.layout_sections()

class Panel:
	def __init__(self, parent, title):
		self.container = tk.Frame(parent, bg=SIDEBAR_BG, highlightthickness=1, highlightbackground=SLOT_BORDER)

		self.header = tk.Frame(self.container, bg=SLOT_HEADER_BG, padx=10, pady=5)
		self.header.pack(fill='x')
		tk.Label(self.header, text=title.upper(), bg=SLOT_HEADER_BG, fg=SUBHEADER_FG, font=SUBHEADER_FONT, anchor='w').pack(side='left')
		self.detail = tk.Label(self.header, bg=SLOT_HEADER_BG, fg=ITEM_FG, font=ITEM_FONT, anchor='e')
		self.detail.pack(side='right')

		tk.Frame(self.container, bg=SLOT_BORDER, height=1).pack(fill='x')

		self.body = tk.Frame(self.container, bg=SIDEBAR_BG, padx=6, pady=6)
		self.body.pack(fill='both', expand=True)
		self.fields = 0
		self.sections = []

	def row(self, text, command, hint=None):
		row = HoverRow(self.body, text, command, SIDEBAR_BG, ROW_HOVER_BG, hint=hint)
		row.widget.pack(fill='x')
		return row

	def field(self, text):
		top = 0 if self.fields == 0 else 8
		self.fields += 1
		tk.Label(self.body, text=text, bg=SIDEBAR_BG, fg=SUBHEADER_FG, font=SUBHEADER_FONT, anchor='w').pack(fill='x', pady=(top, 1))
		value = tk.Label(self.body, bg=SIDEBAR_BG, fg=ITEM_FG, font=ITEM_FONT, anchor='w', justify='left', padx=4, wraplength=LAYOUT["sidebar_width"] - 40)
		value.pack(fill='x')
		return value

	def entry(self, value, on_save, max_length=None):
		return make_entry(self.body, value, on_save, max_length)

	def section(self, title):
		section = Section(self, title)
		self.sections.append(section)
		self.layout_sections()
		return section

	def layout_sections(self):
		for section in self.sections:
			section.frame.pack_forget()
		first = True
		for section in self.sections:
			if not section.visible:
				continue
			section.frame.pack(fill='x', pady=(0 if first else SECTION_GAP, 0))
			first = False

	def log(self):
		panel = LogPanel(self.body)
		panel.frame.pack(fill='both', expand=True)
		return panel