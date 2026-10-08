import tkinter as tk

from app.settings import APP_NAME
from app.theme import TITLE_BG, TITLE_FG, TITLE_ACTIVE_FG, TITLE_FONT, BUTTON_FONT, ROW_HOVER_BG
from util.win32 import user32, get_window_rect, get_work_area
from util.win32.constants import GWL_STYLE, WS_CAPTION, WS_THICKFRAME, WS_SYSMENU, WS_MINIMIZEBOX, WS_MAXIMIZEBOX, SWP_NOMOVE, SWP_NOSIZE, SWP_NOZORDER, SWP_NOACTIVATE, SWP_FRAMECHANGED, WM_NCLBUTTONDOWN, HTCAPTION
from .widgets import IconButton, draw_close_icon, draw_maximize_icon

class ChromeMixin:
	def init_chrome(self):
		self.maximized = False
		self.normal_rect = None

	def build_titlebar(self, parent):
		self.titlebar = tk.Frame(parent, bg=TITLE_BG, padx=12, pady=8)
		self.titlebar.pack(fill='x')

		title = tk.Label(self.titlebar, text=APP_NAME, bg=TITLE_BG, fg=TITLE_FG, font=TITLE_FONT, anchor='w')
		title.pack(side='left')

		minimize_button = self.make_title_button("—", self.minimize)
		self.root.update_idletasks()
		width = minimize_button.winfo_reqwidth()
		height = minimize_button.winfo_reqheight()

		IconButton(self.titlebar, width, height, draw_close_icon, self.on_close).canvas.pack(side='right', padx=(4, 0))
		self.max_button = IconButton(self.titlebar, width, height, lambda canvas, w, h, color: draw_maximize_icon(canvas, w, h, color, self.maximized), self.toggle_maximize)
		self.max_button.canvas.pack(side='right', padx=(4, 0))
		minimize_button.pack(side='right', padx=(4, 0))

		for widget in (self.titlebar, title):
			widget.bind('<Button-1>', self.drag_start)
			widget.bind('<Double-Button-1>', self.on_title_double_click)

	def make_title_button(self, text, command):
		button = tk.Button(self.titlebar, text=text, command=command, bg=TITLE_BG, fg=TITLE_FG, relief='flat', font=BUTTON_FONT, activebackground=ROW_HOVER_BG, activeforeground=TITLE_ACTIVE_FG, bd=0, padx=8, cursor='hand2')
		button.bind('<Enter>', lambda event: button.config(bg=ROW_HOVER_BG))
		button.bind('<Leave>', lambda event: button.config(bg=TITLE_BG))
		return button

	def apply_borderless(self):
		style = user32.GetWindowLongPtrW(self.hwnd, GWL_STYLE)
		new_style = (style & ~(WS_CAPTION | WS_THICKFRAME)) | WS_SYSMENU | WS_MINIMIZEBOX | WS_MAXIMIZEBOX
		if new_style != style:
			user32.SetWindowLongPtrW(self.hwnd, GWL_STYLE, new_style)
			user32.SetWindowPos(self.hwnd, None, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED)

	def set_window_rect(self, x, y, w, h):
		user32.SetWindowPos(self.hwnd, None, x, y, w, h, SWP_NOZORDER | SWP_NOACTIVATE)

	def center(self, width, height):
		x, y, w, h = get_work_area(self.hwnd)
		width = min(width, w)
		height = min(height, h)
		self.set_window_rect(x + (w - width) // 2, y + (h - height) // 2, width, height)

	def minimize(self):
		self.root.iconify()

	def toggle_maximize(self):
		if self.maximized:
			self.maximized = False
			self.inner.pack_configure(padx=2, pady=2)
			self.set_window_rect(*self.normal_rect)
		else:
			self.normal_rect = get_window_rect(self.hwnd)
			self.maximized = True
			self.inner.pack_configure(padx=0, pady=0)
			self.set_window_rect(*get_work_area(self.hwnd))
		self.max_button.redraw()

	def on_title_double_click(self, event):
		self.toggle_maximize()
		return "break"

	def drag_start(self, event):
		if self.maximized:
			wx, wy, ww, wh = get_window_rect(self.hwnd)
			ratio = (event.x_root - wx) / max(1, ww)
			self.toggle_maximize()
			x, y, w, h = self.normal_rect
			self.set_window_rect(int(event.x_root - ratio * w), wy, w, h)
			self.root.update_idletasks()
		user32.ReleaseCapture()
		user32.PostMessageW(self.hwnd, WM_NCLBUTTONDOWN, HTCAPTION, 0)
		return "break"
