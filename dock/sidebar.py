import tkinter as tk

from app.settings import LAYOUT
from app.theme import GRID_BG
from .panel import Panel

class Sidebar:
	def __init__(self, parent):
		self.frame = tk.Frame(parent, bg=GRID_BG, width=LAYOUT["sidebar_width"], padx=4, pady=4)
		self.frame.pack(side='left', fill='y')
		self.frame.pack_propagate(False)
		self.panels = []
		self.editor_panel = None

	def pack_panel(self, panel, expand):
		panel.container.pack(fill='both' if expand else 'x', expand=expand, padx=LAYOUT["slot_pad"], pady=LAYOUT["slot_pad"])

	def panel(self, title, expand=False):
		panel = Panel(self.frame, title)
		self.panels.append((panel, expand))
		self.pack_panel(panel, expand)
		return panel

	def show_editor(self, title):
		for panel, expand in self.panels:
			panel.container.pack_forget()
		self.editor_panel = Panel(self.frame, title)
		self.pack_panel(self.editor_panel, True)
		return self.editor_panel

	def hide_editor(self):
		if self.editor_panel is not None:
			self.editor_panel.container.destroy()
			self.editor_panel = None
		for panel, expand in self.panels:
			self.pack_panel(panel, expand)