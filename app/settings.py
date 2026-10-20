import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APP_NAME = "GPO Trick-or-treat Macro"

DOCK = {
	"roblox_exe": "robloxplayerbeta.exe",
	"poll_ms": 500,
	"max_slots": 4,
	"min_client_size": 200,
}

LAYOUT = {
	"sidebar_width": 200,
	"slot_pad": 3,
	"client_width": 784,
	"client_height": 441,
}

LOG = {
	"limit": 500,
}

FILES = {
	"config": os.path.join(ROOT, "config.json"),
}

SERVER_CODE = {
	"length": 10,
}

TIMEOUTS = {
	"default": 60,
	"main_game": 360,
	"menu_screen": 360,
	"knock": 20,
	"knock_confirm": 5,
}

KEYBOARD = {
	"press_hold": 0.1,
	"type_hold": (0.05, 0.09),
	"type_gap": (0.08, 0.14),
	"word_pause": (0.15, 0.25),
}

MOUSE = {
	"click_hold": 0.05,
	"click_glide": 0.1,
}

SAFE_CLICK = {
	"x": 0.95,
	"y": 0.95,
	"glide": 0.1,
	"hold": 0.1,
	"gap": 0.1,
}

RECOVERY = {
	"retries": 5,
	"gap": 0.5,
	"button_delay": 5,
}

CHECK_SETTINGS = {
	"key": "m",
	"menu_delay": 0.5,
	"tab_delay": 0.5,
	"recheck_delay": 0.5,
	"min_brightness": 50,
	"dominance": 1.3,
	"min_green": 0.02,
}

DISCONNECT = {
	"area": (0.245, 0.22, 0.755, 0.78),
	"watch_interval": 1.0,
	"prompts": {
		"disconnected": "leave",
		"connection failed": "cancel",
	},
}

REJOIN = {
	"exit_gap": 0.5,
	"menu_delay": 1.5,
	"spam_gap": 0.1,
	"server_delay": 1.5,
	"type_delay": 0.5,
	"click_gap": 0.1,
	"chat_delay": 1.5,
	"chat_gap": 0.3,
}

EQUIP = {
	"key": "1",
	"hold": 0.2,
}

KNOCK = {
	"key": "e",
	"delay": 0.1,
	"hold": 0.1,
	"confirm_delay": 6.5,
}

HOUSES = {
	"House 1": ["a 5.3", "w 1.5"],
	"House 2": ["a 2.375"],
	"House 3": ["s 0.3", "a 2.33", "w 0.3"],
	"House 4": ["a 2.435"],
	"House 5": ["s+a 1.5", "a 0.1"],
	"House 6": ["s 2.335"],
	"House 7": ["d 0.3", "s 2.42", "a 0.3"],
	"House 8": ["d 0.3", "s 2.415", "a 0.3"],
}

DROWNING = {
	"jump_hold": 0.2,
	"jump_gap": 0.1,
	"swim_delay": 0.7,
	"swim": 3.5,
	"key_gap": 0.2,
	"key_hold": 0.1,
}

ANTI_MACRO = {
	"black_threshold": 0.5,
	"key": "2",
	"spam_delay": 0.25,
	"reequip_key": "1",
}

FOCUS = {
	"settle": 0.2,
	"attempts": 3,
	"retry_delay": 0.1,
}

OCR = {
	"read_interval": 0.25,
}

REPOSITION = {
	"Drowning": {
		"clients": (2, DOCK["max_slots"]),
		"stagger_from": 3,
		"stagger_cooldown": {
			3: 30,
			4: 15,
		},
	},
	"Rejoining": {
		"clients": (1, DOCK["max_slots"]),
		"default": True,
		"first_client_only": True,
		"rejoin": True,
	},
}

MAIN_GAME_OCR = "main_game_ocr"
MENU_SCREEN_OCR = "menu_screen_ocr"
KNOCK_DETECTION = "knock_detection"
PRIVATE_SERVERS = "private_servers"
AUTO_RUN = "auto_run"

CONFIG_SETTINGS = ("auto_dock", "private_server_code", "reposition_by", "keybinds", "check_settings")

DEFAULT_KEYBINDS = {
	"start_key": "f7",
	"stop_key": "f8",
}

REGIONS = {
	MAIN_GAME_OCR: {
		"label": "Main Game OCR",
		"category": "Main Game",
		"ocr_text": "menu",
		"default": {"x1": 0.0, "y1": 0.9365079365079365, "x2": 0.10459183673469388, "y2": 1.0},
	},
	MENU_SCREEN_OCR: {
		"label": "Menu Screen OCR",
		"rejoin": True,
		"category": "Menu Screen",
		"ocr_text": "press any key to continue",
		"default": {"x1": 0.3392857142857143, "y1": 0.854875283446712, "x2": 0.6530612244897959, "y2": 1.0},
	},
	PRIVATE_SERVERS: {
		"label": "Private Servers",
		"rejoin": True,
		"category": "Menu Screen",
		"ocr_text": "private servers/ friend join",
		"default": {"x1": 0.5969387755102041, "y1": 0.6213151927437641, "x2": 0.9005102040816326, "y2": 0.6802721088435374},
	},
	AUTO_RUN: {
		"label": "Auto Run",
		"check_settings": True,
		"category": "Settings",
		"check": "green",
		"default": {"x1": 0.5063775510204082, "y1": 0.5668934240362812, "x2": 0.5803571428571429, "y2": 0.6190476190476191},
	},
	KNOCK_DETECTION: {
		"label": "Knock Detection",
		"category": "Main Game",
		"ocr_text": "knock",
		"match": "word",
		"default": {"x1": 0.23979591836734693, "y1": 0.3673469387755102, "x2": 0.6466836734693877, "y2": 0.671201814058957},
	},
}

MARKERS = {
	"settings_tab": {
		"label": "Settings",
		"check_settings": True,
		"category": "Settings",
		"default": {"x": 0.43494897959183676, "y": 0.4489795918367347},
	},
	"chat_button": {
		"label": "Chat Button",
		"rejoin": True,
		"category": "Main Game",
		"default": {"x": 0.10331632653061225, "y": 0.07482993197278912},
	},
	"exit": {
		"label": "Exit",
		"rejoin": True,
		"category": "Main Game",
		"default": {"x": 0.2971938775510204, "y": 0.07709750566893424},
	},
	"main_menu": {
		"label": "Main Menu",
		"rejoin": True,
		"category": "Main Game",
		"default": {"x": 0.28188775510204084, "y": 0.2199546485260771},
	},
	"server_code_box": {
		"label": "Server Code Box",
		"rejoin": True,
		"category": "Menu Screen",
		"default": {"x": 0.5012755102040817, "y": 0.6281179138321995},
	},
	"regular": {
		"label": "Regular",
		"rejoin": True,
		"category": "Menu Screen",
		"default": {"x": 0.39285714285714285, "y": 0.5170068027210885},
	},
	"first_sea": {
		"label": "First Sea",
		"rejoin": True,
		"category": "Menu Screen",
		"default": {"x": 0.4247448979591837, "y": 0.5192743764172335},
	},
	"play": {
		"label": "Play",
		"rejoin": True,
		"category": "Disconnect",
		"default": {"x": 0.5510204081632653, "y": 0.5804988662131519},
	},
}