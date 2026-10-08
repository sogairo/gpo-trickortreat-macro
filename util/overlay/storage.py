from util.config import read_config, write_config

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