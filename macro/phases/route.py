from app.settings import KNOCK_DETECTION, HOUSES, EQUIP, KNOCK

class RoutePhase:
	def equip(self, client):
		self.press(client, EQUIP["key"], EQUIP["hold"])

	def knock(self, client, house):
		for move in HOUSES[house]:
			self.walk(client, move)
		self.wait_for(client, KNOCK_DETECTION, "knock", f" at {house}")
		self.sleep(KNOCK["delay"])
		self.press(client, KNOCK["key"], KNOCK["hold"])

	def confirm_knock(self, client, house):
		self.wait_for(client, KNOCK_DETECTION, "knock_confirm", f" to confirm {house}")

	def trick_or_treat(self, client):
		self.equip(client)
		for house in HOUSES:
			self.knock(client, house)
			self.sleep(KNOCK["confirm_delay"])
			self.confirm_knock(client, house)