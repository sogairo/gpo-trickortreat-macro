import os
import json

def read_config(config_file):
	if not os.path.exists(config_file):
		return {}
	try:
		with open(config_file, "r") as f:
			return json.load(f)
	except Exception as e:
		print(f"Config load error, using defaults: {e}")
		return {}

def write_config(config_file, data):
	with open(config_file, "w") as f:
		json.dump(data, f, indent="\t")

def prune_config(config_file, settings, sections):
	if not os.path.exists(config_file):
		return False
	data = read_config(config_file)
	clean = {"settings": {key: value for key, value in data.get("settings", {}).items() if key in settings}}
	for section, names in sections.items():
		stored = data.get(section, {})
		clean[section] = {name: stored[name] for name in names if name in stored}
	if clean == data:
		return False
	write_config(config_file, clean)
	return True

def load_setting(config_file, key, default):
	return read_config(config_file).get("settings", {}).get(key, default)

def save_setting(config_file, key, value):
	data = read_config(config_file)
	data.setdefault("settings", {})[key] = value
	write_config(config_file, data)

REGION_KEYS = ("x1", "y1", "x2", "y2")
MARKER_KEYS = ("x", "y")

def load_section(config_file, section, defaults, keys):
	items = {name: dict(value) for name, value in defaults.items()}
	for name, value in read_config(config_file).get(section, {}).items():
		if name in items and isinstance(value, dict) and all(key in value for key in keys):
			items[name].update({key: value[key] for key in keys})
	return items

def save_section(config_file, section, items):
	data = read_config(config_file)
	stored = data.setdefault(section, {})
	for name, value in items.items():
		stored.setdefault(name, {}).update(value)
	write_config(config_file, data)