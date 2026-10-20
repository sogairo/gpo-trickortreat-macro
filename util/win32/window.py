import time
import ctypes
from ctypes import wintypes

from .api import user32, kernel32, MONITORINFO, WNDENUMPROC, CONSOLE_HANDLER
from .process import process_start_time, forget_exited
from .constants import GW_OWNER, GWL_STYLE, WS_VISIBLE, SW_HIDE, SW_SHOWNA, SWP_NOZORDER, SWP_FRAMECHANGED, CTRL_CLOSE_EVENT, CTRL_LOGOFF_EVENT, CTRL_SHUTDOWN_EVENT, MONITOR_DEFAULTTONEAREST, VK_MENU, KEYEVENTF_KEYUP, WM_GETTEXTLENGTH, SMTO_ABORTIFHUNG, GWLP_HWNDPARENT, GW_HWNDPREV, SWP_NOMOVE, SWP_NOSIZE, SWP_NOACTIVATE

TITLE_TIMEOUT_MS = 200
TAG = "TrickOrTreat."
TAG_FIELDS = ("Style", "X", "Y", "W", "H", "Owner")
TAG_DOCKED = TAG + "Docked"
STYLE_MASK = 0xFFFFFFFF & ~WS_VISIBLE
UNDOCK_ATTEMPTS = 3
UNDOCK_SETTLE = 0.1

def get_window_pid(hwnd):
	pid = wintypes.DWORD()
	user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
	return pid.value

def title_length(hwnd):
	length = ctypes.c_size_t()
	if not user32.SendMessageTimeoutW(hwnd, WM_GETTEXTLENGTH, 0, 0, SMTO_ABORTIFHUNG, TITLE_TIMEOUT_MS, ctypes.byref(length)):
		return None
	return length.value

def get_window_rect(hwnd):
	rect = wintypes.RECT()
	user32.GetWindowRect(hwnd, ctypes.byref(rect))
	return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top

def get_work_area(hwnd):
	monitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
	info = MONITORINFO()
	info.cbSize = ctypes.sizeof(info)
	user32.GetMonitorInfoW(monitor, ctypes.byref(info))
	work = info.rcWork
	return work.left, work.top, work.right - work.left, work.bottom - work.top

def live_owner(owner):
	return owner if owner and user32.IsWindow(owner) else 0

def tag_window(hwnd, style, rect, owner):
	for name, value in zip(TAG_FIELDS, (style, *rect, owner)):
		user32.SetPropW(hwnd, TAG + name, value)
	user32.SetPropW(hwnd, TAG_DOCKED, 1)

def read_tag(hwnd):
	if not user32.GetPropW(hwnd, TAG_DOCKED):
		return None
	style, x, y, w, h, owner = (user32.GetPropW(hwnd, TAG + name) for name in TAG_FIELDS)
	return style, (x, y, w, h), owner

def clear_tag(hwnd):
	for name in TAG_FIELDS:
		user32.RemovePropW(hwnd, TAG + name)
	user32.RemovePropW(hwnd, TAG_DOCKED)

def restore_window(hwnd, style, rect, owner):
	user32.ShowWindow(hwnd, SW_HIDE)
	user32.SetWindowLongPtrW(hwnd, GWLP_HWNDPARENT, live_owner(owner))
	user32.SetWindowLongPtrW(hwnd, GWL_STYLE, style)
	x, y, w, h = rect
	user32.SetWindowPos(hwnd, None, x, y, w, h, SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED)
	user32.ShowWindow(hwnd, SW_SHOWNA)

def is_restored(hwnd, style, owner):
	current = user32.GetWindowLongPtrW(hwnd, GWL_STYLE)
	return (current & STYLE_MASK) == (style & STYLE_MASK) and user32.GetWindowLongPtrW(hwnd, GWLP_HWNDPARENT) == live_owner(owner) and bool(user32.IsWindowVisible(hwnd))

def undock_window(hwnd, style, rect, owner):
	for _ in range(UNDOCK_ATTEMPTS):
		if not user32.IsWindow(hwnd):
			return True
		try:
			restore_window(hwnd, style, rect, owner)
		except Exception:
			pass
		time.sleep(UNDOCK_SETTLE)
		if user32.IsWindow(hwnd) and is_restored(hwnd, style, owner):
			clear_tag(hwnd)
			return True
	return not user32.IsWindow(hwnd)

def restore_tagged(pids):
	tagged = []
	if not pids:
		return 0, 0

	def callback(hwnd, lparam):
		if get_window_pid(hwnd) in pids and user32.GetPropW(hwnd, TAG_DOCKED):
			tagged.append(hwnd)
		return True

	user32.EnumWindows(WNDENUMPROC(callback), 0)
	restored = failed = 0
	for hwnd in tagged:
		tag = read_tag(hwnd)
		if tag is None:
			continue
		if undock_window(hwnd, *tag):
			restored += 1
		else:
			failed += 1
	return restored, failed

def on_console_close(callback):
	def handler(event):
		if event in (CTRL_CLOSE_EVENT, CTRL_LOGOFF_EVENT, CTRL_SHUTDOWN_EVENT):
			try:
				callback()
			except Exception:
				pass
		return False

	handler = CONSOLE_HANDLER(handler)
	kernel32.SetConsoleCtrlHandler(handler, True)
	return handler

def rescue_orphans(pids):
	rescued = []
	if not pids:
		return rescued

	def callback(hwnd, lparam):
		if get_window_pid(hwnd) not in pids:
			return True
		owner = user32.GetWindowLongPtrW(hwnd, GWLP_HWNDPARENT)
		if owner and not user32.IsWindow(owner):
			user32.SetWindowLongPtrW(hwnd, GWLP_HWNDPARENT, 0)
			user32.ShowWindow(hwnd, SW_SHOWNA)
			rescued.append(hwnd)
		return True

	user32.EnumWindows(WNDENUMPROC(callback), 0)
	return rescued

def find_roblox_windows(pids, min_size):
	found = []
	if not pids:
		return found

	def callback(hwnd, lparam):
		if not user32.IsWindowVisible(hwnd):
			return True
		if user32.GetWindow(hwnd, GW_OWNER):
			return True
		if title_length(hwnd) == 0:
			return True
		if get_window_pid(hwnd) not in pids:
			return True
		if not user32.IsIconic(hwnd):
			x, y, w, h = get_window_rect(hwnd)
			if w < min_size or h < min_size:
				return True
		found.append(hwnd)
		return True

	user32.EnumWindows(WNDENUMPROC(callback), 0)
	forget_exited(pids)
	found.sort(key=lambda hwnd: (process_start_time(get_window_pid(hwnd)), get_window_pid(hwnd)))
	return found

def is_foreground(hwnd):
	return bool(hwnd) and user32.GetForegroundWindow() == hwnd

def focus_window(hwnd, attempts=3, settle=0.1):
	for _ in range(attempts):
		if is_foreground(hwnd):
			return True
		user32.keybd_event(VK_MENU, 0, 0, 0)
		user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
		user32.SetForegroundWindow(hwnd)
		user32.BringWindowToTop(hwnd)
		time.sleep(settle)
	return is_foreground(hwnd)

def window_handle(window):
	window.update_idletasks()
	return user32.GetParent(window.winfo_id()) or window.winfo_id()

def attach(window, owner):
	window.attributes('-topmost', False)
	user32.SetWindowLongPtrW(window_handle(window), GWLP_HWNDPARENT, owner)

def place_above(window, target):
	hwnd = window_handle(window)
	above = user32.GetWindow(target, GW_HWNDPREV)
	if above == hwnd:
		return
	user32.SetWindowPos(hwnd, above or 0, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
