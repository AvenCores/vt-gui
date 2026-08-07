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


def build_history_view(lang, page, on_back, on_rescan, on_open_in_app=None):
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

        def on_rescan_click(e, path=file_path, rt=record_type, lt=lookup_type, q=query, rec=record):
            if rt == "lookup":
                on_rescan(rec)
            elif path and os.path.exists(path):
                on_rescan(path)
            else:
                def open_report_from_missing(e_or):
                    page.pop_dialog()
                    on_open_report_click(e_or, rec=rec)

                display_path = path if path else filename
                btn_controls = []
                if rec.get("results") or rec.get("sha256"):
                    btn_controls.append(
                        ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.ASSESSMENT_ROUNDED, size=18),
                                ft.Text(STRINGS[lang].get("history_open_report_title", "Открыть отчет"), weight=ft.FontWeight.W_600)
                            ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                            on_click=open_report_from_missing,
                            bgcolor="#008DDA",
                            color="#FFFFFF",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                            width=440
                        )
                    )
                btn_controls.append(
                    ft.TextButton(
                        content=ft.Text(STRINGS[lang].get("btn_close", "Закрыть"), color="#94A3B8", size=13),
                        on_click=lambda _: page.pop_dialog(),
                        width=440
                    )
                )

                missing_dlg = ft.AlertDialog(
                    title=ft.Row([
                        ft.Icon(ft.Icons.WARNING_ROUNDED, color="#F59E0B", size=22),
                        ft.Text(
                            STRINGS[lang].get("file_not_found_title", "Файл не найден"),
                            color="#FFFFFF",
                            weight=ft.FontWeight.BOLD
                        )
                    ], spacing=8),
                    content=ft.Container(
                        width=440,
                        content=ft.Column([
                            ft.Text(
                                STRINGS[lang].get(
                                    "file_not_found_desc",
                                    "Файл по пути «{path}» был удален или перемещен. Повторное сканирование невозможно."
                                ).format(path=display_path),
                                color="#E2E8F0",
                                size=13
                            ),
                            ft.Container(height=14),
                            ft.Column(btn_controls, spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                        ], tight=True)
                    ),
                    actions_padding=ft.Padding(0, 0, 0, 0),
                    content_padding=ft.Padding(left=24, right=24, top=20, bottom=20),
                    bgcolor="#151E33"
                )
                page.show_dialog(missing_dlg)

        def on_web_report(e, rt=record_type, lt=lookup_type, q=query, h=sha256):
            if rt == "lookup":
                if lt == "domain":
                    webbrowser.open(f"https://www.virustotal.com/gui/domain/{q}")
                elif lt == "ip":
                    webbrowser.open(f"https://www.virustotal.com/gui/ip/{q}")
                elif lt in ("url", "search"):
                    webbrowser.open(f"https://www.virustotal.com/gui/search/{q}")
            elif h:
                webbrowser.open(f"https://www.virustotal.com/gui/file/{h}")

        def on_open_report_click(e, rec=record):
            def open_in_browser(e_b):
                page.pop_dialog()
                on_web_report(
                    e_b,
                    rt=rec.get("type", "file"),
                    lt=rec.get("lookup_type", ""),
                    q=rec.get("query", ""),
                    h=rec.get("sha256", "")
                )

            def open_in_app(e_a):
                page.pop_dialog()
                if rec.get("results"):
                    if on_open_in_app:
                        on_open_in_app(rec)
                else:
                    def confirm_browser(e_cb):
                        page.pop_dialog()
                        on_web_report(
                            e_cb,
                            rt=rec.get("type", "file"),
                            lt=rec.get("lookup_type", ""),
                            q=rec.get("query", ""),
                            h=rec.get("sha256", "")
                        )

                    no_res_dlg = ft.AlertDialog(
                        title=ft.Text(
                            STRINGS[lang].get("history_open_report_title", "Открыть отчет"),
                            color="#FFFFFF",
                            weight=ft.FontWeight.BOLD
                        ),
                        content=ft.Container(
                            width=420,
                            content=ft.Text(
                                STRINGS[lang].get("history_no_local_results", "Для этой записи нет сохраненных локальных данных отчета."),
                                color="#E2E8F0",
                                size=13
                            )
                        ),
                        actions=[
                            ft.TextButton(
                                STRINGS[lang].get("btn_close", "Закрыть"),
                                on_click=lambda _: page.pop_dialog()
                            ),
                            ft.ElevatedButton(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.LANGUAGE_ROUNDED, size=16),
                                    ft.Text(STRINGS[lang].get("btn_open_in_browser", "В браузере"))
                                ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                                on_click=confirm_browser,
                                bgcolor="#008DDA",
                                color="#FFFFFF",
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                            )
                        ],
                        actions_alignment=ft.MainAxisAlignment.END,
                        bgcolor="#151E33"
                    )
                    page.show_dialog(no_res_dlg)

            dlg = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.ASSESSMENT_ROUNDED, color="#00F0FF", size=22),
                    ft.Text(
                        STRINGS[lang].get("history_open_report_title", "Открыть отчет"),
                        color="#FFFFFF",
                        weight=ft.FontWeight.BOLD
                    )
                ], spacing=8),
                content=ft.Container(
                    width=420,
                    content=ft.Column([
                        ft.Text(
                            STRINGS[lang].get("history_open_report_desc", "Выберите, где вы хотите открыть отчет:"),
                            color="#E2E8F0",
                            size=13
                        ),
                        ft.Container(height=12),
                        ft.Row([
                            ft.ElevatedButton(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.DESKTOP_WINDOWS_ROUNDED, size=18),
                                    ft.Text(STRINGS[lang].get("btn_open_in_app", "В программе"), weight=ft.FontWeight.W_600)
                                ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                                on_click=open_in_app,
                                bgcolor="#008DDA",
                                color="#FFFFFF",
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                                expand=True
                            ),
                            ft.ElevatedButton(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.LANGUAGE_ROUNDED, size=18),
                                    ft.Text(STRINGS[lang].get("btn_open_in_browser", "В браузере"), weight=ft.FontWeight.W_600)
                                ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                                on_click=open_in_browser,
                                bgcolor="#1E293B",
                                color="#00F0FF",
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                    side=ft.BorderSide(1, "#00F0FF")
                                ),
                                expand=True
                            )
                        ], spacing=10)
                    ], alignment=ft.MainAxisAlignment.CENTER, tight=True)
                ),
                actions=[
                    ft.TextButton(STRINGS[lang].get("btn_cancel", "Отмена"), on_click=lambda _: page.pop_dialog())
                ],
                actions_alignment=ft.MainAxisAlignment.END,
                bgcolor="#151E33"
            )
            page.show_dialog(dlg)

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
                            icon=ft.Icons.REFRESH_ROUNDED,
                            icon_color="#00F0FF",
                            icon_size=18,
                            tooltip=STRINGS[lang]["history_rescan"],
                            on_click=on_rescan_click,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ASSESSMENT_ROUNDED,
                            icon_color="#00F0FF",
                            icon_size=18,
                            tooltip=STRINGS[lang].get("history_open_report_title", STRINGS[lang]["btn_web_report"]),
                            on_click=on_open_report_click,
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

    # Animated Header Back Action
    back_icon = ft.Icon(
        ft.Icons.ARROW_BACK_ROUNDED,
        color="#FFFFFF",
        size=22,
        offset=ft.Offset(0, 0),
        animate_offset=ft.Animation(50, ft.AnimationCurve.EASE_OUT)
    )

    def handle_back_click(e):
        back_icon.offset = ft.Offset(-0.25, 0)
        back_button_wrapper.scale = 0.90
        page.update()
        
        def run_back():
            import time
            time.sleep(0.04)
            on_back()
            
        import threading
        threading.Thread(target=run_back, daemon=True).start()

    back_button_wrapper = ft.Container(
        content=back_icon,
        padding=6,
        border_radius=20,
        scale=1.0,
        animate_scale=ft.Animation(50, ft.AnimationCurve.EASE_OUT),
        on_click=handle_back_click,
        tooltip=STRINGS[lang].get("btn_back", "Back"),
        ink=True
    )

    # Header
    header = ft.Row([
        back_button_wrapper,
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
