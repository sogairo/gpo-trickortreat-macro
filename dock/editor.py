import random
import colorsys
import tkinter as tk

from app.theme import SIDEBAR_BG, ROW_HOVER_BG, CATEGORY_FG, CATEGORY_FONT, SUBHEADER_FG, SUBHEADER_FONT, ITEM_FG, TITLE_FG, REGION_LABEL_FG, REGION_ALPHA, MARKER_ALPHA, OVERLAY_SATURATION, OVERLAY_DARK, OVERLAY_BRIGHT
from util.overlay import RegionOverlay, MarkerOverlay
from .panel import Panel
from .widgets import HoverRow, ThinScrollbar

INDENT = 12
BOX_GAP = 6

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
		self.sidebar = sidebar
		self.items = items
		self.slots = slots
		self.client_index = 0
		self.on_commit = on_commit
		self.selected = None
		self.overlay = None
		self.rows = {}
		self.client_rows = []

		self.panel = sidebar.show_editor("Editor")
		close = self.panel.detail
		close.config(text="✕", cursor='hand2')
		close.bind('<Enter>', lambda event: close.config(fg=TITLE_FG))
		close.bind('<Leave>', lambda event: close.config(fg=ITEM_FG))
		close.bind('<Button-1>', lambda event: on_close())

		self.client_box = Panel(self.panel.body, "Client")
		self.client_box.container.pack(fill='x')
		self.tree_box = Panel(self.panel.body, "Regions & Markers")
		self.tree_box.container.pack(fill='both', expand=True, pady=(BOX_GAP, 0))

		self.build_clients()
		self.build_tree()

	def get_bounds(self):
		return self.slots[self.client_index].host_rect()

	def client_text(self, index):
		slot = self.slots[index]
		return slot.name if slot.hwnd else f"{slot.name} (empty)"

	def build_clients(self):
		for index in range(len(self.slots)):
			row = HoverRow(self.client_box.body, self.client_text(index), lambda index=index: self.pick_client(index), SIDEBAR_BG, ROW_HOVER_BG)
			row.widget.pack(fill='x')
			row.set_selected(index == self.client_index)
			self.client_rows.append(row)

	def refresh_clients(self):
		for index, row in enumerate(self.client_rows):
			text = self.client_text(index)
			if row.text != text:
				row.set_text(text)

	def pick_client(self, index):
		if index == self.client_index:
			return
		self.client_rows[self.client_index].set_selected(False)
		self.client_index = index
		self.client_rows[index].set_selected(True)
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

	def show(self):
		if self.overlay:
			self.overlay.show()

	def hide(self):
		if self.overlay:
			self.overlay.hide()

	def destroy(self):
		self.deselect()
		self.root.unbind_all('<MouseWheel>')
		self.sidebar.hide_editor()