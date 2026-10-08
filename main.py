import ctypes

from app import runtime

def set_dpi_awareness():
	try:
		ctypes.windll.shcore.SetProcessDpiAwareness(2)
	except Exception:
		try:
			ctypes.windll.user32.SetProcessDPIAware()
		except Exception:
			pass

def main():
	set_dpi_awareness()
	runtime.run()

if __name__ == "__main__":
	main()
