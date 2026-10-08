import os
import queue
import threading
import tkinter as tk

import keyboard

from app.settings import APP_NAME, DOCK, LAYOUT, FILES, SERVER_CODE, REPOSITION, REGIONS, MARKERS, DEFAULT_KEYBINDS
from app.theme import WINDOW_BORDER, SIDEBAR_BG, GRID_BG, SEPARATOR, TITLE_FG, ITEM_FG
from macro import Macro
from macro.runner import client_requirement
from macro.actions import StepContext, load_steps, load_rejoin
from util import ocr
from util.config import load_setting, save_setting
from util.overlay import load_section, save_section, REGION_KEYS, MARKER_KEYS
from util.win32.constants import WM_NULL
from util.win32 import user32, get_roblox_pids, find_roblox_windows, get_window_pid, get_window_rect, get_work_area
from .chrome import ChromeMixin
from .editor import Editor
from .sidebar import Sidebar
from .widgets import Dropdown
from .slot import Slot

PENDING_MS = 20
DEFAULT_REPOSITION = next((name for name, config in REPOSITION.items() if config.get("default")), next(iter(REPOSITION)))

def is_rejoin(option):
	return bool(REPOSITION[option].get("rejoin"))
GENERAL_GROUP = "Macro"

class Dock(ChromeMixin):
	def __init__(self):
		self.root = tk.Tk()
		self.root.title(APP_NAME)
		self.root.configure(bg=WINDOW_BORDER)
		self.root.protocol("WM_DELETE_WINDOW", self.on_close)

		self.ignored = set()
		self.full_notified = set()
		self.min_size = None
		self.min_width = LAYOUT["min_width"]
		self.min_height = LAYOUT["min_height"]
		self.auto_dock = bool(load_setting(FILES["config"], "auto_dock", True))
		self.regions = load_section(FILES["config"], "regions", {name: config["default"] for name, config in REGIONS.items()}, REGION_KEYS)
		self.markers = load_section(FILES["config"], "markers", {name: config["default"] for name, config in MARKERS.items()}, MARKER_KEYS)
		self.editor = None
		self.server_code = load_setting(FILES["config"], "private_server_code", "")
		self.reposition_by = load_setting(FILES["config"], "reposition_by", DEFAULT_REPOSITION)
		if self.reposition_by not in REPOSITION:
			self.reposition_by = DEFAULT_REPOSITION
		self.keybinds = dict(DEFAULT_KEYBINDS)
		self.keybinds.update(load_setting(FILES["config"], "keybinds", {}))
		self.pending = queue.Queue()
		self.wake_signal = threading.Event()
		self.start_pending = False
		self.start_lock = threading.Lock()
		self.macro = Macro(lambda message, group=None: self.from_thread(self.log, message, group), lambda stopped: self.from_thread(self.on_macro_finished, stopped))

		self.init_chrome()

		self.inner = tk.Frame(self.root, bg=SIDEBAR_BG)
		self.inner.pack(fill='both', expand=True, padx=2, pady=2)
		inner = self.inner

		self.build_titlebar(inner)
		tk.Frame(inner, bg=SEPARATOR, height=1).pack(fill='x')

		self.body = tk.Frame(inner, bg=SIDEBAR_BG)
		self.body.pack(fill='both', expand=True)
		self.build_sidebar(self.body)
		tk.Frame(self.body, bg=SEPARATOR, width=1).pack(side='left', fill='y')
		self.build_grid(self.body)

		self.root.bind('<Map>', self.on_map)
		self.root.bind('<Unmap>', self.on_unmap)
		self.root.bind('<Configure>', self.on_root_configure)
		self.root.bind_all('<Button-1>', self.clear_focus, add='+')

		self.root.minsize(self.min_width, self.min_height)
		self.root.update_idletasks()
		self.hwnd = user32.GetParent(self.root.winfo_id())
		self.apply_borderless()
		self.center(1800, 1100)

		if self.auto_dock:
			self.log(f"{APP_NAME} started, watching for clients")
		else:
			self.log(f"{APP_NAME} started, auto-dock off")
		self.log("Loading OCR model")
		ocr.preload(lambda: self.from_thread(self.log, "OCR model ready"))
		self.bind_hotkeys()
		self.root.after(PENDING_MS, self.poll_pending)
		threading.Thread(target=self.wake_loop, daemon=True).start()
		self.root.after(300, self.tick)

	def build_sidebar(self, parent):
		self.sidebar = Sidebar(parent)

		self.dock_panel = self.sidebar.panel("Dock")
		self.dock_panel.row("Dock All", self.dock_all)
		self.dock_panel.row("Undock All", self.undock_all)
		self.auto_dock_row = self.dock_panel.row(self.auto_dock_text(), self.toggle_auto_dock)
		self.update_count(0)

		self.settings_panel = self.sidebar.panel("Macro Settings")
		self.settings_panel.section("Reposition By").dropdown(tuple(REPOSITION), self.reposition_by, self.save_reposition)
		self.server_section = self.settings_panel.section("Private Server")
		self.server_section.entry(self.server_code, self.save_server_code, max_length=SERVER_CODE["length"], secret=True)
		self.server_section.set_visible(is_rejoin(self.reposition_by))

		self.macro_panel = self.sidebar.panel("Macro")
		self.macro_panel.row("Start", self.start_macro, hint=self.keybinds["start_key"].upper())
		self.macro_panel.row("Stop", self.stop_macro, hint=self.keybinds["stop_key"].upper())
		self.set_macro_state(False)

		self.overlay_panel = self.sidebar.panel("Regions & Markers")
		self.overlay_panel.row("Edit", self.open_editor)

		self.log_panel = self.sidebar.panel("Log", expand=True).log()

	def build_grid(self, parent):
		self.grid = tk.Frame(parent, bg=GRID_BG, padx=4, pady=4)
		self.grid.pack(side='left', fill='both', expand=True)
		for i in range(2):
			self.grid.rowconfigure(i, weight=1, uniform='slot')
			self.grid.columnconfigure(i, weight=1, uniform='slot')

		self.slots = []
		for index in range(DOCK["max_slots"]):
			slot = Slot(self, index, self.grid)
			slot.container.grid(row=index // 2, column=index % 2, sticky='nsew', padx=LAYOUT["slot_pad"], pady=LAYOUT["slot_pad"])
			self.slots.append(slot)

	def log(self, message, group=None):
		group = group or GENERAL_GROUP
		print(f"[{group}] {message}")
		self.log_panel.add(message, group)

	def from_thread(self, fn, *args):
		self.pending.put((fn, args))
		self.wake_signal.set()

	def wake_loop(self):
		while True:
			self.wake_signal.wait()
			self.wake_signal.clear()
			if self.hwnd:
				user32.PostMessageW(self.hwnd, WM_NULL, 0, 0)

	def drain_pending(self, event=None):
		while True:
			try:
				fn, args = self.pending.get_nowait()
			except queue.Empty:
				break
			try:
				fn(*args)
			except Exception as error:
				self.log(f"{APP_NAME} error: {error}")

	def poll_pending(self):
		self.drain_pending()
		self.root.after(PENDING_MS, self.poll_pending)

	def hotkey_stop(self):
		if self.macro.stop():
			self.from_thread(self.log, "Macro stopped")
		else:
			self.cancel_queued_start()

	def cancel_queued_start(self):
		with self.start_lock:
			if not self.start_pending:
				return
			self.start_pending = False
		self.from_thread(self.log, "Queued start cancelled")

	def clear_focus(self, event):
		if not isinstance(event.widget, tk.Entry):
			self.root.focus_set()
		if isinstance(event.widget, tk.Misc):
			Dropdown.close_others(event.widget)

	def save_reposition(self, option):
		self.reposition_by = option
		self.server_section.set_visible(is_rejoin(option))
		try:
			save_setting(FILES["config"], "reposition_by", option)
		except Exception as error:
			self.log(f"Reposition save error: {error}")
			return
		self.log(f"Reposition by {option}")

	def bind_hotkeys(self):
		try:
			keyboard.on_press_key(self.keybinds["start_key"], lambda event: self.start_macro())
			keyboard.on_press_key(self.keybinds["stop_key"], lambda event: self.hotkey_stop())
		except Exception as error:
			self.log(f"Hotkey error: {error}")

	def save_server_code(self, code):
		self.server_code = code
		try:
			save_setting(FILES["config"], "private_server_code", code)
		except Exception as error:
			self.log(f"Server code save error: {error}")
			return
		if code:
			self.log("Saved private server code")
		else:
			self.log("Cleared private server code")

	def set_macro_state(self, running):
		if running:
			self.macro_panel.detail.config(text="Running", fg=TITLE_FG)
		else:
			self.macro_panel.detail.config(text="Stopped", fg=ITEM_FG)

	def start_macro(self):
		with self.start_lock:
			if self.macro.stopping:
				if not self.start_pending:
					self.start_pending = True
					self.from_thread(self.log, "Previous run still finishing, starting when it's done")
					threading.Thread(target=self.start_after_stop, daemon=True).start()
				return
			if self.macro.running:
				return
			self.begin_macro()

	def start_after_stop(self):
		self.macro.wait_until_done(timeout=30)
		with self.start_lock:
			if not self.start_pending:
				return
			self.start_pending = False
			if self.macro.running:
				return
			self.begin_macro()

	def prepare_run(self):
		if not ocr.is_ready():
			return "OCR model is still loading, start again once it's ready", None
		if is_rejoin(self.reposition_by) and not self.server_code:
			return "Set a private server code before starting", None
		count = len(self.docked_clients())
		low, high = REPOSITION[self.reposition_by]["clients"]
		if not low <= count <= high:
			return f"{self.reposition_by} needs {client_requirement(low, high)} ({count} docked)", None
		path = os.path.join(FILES["reposition_dir"], REPOSITION[self.reposition_by]["file"])
		if not os.path.exists(path):
			return f"No reposition file for {self.reposition_by} yet ({path})", None
		try:
			scripts = {"steps": load_steps(FILES["steps"]), "reposition": self.reposition_by, "clients": (low, high), "first_client_only": bool(REPOSITION[self.reposition_by].get("first_client_only")), "stagger_from": REPOSITION[self.reposition_by].get("stagger_from"), "stagger_cooldown": REPOSITION[self.reposition_by].get("stagger_cooldown", 0)}
			if is_rejoin(self.reposition_by):
				scripts["leave"], scripts["join"] = load_rejoin(path)
				scripts["recovery"] = load_steps(FILES["connection_failed"])
			else:
				scripts["inline"] = load_steps(path)
		except Exception as error:
			return f"Could not load steps: {error}", None
		ocr_texts = {key: config.get("ocr_text", "") for key, config in REGIONS.items()}
		for key, config in REGIONS.items():
			if not ocr_texts[key]:
				return f"Set ocr_text for {config['label']} in settings.py before starting", None
		ctx = StepContext(lambda message, group=None: self.from_thread(self.log, message, group), dict(self.markers), dict(self.regions), ocr_texts, self.server_code)
		return None, (scripts, ctx)

	def begin_macro(self):
		error, prepared = self.prepare_run()
		if error:
			self.from_thread(self.log, error)
			return
		scripts, ctx = prepared
		if self.editor:
			self.from_thread(self.close_editor)
		self.macro.start(scripts, self.docked_clients, ctx)
		self.from_thread(self.set_macro_state, True)
		self.from_thread(self.log, "Macro started")
		clients = self.docked_clients()
		if scripts["first_client_only"] and len(clients) > 1:
			self.from_thread(self.log, f"{self.reposition_by} only plays on {clients[0].name} ({len(clients)} docked)")

	def docked_clients(self):
		return [slot for slot in self.slots if slot.hwnd]

	def stop_macro(self):
		if self.macro.stop():
			self.log("Macro stopped")
		else:
			self.cancel_queued_start()

	def on_macro_finished(self, stopped):
		self.set_macro_state(False)
		if not stopped:
			self.log("Macro finished")

	def on_map(self, event):
		if event.widget is self.root:
			self.apply_borderless()
			self.fit_all()
			for slot in self.slots:
				slot.raise_above_owner()
			if self.editor:
				self.editor.show()

	def on_unmap(self, event):
		if event.widget is self.root and self.editor:
			self.editor.hide()

	def on_root_configure(self, event):
		if event.widget is self.root:
			self.fit_all()
			self.root.after_idle(self.follow_editor)

	def follow_editor(self):
		if self.editor:
			self.editor.follow()

	def editor_items(self):
		items = []
		for kind, configs, values in (("region", REGIONS, self.regions), ("marker", MARKERS, self.markers)):
			for key, config in configs.items():
				items.append({
					"kind": kind,
					"key": key,
					"label": config["label"],
					"category": config.get("category", "General"),
					"value": values[key],
				})
		return items

	def open_editor(self):
		if self.editor:
			return
		self.editor = Editor(self.root, self.sidebar, self.editor_items(), self.slots, self.commit_editor_item, self.close_editor)

	def close_editor(self):
		if not self.editor:
			return
		editor = self.editor
		self.editor = None
		editor.destroy()

	def commit_editor_item(self, item):
		if item["kind"] == "region":
			section = "regions"
			values = self.regions
		else:
			section = "markers"
			values = self.markers
		values[item["key"]] = item["value"]
		try:
			save_section(FILES["config"], section, values)
			self.log(f"Edited {item['label']}")
		except Exception as error:
			self.log(f"Save error: {error}")

	def fit_all(self):
		for slot in self.slots:
			slot.fit(wait=False)

	def pick_slot(self, pid):
		for slot in self.slots:
			if slot.pid == pid and slot.hwnd is None:
				return slot
		for slot in self.slots:
			if slot.pid is None:
				return slot
		return None

	def smallest_host(self):
		sizes = [slot.host_rect() for slot in self.slots]
		return min(size[2] for size in sizes), min(size[3] for size in sizes)

	def check_client_sizes(self):
		for slot in self.slots:
			if not slot.hwnd:
				continue
			x, y, w, h = get_window_rect(slot.hwnd)
			hx, hy, hw, hh = slot.host_rect()
			if w > hw + 1 or h > hh + 1:
				self.update_min_size(w, h)

	def update_min_size(self, w, h):
		old_w, old_h = self.min_size or (0, 0)
		w = max(w, old_w)
		h = max(h, old_h)
		if (w, h) == (old_w, old_h):
			return
		self.min_size = (w, h)

		self.root.update_idletasks()
		wx, wy, ww, wh = get_window_rect(self.hwnd)
		host_w, host_h = self.smallest_host()
		self.min_width = max(LAYOUT["min_width"], ww + 2 * (w - host_w) + 2)
		self.min_height = max(LAYOUT["min_height"], wh + 2 * (h - host_h) + 2)
		self.root.minsize(self.min_width, self.min_height)

		if ww >= self.min_width and wh >= self.min_height:
			self.log(f"Roblox minimum size is {w}x{h}")
			return
		ax, ay, aw, ah = get_work_area(self.hwnd)
		if self.maximized or self.min_width > aw or self.min_height > ah:
			self.log(f"Roblox minimum size is {w}x{h}, screen too small for 4 clients")
			return
		new_w = max(ww, self.min_width)
		new_h = max(wh, self.min_height)
		new_x = max(ax, min(wx, ax + aw - new_w))
		new_y = max(ay, min(wy, ay + ah - new_h))
		self.set_window_rect(new_x, new_y, new_w, new_h)
		self.root.update_idletasks()
		self.fit_all()
		self.log(f"Roblox minimum size is {w}x{h}, dock expanded to fit")

	def dock_into(self, slot, hwnd):
		slot.dock(hwnd)
		self.log(f"Docked {slot.name} (PID {slot.pid})")

	def refresh(self, force=False):
		dock_new = self.auto_dock or force
		pids = get_roblox_pids(DOCK["roblox_exe"])

		for slot in self.slots:
			if slot.hwnd and not user32.IsWindow(slot.hwnd):
				if slot.pid in pids:
					slot.reset(keep_pid=True)
					self.log(f"{slot.name} window lost, waiting for PID {slot.pid}")
				else:
					slot.reset()
					self.log(f"{slot.name} closed, slot freed")
			elif slot.hwnd is None and slot.pid and slot.pid not in pids:
				slot.reset()
				self.log(f"{slot.name} closed, slot freed")

		self.ignored = {hwnd for hwnd in self.ignored if user32.IsWindow(hwnd)}
		self.full_notified = {hwnd for hwnd in self.full_notified if user32.IsWindow(hwnd)}
		docked_pids = {slot.pid for slot in self.slots if slot.hwnd}

		for hwnd in find_roblox_windows(pids, DOCK["min_client_size"]):
			if hwnd in self.ignored:
				continue
			pid = get_window_pid(hwnd)
			if pid in docked_pids:
				continue
			waiting = any(slot.pid == pid and slot.hwnd is None for slot in self.slots)
			if not dock_new and not waiting:
				continue
			slot = self.pick_slot(pid)
			if slot is None:
				if hwnd not in self.full_notified:
					self.full_notified.add(hwnd)
					self.log("Grid full, client left undocked")
				continue
			self.dock_into(slot, hwnd)
			docked_pids.add(pid)

		docked = sum(1 for slot in self.slots if slot.hwnd)
		self.update_count(docked)
		if self.editor:
			self.editor.refresh_clients()

	def update_count(self, docked):
		color = TITLE_FG if docked == DOCK["max_slots"] else ITEM_FG
		self.dock_panel.detail.config(text=f"{docked} / {DOCK['max_slots']}", fg=color)

	def tick(self):
		try:
			self.refresh()
			self.check_client_sizes()
		except Exception as error:
			self.log(f"{APP_NAME} error: {error}")
		self.root.after(DOCK["poll_ms"], self.tick)

	def undock_slot(self, slot):
		name = slot.name
		hwnd = slot.undock()
		if hwnd:
			self.ignored.add(hwnd)
			self.log(f"Undocked {name}")
		self.refresh()

	def undock_all(self):
		for slot in self.slots:
			hwnd = slot.undock()
			if hwnd:
				self.ignored.add(hwnd)
		self.log("Undocked all clients")
		self.refresh()

	def dock_all(self):
		self.ignored.clear()
		self.log("Docking all clients")
		self.refresh(force=True)

	def auto_dock_text(self):
		return f"Auto-Dock: {'On' if self.auto_dock else 'Off'}"

	def toggle_auto_dock(self):
		self.auto_dock = not self.auto_dock
		self.auto_dock_row.set_text(self.auto_dock_text())
		try:
			save_setting(FILES["config"], "auto_dock", self.auto_dock)
		except Exception as error:
			self.log(f"Auto-dock save error: {error}")
		self.log(f"Auto-dock {'on' if self.auto_dock else 'off'}")
		if self.auto_dock:
			self.refresh()

	def on_close(self):
		print("Closing. Undocking all clients first.")
		self.macro.stop()
		try:
			keyboard.unhook_all()
		except Exception:
			pass
		self.close_editor()
		for slot in self.slots:
			slot.undock()
		self.root.destroy()

	def run(self):
		try:
			self.root.mainloop()
		except KeyboardInterrupt:
			self.on_close()