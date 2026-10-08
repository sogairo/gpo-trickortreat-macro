import ctypes
from ctypes import wintypes

from .api import user32, gdi32, BLENDFUNCTION, BITMAPINFO, BITMAPINFOHEADER
from .constants import GWL_EXSTYLE, WS_EX_LAYERED, ULW_ALPHA, AC_SRC_OVER, AC_SRC_ALPHA, DIB_RGB_COLORS

def apply_layered_image(hwnd, width, height, bgra):
	style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
	user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED)

	hdc_screen = user32.GetDC(None)
	hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)

	info = BITMAPINFO()
	info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
	info.bmiHeader.biWidth = width
	info.bmiHeader.biHeight = -height
	info.bmiHeader.biPlanes = 1
	info.bmiHeader.biBitCount = 32
	info.bmiHeader.biCompression = 0

	bits = ctypes.c_void_p()
	bitmap = gdi32.CreateDIBSection(hdc_mem, ctypes.byref(info), DIB_RGB_COLORS, ctypes.byref(bits), None, 0)
	ctypes.memmove(bits, bgra, width * height * 4)
	old_bitmap = gdi32.SelectObject(hdc_mem, bitmap)

	size = wintypes.SIZE(width, height)
	source = wintypes.POINT(0, 0)
	blend = BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)
	user32.UpdateLayeredWindow(hwnd, hdc_screen, None, ctypes.byref(size), hdc_mem, ctypes.byref(source), 0, ctypes.byref(blend), ULW_ALPHA)

	gdi32.SelectObject(hdc_mem, old_bitmap)
	gdi32.DeleteObject(bitmap)
	gdi32.DeleteDC(hdc_mem)
	user32.ReleaseDC(None, hdc_screen)
