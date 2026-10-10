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
	"min_width": 800,
	"min_height": 500,
}

LOG = {
	"limit": 500,
}

FILES = {
	"config": os.path.join(ROOT, "config.json"),
	"steps": os.path.join(ROOT, "resources", "steps.json"),
	"reposition_dir": os.path.join(ROOT, "resources", "reposition"),
	"connection_failed": os.path.join(ROOT, "resources", "connection_failed", "recovery.json"),
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
	"type_code_hold": 0.03,
	"type_code_gap": 0.03,
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
		"file": "drowning.json",
		"clients": (2, DOCK["max_slots"]),
		"default": True,
		"stagger_from": 3,
		"stagger_cooldown": {
			3: 30,
			4: 15,
		},
	},
	"Rejoining": {
		"file": "rejoining.json",
		"clients": (1, DOCK["max_slots"]),
		"first_client_only": True,
		"rejoin": True,
	},
}

MAIN_GAME_OCR = "main_game_ocr"
MENU_SCREEN_OCR = "menu_screen_ocr"
KNOCK_DETECTION = "knock_detection"
FAIL_DETECTION = "fail_detection"

DEFAULT_KEYBINDS = {
	"start_key": "f7",
	"stop_key": "f8",
}

REGIONS = {
	MAIN_GAME_OCR: {
		"label": "Main Game OCR",
		"category": "Main Game",
		"ocr_text": "menu",
		"safe_click": True,
		"default": {"x1": 0.0, "y1": 0.9371069182389937, "x2": 0.11337579617834395, "y2": 1.0},
	},
	MENU_SCREEN_OCR: {
		"label": "Menu Screen OCR",
		"category": "Menu Screen",
		"ocr_text": "press any key to continue",
		"default": {"x1": 0.33885350318471336, "y1": 0.8679245283018868, "x2": 0.6535031847133758, "y2": 1.0},
	},
	KNOCK_DETECTION: {
		"label": "Knock Detection",
		"category": "Main Game",
		"ocr_text": "knock",
		"match": "word",
		"default": {"x1": 0.2522292993630573, "y1": 0.3857442348008386, "x2": 0.5987261146496815, "y2": 0.6561844863731656},
	},
	FAIL_DETECTION: {
		"label": "Fail Detection",
		"category": "Disconnect",
		"ocr_text": "connection failed",
		"default": {"x1": 0.39363057324840767, "y1": 0.2620545073375262, "x2": 0.6101910828025477, "y2": 0.32914046121593293},
	},
}

MARKERS = {
	"exit": {
		"label": "Exit",
		"category": "Main Game",
		"default": {"x": 0.37070063694267513, "y": 0.07127882599580712},
	},
	"main_menu": {
		"label": "Main Menu",
		"category": "Main Game",
		"default": {"x": 0.34777070063694265, "y": 0.1970649895178197},
	},
	"private_servers": {
		"label": "Private Servers",
		"category": "Menu Screen",
		"default": {"x": 0.7528662420382166, "y": 0.639412997903564},
	},
	"server_code_box": {
		"label": "Server Code Box",
		"category": "Menu Screen",
		"default": {"x": 0.5019108280254777, "y": 0.6163522012578616},
	},
	"regular": {
		"label": "Regular",
		"category": "Menu Screen",
		"default": {"x": 0.39363057324840767, "y": 0.5178197064989518},
	},
	"first_sea": {
		"label": "First Sea",
		"category": "Menu Screen",
		"default": {"x": 0.42165605095541403, "y": 0.519916142557652},
	},
	"cancel": {
		"label": "Cancel",
		"category": "Disconnect",
		"default": {"x": 0.378343949044586, "y": 0.6834381551362684},
	},
	"play": {
		"label": "Play",
		"category": "Disconnect",
		"default": {"x": 0.5515923566878981, "y": 0.5345911949685535},
	},
}