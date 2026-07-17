import json
import urllib.request
import urllib.error
import subprocess
import sys
import os

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

def check_file_exists_direct(sha256, api_key):
    """Check if the file hash already exists on VirusTotal using HTTP API."""
    url = f"https://www.virustotal.com/api/v3/files/{sha256}"
    req = urllib.request.Request(
        url,
        headers={"x-apikey": api_key, "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        if e.code in (401, 403):
            raise ValueError("api_key_invalid_err")
        raise e
    except Exception:
        return None

def check_file_exists_vt(vt_path, sha256):
    """Check if the file hash already exists on VirusTotal using vt CLI."""
    try:
        cmd = [vt_path, 'file', sha256, '--format', 'json']
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            creationflags=_NO_WINDOW
        )
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            elif isinstance(data, dict):
                return data
    except Exception:
        pass
    return None
