import flet as ft
import os
import webbrowser
from datetime import datetime

from ...core.config import STRINGS
from ...services.history_service import load_history, delete_scan_record, clear_history

LOOKUP_TYPE_ICONS = {
    "url": ft.Icons.LINK_ROUNDED,
    "domain": ft.Icons.LANGUAGE_ROUNDED,
    "ip": ft.Icons.CELL_TOWER_ROUNDED,
    "search": ft.Icons.SEARCH_ROUNDED,
    "diff": ft.Icons.COMPARE_ARROWS_ROUNDED,
    "yara": ft.Icons.BUG_REPORT_ROUNDED,
}

LOOKUP_TYPE_NAMES = {
    "url": "URL",
    "domain": "Domain",
    "ip": "IP",
    "search": "Search",
    "diff": "File Diff",
    "yara": "YARA Rules",
}


def build_history_view(lang, page, on_back, on_rescan, on_open_in_app=None, on_import_click=None):
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
                ft.Button(STRINGS[lang]["history_clear"], on_click=confirm_clear, bgcolor="#EF4444", color="#FFFFFF"),
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
                        ft.Button(
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
            overlay_holder = [None]

            def close_overlay():
                ov = overlay_holder[0]
                if ov is not None and ov in page.overlay:
                    page.overlay.remove(ov)
                    page.update()
                overlay_holder[0] = None

            def open_in_browser(e_b):
                close_overlay()
                on_web_report(
                    e_b,
                    rt=rec.get("type", "file"),
                    lt=rec.get("lookup_type", ""),
                    q=rec.get("query", ""),
                    h=rec.get("sha256", "")
                )

            def open_in_app(e_a):
                close_overlay()
                if on_open_in_app:
                    on_open_in_app(rec)

            target_name = rec.get("filename") or rec.get("query") or rec.get("sha256", "Report")
            if len(target_name) > 36:
                target_name = target_name[:33] + "..."

            results_data = rec.get("results")
            malicious_count = 0
            if results_data:
                stats = None
                if rec.get("type") == "lookup" and isinstance(results_data, dict):
                    stats = results_data.get("last_analysis_stats")
                elif isinstance(results_data, dict):
                    stats = results_data.get("data", {}).get("attributes", {}).get("last_analysis_stats")
                    if not stats:
                        stats = results_data.get("last_analysis_stats")
                elif isinstance(results_data, list) and len(results_data) > 0:
                    stats = results_data[0].get("last_analysis_stats")

                if isinstance(stats, dict):
                    malicious_count = stats.get("malicious", 0)
            elif rec.get("positives") is not None:
                malicious_count = rec.get("positives", 0)
            elif rec.get("detections") is not None:
                malicious_count = rec.get("detections", 0)

            raw_ts = rec.get("timestamp", 0)
            if isinstance(raw_ts, (int, float)) and raw_ts > 0:
                scan_time_str = datetime.fromtimestamp(raw_ts).strftime("%d.%m.%Y %H:%M")
            else:
                scan_time_str = str(raw_ts) if raw_ts else ""

            raw_sha = rec.get("sha256", "")
            raw_query = rec.get("query", "")
            if raw_sha:
                hash_text = f"SHA-256: {raw_sha[:16]}..." if len(raw_sha) > 16 else f"SHA-256: {raw_sha}"
            elif raw_query and rec.get("type") == "lookup":
                hash_text = f"{rec.get('lookup_type', 'Lookup')}: {raw_query[:20]}"
            else:
                hash_text = ""

            detections_label = STRINGS[lang].get("history_detections", "Обнаружений: {count}").format(count=malicious_count)

            item_info_card = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.INSERT_DRIVE_FILE_ROUNDED, color="#00F0FF", size=22),
                        ft.Column(
                            [
                                ft.Text(target_name, color="#FFFFFF", size=13, weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(hash_text, color="#94A3B8", size=11) if hash_text else ft.Container(),
                                ft.Row(
                                    [
                                        ft.Text(
                                            detections_label,
                                            color="#EF4444" if malicious_count > 0 else "#10B981",
                                            size=11,
                                            weight=ft.FontWeight.W_600
                                        ),
                                        ft.Text(f"• {scan_time_str}" if scan_time_str else "", color="#94A3B8", size=11)
                                    ],
                                    spacing=6
                                )
                            ],
                            spacing=3,
                            expand=True
                        )
                    ],
                    spacing=12
                ),
                padding=ft.Padding(left=14, right=14, top=10, bottom=10),
                bgcolor="#0F172A",
                border=ft.Border.all(1, "#1E293B"),
                border_radius=10
            )

            modal_header = ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Icon(ft.Icons.ASSESSMENT_ROUNDED, color="#00F0FF", size=36),
                            padding=12,
                            bgcolor="#1E2A47",
                            border=ft.Border.all(1.5, "#00F0FF"),
                            shape=ft.BoxShape.CIRCLE
                        ),
                        ft.Text(
                            STRINGS[lang].get("history_open_report_title", "Открыть отчет"),
                            color="#FFFFFF",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            STRINGS[lang].get("history_open_report_desc", "Выберите, где вы хотите открыть отчет:"),
                            color="#94A3B8",
                            size=12,
                            text_align=ft.TextAlign.CENTER
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8
                ),
                padding=ft.Padding(top=6, bottom=6, left=6, right=6),
                alignment=ft.Alignment.CENTER
            )

            open_app_btn = ft.Button(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.DESKTOP_WINDOWS_ROUNDED, size=18, color="#FFFFFF"),
                        ft.Text(STRINGS[lang].get("btn_open_in_app", "В программе"), weight=ft.FontWeight.W_600, color="#FFFFFF")
                    ],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                on_click=open_in_app,
                bgcolor="#008DDA",
                color="#FFFFFF",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                expand=True,
                height=44
            )

            open_browser_btn = ft.Button(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.LANGUAGE_ROUNDED, size=18, color="#00F0FF"),
                        ft.Text(STRINGS[lang].get("btn_open_in_browser", "В браузере"), weight=ft.FontWeight.W_600, color="#00F0FF")
                    ],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                on_click=open_in_browser,
                bgcolor="#1E293B",
                color="#00F0FF",
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    side=ft.BorderSide(1, "#00F0FF")
                ),
                expand=True,
                height=44
            )

            panel = ft.Container(
                width=440,
                bgcolor="#151E33",
                border_radius=14,
                padding=ft.Padding(left=20, right=20, top=20, bottom=16),
                content=ft.Column(
                    [
                        modal_header,
                        item_info_card,
                        ft.Row([open_app_btn, open_browser_btn], spacing=10),
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.TextButton(
                                        STRINGS[lang].get("btn_cancel", "Отмена"),
                                        on_click=lambda _: close_overlay()
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.END
                            ),
                            padding=ft.Padding(top=4)
                        )
                    ],
                    spacing=14,
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
            )

            report_overlay = ft.Container(
                expand=True,
                bgcolor="#88000000",
                alignment=ft.Alignment.CENTER,
                on_click=lambda _: close_overlay(),
                content=panel
            )
            overlay_holder[0] = report_overlay
            page.overlay.append(report_overlay)
            page.update()

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

    import_btn = ft.Button(
        content=ft.Row([
            ft.Icon(ft.Icons.UPLOAD_FILE_ROUNDED, size=16),
            ft.Text(STRINGS[lang].get("btn_import_report", "Import Report"), size=12, weight=ft.FontWeight.W_600)
        ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        on_click=on_import_click,
        bgcolor="#1E293B",
        color="#00F0FF",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    ) if on_import_click else None

    header_controls = [
        back_button_wrapper,
        ft.Text(STRINGS[lang]["tab_history"], size=20, weight=ft.FontWeight.BOLD, color="#FFFFFF", expand=True)
    ]
    if import_btn:
        header_controls.append(import_btn)
    if history:
        header_controls.append(
            ft.TextButton(
                content=ft.Text(STRINGS[lang]["history_clear"], color="#EF4444", size=13),
                icon=ft.Icons.DELETE_SWEEP_ROUNDED,
                icon_color="#EF4444",
                on_click=on_clear_click,
            )
        )

    # Header
    header = ft.Row(header_controls, alignment=ft.MainAxisAlignment.START, spacing=8)

    if not history:
        empty_placeholder = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.HISTORY_ROUNDED, size=64, color="#2E3C56"),
                    ft.Text(STRINGS[lang]["history_empty"], size=16, color="#64748B", text_align=ft.TextAlign.CENTER)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12
            ),
            alignment=ft.Alignment.CENTER,
            expand=True
        )
        content = ft.Column([header, empty_placeholder], spacing=10, expand=True)
    else:
        cards = [make_history_card(record) for record in history]
        content = ft.Column([
            header,
            ft.Container(height=5),
            ft.ListView(cards, spacing=8, expand=True),
        ], expand=True)

    return content
