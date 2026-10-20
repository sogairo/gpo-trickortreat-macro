import time

from app.settings import ANTI_MACRO, DISCONNECT, REGIONS, KEYBOARD, SAFE_CLICK, FOCUS, OCR
from util.automation import ocr
from util.automation.screen import black_ratio
from util.overlay.coords import to_pixels, point_to_pixels
from util.win32.window import get_window_rect

class ConnectionFailed(Exception):
	def __init__(self, button):
		super().__init__(button)
		self.button = button

class StepContext:
	def __init__(self, log, markers, regions, ocr_texts, server_code):
		self.log = log
		self.markers = markers
		self.regions = regions
		self.ocr_texts = ocr_texts
		self.server_code = server_code
		self.fail_watch = False

def client_note(ctx, client, text):
	ctx.log(text, client.name)

def seconds(value):
	return f"{round(value, 1):g}s"

def ensure_focus(player, client, ctx):
	if player.halted:
		return False
	if client.is_focused():
		return True
	if client.focus():
		return player.sleep(FOCUS["settle"])
	client_note(ctx, client, "Couldn't focus the window")
	return False

def region_label(region):
	return REGIONS.get(region, {}).get("label", region)

def region_shows(client, ctx, region, text=None):
	box = ctx.regions.get(region)
	target = text or ctx.ocr_texts.get(region)
	if box is None or not target:
		return False, ""
	x1, y1, x2, y2 = to_pixels(box, get_window_rect(client.hwnd))
	read = ocr.read(x1, y1, x2, y2)
	mode = REGIONS.get(region, {}).get("match", "contains")
	return ocr.matches(target, read, mode=mode), read

def area_box(area, client):
	return to_pixels(dict(zip(("x1", "y1", "x2", "y2"), area)), get_window_rect(client.hwnd))

def disconnect_button(client, ctx):
	read = ocr.read(*area_box(DISCONNECT["area"], client))
	for title, button in DISCONNECT["prompts"].items():
		if ocr.matches(title, read):
			client_note(ctx, client, f"Saw the {title.title()} prompt")
			return button
	return None

def on_anti_macro_screen(client):
	return black_ratio(*get_window_rect(client.hwnd)) >= ANTI_MACRO["black_threshold"]

def clear_anti_macro(player, client, ctx):
	if player.halted:
		return False
	if not on_anti_macro_screen(client):
		return True
	client_note(ctx, client, "Hit the anti-macro screen, clearing it")
	taps = 0
	while not player.halted:
		if not on_anti_macro_screen(client):
			if taps and ANTI_MACRO.get("reequip_key"):
				if not ensure_focus(player, client, ctx):
					return False
				if not player.tap_key(ANTI_MACRO["reequip_key"], hold=KEYBOARD["press_hold"]):
					return False
				client_note(ctx, client, f"Cleared the anti-macro screen, re-equipped slot {ANTI_MACRO['reequip_key']}")
				return True
			client_note(ctx, client, "Cleared the anti-macro screen")
			return True
		if not ensure_focus(player, client, ctx):
			return False
		player.tap_key(ANTI_MACRO["key"], hold=KEYBOARD["press_hold"])
		taps += 1
		player.sleep(ANTI_MACRO["spam_delay"])
	return False

def wait_for_text(player, client, ctx, region, text, timeout):
	watch_fail = ctx.fail_watch
	deadline = time.perf_counter() + timeout
	read = ""
	while not player.halted:
		if not clear_anti_macro(player, client, ctx):
			return False, read
		found, read = region_shows(client, ctx, region, text)
		if found:
			return True, read
		if watch_fail:
			button = disconnect_button(client, ctx)
			if button:
				raise ConnectionFailed(button)
		if time.perf_counter() >= deadline:
			return False, read
		player.sleep(OCR["read_interval"])
	return False, read

def release_stuck(player, client, ctx):
	for name in player.release_stuck_buttons():
		client_note(ctx, client, f"Released stuck {name} mouse button")

def click_safe_spot(player, client, ctx):
	release_stuck(player, client, ctx)
	x, y = point_to_pixels(SAFE_CLICK, get_window_rect(client.hwnd))
	return player.safe_double_click(x, y, SAFE_CLICK["glide"], SAFE_CLICK["hold"], SAFE_CLICK["gap"])

def detect_screen(player, client, ctx, regions, timeout):
	names = " or ".join(region_label(region) for region in regions)
	if not ensure_focus(player, client, ctx):
		return None
	start = time.perf_counter()
	deadline = start + timeout
	while not player.halted:
		if not clear_anti_macro(player, client, ctx):
			return None
		for region in regions:
			found, read = region_shows(client, ctx, region)
			if found:
				return region
		if ctx.fail_watch:
			button = disconnect_button(client, ctx)
			if button:
				raise ConnectionFailed(button)
		if time.perf_counter() >= deadline:
			client_note(ctx, client, f"Couldn't find {names} after {seconds(timeout)}")
			return None
		player.sleep(OCR["read_interval"])
	return None
