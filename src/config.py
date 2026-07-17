import os
import locale
import sys

# Official SHA-256 hashes of vt.exe itself
KNOWN_HASHES = {
    # Version 1.3.1
    "1f46c735b74a0a094b10faa3c58fee84577e767e2c7df3c2b0799ec8ff85c404": "1.3.1 (Windows 64-bit)",
    "b8a1acb1a5e857046852f9ca806099a9c48faedfc690ec3c8233659a6c8cc1e7": "1.3.1 (Windows 32-bit)",
    # Version 1.3.0
    "8ee13a9b3ab9e4cb289b7946eba9743143988573233149d8a0072b061d7fde75": "1.3.0 (Windows 64-bit)",
    "dd0385c676cf492393ca879427a80bafd1e5cafd9262b00d40a286ae6824c0e6": "1.3.0 (Windows 32-bit)",
    # Version 1.2.0
    "376de9530f0d22f3db8a13bf77a38b1fde52a91cef71b197c743a20e9c1a246c": "1.2.0 (Windows 64-bit)",
    "23b129ed48596c42e8471d82f74d618bdf51ed1db71d16c8a83aed10f9317e63": "1.2.0 (Windows 32-bit)"
}

STRINGS = {
    "en": {
        "app_title": "VirusTotal File Scanner",
        "scanner_tab": "Scanner",
        "settings_title": "Settings",
        "api_key_label": "VirusTotal API Key",
        "api_key_hint": "Enter your VirusTotal API key",
        "vt_exe_status": "VirusTotal CLI Status",
        "vt_exe_verified": "Verified (Official {version})",
        "vt_exe_unapproved": "Unapproved (Hash: {hash})",
        "vt_exe_missing": "Not Installed",
        "vt_exe_custom": "Verified (Custom approved binary)",
        "download_instructions_title": "VirusTotal CLI (vt.exe) Required",
        "download_instructions_text": "To scan files using the official CLI, you need to download it manually:\n\n1. Click the button below to open GitHub releases.\n2. Download the Windows ZIP archive (Windows64.zip or Windows32.zip).\n3. Click 'Select Downloaded File' below to verify and install it.",
        "open_releases": "Open GitHub Releases Page",
        "select_file_zip": "Select Downloaded ZIP or vt.exe",
        "install_desc": "The official VirusTotal command-line tool (vt.exe) is required to perform fast and complete file scans. Install it automatically below.",
        "btn_auto_install": "Download and Install CLI",
        "btn_manual_install": "Select ZIP or vt.exe manually",
        "installing_cli": "Installing vt-cli...",
        "verify_success": "vt.exe successfully verified and installed!",
        "verify_fail": "Verification failed: {e}",
        "hash_warning_title": "Unknown Binary Hash",
        "hash_warning_text": "The SHA-256 hash of this file ({hash}) does not match any known official release of vt-cli.\n\nDo you want to use this binary anyway?",
        "btn_yes": "Yes, I trust it",
        "btn_no": "Cancel",
        "btn_close": "Close",
        "btn_save": "Save Settings",
        "api_saved": "Settings saved successfully!",
        "link_copied": "Link copied to clipboard!",
        "scan_in_progress": "SCAN IN PROGRESS",
        "drag_drop_text": "Click here to choose a file or browse",
        "btn_select_file": "Select File to Scan",
        "btn_scan": "Scan Now",
        "api_key_missing": "API Key is missing! Please configure it in Settings.",
        "api_key_invalid_err": "Authentication failed. Please verify your API Key.",
        "computing_hash": "Computing file SHA-256 hash...",
        "checking_vt": "Checking if file was already analyzed...",
        "uploading_file": "File not found in database. Uploading file...",
        "upload_progress": "Uploading: {percent}% ({current:.2f}/{total:.2f} MB)",
        "waiting_analysis": "Waiting for analysis to complete...",
        "opening_report": "Opening report in browser...",
        "scan_success": "Scan completed!",
        "scan_failed": "Scan failed: {e}",
        "results_summary": "Scan Results Summary",
        "stats_malicious": "Malicious",
        "stats_suspicious": "Suspicious",
        "stats_harmless": "Harmless",
        "stats_undetected": "Undetected",
        "verdict_safe": "SAFE: No engines flagged this file as malicious.",
        "verdict_suspicious": "SUSPICIOUS: {suspicious} engine(s) flagged this file.",
        "verdict_malicious": "DANGER: Flagged as malicious by {malicious} engine(s)!",
        "btn_open_web": "Open Web Report",
        "btn_back": "Back to Scanner",
        "detections_title": "Antivirus Detections",
        "show_all_engines": "Show All Engines ({count})",
        "hide_all_engines": "Hide All Engines",
        "column_engine": "Engine",
        "column_category": "Category",
        "column_result": "Result",
        "column_method": "Method",
        "file_details": "File Details",
        "file_name": "File Name",
        "file_size": "File Size",
        "file_hash": "SHA-256",
        "unknown": "Unknown"
    },
    "ru": {
        "app_title": "Сканер файлов VirusTotal",
        "scanner_tab": "Сканер",
        "settings_title": "Настройки",
        "api_key_label": "API Ключ VirusTotal",
        "api_key_hint": "Введите ваш API-ключ",
        "vt_exe_status": "Статус VirusTotal CLI",
        "vt_exe_verified": "Проверен (Официальный {version})",
        "vt_exe_unapproved": "Не одобрен (Хэш: {hash})",
        "vt_exe_missing": "Не установлен",
        "vt_exe_custom": "Проверен (Пользовательский одобренный)",
        "download_instructions_title": "Требуется VirusTotal CLI (vt.exe)",
        "download_instructions_text": "Для сканирования через CLI необходимо скачать его вручную:\n\n1. Нажмите кнопку ниже для перехода к релизам на GitHub.\n2. Скачайте ZIP-архив для Windows (Windows64.zip или Windows32.zip).\n3. Нажмите кнопку 'Выбрать скачанный файл' ниже для проверки и установки.",
        "open_releases": "Открыть страницу релизов на GitHub",
        "select_file_zip": "Выбрать скачанный ZIP или vt.exe",
        "install_desc": "Для быстрого и полного сканирования файлов требуется официальная утилита VirusTotal (vt.exe). Установите ее автоматически ниже.",
        "btn_auto_install": "Скачать и установить CLI",
        "btn_manual_install": "Выбрать ZIP или vt.exe вручную",
        "installing_cli": "Установка vt-cli...",
        "verify_success": "vt.exe успешно проверен и установлен!",
        "verify_fail": "Ошибка проверки: {e}",
        "hash_warning_title": "Неизвестный хэш файла",
        "hash_warning_text": "SHA-256 хэш этого файла ({hash}) не совпадает с официальными релизами vt-cli.\n\nВы хотите использовать этот файл на свой страх и риск?",
        "btn_yes": "Да, я доверяю",
        "btn_no": "Отмена",
        "btn_close": "Закрыть",
        "btn_save": "Сохранить настройки",
        "api_saved": "Настройки успешно сохранены!",
        "link_copied": "Ссылка скопирована в буфер обмена!",
        "scan_in_progress": "ИДЕТ СКАНИРОВАНИЕ",
        "drag_drop_text": "Нажмите здесь для выбора файла на ПК",
        "btn_select_file": "Выбрать файл для сканирования",
        "btn_scan": "Сканировать",
        "api_key_missing": "API-ключ отсутствует! Пожалуйста, настройте его в Настройках.",
        "api_key_invalid_err": "Ошибка авторизации. Проверьте правильность API-ключа.",
        "computing_hash": "Вычисление SHA-256 хэша файла...",
        "checking_vt": "Проверка файла в базе данных VirusTotal...",
        "uploading_file": "Файл не найден в базе. Загрузка файла...",
        "upload_progress": "Загрузка: {percent}% ({current:.2f}/{total:.2f} МБ)",
        "waiting_analysis": "Ожидание завершения анализа на сервере...",
        "opening_report": "Открытие отчета в браузере...",
        "scan_success": "Сканирование завершено!",
        "scan_failed": "Ошибка сканирования: {e}",
        "results_summary": "Результаты сканирования",
        "stats_malicious": "Вредоносные",
        "stats_suspicious": "Подозрительные",
        "stats_harmless": "Безвредные",
        "stats_undetected": "Не обнаруженные",
        "verdict_safe": "БЕЗОПАСНО: Ни один антивирус не обнаружил угроз.",
        "verdict_suspicious": "ПОДОЗРИТЕЛЬНО: {suspicious} антивирус(ов) выявили угрозу.",
        "verdict_malicious": "ОПАСНО: Файл помечен как вредоносный ({malicious} антивирус(ов))!",
        "btn_open_web": "Открыть веб-отчет",
        "btn_back": "Назад к сканеру",
        "detections_title": "Вердикты антивирусов",
        "show_all_engines": "Показать все антивирусы ({count})",
        "hide_all_engines": "Скрыть все антивирусы",
        "column_engine": "Антивирус",
        "column_category": "Категория",
        "column_result": "Вердикт",
        "column_method": "Метод",
        "file_details": "Детали файла",
        "file_name": "Имя файла",
        "file_size": "Размер файла",
        "file_hash": "SHA-256",
        "unknown": "Неизвестно"
    }
}

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

def get_app_lang():
    """Determines application language (RU or EN)."""
    env_vars = load_env_vars()
    saved_lang = env_vars.get("LANGUAGE")
    if saved_lang in ("ru", "en"):
        return saved_lang
    try:
        lang = None
        for env_var in ('LANG', 'LC_ALL', 'LC_CTYPE', 'LANGUAGE'):
            val = os.environ.get(env_var)
            if val:
                lang = val
                break
        if not lang:
            try:
                lang, _ = locale.getlocale()
            except Exception:
                pass
        return "ru" if lang and lang.lower().startswith("ru") else "en"
    except Exception:
        return "en"
