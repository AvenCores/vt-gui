import sys
import os

try:
    import winreg
except ImportError:
    winreg = None

def register_context_menu():
    """Register 'Scan with VirusTotal' in Windows Explorer context menu."""
    if sys.platform != "win32" or winreg is None:
        return False, "Only supported on Windows"
        
    try:
        if getattr(sys, 'frozen', False):
            command_str = f'"{sys.executable}" "%1" --context-menu'
        else:
            # We want to run main.py in the workspace
            # sys.argv[0] might be main.py or other script, let's determine main.py path
            script_path = os.path.abspath(sys.argv[0])
            if not script_path.endswith("main.py"):
                # fallback to looking for main.py in the same folder as this file's parent
                script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
            command_str = f'"{sys.executable}" "{script_path}" "%1" --context-menu'
            
        key_path = r"Software\Classes\*\shell\VirusTotalScan"
        
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "&Scan with VirusTotal")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, "shell32.dll,224")
            
        command_key_path = rf"{key_path}\command"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_key_path) as cmd_key:
            winreg.SetValue(cmd_key, "", winreg.REG_SZ, command_str)
            
        return True, None
    except Exception as e:
        return False, str(e)

def unregister_context_menu():
    """Remove 'Scan with VirusTotal' from context menu."""
    if sys.platform != "win32" or winreg is None:
        return False, "Only supported on Windows"
        
    key_path = r"Software\Classes\*\shell\VirusTotalScan"
    try:
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, rf"{key_path}\command")
        except FileNotFoundError:
            pass
            
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except FileNotFoundError:
            pass
            
        return True, None
    except Exception as e:
        return False, str(e)
