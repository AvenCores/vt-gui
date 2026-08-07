import os
import json
import threading
import flet as ft

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
    from .config import STRINGS

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
