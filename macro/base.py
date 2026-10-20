import time
import threading

from app.settings import KEYBOARD, MOUSE, TIMEOUTS, CHECK_SETTINGS, DISCONNECT, SAFE_CLICK, REJOIN
from util.automation import ocr
from util.automation.screen import green_red_ratios
from util.overlay.coords import to_pixels, point_to_pixels
from util.win32.window import get_window_rect
from .helpers import client_note, seconds, region_label, ensure_focus, clear_anti_macro, wait_for_text, detect_screen, region_shows, release_stuck, click_safe_spot, area_box, disconnect_button, ConnectionFailed

class Aborted(Exception):
	pass

def read_text(read):
	read = read.strip()
	return f" (read \"{read}\")" if read else " (read nothing)"

def parse_walk(move):
	keys, duration = move.split()
	return keys.split("+"), float(duration)

class MacroBase:
	def sequence(self, action, client, *args):
		try:
			self.focus(client)
			result = action(client, *args)
		except Aborted:
			return False
		return result is not False and not self.input.halted

	def watched(self, client, action, *args):
		found = []
		done = threading.Event()

		def watch():
			while not done.wait(DISCONNECT["watch_interval"]):
				try:
					button = disconnect_button(client, self.ctx)
				except Exception as error:
					self.note(client, f"Disconnect check error: {error}")
					return
				if button:
					found.append(button)
					self.input.interrupt()
					return

		fail_watch = self.ctx.fail_watch
		self.ctx.fail_watch = False
		thread = threading.Thread(target=watch, daemon=True)
		thread.start()
		try:
			result = self.sequence(action, client, *args)
		finally:
			done.set()
			thread.join()
			self.ctx.fail_watch = fail_watch
			self.input.resume()
		if found:
			raise ConnectionFailed(found[0])
		return result

	def note(self, client, text):
		client_note(self.ctx, client, text)

	def step(self, client):
		if self.input.halted or not clear_anti_macro(self.input, client, self.ctx):
			raise Aborted()

	def focus(self, client):
		self.step(client)
		if not ensure_focus(self.input, client, self.ctx):
			raise Aborted()

	def sleep(self, duration):
		if not self.input.sleep(duration):
			raise Aborted()

	def press(self, client, key, hold=None):
		self.focus(client)
		if not self.input.tap_key(key, hold=KEYBOARD["press_hold"] if hold is None else hold):
			raise Aborted()

	def walk(self, client, move):
		keys, duration = parse_walk(move)
		self.focus(client)
		if not self.input.hold_keys(keys, duration):
			raise Aborted()

	def click(self, client, key):
		self.step(client)
		rect = get_window_rect(client.hwnd)
		if key in self.ctx.regions:
			x1, y1, x2, y2 = to_pixels(self.ctx.regions[key], rect)
			x, y = (x1 + x2) // 2, (y1 + y2) // 2
		else:
			x, y = point_to_pixels(self.ctx.markers[key], rect)
		release_stuck(self.input, client, self.ctx)
		self.input.click_at(x, y, hold=MOUSE["click_hold"], duration=MOUSE["click_glide"])
		if self.input.halted:
			raise Aborted()

	def is_green(self, client, region):
		self.step(client)
		box = to_pixels(self.ctx.regions[region], get_window_rect(client.hwnd))
		green, red = green_red_ratios(*box, CHECK_SETTINGS["min_brightness"], CHECK_SETTINGS["dominance"])
		return green > red and green >= CHECK_SETTINGS["min_green"]

	def click_text(self, client, area, text):
		self.step(client)
		for read, x, y in ocr.locate(*area_box(area, client)):
			if ocr.matches(text, read):
				self.note(client, f"Click {text.title()}")
				release_stuck(self.input, client, self.ctx)
				self.input.click_at(x, y, hold=MOUSE["click_hold"], duration=MOUSE["click_glide"])
				if self.input.halted:
					raise Aborted()
				return True
		self.note(client, f"Couldn't find {text.title()} on the prompt")
		return False

	def safe_click(self, client):
		self.step(client)
		if not click_safe_spot(self.input, client, self.ctx):
			raise Aborted()

	def wait_for(self, client, region, timeout, where=""):
		self.step(client)
		timeout = TIMEOUTS[timeout]
		found, read = wait_for_text(self.input, client, self.ctx, region, self.ctx.ocr_texts[region], timeout)
		if found:
			return True
		if self.input.halted:
			raise Aborted()
		self.note(client, f"Couldn't find {region_label(region)}{where} after {seconds(timeout)}{read_text(read)}")
		return False

	def click_until(self, client, region, timeout):
		timeout = TIMEOUTS[timeout]
		start = time.perf_counter()
		while True:
			self.step(client)
			release_stuck(self.input, client, self.ctx)
			x, y = point_to_pixels(SAFE_CLICK, get_window_rect(client.hwnd))
			self.input.click_at(x, y, hold=SAFE_CLICK["hold"], duration=SAFE_CLICK["glide"])
			if self.input.halted:
				raise Aborted()
			found, read = region_shows(client, self.ctx, region)
			if found:
				return True
			if self.ctx.fail_watch:
				button = disconnect_button(client, self.ctx)
				if button:
					raise ConnectionFailed(button)
			if time.perf_counter() - start >= timeout:
				self.note(client, f"Couldn't find {region_label(region)} after {seconds(timeout)}{read_text(read)}")
				return False
			self.sleep(REJOIN["spam_gap"])

	def detect(self, client, regions, timeout):
		self.step(client)
		screen = detect_screen(self.input, client, self.ctx, regions, TIMEOUTS[timeout])
		if screen is None and self.input.halted:
			raise Aborted()
		return screen

	def type_code(self, client):
		code = self.ctx.server_code
		if not code.isalnum():
			self.note(client, "Couldn't type the server code, it must be letters and numbers only")
			return False
		self.focus(client)
		if not self.input.type_text(code, KEYBOARD["type_hold"], KEYBOARD["type_gap"], KEYBOARD["word_pause"]):
			raise Aborted()
		self.press(client, "enter")
		return True
