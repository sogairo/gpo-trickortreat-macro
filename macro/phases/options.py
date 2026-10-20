from app.settings import AUTO_RUN, CHECK_SETTINGS

class OptionsPhase:
	def check_settings(self, client):
		self.press(client, CHECK_SETTINGS["key"])
		self.sleep(CHECK_SETTINGS["menu_delay"])
		self.click(client, "settings_tab")
		self.sleep(CHECK_SETTINGS["tab_delay"])
		if self.is_green(client, AUTO_RUN):
			self.click(client, AUTO_RUN)
			self.sleep(CHECK_SETTINGS["recheck_delay"])
			if self.is_green(client, AUTO_RUN):
				self.note(client, "Couldn't turn off Auto Run, it still looks on")
			else:
				self.note(client, "Turned off Auto Run")
		else:
			self.note(client, "Auto Run was already off")
		self.press(client, CHECK_SETTINGS["key"])