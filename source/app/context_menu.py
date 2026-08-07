import os
import sys

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import winreg

REG_KEY_PATH = r"Software\Classes\*\shell\VirusTotalScanner"

def is_context_menu_enabled():
    """Checks if the context menu entry exists in Windows Registry."""
    if not IS_WINDOWS:
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ)
        winreg.CloseKey(key)
        return True
    except OSError:
        return False

def toggle_context_menu(enable=True):
    """Registers or unregisters the 'Scan with VirusTotal' context menu entry."""
    if not IS_WINDOWS:
        return False, "Context menu integration is only available on Windows."

    try:
        if enable:
            # Determine command to run
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
                cmd_str = f'"{exe_path}" "%1"'
            else:
                script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
                python_exe = sys.executable
                cmd_str = f'"{python_exe}" "{script_path}" "%1"'

            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH)
            winreg.SetValue(key, "", winreg.REG_SZ, "Scan with VirusTotal (VT-GUI)")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, sys.executable)
            winreg.CloseKey(key)

            command_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{REG_KEY_PATH}\command")
            winreg.SetValue(command_key, "", winreg.REG_SZ, cmd_str)
            winreg.CloseKey(command_key)
            return True, "Context menu entry added successfully!"
        else:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, rf"{REG_KEY_PATH}\command")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH)
            return True, "Context menu entry removed successfully!"
    except Exception as ex:
        return False, str(ex)
