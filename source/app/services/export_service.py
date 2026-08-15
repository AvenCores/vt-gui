import os
import json
import threading
import uuid
import time
import flet as ft

from ..core.config import STRINGS
from .history_service import save_history, load_history


def export_report_to_path(data_dict, out_path):
    """Export scan report or intelligence report to a specific file path."""
    try:
        dir_name = os.path.dirname(out_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, indent=4, ensure_ascii=False)
        return True, out_path
    except Exception as ex:
        return False, str(ex)


def export_report_to_file(data_dict, file_name, file_format="json"):
    """Export scan report or intelligence report to user Downloads folder."""
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(downloads_dir, exist_ok=True)
    clean_name = "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in file_name)
    out_filename = f"vt_report_{clean_name}.{file_format}"
    out_path = os.path.join(downloads_dir, out_filename)
    return export_report_to_path(data_dict, out_path)


def prompt_export_report(page, data_dict, default_name, lang):
    """Opens native OS file save dialog allowing user to select destination folder and filename."""
    clean_name = "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in default_name)
    suggested_filename = f"vt_report_{clean_name}.json"

    def worker():
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            chosen_path = filedialog.asksaveasfilename(
                title=STRINGS[lang].get("btn_export_report", "Export Report"),
                initialfile=suggested_filename,
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            root.destroy()

            if chosen_path:
                ok, path_or_err = export_report_to_path(data_dict, chosen_path)
                if ok:
                    msg = STRINGS[lang].get("toast_export_success", "Report exported to {file}!").format(file=os.path.basename(chosen_path))
                    page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor="#10B981"))
                else:
                    msg = STRINGS[lang].get("toast_export_fail", "Export failed: {e}").format(e=path_or_err)
                    page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor="#EF4444"))
        except Exception as ex:
            ok, path = export_report_to_file(data_dict, default_name)
            if ok:
                msg = STRINGS[lang].get("toast_export_success", "Report exported to {file}!").format(file=os.path.basename(path))
                page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor="#10B981"))
            else:
                msg = STRINGS[lang].get("toast_export_fail", "Export failed: {e}").format(e=str(ex))
                page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor="#EF4444"))

    threading.Thread(target=worker, daemon=True).start()


def parse_imported_report(data_dict, file_path=""):
    """Parses imported JSON data and converts it to a standard history record structure safely."""
    if not isinstance(data_dict, (dict, list)):
        raise ValueError("Invalid report structure: JSON root must be an object or array.")

    # Handle array of items (e.g. search output or multi-item export)
    if isinstance(data_dict, list):
        if not data_dict:
            raise ValueError("Empty report data.")
        first_item = data_dict[0] if len(data_dict) > 0 and isinstance(data_dict[0], dict) else {}
        item_id = str(first_item.get("_id") or first_item.get("id") or "Search Export")
        return {
            "id": uuid.uuid4().hex[:16],
            "type": "lookup",
            "lookup_type": "search",
            "query": item_id,
            "filename": item_id,
            "status": "completed",
            "results": data_dict,
            "error": None,
            "timestamp": time.time()
        }

    # Extract data object if nested under "data"
    data_obj = data_dict.get("data") if isinstance(data_dict, dict) else None
    if isinstance(data_obj, list) and len(data_obj) > 0 and isinstance(data_obj[0], dict):
        data_obj = data_obj[0]

    if not isinstance(data_obj, dict):
        data_obj = data_dict

    attrs = data_obj.get("attributes") if isinstance(data_obj, dict) else None
    if not isinstance(attrs, dict):
        attrs = data_obj if isinstance(data_obj, dict) else {}

    item_type = str(data_obj.get("_type") or data_obj.get("type") or attrs.get("type", ""))
    item_id = str(data_obj.get("_id") or data_obj.get("id") or attrs.get("id", ""))

    sha256 = ""
    if isinstance(attrs, dict):
        sha256 = str(attrs.get("sha256") or attrs.get("meaningful_name") or "")
    if not sha256 and isinstance(data_dict, dict):
        sha256 = str(data_dict.get("sha256") or "")
    if not sha256 and len(item_id) == 64 and item_type in ("file", ""):
        sha256 = item_id

    names = attrs.get("names", []) if isinstance(attrs, dict) else []
    if not names and isinstance(data_dict, dict):
        names = data_dict.get("names", [])

    meaningful_name = attrs.get("meaningful_name") if isinstance(attrs, dict) else None
    if not meaningful_name and isinstance(data_dict, dict):
        meaningful_name = data_dict.get("meaningful_name")

    if isinstance(names, list) and len(names) > 0 and isinstance(names[0], str):
        filename = names[0]
    elif meaningful_name and isinstance(meaningful_name, str):
        filename = meaningful_name
    elif file_path:
        filename = os.path.basename(file_path)
    else:
        filename = "imported_report"

    if item_type == "file" or sha256:
        return {
            "id": uuid.uuid4().hex[:16],
            "type": "file",
            "filename": filename,
            "file_path": file_path,
            "sha256": sha256 or "",
            "status": "completed",
            "results": data_dict,
            "error": None,
            "timestamp": time.time()
        }

    lookup_type = "search"
    if item_type in ("domain",):
        lookup_type = "domain"
    elif item_type in ("ip_address", "ip"):
        lookup_type = "ip"
    elif item_type in ("url",):
        lookup_type = "url"
    else:
        if item_id and "." in item_id and "/" not in item_id:
            lookup_type = "domain"
        elif item_id and item_id.replace(".", "").isdigit():
            lookup_type = "ip"
        elif item_id and item_id.startswith("http"):
            lookup_type = "url"

    query = item_id or filename

    return {
        "id": uuid.uuid4().hex[:16],
        "type": "lookup",
        "lookup_type": lookup_type,
        "query": query,
        "filename": query,
        "status": "completed",
        "results": data_dict,
        "error": None,
        "timestamp": time.time()
    }


def prompt_import_report(page, lang, on_report_imported):
    """Opens native OS file dialog allowing user to select an exported JSON report to open."""
    def worker():
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            chosen_path = filedialog.askopenfilename(
                title=STRINGS[lang].get("btn_import_report", "Import Report"),
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            root.destroy()

            if chosen_path and os.path.exists(chosen_path):
                importing_msg = STRINGS[lang].get("toast_importing", "Importing report...")
                importing_snack = ft.SnackBar(
                    content=ft.Row([
                        ft.ProgressRing(width=18, height=18, stroke_width=2.5, color="#00F0FF"),
                        ft.Text(importing_msg, color="#FFFFFF", size=13, weight=ft.FontWeight.W_600)
                    ], spacing=10),
                    bgcolor="#1E293B",
                    duration=4000
                )
                page.show_dialog(importing_snack)

                time.sleep(0.05)
                with open(chosen_path, "r", encoding="utf-8") as f:
                    data_dict = json.load(f)

                record = parse_imported_report(data_dict, file_path=chosen_path)

                records = load_history()
                records.insert(0, record)
                save_history(records)

                if on_report_imported:
                    on_report_imported(record)

                msg = STRINGS[lang].get("toast_import_success", "Report imported successfully!")
                page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor="#10B981"))

        except Exception as ex:
            msg = STRINGS[lang].get("toast_import_fail", "Import failed: {e}").format(e=str(ex))
            page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor="#EF4444"))

    threading.Thread(target=worker, daemon=True).start()
