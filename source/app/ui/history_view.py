import flet as ft
import os
import webbrowser
from datetime import datetime
from ..config import STRINGS
from ..history_manager import load_history, delete_scan_record, clear_history


LOOKUP_TYPE_ICONS = {
    "url": ft.Icons.LINK_ROUNDED,
    "domain": ft.Icons.LANGUAGE_ROUNDED,
    "ip": ft.Icons.CELL_TOWER_ROUNDED,
    "search": ft.Icons.SEARCH_ROUNDED,
}

LOOKUP_TYPE_NAMES = {
    "url": "URL",
    "domain": "Domain",
    "ip": "IP",
    "search": "Search",
}


def build_history_view(lang, page, on_back, on_rescan):
    """Build the scan history view."""
    history = load_history()

    def refresh_view():
        on_back()

    def on_clear_click(e):
        def confirm_clear(e2):
            page.pop_dialog()
            clear_history()
            refresh_view()

        dlg = ft.AlertDialog(
            title=ft.Text(STRINGS[lang]["history_clear"], color="#FFFFFF", weight=ft.FontWeight.BOLD),
            content=ft.Text(STRINGS[lang]["history_clear_confirm"], color="#E2E8F0"),
            actions=[
                ft.TextButton(STRINGS[lang]["btn_no"], on_click=lambda _: page.pop_dialog()),
                ft.ElevatedButton(STRINGS[lang]["history_clear"], on_click=confirm_clear, bgcolor="#EF4444", color="#FFFFFF"),
            ],
            bgcolor="#151E33"
        )
        page.show_dialog(dlg)

    def make_history_card(record):
        status = record.get("status", "unknown")
        record_type = record.get("type", "file")
        filename = record.get("filename", "Unknown")
        file_path = record.get("file_path", "")
        sha256 = record.get("sha256", "")
        lookup_type = record.get("lookup_type", "")
        query = record.get("query", "")
        results = record.get("results")
        timestamp = record.get("timestamp", 0)
        record_id = record.get("id", 0)

        date_str = datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y %H:%M") if timestamp else ""

        # Determine display name and icon
        if record_type == "lookup":
            display_name = query
            item_icon = LOOKUP_TYPE_ICONS.get(lookup_type, ft.Icons.HELP_OUTLINE_ROUNDED)
            item_color = "#00F0FF"
            subtitle = LOOKUP_TYPE_NAMES.get(lookup_type, lookup_type)
        else:
            display_name = filename
            item_icon = ft.Icons.ATTACH_FILE_ROUNDED
            item_color = "#00F0FF"
            subtitle = sha256[:12] + "..." if sha256 else ""

        # Status icon and color
        if status == "completed":
            if results:
                stats = None
                if record_type == "lookup":
                    stats = results.get("last_analysis_stats", {})
                else:
                    stats = results.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                    if not stats and isinstance(results, list) and len(results) > 0:
                        stats = results[0].get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0) if stats else 0
                if malicious > 0:
                    status_icon = ft.Icons.ERROR_ROUNDED
                    status_color = "#EF4444"
                    detections_text = STRINGS[lang]["history_detections"].format(count=malicious)
                else:
                    status_icon = ft.Icons.CHECK_CIRCLE_ROUNDED
                    status_color = "#10B981"
                    detections_text = STRINGS[lang]["history_detections"].format(count=0)
            else:
                status_icon = ft.Icons.CHECK_CIRCLE_ROUNDED
                status_color = "#10B981"
                detections_text = ""
        elif status == "failed":
            status_icon = ft.Icons.WARNING_ROUNDED
            status_color = "#F59E0B"
            detections_text = record.get("error", "")[:50]
        else:
            status_icon = ft.Icons.HELP_OUTLINE_ROUNDED
            status_color = "#94A3B8"
            detections_text = ""

        def on_delete_click(e, rid=record_id):
            delete_scan_record(rid)
            refresh_view()

        def on_rescan_click(e, path=file_path, rt=record_type, lt=lookup_type, q=query):
            if rt == "lookup":
                on_back()
            elif path and os.path.exists(path):
                on_rescan(path)

        def on_web_report(e, rt=record_type, lt=lookup_type, q=query, h=sha256):
            if rt == "lookup":
                if lt == "url":
                    webbrowser.open(f"https://www.virustotal.com/gui/domain/{q}")
                elif lt == "domain":
                    webbrowser.open(f"https://www.virustotal.com/gui/domain/{q}")
                elif lt == "ip":
                    webbrowser.open(f"https://www.virustotal.com/gui/ip/{q}")
                elif lt == "search":
                    webbrowser.open(f"https://www.virustotal.com/search?q={q}")
            elif h:
                webbrowser.open(f"https://www.virustotal.com/gui/file/{h}")

        detail_text = STRINGS[lang]["history_scanned_at"].format(date=date_str)
        if detections_text:
            detail_text += f"  •  {detections_text}"

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(status_icon, color=status_color, size=22),
                    ft.Icon(item_icon, color=item_color, size=16),
                    ft.Column([
                        ft.Text(display_name, size=13, weight=ft.FontWeight.BOLD, color="#FFFFFF", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(subtitle, size=10, color="#64748B", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ], spacing=1, expand=True),
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.LANGUAGE_ROUNDED,
                            icon_color="#94A3B8",
                            icon_size=18,
                            tooltip=STRINGS[lang]["btn_web_report"],
                            on_click=on_web_report,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_ROUNDED,
                            icon_color="#EF4444",
                            icon_size=18,
                            tooltip=STRINGS[lang]["history_delete"],
                            on_click=on_delete_click,
                        ),
                    ], spacing=0),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(detail_text, size=10, color="#64748B"),
            ], spacing=4),
            bgcolor="#151E33",
            border=ft.Border.all(1, "#2E3C56"),
            border_radius=12,
            padding=ft.Padding(left=14, right=10, top=10, bottom=10),
        )

    # Header
    header = ft.Row([
        ft.IconButton(
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            icon_color="#FFFFFF",
            on_click=lambda _: on_back(),
        ),
        ft.Text(STRINGS[lang]["tab_history"], size=20, weight=ft.FontWeight.BOLD, color="#FFFFFF", expand=True),
        ft.TextButton(
            content=ft.Text(STRINGS[lang]["history_clear"], color="#EF4444", size=13),
            icon=ft.Icons.DELETE_SWEEP_ROUNDED,
            icon_color="#EF4444",
            on_click=on_clear_click,
        ) if history else ft.Container(),
    ], alignment=ft.MainAxisAlignment.START)

    if not history:
        content = ft.Column([
            header,
            ft.Container(height=40),
            ft.Icon(ft.Icons.HISTORY_ROUNDED, size=64, color="#2E3C56"),
            ft.Text(STRINGS[lang]["history_empty"], size=16, color="#64748B", text_align=ft.TextAlign.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, expand=True)
    else:
        cards = [make_history_card(record) for record in history]
        content = ft.Column([
            header,
            ft.Container(height=5),
            ft.ListView(cards, spacing=8, expand=True),
        ], expand=True)

    return content
