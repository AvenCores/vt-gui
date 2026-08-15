import sys
import time
import ctypes
import flet as ft


def set_clipboard_win32(text: str) -> bool:
    """Sets clipboard text using Win32 API with retry loop for Windows lock errors."""
    if sys.platform != "win32":
        return False
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        CF_UNICODETEXT = 13
        GHND = 0x0042

        # Retry up to 10 times if clipboard is locked by another process (error 5)
        for _ in range(10):
            if user32.OpenClipboard(None):
                try:
                    user32.EmptyClipboard()
                    encoded = text.encode('utf-16-le') + b'\x00\x00'
                    h_mem = kernel32.GlobalAlloc(GHND, len(encoded))
                    if h_mem:
                        p_mem = kernel32.GlobalLock(h_mem)
                        if p_mem:
                            ctypes.memmove(p_mem, encoded, len(encoded))
                            kernel32.GlobalUnlock(h_mem)
                            user32.SetClipboardData(CF_UNICODETEXT, h_mem)
                            return True
                finally:
                    user32.CloseClipboard()
            time.sleep(0.05)
    except Exception:
        pass
    return False


async def safe_copy_to_clipboard(page: ft.Page, text: str, clipboard_service=None):
    """Safely copies text to clipboard, catching PlatformException/RuntimeError and trying Win32 fallback."""
    copied = False
    if clipboard_service:
        try:
            await clipboard_service.set(text)
            copied = True
        except Exception:
            copied = False
    
    if not copied:
        set_clipboard_win32(text)
