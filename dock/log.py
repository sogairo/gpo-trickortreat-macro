import time
import tkinter as tk

from app.settings import LOG
from app.theme import SIDEBAR_BG, SUBHEADER_FG, SUBHEADER_FONT, ITEM_FG, ITEM_FONT
from .widgets import ThinScrollbar

class LogPanel:
	def __init__(self, parent):
		self.count = 0
		self.group = None
		self.frame = tk.Frame(parent, bg=SIDEBAR_BG)
		self.text = tk.Text(self.frame, width=1, height=1, bg=SIDEBAR_BG, fg=ITEM_FG, font=ITEM_FONT, wrap='word', bd=0, highlightthickness=0, padx=4, pady=0, spacing3=4, cursor='arrow', takefocus=0, state='disabled')
		self.text.tag_configure('time', foreground=SUBHEADER_FG)
		self.text.tag_configure('header', foreground=SUBHEADER_FG, font=SUBHEADER_FONT, spacing1=4)
		self.scrollbar = ThinScrollbar(self.frame, SIDEBAR_BG, self.text)
		self.text.config(yscrollcommand=self.scrollbar.set)
		self.scrollbar.canvas.pack(side='right', fill='y', padx=(4, 0))
		self.text.pack(side='left', fill='both', expand=True)

	def insert_line(self, index, message):
		stamp = time.strftime("%H:%M:%S")
		self.text.insert(index, f"{message}\n")
		self.text.insert(index, f"[{stamp}] ", 'time')

	def add(self, message, group):
		at_top = self.text.yview()[0] <= 0
		first = int(self.text.index('@0,0').split('.')[0])

		self.text.config(state='normal')
		if group == self.group:
			self.insert_line('2.0', message)
			inserted = 1
		else:
			self.insert_line('1.0', message)
			self.text.insert('1.0', f"── {group} ──\n", 'header')
			self.group = group
			inserted = 2

		self.count += inserted
		if self.count > LOG["limit"]:
			self.text.delete(f"{LOG['limit'] + 1}.0", 'end')
			self.count = LOG["limit"]
		self.text.config(state='disabled')

		if at_top:
			self.text.yview_moveto(0)
		else:
			self.text.yview(f"{min(first + inserted, self.count)}.0")