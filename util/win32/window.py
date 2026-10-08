import time
import ctypes
from ctypes import wintypes

from .api import user32, MONITORINFO, WNDENUMPROC
from .process import process_start_time, forget_exited
from .constants import GW_OWNER, MONITOR_DEFAULTTONEAREST, VK_MENU, KEYEVENTF_KEYUP, WM_GETTEXTLENGTH, SMTO_ABORTIFHUNG

TITLE_TIMEOUT_MS = 200

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