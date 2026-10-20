from app.settings import DROWNING
from ..base import Aborted

class DrowningPhase:
	def drown(self, client):
		self.press(client, "space", DROWNING["jump_hold"])
		self.sleep(DROWNING["jump_gap"])
		self.focus(client)
		self.note(client, "Hold Space and A")
		if not self.input.key_down("space"):
			raise Aborted()
		try:
			self.sleep(DROWNING["swim_delay"])
			if not self.input.hold_keys(["a"], DROWNING["swim"]):
				raise Aborted()
		finally:
			self.input.key_up("space")
		for key in ("esc", "r", "r", "enter", "enter"):
			self.sleep(DROWNING["key_gap"])
			self.press(client, key, DROWNING["key_hold"])
