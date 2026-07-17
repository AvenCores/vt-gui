import os
import json
import time
from .config import _get_config_dir

HISTORY_FILE = "scan_history.json"
MAX_RECORDS = 100


def _get_history_path():
    return os.path.join(_get_config_dir(), HISTORY_FILE)


def load_history():
    """Load scan history from JSON file. Returns list of records, newest first."""
    path = _get_history_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            records = json.load(f)
        records.sort(key=lambda r: r.get("timestamp", 0), reverse=True)
        return records
    except Exception:
        return []


def save_history(records):
    """Save scan history to JSON file."""
    path = _get_history_path()
    try:
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        records.sort(key=lambda r: r.get("timestamp", 0), reverse=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def add_scan_record(filename, file_path, sha256, status, results=None, error=None):
    """Add a completed scan record to history. Returns the record."""
    record = {
        "id": int(time.time() * 1000),
        "type": "file",
        "filename": filename,
        "file_path": file_path,
        "sha256": sha256,
        "status": status,
        "results": results,
        "error": error,
        "timestamp": time.time(),
    }
    records = load_history()
    records.insert(0, record)
    if len(records) > MAX_RECORDS:
        records = records[:MAX_RECORDS]
    save_history(records)
    return record


def add_lookup_record(lookup_type, query, status, results=None, error=None):
    """Add a completed lookup record (url/domain/ip/search) to history."""
    record = {
        "id": int(time.time() * 1000),
        "type": "lookup",
        "lookup_type": lookup_type,
        "query": query,
        "filename": query,
        "status": status,
        "results": results,
        "error": error,
        "timestamp": time.time(),
    }
    records = load_history()
    records.insert(0, record)
    if len(records) > MAX_RECORDS:
        records = records[:MAX_RECORDS]
    save_history(records)
    return record


def delete_scan_record(record_id):
    """Delete a scan record by its ID."""
    records = load_history()
    records = [r for r in records if r.get("id") != record_id]
    save_history(records)


def clear_history():
    """Clear all scan history."""
    save_history([])
