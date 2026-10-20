import time

from app.settings import DROWNING
from ..base import Aborted, parse_walk

class DrowningPhase:
	def drown(self, client):
		for move in DROWNING["moves"]:
			keys, duration = parse_walk(move)
			if DROWNING["spam_during"] in keys:
				self.hold_spamming(client, keys, duration)
			else:
				self.walk(client, move)
		for key in ("esc", "r", "r", "enter", "enter"):
			self.sleep(DROWNING["key_gap"])
			self.press(client, key, DROWNING["key_hold"])

	def hold_spamming(self, client, keys, duration):
		self.focus(client)
		held = []
		try:
			for key in keys:
				if not self.input.key_down(key):
					raise Aborted()
				held.append(key)
			end = time.perf_counter() + duration
			while time.perf_counter() < end:
				if not self.input.tap_key(DROWNING["spam_key"], hold=DROWNING["spam_hold"]):
					raise Aborted()
				if not self.input.sleep(min(DROWNING["spam_gap"], max(0.0, end - time.perf_counter()))):
					raise Aborted()
		finally:
			for key in held:
				self.input.key_up(key)