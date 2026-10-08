import time
import ctypes
from ctypes import wintypes

import pydirectinput

from util.win32 import user32
from util.win32.constants import MOUSEEVENTF_MOVE

pydirectinput.FAILSAFE = False
pydirectinput.PAUSE = 0

winmm = ctypes.WinDLL("winmm")

SLEEP_CHUNK = 0.02
MOUSE_BUTTONS = (("left", 0x01), ("right", 0x02))

class Input:
	def __init__(self):
		self.stopped = False
		self.held_keys = set()
		self.mouse_down = False
		self.tween_duration = 0.15
		self.tween_steps = 30

	def reset(self):
		self.stopped = False

	def sleep(self, seconds):
		deadline = time.perf_counter() + seconds
		while not self.stopped:
			remaining = deadline - time.perf_counter()
			if remaining <= 0:
				return True
			time.sleep(min(remaining, SLEEP_CHUNK))
		return False

	def wait_until(self, target):
		while not self.stopped:
			remaining = target - time.perf_counter()
			if remaining <= 0:
				return True
			time.sleep(min(remaining, SLEEP_CHUNK))
		return False

	def play_keys(self, events, on_action=None, on_key=None):
		held = set()
		winmm.timeBeginPeriod(1)
		try:
			clock = time.perf_counter()
			for index, event in enumerate(events):
				clock += event["dt"]
				if not self.wait_until(clock):
					return False
				if "key" not in event:
					if on_action:
						on_action(event)
					if self.stopped:
						return False
					clock = time.perf_counter()
					continue
				key = event["key"]
				if event["down"]:
					if not self.key_down(key):
						return False
					held.add(key)
				else:
					self.key_up(key)
					held.discard(key)
				if on_key:
					on_key(key, event["down"], index)
			return True
		finally:
			for key in held:
				self.key_up(key)
			winmm.timeEndPeriod(1)

	def key_down(self, key):
		if self.stopped:
			return False
		pydirectinput.keyDown(key)
		self.held_keys.add(key)
		return True

	def key_up(self, key):
		pydirectinput.keyUp(key)
		self.held_keys.discard(key)

	def tap_key(self, key, hold=0.05):
		if not self.key_down(key):
			return False
		try:
			self.sleep(hold)
		finally:
			self.key_up(key)
		return not self.stopped

	def hold_keys(self, keys, duration):
		if self.stopped:
			return False
		for key in keys:
			self.key_down(key)
		try:
			return self.sleep(duration)
		finally:
			for key in keys:
				self.key_up(key)

	def type_text(self, text, hold=0.03, gap=0.03):
		for char in text:
			if self.stopped:
				return False
			if char.isupper():
				self.key_down("shift")
				try:
					self.tap_key(char.lower(), hold=hold)
				finally:
					self.key_up("shift")
			else:
				self.tap_key(char, hold=hold)
			time.sleep(gap)
		return True

	def ratio_to_screen(self, x_ratio, y_ratio, rect):
		x, y, w, h = rect
		return round(x + x_ratio * w), round(y + y_ratio * h)

	def tween_to(self, x, y, duration):
		pt = wintypes.POINT()
		user32.GetCursorPos(ctypes.byref(pt))
		sx, sy = pt.x, pt.y

		if sx == x and sy == y:
			return

		prev_x, prev_y = sx, sy

		for i in range(1, self.tween_steps + 1):
			if self.stopped:
				return

			t = i / self.tween_steps
			ease = t * t * (3 - 2 * t)
			ix = sx + (x - sx) * ease
			iy = sy + (y - sy) * ease

			dx = int(round(ix - prev_x))
			dy = int(round(iy - prev_y))
			if dx or dy:
				user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)
				prev_x += dx
				prev_y += dy

			time.sleep(duration / self.tween_steps)

		pydirectinput.moveTo(x, y)

	def click_at(self, x, y, hold=0.07, duration=None):
		winmm.timeBeginPeriod(1)
		try:
			self.tween_to(x, y, duration if duration is not None else self.tween_duration)
			if self.stopped:
				return
			pydirectinput.mouseDown(button="left")
			self.mouse_down = True
			time.sleep(hold)
			pydirectinput.mouseUp(button="left")
			self.mouse_down = False
		finally:
			winmm.timeEndPeriod(1)

	def release_stuck_buttons(self):
		released = []
		for name, vk in MOUSE_BUTTONS:
			if user32.GetAsyncKeyState(vk) & 0x8000:
				pydirectinput.mouseUp(button=name)
				released.append(name)
		return released

	def cursor(self):
		point = wintypes.POINT()
		user32.GetCursorPos(ctypes.byref(point))
		return point.x, point.y

	def safe_double_click(self, x, y, glide, hold, gap):
		if self.stopped:
			return False
		winmm.timeBeginPeriod(1)
		try:
			self.tween_to(x, y, glide)
			for click in range(2):
				if self.stopped:
					return False
				pydirectinput.mouseDown(button="left")
				self.mouse_down = True
				time.sleep(hold)
				pydirectinput.mouseUp(button="left")
				self.mouse_down = False
				if click == 0:
					time.sleep(gap)
			return not self.stopped
		finally:
			winmm.timeEndPeriod(1)

	def release_all(self):
		for key in list(self.held_keys):
			try:
				pydirectinput.keyUp(key)
			except Exception:
				pass
		self.held_keys.clear()

		if self.mouse_down:
			try:
				pydirectinput.mouseUp(button="left")
			except Exception:
				pass
			self.mouse_down = False

	def stop(self):
		self.stopped = True
		self.release_all()