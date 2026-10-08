import time
import threading

from app.settings import MAIN_GAME_OCR, MENU_SCREEN_OCR, RECOVERY, TIMEOUTS
from util.input import Input
from util.win32 import user32
from .actions import ConnectionFailed, detect_screen, run_steps

def client_requirement(low, high):
	if low == high:
		return f"exactly {low} client{'' if low == 1 else 's'}"
	return f"{low} to {high} clients"

def split_step(step):
	events = step.get("events") if step.get("type") == "keys" else None
	if not events or len(events) < 2 or "wait_for" not in events[-1]:
		return step, None
	return dict(step, events=events[:-1]), events[-1]

def format_duration(seconds):
	seconds = int(seconds)
	hours, seconds = divmod(seconds, 3600)
	minutes, seconds = divmod(seconds, 60)
	if hours:
		return f"{hours}h {minutes}m {seconds}s"
	if minutes:
		return f"{minutes}m {seconds}s"
	return f"{seconds}s"

class Macro:
	def __init__(self, log, on_finish):
		self.log = log
		self.on_finish = on_finish
		self.input = Input()
		self.get_clients = None
		self.thread = None
		self.queue = []
		self.runs = {}
		self.started_at = 0.0
		self.played = set()

	@property
	def running(self):
		return self.thread is not None and self.thread.is_alive()

	def start(self, scripts, get_clients, ctx):
		self.input.reset()
		self.queue = []
		self.played = set()
		self.runs = {}
		self.started_at = time.perf_counter()
		self.thread = threading.Thread(target=self.run, args=(scripts, get_clients, ctx), daemon=True)
		self.thread.start()

	def wait_until_done(self, timeout=1.0):
		if self.thread is not None and self.thread is not threading.current_thread():
			self.thread.join(timeout)

	@property
	def stopping(self):
		return self.running and self.input.stopped

	def stop(self):
		if not self.running or self.input.stopped:
			return False
		self.input.stop()
		return True

	def run(self, scripts, get_clients, ctx):
		self.get_clients = get_clients
		ctx.fail_watch = {MAIN_GAME_OCR, MENU_SCREEN_OCR} if "leave" in scripts else set()
		try:
			waiting = None
			while not self.input.stopped:
				clients = [client for client in get_clients() if self.alive(client)]
				if scripts.get("first_client_only"):
					clients = clients[:1]
				keys = {self.key(client) for client in clients}
				self.queue = [client for client in self.queue if self.key(client) in keys]
				self.played &= keys

				low, high = scripts["clients"]
				if not low <= len(clients) <= high:
					if waiting != len(clients):
						self.log(f"{scripts['reposition']} needs {client_requirement(low, high)} ({len(clients)} docked), waiting")
						waiting = len(clients)
					self.input.sleep(1)
					continue
				waiting = None

				stagger_from = scripts.get("stagger_from")
				if "inline" in scripts and stagger_from and len(clients) >= stagger_from:
					self.run_staggered(clients, scripts, ctx)
					continue

				for client in clients:
					if self.input.stopped:
						break
					if not self.alive(client):
						self.log("Window gone, skipping", self.group(client))
						self.dequeue(client)
						continue
					if "inline" in scripts:
						self.take_inline_turn(client, scripts, ctx)
					else:
						self.take_turn(client, scripts, ctx)
		except Exception as error:
			self.log(f"Macro error: {error}")
		finally:
			self.input.release_all()
			self.log_summary()
			self.on_finish(self.input.stopped)

	def take_turn(self, client, scripts, ctx):
		key = self.key(client)

		queued = self.dequeue(client)
		in_game = self.ensure_in_game(client, scripts, ctx, need_join=queued, detect=key not in self.played and not queued)
		self.played.add(key)
		if self.input.stopped:
			return

		if in_game:
			self.log("Playing", self.group(client))
			self.play(client, scripts, ctx)
			if self.input.stopped:
				return
			self.log("Returning to main menu", self.group(client))
			run_steps(self.input, client, scripts["leave"], ctx)
			if self.input.stopped:
				return

		if self.queue:
			other = self.queue.pop(0)
			if self.alive(other) and not self.ensure_in_game(other, scripts, ctx, need_join=True, check=False):
				if self.input.stopped:
					return
				self.queue.append(other)

		self.queue.append(client)

	def take_inline_turn(self, client, scripts, ctx):
		self.played.add(self.key(client))
		if not run_steps(self.input, client, [{"type": "safe_click"}], ctx):
			return

		self.log("Playing", self.group(client))
		self.play(client, scripts, ctx)
		if self.input.stopped:
			return
		self.log(f"Repositioning ({scripts['reposition']})", self.group(client))
		run_steps(self.input, client, scripts["inline"], ctx)

	def group(self, client):
		return client.name

	def run_staggered(self, clients, scripts, ctx):
		self.log(f"Staggering {len(clients)} clients")
		states = [{"client": client, "next": 0, "pending": None, "due": 0.0, "done": False} for client in clients]
		round_number = 0
		while not self.input.stopped and not all(state["done"] for state in states):
			round_number += 1
			for position, state in enumerate(states):
				if self.input.stopped:
					return
				if state["done"] or position >= round_number:
					continue
				if not self.alive(state["client"]):
					self.log("Window gone, skipping", self.group(state["client"]))
					state["done"] = True
					continue
				self.staggered_turn(state, scripts, ctx)

		cooldown = scripts.get("stagger_cooldown") or 0
		if isinstance(cooldown, dict):
			cooldown = cooldown.get(len(clients), 0)
		if cooldown and not self.input.stopped:
			self.log(f"All clients drowned, restarting in {cooldown:g}s")
			self.input.sleep(cooldown)

	def staggered_turn(self, state, scripts, ctx):
		client = state["client"]
		steps = scripts["steps"]

		if state["next"] == 0 and state["pending"] is None:
			self.played.add(self.key(client))
			if not run_steps(self.input, client, [{"type": "safe_click"}], ctx):
				return
			self.log("Playing", self.group(client))

		if state["pending"] is not None:
			if not self.input.sleep(max(0.0, state["due"] - time.perf_counter())):
				return
			confirm = dict(state["pending"], dt=0.0)
			state["pending"] = None
			run_steps(self.input, client, [{"type": "keys", "events": [confirm]}], ctx)
			if self.input.stopped:
				return

		while state["next"] < len(steps):
			step, pending = split_step(steps[state["next"]])
			state["next"] += 1
			run_steps(self.input, client, [step], ctx)
			if self.input.stopped:
				return
			if pending is not None:
				state["pending"] = pending
				state["due"] = time.perf_counter() + pending["dt"]
				return

		self.runs[client.name] = self.runs.get(client.name, 0) + 1
		self.log(f"Repositioning ({scripts['reposition']})", self.group(client))
		run_steps(self.input, client, scripts["inline"], ctx)
		state["done"] = True

	def play(self, client, scripts, ctx):
		if run_steps(self.input, client, scripts["steps"], ctx):
			self.runs[client.name] = self.runs.get(client.name, 0) + 1

	def log_summary(self):
		self.log(f"Ran for {format_duration(time.perf_counter() - self.started_at)}")
		total = sum(self.runs.values())
		self.log(f"Completed {total} run{'' if total == 1 else 's'}")
		for name in sorted(self.runs):
			count = self.runs[name]
			self.log(f"{name}: {count} run{'' if count == 1 else 's'}")

	def check_in_game(self, client, ctx):
		return run_steps(self.input, client, [{"type": "wait_for", "region": MAIN_GAME_OCR, "timeout": "main_game"}], ctx)

	def ensure_in_game(self, client, scripts, ctx, need_join, check=True, detect=False):
		failures = 0
		while not self.input.stopped:
			try:
				if detect:
					detect = False
					screen = detect_screen(self.input, client, ctx, (MAIN_GAME_OCR, MENU_SCREEN_OCR), TIMEOUTS["main_game"])
					if screen is None:
						return False
					if screen == MAIN_GAME_OCR:
						return True
					need_join = True
				if need_join:
					if not self.join(client, scripts, ctx):
						return False
					need_join = False
				if not check:
					return True
				return self.check_in_game(client, ctx)
			except ConnectionFailed:
				failures += 1
				if failures > RECOVERY["retries"]:
					self.log(f"Connection failed {failures} times in a row, skipping turn", self.group(client))
					return False
				self.log(f"Connection failed, recovering ({failures}/{RECOVERY['retries']})", self.group(client))
				if not self.recover(client, scripts, ctx):
					return False
				need_join = True
		return False

	def recover(self, client, scripts, ctx):
		return run_steps(self.input, client, scripts["recovery"], ctx)

	def join(self, client, scripts, ctx):
		self.log("Joining private server", self.group(client))
		return run_steps(self.input, client, scripts["join"], ctx)

	def dequeue(self, client):
		key = self.key(client)
		for i, queued in enumerate(self.queue):
			if self.key(queued) == key:
				del self.queue[i]
				return True
		return False

	def key(self, client):
		return (client.index, client.hwnd)

	def alive(self, client):
		return bool(client.hwnd) and bool(user32.IsWindow(client.hwnd))