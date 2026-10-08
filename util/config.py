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

def load_setting(config_file, key, default):
	return read_config(config_file).get("settings", {}).get(key, default)

def save_setting(config_file, key, value):
	data = read_config(config_file)
	data.setdefault("settings", {})[key] = value
	write_config(config_file, data)
