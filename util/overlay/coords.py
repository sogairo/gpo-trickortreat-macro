def to_pixels(box, rect):
	x, y, w, h = rect
	return x + round(box["x1"] * w), y + round(box["y1"] * h), x + round(box["x2"] * w), y + round(box["y2"] * h)

def to_percent(x1, y1, x2, y2, rect):
	x, y, w, h = rect
	return {
		"x1": (x1 - x) / max(1, w),
		"y1": (y1 - y) / max(1, h),
		"x2": (x2 - x) / max(1, w),
		"y2": (y2 - y) / max(1, h),
	}

def point_to_pixels(point, rect):
	x, y, w, h = rect
	return x + round(point["x"] * w), y + round(point["y"] * h)

def point_to_percent(px, py, rect):
	x, y, w, h = rect
	return {
		"x": (px - x) / max(1, w),
		"y": (py - y) / max(1, h),
	}
