import json
import time

from app.settings import ANTI_MACRO, FAIL_DETECTION, REGIONS, MARKERS, TIMEOUTS, KEYBOARD, MOUSE, SAFE_CLICK, FOCUS, OCR
from util import ocr
from util.screen import black_ratio
from util.overlay import to_pixels, point_to_pixels
from util.win32 import get_window_rect

STEP_HANDLERS = {}

MOVE_KEYS = {"w", "a", "s", "d"}
ACTION_KEYS = {"e", "1"}
EXTRA_KEYS = {"space", "esc", "r", "enter"}
PRESS_KEYS = ACTION_KEYS | EXTRA_KEYS
TIMELINE_KEYS = MOVE_KEYS | ACTION_KEYS | EXTRA_KEYS

class ConnectionFailed(Exception):
	pass

class StepContext:
	def __init__(self, log, markers, regions, ocr_texts, server_code):
		self.log = log
		self.markers = markers
		self.regions = regions
		self.ocr_texts = ocr_texts
		self.server_code = server_code
		self.fail_watch = set()

def step(name):
	def register(fn):
		STEP_HANDLERS[name] = fn
		return fn
	return register

PRESS_TOGETHER = 0.02

def note(ctx, client, text):
	ctx.log(text, client.name)

def key_name(key):
	if key == "space":
		return "Space"
	if key == "enter":
		return "Enter"
	if key == "esc":
		return "Esc"
	return key.upper()

def join_names(names):
	if len(names) == 1:
		return names[0]
	return ", ".join(names[:-1]) + " and " + names[-1]

def seconds(value):
	return f"{round(value, 1):g}s"

def load_steps(path):
	with open(path, "r") as f:
		steps = json.load(f)
	if not isinstance(steps, list):
		raise ValueError(f"{path} must be a list of steps")
	return steps

def load_rejoin(path):
	with open(path, "r") as f:
		data = json.load(f)
	if not isinstance(data, dict):
		raise ValueError(f"{path} must have \"leave\" and \"join\" lists")
	for part in ("leave", "join"):
		if not isinstance(data.get(part), list):
			raise ValueError(f"{path} needs a \"{part}\" list")
	return data["leave"], data["join"]

def ensure_focus(player, client, ctx):
	if player.stopped:
		return False
	if client.is_focused():
		return True
	if client.focus():
		return player.sleep(FOCUS["settle"])
	note(ctx, client, "Couldn't focus window")
	return False

def timeout_error(value):
	if value is None or isinstance(value, (int, float)):
		return None
	if value not in TIMEOUTS:
		return f"has an unknown timeout '{value}'"
	return None

def resolve_timeout(value):
	if value is None:
		return TIMEOUTS["default"]
	if isinstance(value, str):
		return TIMEOUTS[value]
	return value

def region_label(region):
	return REGIONS.get(region, {}).get("label", region)

def marker_label(marker):
	return MARKERS.get(marker, {}).get("label", marker)

def region_shows(client, ctx, region, text=None):
	box = ctx.regions.get(region)
	target = text or ctx.ocr_texts.get(region)
	if box is None or not target:
		return False, ""
	x1, y1, x2, y2 = to_pixels(box, get_window_rect(client.hwnd))
	read = ocr.read(x1, y1, x2, y2)
	mode = REGIONS.get(region, {}).get("match", "contains")
	return ocr.matches(target, read, mode=mode), read

def on_anti_macro_screen(client):
	return black_ratio(*get_window_rect(client.hwnd)) >= ANTI_MACRO["black_threshold"]

def clear_anti_macro(player, client, ctx):
	if player.stopped:
		return False
	if not on_anti_macro_screen(client):
		return True
	note(ctx, client, "Anti-macro screen detected")
	taps = 0
	while not player.stopped:
		if not on_anti_macro_screen(client):
			note(ctx, client, "Anti-macro screen cleared")
			if taps and ANTI_MACRO.get("reequip_key"):
				if not ensure_focus(player, client, ctx):
					return False
				note(ctx, client, f"Press {key_name(ANTI_MACRO['reequip_key'])} to re-equip")
				return player.tap_key(ANTI_MACRO["reequip_key"], hold=KEYBOARD["press_hold"])
			return True
		if not ensure_focus(player, client, ctx):
			return False
		player.tap_key(ANTI_MACRO["key"], hold=KEYBOARD["press_hold"])
		taps += 1
		player.sleep(ANTI_MACRO["spam_delay"])
	return False

def wait_for_text(player, client, ctx, region, text, timeout):
	note(ctx, client, f"Waiting for {region_label(region)} ({seconds(timeout)})")
	watch_fail = region in ctx.fail_watch
	start = time.perf_counter()
	deadline = start + timeout
	while not player.stopped:
		if not clear_anti_macro(player, client, ctx):
			return False
		found, read = region_shows(client, ctx, region, text)
		if found:
			note(ctx, client, f"Found {region_label(region)} ({seconds(time.perf_counter() - start)}, read \"{read.strip()}\")")
			if REGIONS.get(region, {}).get("safe_click"):
				return safe_click(player, client, ctx)
			return True
		if watch_fail:
			failed, read = region_shows(client, ctx, FAIL_DETECTION)
			if failed:
				note(ctx, client, f"Found {region_label(FAIL_DETECTION)} (read \"{read.strip()}\")")
				raise ConnectionFailed()
		if time.perf_counter() >= deadline:
			return False
		player.sleep(OCR["read_interval"])
	return False

def release_stuck(player, client, ctx):
	for name in player.release_stuck_buttons():
		note(ctx, client, f"Released stuck {name} mouse button")

def safe_click(player, client, ctx):
	release_stuck(player, client, ctx)
	x, y = point_to_pixels(SAFE_CLICK, get_window_rect(client.hwnd))
	return player.safe_double_click(x, y, SAFE_CLICK["glide"], SAFE_CLICK["hold"], SAFE_CLICK["gap"])

def detect_screen(player, client, ctx, regions, timeout):
	names = " or ".join(region_label(region) for region in regions)
	note(ctx, client, f"Detecting {names} ({seconds(timeout)})")
	if not ensure_focus(player, client, ctx):
		return None
	start = time.perf_counter()
	deadline = start + timeout
	while not player.stopped:
		if not clear_anti_macro(player, client, ctx):
			return None
		for region in regions:
			found, read = region_shows(client, ctx, region)
			if found:
				note(ctx, client, f"Found {region_label(region)} ({seconds(time.perf_counter() - start)}, read \"{read.strip()}\")")
				if REGIONS.get(region, {}).get("safe_click") and not safe_click(player, client, ctx):
					return None
				return region
		if ctx.fail_watch:
			failed, read = region_shows(client, ctx, FAIL_DETECTION)
			if failed:
				note(ctx, client, f"Found {region_label(FAIL_DETECTION)} (read \"{read.strip()}\")")
				raise ConnectionFailed()
		if time.perf_counter() >= deadline:
			note(ctx, client, f"{names} not found after {seconds(timeout)}, skipping")
			return None
		player.sleep(OCR["read_interval"])
	return None

@step("walk")
def handle_walk(player, client, step_data, ctx):
	keys = step_data.get("keys", "")
	if not keys or any(key not in MOVE_KEYS for key in keys):
		note(ctx, client, f"Skipped walk step: invalid keys '{keys}'")
		return
	if not ensure_focus(player, client, ctx):
		return False
	duration = step_data.get("duration", 0)
	note(ctx, client, f"Walk {join_names([key_name(key) for key in keys])} for {seconds(duration)}")
	return player.hold_keys(list(keys), duration)

@step("press")
def handle_press(player, client, step_data, ctx):
	key = step_data.get("key", "")
	if key not in PRESS_KEYS:
		note(ctx, client, f"Skipped press step: invalid key '{key}'")
		return
	if not ensure_focus(player, client, ctx):
		return False
	note(ctx, client, f"Press {key_name(key)}")
	return player.tap_key(key, hold=KEYBOARD["press_hold"])

def event_error(event, ctx):
	if "wait_for" in event:
		region = event["wait_for"]
		if region not in ctx.regions:
			return f"has an unknown region '{region}'"
		if not (event.get("text") or ctx.ocr_texts.get(region)):
			return f"has no OCR text for {region_label(region)}"
		return timeout_error(event.get("timeout"))
	if "key" in event:
		if event["key"] not in TIMELINE_KEYS:
			return f"uses key '{event['key']}', which isn't allowed"
		return None
	return "has no key or wait_for"

@step("keys")
def handle_keys(player, client, step_data, ctx):
	events = step_data.get("events", [])
	for i, event in enumerate(events, 1):
		error = event_error(event, ctx)
		if error:
			note(ctx, client, f"Skipped keys step: event {i} {error}")
			return
	if not ensure_focus(player, client, ctx):
		return False

	downs = {}
	merged = set()

	def log_held(keys, start, end):
		note(ctx, client, f"Held {join_names([key_name(key) for key in keys])} for {seconds(end - start)}")

	def on_key(key, down, index):
		now = time.perf_counter()
		if down:
			downs[key] = now
			return
		start = downs.pop(key, now)
		if key in merged:
			merged.discard(key)
			return
		together = [key]
		for event in events[index + 1:]:
			if "key" not in event or event["down"] or event["dt"] != 0:
				break
			other = event["key"]
			if other in downs and abs(downs[other] - start) <= PRESS_TOGETHER:
				together.append(other)
				merged.add(other)
		log_held(together, start, now)

	def on_action(event):
		if "wait_for" in event:
			region = event["wait_for"]
			timeout = resolve_timeout(event.get("timeout"))
			text = event.get("text") or ctx.ocr_texts.get(region)
			if not wait_for_text(player, client, ctx, region, text, timeout) and not player.stopped:
				note(ctx, client, f"{region_label(region)} not found, continuing")

	result = player.play_keys(events, on_action, on_key)
	if downs:
		now = time.perf_counter()
		groups = {}
		for key, start in downs.items():
			groups.setdefault(round(start / PRESS_TOGETHER), (start, []))[1].append(key)
		for start, keys in groups.values():
			log_held(keys, start, now)
	return result

@step("click")
def handle_click(player, client, step_data, ctx):
	rect = get_window_rect(client.hwnd)
	marker = step_data.get("marker")
	if marker is not None:
		point = ctx.markers.get(marker)
		if point is None:
			note(ctx, client, f"Skipped click: unknown marker '{marker}'")
			return
		x, y = point_to_pixels(point, rect)
		target = marker_label(marker)
	elif "x" in step_data and "y" in step_data:
		x, y = player.ratio_to_screen(step_data["x"], step_data["y"], rect)
		if step_data["x"] == 0.5 and step_data["y"] == 0.5:
			target = "centre"
		else:
			target = f"{step_data['x']:g}, {step_data['y']:g}"
	else:
		note(ctx, client, "Skipped click: needs a marker or x and y")
		return
	note(ctx, client, f"Click {target}")
	release_stuck(player, client, ctx)
	player.click_at(x, y, hold=MOUSE["click_hold"], duration=MOUSE["click_glide"])

@step("safe_click")
def handle_safe_click(player, client, step_data, ctx):
	return safe_click(player, client, ctx)

@step("wait")
def handle_wait(player, client, step_data, ctx):
	duration = step_data.get("duration", 0)
	note(ctx, client, f"Wait {seconds(duration)}")
	player.sleep(duration)

@step("type_code")
def handle_type_code(player, client, step_data, ctx):
	code = ctx.server_code
	if not code.isalnum():
		note(ctx, client, "Server code must be letters and numbers only")
		return False
	if not ensure_focus(player, client, ctx):
		return False
	note(ctx, client, "Typing server code")
	if not player.type_text(code, hold=KEYBOARD["type_code_hold"], gap=KEYBOARD["type_code_gap"]):
		return False
	note(ctx, client, "Press Enter")
	return player.tap_key("enter", hold=KEYBOARD["press_hold"])

@step("wait_for")
def handle_wait_for(player, client, step_data, ctx):
	region = step_data.get("region")
	text = step_data.get("text") or ctx.ocr_texts.get(region)
	if region not in ctx.regions:
		note(ctx, client, f"Skipped wait: unknown region '{region}'")
		return False
	if not text:
		note(ctx, client, f"No OCR text set for {region_label(region)}")
		return False

	if timeout_error(step_data.get("timeout")):
		note(ctx, client, f"Skipped wait: unknown timeout '{step_data.get('timeout')}'")
		return False
	timeout = resolve_timeout(step_data.get("timeout"))
	if wait_for_text(player, client, ctx, region, text, timeout):
		return True
	if not player.stopped:
		note(ctx, client, f"{region_label(region)} not found after {seconds(timeout)}, skipping")
	return False

def run_steps(player, client, steps, ctx):
	if not ensure_focus(player, client, ctx):
		return False

	for step_data in steps:
		if player.stopped:
			return False

		if not clear_anti_macro(player, client, ctx):
			return False

		if step_data.get("name"):
			note(ctx, client, step_data["name"])

		handler = STEP_HANDLERS.get(step_data.get("type"))
		if handler is None:
			note(ctx, client, f"Skipped unknown step type '{step_data.get('type')}'")
			continue

		if handler(player, client, step_data, ctx) is False:
			return False

	return not player.stopped