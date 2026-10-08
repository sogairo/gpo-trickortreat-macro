import ctypes
from ctypes import wintypes

from .api import kernel32, PROCESSENTRY32W
from .constants import TH32CS_SNAPPROCESS, INVALID_HANDLE_VALUE, PROCESS_QUERY_LIMITED_INFORMATION

_start_times = {}

def get_roblox_pids(exe_name):
	pids = set()
	snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
	if snap in (None, INVALID_HANDLE_VALUE):
		return pids
	entry = PROCESSENTRY32W()
	entry.dwSize = ctypes.sizeof(entry)
	try:
		ok = kernel32.Process32FirstW(snap, ctypes.byref(entry))
		while ok:
			if entry.szExeFile.lower() == exe_name:
				pids.add(entry.th32ProcessID)
			ok = kernel32.Process32NextW(snap, ctypes.byref(entry))
	finally:
		kernel32.CloseHandle(snap)
	return pids

def forget_exited(pids):
	for pid in list(_start_times):
		if pid not in pids:
			del _start_times[pid]

def process_start_time(pid):
	if pid in _start_times:
		return _start_times[pid]
	handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
	if not handle:
		return float("inf")
	try:
		created = wintypes.FILETIME()
		unused = wintypes.FILETIME()
		if not kernel32.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(unused), ctypes.byref(unused), ctypes.byref(unused)):
			return float("inf")
		value = (created.dwHighDateTime << 32) | created.dwLowDateTime
	finally:
		kernel32.CloseHandle(handle)
	_start_times[pid] = value
	return value