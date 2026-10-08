import re
import threading

import numpy as np
from PIL import ImageGrab
from rapidfuzz import fuzz

_reader = None
_reader_lock = threading.Lock()

FUZZY_THRESHOLD = 80

def get_reader():
	global _reader
	with _reader_lock:
		if _reader is None:
			import warnings
			warnings.filterwarnings("ignore", message=".*pin_memory.*no accelerator.*", category=UserWarning)
			warnings.filterwarnings("ignore", message=".*quantize_per_tensor.*", category=UserWarning)
			import easyocr
			_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
		return _reader

def is_ready():
	return _reader is not None

def preload(on_ready=None):
	def load():
		get_reader()
		if on_ready:
			on_ready()
	threading.Thread(target=load, daemon=True).start()

def read(x1, y1, x2, y2):
	img = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)
	results = get_reader().readtext(np.array(img), detail=0)
	return " ".join(results)

def words(text):
	return re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()

def matches_exact(target, text, threshold=FUZZY_THRESHOLD):
	target_words = words(target)
	text_words = words(text)
	if len(text_words) != len(target_words):
		return False
	for want, got in zip(target_words, text_words):
		if abs(len(want) - len(got)) > 1:
			return False
		if fuzz.ratio(want, got) < threshold:
			return False
	return True

def matches_word(target, text, threshold=FUZZY_THRESHOLD):
	target_words = words(target)
	text_words = words(text)
	size = len(target_words)
	for start in range(len(text_words) - size + 1):
		window = text_words[start:start + size]
		if all(len(want) == len(got) and fuzz.ratio(want, got) >= threshold for want, got in zip(target_words, window)):
			return True
	return False

def matches(target, text, threshold=FUZZY_THRESHOLD, mode="contains"):
	if mode == "exact":
		return matches_exact(target, text, threshold)
	if mode == "word":
		return matches_word(target, text, threshold)
	target = target.lower().strip()
	text = text.lower().strip()
	if not text:
		return False
	if target in text:
		return True
	if len(text) < len(target):
		return fuzz.ratio(target, text) >= threshold
	return fuzz.partial_ratio(target, text) >= threshold