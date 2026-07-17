import os
import json
import locale
import sys
import platform

# Platform-aware binary name
IS_WINDOWS = sys.platform == "win32"
CLI_BINARY_NAME = "vt.exe" if IS_WINDOWS else "vt"

def get_cli_display_name():
    """Returns a human-readable name for the CLI binary."""
    return "vt.exe" if IS_WINDOWS else "vt"

# Official SHA-256 hashes of the vt CLI binary itself
KNOWN_HASHES = {
    # Version 1.3.1 — Windows
    "1f46c735b74a0a094b10faa3c58fee84577e767e2c7df3c2b0799ec8ff85c404": "1.3.1 (Windows 64-bit)",
    "b8a1acb1a5e857046852f9ca806099a9c48faedfc690ec3c8233659a6c8cc1e7": "1.3.1 (Windows 32-bit)",
    # Version 1.3.1 — Linux
    "600b19a99dced17d9e8d075f76a719ff30d7b6e3b18884d1eac670b128c34f8c": "1.3.1 (Linux 64-bit)",
    "1310faa6e352a22e3a95c8c82e3ff69ced1f507a7be2d2de3dc7a2c4e1465dee": "1.3.1 (Linux 32-bit)",
    # Version 1.3.1 — macOS
    "d32449caf0cb059c9331e3f2dfce7703823ff0faf8a40270a20f68ebb618a970": "1.3.1 (macOS)",
    # Version 1.3.1 — FreeBSD
    "87edffbd677e81083c4d0954383ad314f76ef3e3b58c01d471c3a152d2b80c56": "1.3.1 (FreeBSD 64-bit)",
    "516fbd51c01aaa086d71a34eb5bc0c5032eb2b1c7c55778b100952e5339573d0": "1.3.1 (FreeBSD 32-bit)",
    # Version 1.3.0 — Windows
    "8ee13a9b3ab9e4cb289b7946eba9743143988573233149d8a0072b061d7fde75": "1.3.0 (Windows 64-bit)",
    "dd0385c676cf492393ca879427a80bafd1e5cafd9262b00d40a286ae6824c0e6": "1.3.0 (Windows 32-bit)",
    # Version 1.2.0 — Windows
    "376de9530f0d22f3db8a13bf77a38b1fde52a91cef71b197c743a20e9c1a246c": "1.2.0 (Windows 64-bit)",
    "23b129ed48596c42e8471d82f74d618bdf51ed1db71d16c8a83aed10f9317e63": "1.2.0 (Windows 32-bit)"
}

def get_release_zip_name():
    """Returns the appropriate release ZIP filename for the current platform."""
    if IS_WINDOWS:
        is_64bit = platform.machine().endswith("64") or "AMD64" in platform.machine()
        return "Windows64.zip" if is_64bit else "Windows32.zip"
    elif sys.platform == "darwin":
        return "MacOSX.zip"
    elif sys.platform.startswith("linux"):
        is_64bit = platform.machine().endswith("64") or "x86_64" in platform.machine() or "aarch64" in platform.machine()
        return "Linux64.zip" if is_64bit else "Linux32.zip"
    elif sys.platform.startswith("freebsd"):
        is_64bit = platform.machine().endswith("64")
        return "FreeBSD64.zip" if is_64bit else "FreeBSD32.zip"
    else:
        # Fallback: try 64-bit
        return "Linux64.zip"

def _load_strings():
    """Load UI strings from the external JSON file."""
    strings_path = os.path.join(os.path.dirname(__file__), "strings.json")
    try:
        with open(strings_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

STRINGS = _load_strings()

# Display names for each language code
LANG_NAMES = {
    "en": "English",
    "ru": "Русский",
    "es": "Español",
    "de": "Deutsch",
    "fr": "Français",
    "pt": "Português",
    "tr": "Türkçe",
    "uk": "Українська",
    "zh": "中文",
    "ja": "日本語",
    "ko": "한국어",
    "ar": "العربية",
}

def get_available_langs():
    """Returns list of (code, display_name) for languages present in strings.json."""
    return [(code, LANG_NAMES.get(code, code)) for code in STRINGS if code in LANG_NAMES]

def get_env_file_path():
    """Returns .env file path, handling naming collisions on Windows."""
    if os.path.exists('.env') and os.path.isdir('.env'):
        return os.path.join('.env', '.env')
    return '.env'

def load_env_vars():
    """Load settings from the environment file."""
    env_path = get_env_file_path()
    vars_dict = {}
    if os.path.exists(env_path) and os.path.isfile(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            key = parts[0].strip()
                            val = parts[1].strip().strip('"').strip("'")
                            vars_dict[key] = val
                            os.environ[key] = val
        except Exception:
            pass
    return vars_dict

def get_vt_toml_path():
    """Returns the path to the user's .vt.toml file."""
    return os.path.join(os.path.expanduser("~"), ".vt.toml")

def read_key_from_vt_toml():
    """Reads the API key from the ~/.vt.toml file."""
    toml_path = get_vt_toml_path()
    if os.path.exists(toml_path) and os.path.isfile(toml_path):
        try:
            with open(toml_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_stripped = line.strip()
                    if not line_stripped or line_stripped.startswith("#"):
                        continue
                    if line_stripped.startswith("apikey"):
                        parts = line_stripped.split("=", 1)
                        if len(parts) == 2:
                            val = parts[1].strip().strip('"').strip("'")
                            return val
        except Exception:
            pass
    return None

def write_key_to_vt_toml(key):
    """Writes or updates the API key in the ~/.vt.toml file."""
    toml_path = get_vt_toml_path()
    lines = []
    found = False
    
    if os.path.exists(toml_path) and os.path.isfile(toml_path):
        try:
            with open(toml_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            pass

    new_lines = []
    for line in lines:
        line_stripped = line.strip()
        if line_stripped.startswith("apikey") and "=" in line_stripped and not line_stripped.startswith("#"):
            leading_whitespace = line[:len(line) - len(line.lstrip())]
            new_lines.append(f'{leading_whitespace}apikey = "{key}"\n')
            found = True
        else:
            new_lines.append(line)
            
    if not found:
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines[-1] += '\n'
        new_lines.append(f'apikey = "{key}"\n')
        
    try:
        dir_name = os.path.dirname(toml_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(toml_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True
    except Exception:
        return False

def write_env_var(key, value):
    """Write settings to the environment file."""
    env_path = get_env_file_path()
    vars_dict = load_env_vars()
    vars_dict[key] = str(value)
    try:
        dir_name = os.path.dirname(env_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(env_path, "w", encoding="utf-8") as f:
            for k, v in vars_dict.items():
                f.write(f"{k}={v}\n")
        os.environ[key] = str(value)
        if key == "VT_APIKEY":
            write_key_to_vt_toml(value)
            os.environ["VTCLI_APIKEY"] = str(value)
        return True
    except Exception:
        return False

def get_api_key():
    """Retrieves configured VirusTotal API Key."""
    # Always check ~/.vt.toml first as the main source of truth for vt-cli
    toml_val = read_key_from_vt_toml()
    
    env_vars = load_env_vars()
    env_val = env_vars.get("VT_APIKEY") or os.environ.get("VT_APIKEY")
    
    if toml_val:
        if toml_val != env_val:
            # Sync to env
            write_env_var("VT_APIKEY", toml_val)
        os.environ["VTCLI_APIKEY"] = toml_val
        return toml_val
        
    # Fallback to env file/environment variables if .vt.toml doesn't exist or is empty
    for var in ['VT_APIKEY', 'VTCLI_APIKEY', 'VIRUSTOTAL_API_KEY']:
        val = env_vars.get(var) or os.environ.get(var)
        if val:
            # Sync to .vt.toml
            write_key_to_vt_toml(val)
            os.environ["VTCLI_APIKEY"] = val
            return val
            
    return None

def _detect_system_lang():
    """Detect system locale and return best matching language code."""
    # Map of locale prefixes to language codes
    locale_map = {
        "ru": "ru", "uk": "uk",
        "es": "es",
        "de": "de",
        "fr": "fr",
        "pt": "pt",
        "tr": "tr",
        "zh": "zh",
        "ja": "ja",
        "ko": "ko",
        "ar": "ar",
    }
    try:
        for env_var in ('LANG', 'LC_ALL', 'LC_CTYPE', 'LANGUAGE'):
            val = os.environ.get(env_var)
            if val:
                prefix = val.split('.')[0].split('_')[0].split('-')[0].lower()
                if prefix in locale_map:
                    return locale_map[prefix]
        try:
            lang, _ = locale.getlocale()
            if lang:
                prefix = lang.split('_')[0].split('-')[0].lower()
                if prefix in locale_map:
                    return locale_map[prefix]
        except Exception:
            pass
    except Exception:
        pass
    return "en"

def get_app_lang():
    """Determines application language from saved settings or system locale."""
    env_vars = load_env_vars()
    saved_lang = env_vars.get("LANGUAGE")
    if saved_lang and saved_lang in STRINGS:
        return saved_lang
    return _detect_system_lang()
