import time
import threading
import traceback

from app.settings import MAIN_GAME_OCR, MENU_SCREEN_OCR, PRIVATE_SERVERS, RECOVERY, TIMEOUTS, HOUSES, KNOCK
from util.automation.input import Input
from util.win32.api import user32
from .helpers import ConnectionFailed, detect_screen, disconnect_button
from .base import MacroBase
from .phases.route import RoutePhase
from .phases.drowning import DrowningPhase
from .phases.rejoin import RejoinPhase
from .phases.options import OptionsPhase

def client_requirement(low, high):
	if low == high:
		return f"exactly {low} client{'' if low == 1 else 's'}"
	return f"{low} to {high} clients"

def runs_text(runs):
	houses = runs * len(HOUSES)
	return f"{runs} run{'' if runs == 1 else 's'}, knocked {houses} house{'' if houses == 1 else 's'}"

def format_duration(seconds):
	seconds = int(seconds)
	hours, seconds = divmod(seconds, 3600)
	minutes, seconds = divmod(seconds, 60)
	if hours:
		return f"{hours}h {minutes}m {seconds}s"
	if minutes:
		return f"{minutes}m {seconds}s"
	return f"{seconds}s"

class Macro(RoutePhase, DrowningPhase, RejoinPhase, OptionsPhase, MacroBase):
	def __init__(self, log, on_finish):
		self.log = log
		self.on_finish = on_finish
		self.input = Input()
		self.ctx = None
		self.scripts = None
		self.checked = set()
		self.get_clients = None
		self.thread = None
		self.queue = []
		self.runs = {}
		self.started_at = 0.0
		self.played = set()
		self.disconnected = {}
		self.dropped = set()

	@property
	def running(self):
		return self.thread is not None and self.thread.is_alive()

	def start(self, scripts, get_clients, ctx):
		self.input.reset()
		self.queue = []
		self.played = set()
		self.checked = set()
		self.disconnected = {}
		self.dropped = set()
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
		self.ctx = ctx
		self.scripts = scripts
		ctx.fail_watch = True
		try:
			waiting = None
			while not self.input.stopped:
				clients = [client for client in get_clients() if self.alive(client) and self.key(client) not in self.dropped]
				if scripts.get("first_client_only"):
					clients = clients[:1]
				keys = {self.key(client) for client in clients}
				self.queue = [client for client in self.queue if self.key(client) in keys]
				self.played &= keys
				self.disconnected = {key: state for key, state in self.disconnected.items() if key in keys}

				low, high = scripts["clients"]
				if not low <= len(clients) <= high:
					if waiting != len(clients):
						self.log(f"{scripts['reposition']} needs {client_requirement(low, high)} ({len(clients)} docked), waiting")
						waiting = len(clients)
					self.input.sleep(1)
					continue
				waiting = None

				stagger_from = scripts.get("stagger_from")
				if not scripts["rejoin"] and stagger_from and len(clients) >= stagger_from:
					self.run_staggered(clients, scripts)
					continue

				for client in clients:
					if self.input.stopped:
						break
					if not self.alive(client):
						self.log("Skipped, the window closed", self.group(client))
						self.dequeue(client)
						continue
					if scripts["rejoin"]:
						self.take_turn(client)
					else:
						self.take_inline_turn(client, scripts)
				if not scripts["rejoin"]:
					self.recover_disconnected()
		except Exception as error:
			traceback.print_exc()
			self.log(f"Macro error: {error}")
		finally:
			self.input.release_all()
			self.log_summary()
			self.on_finish(self.input.stopped)

	def take_turn(self, client):
		key = self.key(client)

		queued = self.dequeue(client)
		in_game = self.ensure_in_game(client, need_join=queued, detect=key not in self.played and not queued)
		self.played.add(key)
		if self.input.stopped:
			return

		if in_game:
			self.check_once(client)
			if self.input.stopped or not self.sequence(self.safe_click, client):
				return
			try:
				self.play(client)
			except ConnectionFailed as error:
				self.log("Disconnected during the route, recovering", self.group(client))
				if not self.sequence(self.recover, client, error.button) and not self.input.stopped:
					self.log("Couldn't recover, retrying when it rejoins", self.group(client))
				self.queue.append(client)
				return
			if self.input.stopped:
				return
			if self.sequence(self.leave, client):
				self.log("Left to the main menu", self.group(client))
			if self.input.stopped:
				return

		if self.queue:
			other = self.queue.pop(0)
			if self.alive(other) and not self.ensure_in_game(other, need_join=True, check=False):
				if self.input.stopped:
					return
				self.queue.append(other)

		self.queue.append(client)

	def take_inline_turn(self, client, scripts):
		if self.sits_out(client):
			return
		self.played.add(self.key(client))
		self.check_once(client)
		if self.input.stopped or not self.sequence(self.safe_click, client):
			return

		try:
			self.play(client)
			if self.input.stopped:
				return
			if self.watched(client, self.drown):
				self.log("Drowned to reposition", self.group(client))
		except ConnectionFailed as error:
			self.mark_disconnected(client, error.button)

	def sits_out(self, client):
		if self.key(client) in self.disconnected:
			return True
		button = disconnect_button(client, self.ctx)
		if button:
			self.mark_disconnected(client, button)
			return True
		return False

	def mark_disconnected(self, client, button):
		key = self.key(client)
		if key in self.disconnected:
			self.disconnected[key]["button"] = button
			return
		self.disconnected[key] = {"client": client, "button": button, "attempts": 0}
		self.log("Disconnected, sitting out until the other clients finish", self.group(client))

	def recover_disconnected(self):
		for key, state in list(self.disconnected.items()):
			if self.input.stopped:
				return
			client = state["client"]
			if not self.alive(client):
				del self.disconnected[key]
				continue
			state["attempts"] += 1
			self.log(f"Recovering ({state['attempts']}/{RECOVERY['retries']})", self.group(client))
			try:
				recovered = self.sequence(self.recover, client, state["button"]) and self.check_in_game(client)
			except ConnectionFailed as error:
				state["button"] = error.button
				recovered = False
			if self.input.stopped:
				return
			if recovered:
				del self.disconnected[key]
				self.log("Recovered, back in the rotation", self.group(client))
			elif state["attempts"] >= RECOVERY["retries"]:
				del self.disconnected[key]
				self.dropped.add(key)
				self.log(f"Gave up recovering after {state['attempts']} tries, dropped it from this run", self.group(client))

	def check_once(self, client):
		key = self.key(client)
		if not self.scripts["check_settings"] or key in self.checked:
			return
		self.checked.add(key)
		self.sequence(self.check_settings, client)

	def group(self, client):
		return client.name

	def run_staggered(self, clients, scripts):
		self.log(f"Staggering {len(clients)} clients")
		states = [{"client": client, "next": 0, "pending": False, "due": 0.0, "done": False} for client in clients]
		round_number = 0
		while not self.input.stopped and not all(state["done"] for state in states):
			round_number += 1
			for position, state in enumerate(states):
				if self.input.stopped:
					return
				if state["done"] or position >= round_number:
					continue
				if not self.alive(state["client"]):
					self.log("Skipped, the window closed", self.group(state["client"]))
					state["done"] = True
					continue
				self.staggered_turn(state, scripts)

		self.recover_disconnected()
		cooldown = scripts.get("stagger_cooldown") or 0
		if isinstance(cooldown, dict):
			cooldown = cooldown.get(len(clients), 0)
		if cooldown and not self.input.stopped:
			self.log(f"All clients drowned, restarting in {cooldown:g}s")
			self.input.sleep(cooldown)

	def staggered_turn(self, state, scripts):
		client = state["client"]
		if self.sits_out(client):
			state["done"] = True
			return
		try:
			self.staggered_steps(state, scripts)
		except ConnectionFailed as error:
			self.mark_disconnected(client, error.button)
			state["done"] = True

	def staggered_steps(self, state, scripts):
		client = state["client"]
		houses = list(HOUSES)

		if state["next"] == 0 and not state["pending"]:
			self.played.add(self.key(client))
			self.check_once(client)
			if self.input.stopped or not self.sequence(self.safe_click, client):
				return
			self.watched(client, self.equip)
			if self.input.stopped:
				return

		if state["pending"]:
			if not self.input.sleep(max(0.0, state["due"] - time.perf_counter())):
				return
			state["pending"] = False
			self.watched(client, self.confirm_knock, houses[state["next"] - 1])
			if self.input.stopped:
				return

		if state["next"] < len(houses):
			house = houses[state["next"]]
			state["next"] += 1
			self.watched(client, self.knock, house)
			if self.input.stopped:
				return
			state["pending"] = True
			state["due"] = time.perf_counter() + KNOCK["confirm_delay"]
			return

		self.count_run(client)
		if self.watched(client, self.drown):
			self.log("Drowned to reposition", self.group(client))
		state["done"] = True

	def play(self, client):
		if self.watched(client, self.trick_or_treat):
			self.count_run(client)

	def count_run(self, client):
		self.runs[client.name] = self.runs.get(client.name, 0) + 1
		self.log(f"Run {self.runs[client.name]} done", self.group(client))

	def log_summary(self):
		self.log(f"Ran for {format_duration(time.perf_counter() - self.started_at)}")
		total = sum(self.runs.values())
		self.log(f"Completed {runs_text(total)}")
		for name in sorted(self.runs):
			self.log(f"{name}: {runs_text(self.runs[name])}")

	def check_in_game(self, client):
		return self.sequence(self.wait_for, client, MAIN_GAME_OCR, "main_game")

	def ensure_in_game(self, client, need_join, check=True, detect=False):
		failures = 0
		screen = None
		while not self.input.stopped:
			try:
				if detect:
					detect = False
					screen = detect_screen(self.input, client, self.ctx, (MAIN_GAME_OCR, MENU_SCREEN_OCR, PRIVATE_SERVERS), TIMEOUTS["main_game"])
					if screen is None:
						return False
					if screen == MAIN_GAME_OCR:
						self.log("Already in the game", self.group(client))
						self.sequence(self.close_chat, client)
						return True
					self.log(f"On the {'menu screen' if screen == MENU_SCREEN_OCR else 'Private Servers screen'}", self.group(client))
					need_join = True
				if need_join:
					joined = self.sequence(self.join, client, screen)
					screen = None
					if not joined:
						return False
					self.log("Joined the private server", self.group(client))
					need_join = False
				if not check:
					return True
				if not self.check_in_game(client):
					return False
				self.sequence(self.close_chat, client)
				return True
			except ConnectionFailed as error:
				failures += 1
				if failures > RECOVERY["retries"]:
					self.log(f"Gave up after disconnecting {failures} times in a row, skipped the turn", self.group(client))
					return False
				self.log(f"Disconnected, recovering ({failures}/{RECOVERY['retries']})", self.group(client))
				screen = None
				if not self.sequence(self.recover, client, error.button):
					return False
				need_join = True
		return False

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