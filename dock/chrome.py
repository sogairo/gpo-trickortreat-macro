import tkinter as tk

from app.settings import APP_NAME
from app.theme import TITLE_BG, TITLE_FG, TITLE_ACTIVE_FG, TITLE_FONT, BUTTON_FONT, ROW_HOVER_BG
from util.win32.api import user32
from util.win32.window import get_work_area
from util.win32.constants import GWL_STYLE, WS_CAPTION, WS_THICKFRAME, WS_SYSMENU, WS_MINIMIZEBOX, WS_MAXIMIZEBOX, SWP_NOMOVE, SWP_NOSIZE, SWP_NOZORDER, SWP_NOACTIVATE, SWP_FRAMECHANGED, WM_NCLBUTTONDOWN, HTCAPTION
from .widgets.buttons import IconButton, draw_close_icon

class ChromeMixin:
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
		minimize_button.pack(side='right', padx=(4, 0))

		for widget in (self.titlebar, title):
			widget.bind('<Button-1>', self.drag_start)
			widget.bind('<Double-Button-1>', lambda event: "break")

	def make_title_button(self, text, command):
		button = tk.Button(self.titlebar, text=text, command=command, bg=TITLE_BG, fg=TITLE_FG, relief='flat', font=BUTTON_FONT, activebackground=ROW_HOVER_BG, activeforeground=TITLE_ACTIVE_FG, bd=0, padx=8, cursor='hand2')
		button.bind('<Enter>', lambda event: button.config(bg=ROW_HOVER_BG))
		button.bind('<Leave>', lambda event: button.config(bg=TITLE_BG))
		return button

	def apply_borderless(self):
		style = user32.GetWindowLongPtrW(self.hwnd, GWL_STYLE)
		new_style = (style & ~(WS_CAPTION | WS_THICKFRAME | WS_MAXIMIZEBOX)) | WS_SYSMENU | WS_MINIMIZEBOX
		if new_style != style:
			user32.SetWindowLongPtrW(self.hwnd, GWL_STYLE, new_style)
			user32.SetWindowPos(self.hwnd, None, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED)

	def set_window_rect(self, x, y, w, h):
		user32.SetWindowPos(self.hwnd, None, x, y, w, h, SWP_NOZORDER | SWP_NOACTIVATE)

	def center(self, width, height):
		x, y, w, h = get_work_area(self.hwnd)
		self.set_window_rect(x + max(0, (w - width) // 2), y + max(0, (h - height) // 2), width, height)

	def minimize(self):
		self.root.iconify()

	def drag_start(self, event):
		user32.ReleaseCapture()
		user32.PostMessageW(self.hwnd, WM_NCLBUTTONDOWN, HTCAPTION, 0)
		return "break"
