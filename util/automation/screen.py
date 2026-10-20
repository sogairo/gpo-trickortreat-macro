import numpy as np
from PIL import ImageGrab

def black_ratio(x, y, w, h):
	if w <= 0 or h <= 0:
		return 0.0
	img = np.asarray(ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True).convert("RGB"))
	black = np.all(img == 0, axis=2)
	return float(black.mean())

def green_red_ratios(x1, y1, x2, y2, brightness, dominance):
	if x2 <= x1 or y2 <= y1:
		return 0.0, 0.0
	img = np.asarray(ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True).convert("RGB"), dtype=np.float32)
	red, green, blue = img[..., 0], img[..., 1], img[..., 2]
	greenish = (green >= brightness) & (green > red * dominance) & (green > blue * dominance)
	reddish = (red >= brightness) & (red > green * dominance) & (red > blue * dominance)
	return float(greenish.mean()), float(reddish.mean())