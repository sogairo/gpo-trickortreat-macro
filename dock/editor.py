import random
import colorsys
import tkinter as tk

from app.theme import SIDEBAR_BG, ROW_HOVER_BG, SLOT_BORDER, CATEGORY_FG, CATEGORY_FONT, SUBHEADER_FG, SUBHEADER_FONT, ITEM_FG, TITLE_FG, REGION_LABEL_FG, REGION_ALPHA, MARKER_ALPHA, OVERLAY_SATURATION, OVERLAY_DARK, OVERLAY_BRIGHT
from util.overlay.region import RegionOverlay
from util.overlay.marker import MarkerOverlay
from util.win32.api import user32
from util.win32.window import attach, place_above
from .widgets.panel import Panel
from .widgets.rows import HoverRow
from .widgets.scroll import ThinScrollbar
from .widgets.dropdown import Dropdown

INDENT = 12
BOX_GAP = 6
HINT_GAP = 8
SHARED_HINT = "Regions and markers are shared by all clients."
NO_CLIENTS = "No clients docked"
STACK_MS = 30

KINDS = (
	("region", "Region"),
	("marker", "Marker"),
)

OVERLAYS = {
	"region": RegionOverlay,
	"marker": MarkerOverlay,
}

def hsv_hex(hue, value):
	r, g, b = colorsys.hsv_to_rgb(hue, OVERLAY_SATURATION, value)
	return f"#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}"

def random_style(kind):
	hue = random.random()
	dark = hsv_hex(hue, OVERLAY_DARK)
	bright = hsv_hex(hue, OVERLAY_BRIGHT)
	if kind == "region":
		return {"fill": dark, "border": bright, "label_fg": REGION_LABEL_FG, "alpha": REGION_ALPHA, "font": SUBHEADER_FONT}
	return {"ring": dark, "fill": bright, "alpha": MARKER_ALPHA}

class Editor:
	def __init__(self, root, sidebar, items, slots, on_commit, on_close):
		self.root = root
		self.stack_job = self.root.after(STACK_MS, self.keep_stacked)
		self.sidebar = sidebar
		self.items = items
		self.slots = slots
		self.client_index = next((index for index, slot in enumerate(slots) if slot.hwnd), 0)
		self.hidden = False
		self.on_commit = on_commit
		self.selected = None
		self.overlay = None
		self.rows = {}

		self.panel = sidebar.show_editor("Editor")
		close = self.panel.detail
		close.config(text="✕", cursor='hand2')
		close.bind('<Enter>', lambda event: close.config(fg=TITLE_FG))
		close.bind('<Leave>', lambda event: close.config(fg=ITEM_FG))
		close.bind('<Button-1>', lambda event: on_close())

		self.preview_box = Panel(self.panel.body, "Preview")
		self.preview_box.container.pack(fill='x')
		self.tree_box = Panel(self.panel.body, "Regions & Markers")
		self.tree_box.container.pack(fill='both', expand=True, pady=(BOX_GAP, 0))

		self.build_clients()
		self.build_tree()

	def get_bounds(self):
		return self.slots[self.client_index].host_rect()

	def docked_names(self):
		return tuple(slot.name for slot in self.slots if slot.hwnd)

	def build_clients(self):
		self.show_on = self.preview_box.section("Show On")
		self.client_dropdown = Dropdown(self.show_on.frame, self.docked_names(), self.slots[self.client_index].name, self.pick_client)
		self.client_dropdown.frame.pack(fill='x')
		tk.Frame(self.preview_box.body, bg=SLOT_BORDER, height=1).pack(fill='x', pady=HINT_GAP)
		hint = tk.Label(self.preview_box.body, text=SHARED_HINT, bg=SIDEBAR_BG, fg=SUBHEADER_FG, font=SUBHEADER_FONT, anchor='w', justify='left')
		hint.pack(fill='x')
		hint.bind('<Configure>', lambda event: hint.config(wraplength=event.width))
		self.client_shown = None
		self.refresh_clients()

	def refresh_clients(self):
		names = self.docked_names()
		if names and not self.slots[self.client_index].hwnd:
			self.client_index = next(index for index, slot in enumerate(self.slots) if slot.hwnd)
			self.follow()
		self.client_dropdown.set_options(names)
		self.client_dropdown.set_value(self.slots[self.client_index].name)
		shown = bool(names)
		if shown == self.client_shown:
			return
		self.client_shown = shown
		self.client_dropdown.set_enabled(shown, NO_CLIENTS)

	def pick_client(self, name):
		index = next(index for index, slot in enumerate(self.slots) if slot.name == name)
		if index == self.client_index:
			return
		self.client_index = index
		self.follow()

	def build_tree(self):
		area = tk.Frame(self.tree_box.body, bg=SIDEBAR_BG)
		area.pack(fill='both', expand=True)

		canvas = tk.Canvas(area, bg=SIDEBAR_BG, highlightthickness=0, bd=0, width=1, height=1)
		scrollbar = ThinScrollbar(area, SIDEBAR_BG, canvas)
		canvas.config(yscrollcommand=scrollbar.set)
		scrollbar.canvas.pack(side='right', fill='y', padx=(4, 0))
		canvas.pack(side='left', fill='both', expand=True)

		content = tk.Frame(canvas, bg=SIDEBAR_BG)
		window = canvas.create_window((0, 0), window=content, anchor='nw')
		content.bind('<Configure>', lambda event: canvas.config(scrollregion=canvas.bbox('all')))
		canvas.bind('<Configure>', lambda event: canvas.itemconfigure(window, width=event.width))
		self.root.bind_all('<MouseWheel>', lambda event: canvas.yview_scroll(int(-event.delta / 120), 'units'))

		categories = {}
		for item in self.items:
			categories.setdefault(item["category"], {}).setdefault(item["kind"], []).append(item)

		first = True
		for category, groups in categories.items():
			tk.Label(content, text=category.upper(), bg=SIDEBAR_BG, fg=CATEGORY_FG, font=CATEGORY_FONT, anchor='w').pack(fill='x', pady=(0 if first else 10, 2))
			first = False

			for kind, noun in KINDS:
				entries = groups.get(kind)
				if not entries:
					continue

				tk.Label(content, text=noun.upper(), bg=SIDEBAR_BG, fg=SUBHEADER_FG, font=SUBHEADER_FONT, anchor='w').pack(fill='x', padx=(INDENT, 0), pady=(4, 1))

				for item in entries:
					row = HoverRow(content, item["label"], lambda item=item: self.select(item), SIDEBAR_BG, ROW_HOVER_BG)
					row.widget.pack(fill='x', padx=(INDENT * 2, 0))
					self.rows[(item["kind"], item["key"])] = row

	def select(self, item):
		if self.selected is item:
			self.deselect()
			return
		self.deselect()
		self.selected = item
		self.overlay = OVERLAYS[item["kind"]](self.root, item["value"], self.get_bounds, item["label"], **random_style(item["kind"]))
		attach(self.overlay.window, user32.GetParent(self.root.winfo_id()))
		self.stack()
		self.rows[(item["kind"], item["key"])].set_selected(True)

	def deselect(self):
		item = self.selected
		if item is None:
			return
		value = self.overlay.close()
		self.overlay = None
		self.selected = None
		self.rows[(item["kind"], item["key"])].set_selected(False)
		if value != item["value"]:
			item["value"] = value
			self.on_commit(item)

	def follow(self):
		if self.overlay:
			self.overlay.follow()
			self.stack()

	def stack(self):
		hwnd = self.slots[self.client_index].hwnd
		if self.overlay and not self.hidden and hwnd and user32.IsWindow(hwnd):
			place_above(self.overlay.window, hwnd)

	def show(self):
		if not self.hidden:
			return
		self.hidden = False
		if self.overlay:
			self.overlay.show()
			self.stack()

	def hide(self):
		if self.hidden:
			return
		self.hidden = True
		if self.overlay:
			self.overlay.hide()

	def keep_stacked(self):
		try:
			self.stack()
		finally:
			self.stack_job = self.root.after(STACK_MS, self.keep_stacked)

	def destroy(self):
		if self.stack_job is not None:
			self.root.after_cancel(self.stack_job)
			self.stack_job = None
		self.deselect()
		self.client_dropdown.destroy()
		self.root.unbind_all('<MouseWheel>')
		self.sidebar.hide_editor()