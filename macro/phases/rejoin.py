from app.settings import MENU_SCREEN_OCR, PRIVATE_SERVERS, REJOIN, RECOVERY, DISCONNECT

class RejoinPhase:
	def leave(self, client):
		self.click(client, "exit")
		self.sleep(REJOIN["exit_gap"])
		self.click(client, "main_menu")
		self.sleep(REJOIN["menu_delay"])
		self.safe_click(client)

	def join(self, client, screen=None):
		if screen is None:
			screen = self.detect(client, (MENU_SCREEN_OCR, PRIVATE_SERVERS), "menu_screen")
		if screen is None:
			return False
		if screen == MENU_SCREEN_OCR and not self.click_until(client, PRIVATE_SERVERS, "default"):
			return False
		return self.enter_server(client)

	def enter_server(self, client):
		self.click(client, PRIVATE_SERVERS)
		self.sleep(REJOIN["server_delay"])
		self.click(client, "server_code_box")
		self.sleep(REJOIN["type_delay"])
		if not self.type_code(client):
			return False
		self.sleep(REJOIN["click_gap"])
		self.click(client, "regular")
		self.sleep(REJOIN["click_gap"])
		self.click(client, "first_sea")

	def close_chat(self, client):
		self.sleep(REJOIN["chat_delay"])
		self.press(client, "/")
		self.sleep(REJOIN["chat_gap"])
		self.click(client, "chat_button")
		self.sleep(REJOIN["chat_gap"])
		self.note(client, "Closed chat")

	def recover(self, client, button):
		self.sleep(RECOVERY["gap"])
		self.safe_click(client)
		self.sleep(RECOVERY["gap"])
		if not self.click_text(client, DISCONNECT["area"], button):
			return False
		self.sleep(RECOVERY["button_delay"])
		self.safe_click(client)
		self.sleep(RECOVERY["gap"])
		self.click(client, "play")
		self.sleep(RECOVERY["gap"])
		self.click(client, "play")
