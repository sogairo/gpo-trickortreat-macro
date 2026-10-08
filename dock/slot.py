import tkinter as tk

from app.theme import SLOT_HOST_BG, SLOT_BORDER, SLOT_HEADER_BG, SLOT_ROW_HOVER_BG, SUBHEADER_FG, SUBHEADER_FONT, ITEM_FG, ITEM_FONT, CATEGORY_FONT
from app.settings import FOCUS
from util.win32 import user32, get_window_pid, get_window_rect, focus_window, is_foreground
from util.win32.constants import GWL_STYLE, GWLP_HWNDPARENT, GW_HWNDPREV, SW_RESTORE, WS_POPUP, STRIP_STYLES, SWP_NOSIZE, SWP_NOMOVE, SWP_NOZORDER, SWP_NOACTIVATE, SWP_FRAMECHANGED, SWP_SHOWWINDOW, SWP_ASYNCWINDOWPOS
from .widgets import HoverRow

class Slot:
	def __init__(self, parent_dock, index, parent):
		self.parent_dock = parent_dock
		self.index = index
		self.name = f"Client {index + 1}"
		self.hwnd = None
		self.pid = None
		self.saved_style = None
		self.saved_rect = None
		self.saved_owner = None

		self.container = tk.Frame(parent, bg=SLOT_HOST_BG, highlightthickness=1, highlightbackground=SLOT_BORDER)

		self.header = tk.Frame(self.container, bg=SLOT_HEADER_BG, padx=10, pady=5)
		self.header.pack(fill='x')
		tk.Label(self.header, text=self.name.upper(), bg=SLOT_HEADER_BG, fg=SUBHEADER_FG, font=SUBHEADER_FONT, anchor='w').pack(side='left')
		self.detail = tk.Label(self.header, bg=SLOT_HEADER_BG, fg=ITEM_FG, font=ITEM_FONT, anchor='w')
		self.detail.pack(side='left', padx=(8, 0))
		self.undock_row = HoverRow(self.header, "Undock", lambda: self.parent_dock.undock_slot(self), SLOT_HEADER_BG, SLOT_ROW_HOVER_BG, wrap=False)

		tk.Frame(self.container, bg=SLOT_BORDER, height=1).pack(fill='x')

		self.host = tk.Frame(self.container, bg=SLOT_HOST_BG)
		self.host.pack(fill='both', expand=True)
		self.placeholder = tk.Label(self.host, text="EMPTY", bg=SLOT_HOST_BG, fg=SUBHEADER_FG, font=CATEGORY_FONT)
		self.host.bind('<Configure>', self.on_resize)

		self.reset()

	def header_height(self):
		return self.header.winfo_reqheight() + 1

	def reset(self, keep_pid=False):
		self.hwnd = None
		self.saved_style = None
		self.saved_rect = None
		self.saved_owner = None
		if not keep_pid:
			self.pid = None
		self.placeholder.place(relx=0.5, rely=0.5, anchor='center')
		self.undock_row.widget.pack_forget()
		self.undock_row.reset()
		self.update_detail()

	def update_detail(self):
		if self.hwnd:
			self.detail.config(text=f"PID {self.pid}")
		elif self.pid:
			self.detail.config(text=f"Waiting for PID {self.pid}")
		else:
			self.detail.config(text="")

	def dock(self, hwnd):
		if user32.IsIconic(hwnd) or user32.IsZoomed(hwnd):
			user32.ShowWindow(hwnd, SW_RESTORE)
		self.saved_rect = get_window_rect(hwnd)
		self.saved_style = user32.GetWindowLongPtrW(hwnd, GWL_STYLE)
		self.saved_owner = user32.GetWindowLongPtrW(hwnd, GWLP_HWNDPARENT)
		user32.SetWindowLongPtrW(hwnd, GWL_STYLE, (self.saved_style & ~STRIP_STYLES) | WS_POPUP)
		user32.SetWindowLongPtrW(hwnd, GWLP_HWNDPARENT, self.parent_dock.hwnd)
		self.hwnd = hwnd
		self.pid = get_window_pid(hwnd)
		self.placeholder.place_forget()
		self.undock_row.widget.pack(side='right')
		self.update_detail()
		x, y, w, h = self.host_rect()
		user32.SetWindowPos(hwnd, None, x, y, w, h, SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED | SWP_SHOWWINDOW)
		self.raise_above_owner()

	def raise_above_owner(self):
		if not self.hwnd:
			return
		above = user32.GetWindow(self.parent_dock.hwnd, GW_HWNDPREV)
		if above == self.hwnd:
			return
		user32.SetWindowPos(self.hwnd, above, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)

	def undock(self):
		hwnd = self.hwnd
		if not hwnd:
			return None
		if user32.IsWindow(hwnd):
			user32.SetWindowLongPtrW(hwnd, GWLP_HWNDPARENT, self.saved_owner or 0)
			user32.SetWindowLongPtrW(hwnd, GWL_STYLE, self.saved_style)
			x, y, w, h = self.saved_rect
			user32.SetWindowPos(hwnd, None, x, y, w, h, SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED | SWP_SHOWWINDOW)
		self.reset()
		return hwnd

	def focus(self):
		return bool(self.hwnd) and focus_window(self.hwnd, attempts=FOCUS["attempts"], settle=FOCUS["retry_delay"])

	def is_focused(self):
		return is_foreground(self.hwnd)

	def host_rect(self):
		return get_window_rect(self.host.winfo_id())

	def fit(self, wait=True):
		if not self.hwnd:
			return
		flags = SWP_NOZORDER | SWP_NOACTIVATE
		if not wait:
			flags |= SWP_ASYNCWINDOWPOS
		x, y, w, h = self.host_rect()
		user32.SetWindowPos(self.hwnd, None, x, y, w, h, flags)

	def on_resize(self, event):
		self.fit(wait=False)