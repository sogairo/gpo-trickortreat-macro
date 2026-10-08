import numpy as np
from PIL import ImageGrab

def black_ratio(x, y, w, h):
	if w <= 0 or h <= 0:
		return 0.0
	img = np.asarray(ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True).convert("RGB"))
	black = np.all(img == 0, axis=2)
	return float(black.mean())