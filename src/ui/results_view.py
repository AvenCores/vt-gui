import flet as ft
import webbrowser
import os
from ..config import STRINGS
from .theme import make_stat_card, make_file_details_card, make_engine_row

def build_results_view(current_scan_results, selected_target_file, last_completed_sha256, lang, back_to_scanner, page):
    """Builds the results dashboard, showing antivirus detections, stats, and a full engine list."""
    
    # Helper to parse the V3 and CLI results format
    def get_stats_and_results(data_dict):
        data = data_dict.get("data", {})
        attributes = data.get("attributes")
        if attributes:
            stats = attributes.get("last_analysis_stats")
            results = attributes.get("last_analysis_results")
            names = attributes.get("names", [])
            size = attributes.get("size", 0)
            return stats, results, names, size
            
        if isinstance(data_dict, list) and len(data_dict) > 0:
            data_dict = data_dict[0]
            
        stats = data_dict.get("last_analysis_stats")
        results = data_dict.get("last_analysis_results")
        names = data_dict.get("names", [])
        size = 0
        if not names and "attributes" in data_dict:
            attrs = data_dict.get("attributes", {})
            stats = stats or attrs.get("last_analysis_stats")
            results = results or attrs.get("last_analysis_results")
            names = attrs.get("names", [])
            size = attrs.get("size", 0)
        else:
            size = data_dict.get("size", 0)
            
        return stats, results, names, size

    stats, results_dict, names, size = get_stats_and_results(current_scan_results)
    
    filename = selected_target_file if selected_target_file else "Unknown_File"
    if names:
        filename = names[0]
    else:
        filename = os.path.basename(filename)
        
    malicious = stats.get("malicious", 0) if stats else 0
    suspicious = stats.get("suspicious", 0) if stats else 0
    harmless = stats.get("harmless", 0) if stats else 0
    undetected = stats.get("undetected", 0) if stats else 0
    
    # 1. Verdict Bar Banner
    if malicious > 0:
        banner_text = STRINGS[lang]["verdict_malicious"].format(malicious=malicious)
        banner_color = "#FF3131"
        banner_icon = ft.Icons.GPP_BAD_ROUNDED
    elif suspicious > 0:
        banner_text = STRINGS[lang]["verdict_suspicious"].format(suspicious=suspicious)
        banner_color = "#FFD700"
        banner_icon = ft.Icons.WARNING_ROUNDED
    else:
        banner_text = STRINGS[lang]["verdict_safe"]
        banner_color = "#10B981"
        banner_icon = ft.Icons.CHECK_CIRCLE_ROUNDED
        
    verdict_banner = ft.Container(
        content=ft.Row([
            ft.Icon(banner_icon, color="#FFFFFF", size=22),
            ft.Text(banner_text, color="#FFFFFF", size=14, weight=ft.FontWeight.BOLD)
        ], spacing=10),
        bgcolor=banner_color,
        padding=15,
        border_radius=12,
        shadow=ft.BoxShadow(blur_radius=8, color="#000000", offset=ft.Offset(0, 2))
    )
    
    # 2. File details card
    details_card = make_file_details_card(filename, size, last_completed_sha256, STRINGS, lang)
    
    # 3. Quick Stats row
    stats_row = ft.Row(
        [
            make_stat_card(STRINGS[lang]["stats_malicious"], malicious, "#FF3131", ft.Icons.REPORT_PROBLEM_ROUNDED),
            make_stat_card(STRINGS[lang]["stats_suspicious"], suspicious, "#FFD700", ft.Icons.WARNING_AMBER_ROUNDED),
            make_stat_card(STRINGS[lang]["stats_harmless"], harmless, "#39FF14", ft.Icons.CHECK_CIRCLE_ROUNDED),
            make_stat_card(STRINGS[lang]["stats_undetected"], undetected, "#94A3B8", ft.Icons.HELP_OUTLINE_ROUNDED)
        ],
        spacing=10,
        alignment=ft.MainAxisAlignment.SPACE_EVENLY
    )
    
    # 4. Action Buttons
    report_url = f"https://www.virustotal.com/gui/file/{last_completed_sha256}"
    actions_row = ft.Row(
        [
            ft.ElevatedButton(
                content=STRINGS[lang]["btn_back"],
                icon=ft.Icons.ARROW_BACK_ROUNDED,
                icon_color="#FFFFFF",
                color="#FFFFFF",
                bgcolor="#1E293B",
                on_click=back_to_scanner,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            ),
            ft.ElevatedButton(
                content=STRINGS[lang]["btn_open_web"],
                icon=ft.Icons.OPEN_IN_BROWSER_ROUNDED,
                icon_color="#FFFFFF",
                color="#FFFFFF",
                bgcolor="#008DDA",
                on_click=lambda _: webbrowser.open(report_url),
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            )
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )
    
    # 5. Detections details list
    detections_list = ft.Column(spacing=5, expand=True)
    
    # Filter detections
    mal_susp_list = []
    clean_list = []
    if results_dict:
        for engine, info in results_dict.items():
            category = info.get("category", "undetected")
            res = info.get("result")
            method = info.get("method", "unknown")
            if category in ("malicious", "suspicious"):
                mal_susp_list.append((engine, category, res, method))
            else:
                clean_list.append((engine, category, res, method))
                
    # Populate detections column
    if mal_susp_list:
        detections_list.controls.append(
            ft.Text(f"{STRINGS[lang]['detections_title']} ({len(mal_susp_list)})", size=16, weight=ft.FontWeight.BOLD, color="#FFFFFF")
        )
        for engine, category, res, method in mal_susp_list:
            detections_list.controls.append(make_engine_row(engine, category, res, method))
    else:
        detections_list.controls.append(
            ft.Text(STRINGS[lang]["verdict_safe"], size=14, color="#94A3B8")
        )
        
    # Toggleable full engines list
    full_list_column = ft.Column(spacing=5, visible=False)
    for engine, category, res, method in sorted(clean_list + mal_susp_list, key=lambda x: x[0].lower()):
        full_list_column.controls.append(make_engine_row(engine, category, res, method))
        
    toggle_button = ft.Ref[ft.TextButton]()
    
    def toggle_full_list(e):
        full_list_column.visible = not full_list_column.visible
        if full_list_column.visible:
            toggle_button.current.content = STRINGS[lang]["hide_all_engines"]
            toggle_button.current.icon = ft.Icons.KEYBOARD_ARROW_UP_ROUNDED
        else:
            toggle_button.current.content = STRINGS[lang]["show_all_engines"].format(count=len(clean_list) + len(mal_susp_list))
            toggle_button.current.icon = ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED
        page.update()
        
    total_engines_count = len(clean_list) + len(mal_susp_list)
    show_all_btn = ft.TextButton(
        ref=toggle_button,
        content=STRINGS[lang]["show_all_engines"].format(count=total_engines_count),
        icon=ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED,
        icon_color="#00F0FF",
        style=ft.ButtonStyle(color="#00F0FF"),
        on_click=toggle_full_list
    )
    
    return ft.ListView(
        [
            verdict_banner,
            ft.Container(height=10),
            details_card,
            stats_row,
            ft.Divider(color="#1E293B"),
            actions_row,
            ft.Divider(color="#1E293B"),
            detections_list,
            ft.Container(height=10),
            show_all_btn,
            full_list_column
        ],
        spacing=10,
        expand=True
    )
