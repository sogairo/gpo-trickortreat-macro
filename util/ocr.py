import os
import re
import time
import threading

import numpy as np
from PIL import ImageGrab
from rapidfuzz import fuzz

_reader = None
_reader_lock = threading.Lock()

FUZZY_THRESHOLD = 80
MODEL_DIR = os.path.join(os.path.expanduser("~"), ".EasyOCR", "model")

def models_downloaded():
	return os.path.isdir(MODEL_DIR) and any(name.endswith(".pth") for name in os.listdir(MODEL_DIR))

def get_reader(on_stage=None):
	global _reader
	with _reader_lock:
		if _reader is not None:
			return _reader

		start = time.perf_counter()
		last = [start]

		def stage(message):
			if on_stage is None:
				return
			now = time.perf_counter()
			on_stage(f"{message} ({now - last[0]:.1f}s)")
			last[0] = now

		import warnings
		warnings.filterwarnings("ignore", message=".*pin_memory.*no accelerator.*", category=UserWarning)
		warnings.filterwarnings("ignore", message=".*quantize_per_tensor.*", category=UserWarning)

		first_run = not models_downloaded()
		if on_stage and first_run:
			on_stage("OCR models not found, downloading on this first run (may take a minute)")

		import torch
		stage(f"Loaded PyTorch {torch.__version__}")
		import easyocr
		stage("Loaded EasyOCR")
		reader = easyocr.Reader(['en'], gpu=False, verbose=False)
		stage("Downloaded and loaded OCR models" if first_run else "Loaded OCR models")
		reader.readtext(np.full((60, 200, 3), 255, dtype=np.uint8), detail=0)
		stage("Warmed up OCR")

		_reader = reader
		if on_stage:
			on_stage(f"OCR model ready ({time.perf_counter() - start:.1f}s total)")
		return _reader

def is_ready():
	return _reader is not None

def preload(on_stage=None):
	def load():
		try:
			get_reader(on_stage)
		except Exception as error:
			if on_stage:
				on_stage(f"OCR model failed to load: {error}")
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