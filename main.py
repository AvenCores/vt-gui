import json
import os
import sys
import threading
import time
import webbrowser
import flet as ft

from src.config import (
    load_env_vars,
    write_env_var,
    get_api_key,
    get_app_lang,
    STRINGS
)
from src.cli_manager import (
    check_installed_binary,
    get_temp_bin_path,
    process_selected_binary,
    compute_sha256,
    download_and_install_cli
)
from src.vt_api import (
    check_file_exists_direct,
    check_file_exists_vt
)
from src.ui.install_view import build_install_view
from src.ui.scanner_view import build_scanner_view
from src.ui.scanning_view import build_scanning_view
from src.ui.results_view import build_results_view
from src.ui.settings_dialog import open_settings

# Parse CLI arguments for context-menu invocation
init_file_path = None
if len(sys.argv) > 1:
    files = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
    if files:
        init_file_path = os.path.normpath(files[0])

class ProgressThrottler:
    """Limits UI updates frequency during uploads."""
    def __init__(self, interval=0.15):
        self.interval = interval
        self.last_update = 0
        
    def should_update(self):
        now = time.time()
        if now - self.last_update >= self.interval:
            self.last_update = now
            return True
        return False

def main(page: ft.Page):
    # Load and sync API key from ~/.vt.toml on startup
    get_api_key()
    
    current_lang = get_app_lang()
    
    # Initialize and register clipboard service
    clipboard_service = ft.Clipboard()
    
    # Page setup
    page.title = STRINGS[current_lang]["app_title"]
    page.theme_mode = ft.ThemeMode.DARK
    page.window.icon = "icon.ico"
    page.window_width = 800
    page.window_height = 700
    page.window_min_width = 650
    page.window_min_height = 600
    page.padding = 0
    
    # Use system font to prevent network loading and font layout shifts (jumping)
    page.theme = ft.Theme(font_family="Segoe UI")
    
    # State variables
    app_state = "scanner"  # scanner, scans, install_cli
    active_scans = []
    current_tab_index = 0
    
    # State for lookup tabs
    active_scanner_tab_index = 0
    search_states = {
        "url": {"input": "", "status": "idle", "results": None, "error": None},
        "domain": {"input": "", "status": "idle", "results": None, "error": None},
        "ip": {"input": "", "status": "idle", "results": None, "error": None},
        "search": {"input": "", "status": "idle", "results": None, "error": None}
    }
    
    install_status_text = ft.Text("", size=14, color="#94A3B8")
    install_progress_bar = ft.ProgressBar(value=0, color="#00F0FF", bgcolor="#334155", height=6, visible=False)
    
    # Temporary variables for installer verification
    selected_installer_data = None
    selected_installer_hash = None
    
    # Helper to show alerts
    def show_alert(title, text):
        dlg = ft.AlertDialog(
            title=ft.Text(title, color="#FFFFFF", weight=ft.FontWeight.BOLD),
            content=ft.Text(text, color="#E2E8F0"),
            actions=[ft.TextButton(STRINGS[current_lang]["btn_close"], on_click=lambda _: page.pop_dialog())],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#1E293B"
        )
        page.show_dialog(dlg)

    # Helper to create social links in footer
    def make_social_link(icon_url, dest_url, tooltip):
        img = ft.Image(
            src=icon_url,
            width=20,
            height=20,
            color="#94A3B8"
        )
        
        def on_hover(e):
            img.color = "#00F0FF" if e.data == "true" else "#94A3B8"
            img.update()
            
        return ft.Container(
            content=img,
            tooltip=tooltip,
            on_click=lambda _: webbrowser.open(dest_url),
            on_hover=on_hover,
            padding=5,
            border_radius=4
        )

    # Helper to render lookup details
    def build_lookup_results_view(data_dict, item_type, item_id):
        stats = data_dict.get("last_analysis_stats", {})
        results = data_dict.get("last_analysis_results", {})
        
        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        harmless = stats.get("harmless", 0)
        undetected = stats.get("undetected", 0)
        
        if malicious > 0:
            banner_text = STRINGS[current_lang]["verdict_malicious"].format(malicious=malicious)
            banner_color = "#FF3131"
            banner_icon = ft.Icons.GPP_BAD_ROUNDED
        elif suspicious > 0:
            banner_text = STRINGS[current_lang]["verdict_suspicious"].format(suspicious=suspicious)
            banner_color = "#FFD700"
            banner_icon = ft.Icons.WARNING_ROUNDED
        else:
            banner_text = STRINGS[current_lang]["verdict_safe"]
            banner_color = "#10B981"
            banner_icon = ft.Icons.CHECK_CIRCLE_ROUNDED
            
        verdict_banner = ft.Container(
            content=ft.Row([
                ft.Icon(banner_icon, color="#FFFFFF", size=20),
                ft.Text(banner_text, color="#FFFFFF", size=13, weight=ft.FontWeight.BOLD)
            ], spacing=8),
            bgcolor=banner_color,
            padding=12,
            border_radius=10
        )
        
        from src.ui.theme import make_stat_card
        stats_row = ft.Row(
            [
                make_stat_card(STRINGS[current_lang]["stats_malicious"], malicious, "#FF3131", ft.Icons.REPORT_PROBLEM_ROUNDED),
                make_stat_card(STRINGS[current_lang]["stats_suspicious"], suspicious, "#FFD700", ft.Icons.WARNING_AMBER_ROUNDED),
                make_stat_card(STRINGS[current_lang]["stats_harmless"], harmless, "#39FF14", ft.Icons.CHECK_CIRCLE_ROUNDED),
                make_stat_card(STRINGS[current_lang]["stats_undetected"], undetected, "#94A3B8", ft.Icons.HELP_OUTLINE_ROUNDED)
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY
        )
        
        details_items = [
            ft.Row([ft.Text(STRINGS[current_lang]["lbl_type"], color="#94A3B8", size=12), ft.Text(item_type.upper(), color="#FFFFFF", size=12, weight=ft.FontWeight.BOLD)]),
            ft.Row([ft.Text(STRINGS[current_lang]["lbl_target"], color="#94A3B8", size=12), ft.Text(item_id, color="#FFFFFF", size=12, weight=ft.FontWeight.BOLD)])
        ]
        
        if item_type == "domain":
            registrar = data_dict.get("registrar")
            if registrar:
                details_items.append(ft.Row([ft.Text(STRINGS[current_lang]["lbl_registrar"], color="#94A3B8", size=12), ft.Text(registrar, color="#FFFFFF", size=12)]))
            reputation = data_dict.get("reputation")
            if reputation is not None:
                details_items.append(ft.Row([ft.Text(STRINGS[current_lang]["lbl_reputation"], color="#94A3B8", size=12), ft.Text(str(reputation), color="#FFFFFF", size=12)]))
        elif item_type == "ip":
            reputation = data_dict.get("reputation")
            if reputation is not None:
                details_items.append(ft.Row([ft.Text(STRINGS[current_lang]["lbl_reputation"], color="#94A3B8", size=12), ft.Text(str(reputation), color="#FFFFFF", size=12)]))
                
        details_card = ft.Container(
            content=ft.Column(details_items, spacing=6),
            padding=15,
            border=ft.Border.all(1, "#2E3C56"),
            border_radius=12,
            bgcolor="#151E33"
        )
        
        from src.ui.theme import make_engine_row
        detections_list = ft.Column(spacing=5)
        mal_susp_list = []
        clean_list = []
        if results:
            for engine, info in results.items():
                category = info.get("category", "undetected")
                res = info.get("result")
                method = info.get("method", "unknown")
                if category in ("malicious", "suspicious"):
                    mal_susp_list.append((engine, category, res, method))
                else:
                    clean_list.append((engine, category, res, method))
                    
        if mal_susp_list:
            detections_list.controls.append(
                ft.Text(f"{STRINGS[current_lang]['detections_title']} ({len(mal_susp_list)})", size=15, weight=ft.FontWeight.BOLD, color="#FFFFFF")
            )
            for engine, category, res, method in mal_susp_list:
                detections_list.controls.append(make_engine_row(engine, category, res, method))
        else:
            detections_list.controls.append(
                ft.Text(STRINGS[current_lang]["verdict_safe"], size=13, color="#94A3B8")
            )
            
        if item_type == "domain":
            web_url = f"https://www.virustotal.com/gui/domain/{item_id}"
        elif item_type == "ip":
            web_url = f"https://www.virustotal.com/gui/ip/{item_id}"
        elif item_type == "url":
            url_id = data_dict.get("_id", "")
            web_url = f"https://www.virustotal.com/gui/url/{url_id}"
            
        web_btn = ft.ElevatedButton(
            content=ft.Text(STRINGS[current_lang]["btn_open_web"]),
            icon=ft.Icons.OPEN_IN_BROWSER_ROUNDED,
            on_click=lambda _: webbrowser.open(web_url),
            bgcolor="#008DDA",
            color="#FFFFFF",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        return ft.Column(
            [
                verdict_banner,
                ft.Container(height=5),
                details_card,
                stats_row,
                ft.Row([web_btn], alignment=ft.MainAxisAlignment.END),
                ft.Divider(color="#1E293B"),
                detections_list
            ],
            spacing=10,
            scroll=ft.ScrollMode.ALWAYS,
            expand=True
        )

    # Helper to render Intel search matches
    def build_search_results_view(results_list):
        if not results_list:
            return ft.Container(
                content=ft.Text(STRINGS[current_lang]["no_results"], color="#94A3B8", size=13),
                alignment=ft.Alignment(0, 0)
            )
            
        list_items = []
        for item in results_list:
            item_id = item.get("_id", "Unknown")
            stats = item.get("last_analysis_stats", {})
            malicious = stats.get("malicious", 0)
            undetected = stats.get("undetected", 0)
            total = malicious + undetected + stats.get("suspicious", 0) + stats.get("harmless", 0)
            
            size_bytes = item.get("size", 0)
            size_kb = size_bytes / 1024
            size_str = f"{size_kb:.2f} KB" if size_kb < 1024 else f"{(size_kb/1024):.2f} MB"
            
            sha256 = item.get("sha256", item_id)
            
            def make_download_handler(file_hash):
                def download_sample(e):
                    def run_download_thread():
                        try:
                            vt_path = get_temp_bin_path()
                            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
                            cmd = [vt_path, 'download', file_hash, '-o', downloads_dir]
                            import subprocess
                            proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
                            if proc.returncode == 0:
                                page.show_dialog(
                                    ft.SnackBar(
                                        content=ft.Text(STRINGS[current_lang]["download_success"], color="#FFFFFF"),
                                        bgcolor="#10B981"
                                    )
                                )
                            else:
                                raise ValueError(proc.stderr or proc.stdout)
                        except Exception as ex:
                            err_title = "Error" if current_lang == "en" else "Ошибка"
                            show_alert(err_title, f"Download failed (requires premium API key): {str(ex)}")
                    threading.Thread(target=run_download_thread, daemon=True).start()
                return download_sample
                
            web_url = f"https://www.virustotal.com/gui/file/{sha256}"
            
            item_card = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.ARTICLE_ROUNDED, color="#00F0FF", size=18),
                                ft.Text(item_id, color="#FFFFFF", size=13, weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.ELLIPSIS),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=6
                        ),
                        ft.Text(f"SHA-256: {sha256}", color="#94A3B8", size=10, selectable=True),
                        ft.Row(
                            [
                                ft.Text(f"{STRINGS[current_lang]['lbl_size']} {size_str}", color="#E2E8F0", size=11),
                                ft.Text(f"{STRINGS[current_lang]['lbl_detections']} {malicious}/{total}", color="#FF3131" if malicious > 0 else "#10B981", size=11, weight=ft.FontWeight.W_600)
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Row(
                            [
                                ft.TextButton(
                                    STRINGS[current_lang]["btn_download_sample"],
                                    icon=ft.Icons.DOWNLOAD_ROUNDED,
                                    on_click=make_download_handler(sha256),
                                    style=ft.ButtonStyle(color="#00F0FF")
                                ),
                                ft.TextButton(
                                    STRINGS[current_lang]["btn_web_report"],
                                    icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                                    on_click=lambda _, url=web_url: webbrowser.open(url),
                                    style=ft.ButtonStyle(color="#94A3B8")
                                )
                            ],
                            alignment=ft.MainAxisAlignment.END,
                            spacing=6
                        )
                    ],
                    spacing=6
                ),
                padding=12,
                border=ft.Border.all(1, "#2E3C56"),
                border_radius=10,
                bgcolor="#151E33"
            )
            list_items.append(item_card)
            
        return ft.Column(
            list_items,
            scroll=ft.ScrollMode.ALWAYS,
            expand=True,
            spacing=8
        )

    # Helper to build lookup tab views
    def build_lookup_tab(tab_key, placeholder_text, helper_desc):
        state = search_states[tab_key]
        
        input_field = ft.TextField(
            hint_text=placeholder_text,
            value=state["input"],
            on_submit=lambda e: run_lookup_query(tab_key),
            border_color="#2E3C56",
            focused_border_color="#00F0FF",
            label_style=ft.TextStyle(color="#94A3B8"),
            text_style=ft.TextStyle(color="#E2E8F0"),
            expand=True,
            height=48
        )
        
        def on_input_change(e):
            state["input"] = e.control.value
            
        input_field.on_change = on_input_change
        
        search_btn = ft.IconButton(
            icon=ft.Icons.SEARCH_ROUNDED,
            icon_color="#00F0FF",
            bgcolor="#1E293B",
            on_click=lambda e: run_lookup_query(tab_key),
            height=48,
            width=48
        )
        
        results_area = ft.Container(expand=True)
        
        if state["status"] == "loading":
            results_area.content = ft.Column(
                [
                    ft.ProgressRing(color="#00F0FF", width=36, height=36),
                    ft.Text(STRINGS[current_lang]["querying_vt"], color="#00F0FF", size=13)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            )
        elif state["status"] == "error":
            results_area.content = ft.Column(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color="#EF4444", size=32),
                    ft.Text(state["error"], color="#EF4444", size=13, text_align=ft.TextAlign.CENTER)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            )
        elif state["status"] == "success" and state["results"] is not None:
            if tab_key == "search":
                results_area.content = build_search_results_view(state["results"])
            else:
                results_area.content = build_lookup_results_view(state["results"], tab_key, state["input"].strip())
        else:
            results_area.content = ft.Container(
                content=ft.Text(helper_desc, color="#94A3B8", size=13, text_align=ft.TextAlign.CENTER),
                alignment=ft.Alignment(0, 0)
            )
            
        return ft.Column(
            [
                ft.Row([input_field, search_btn], spacing=10),
                ft.Divider(color="#2E3C56", height=1),
                results_area
            ],
            spacing=10,
            expand=True
        )

    # Async executor for lookup queries
    def run_lookup_query(tab_key):
        state = search_states[tab_key]
        query_val = state["input"].strip()
        if not query_val:
            return
            
        state["status"] = "loading"
        state["error"] = None
        state["results"] = None
        build_ui()
        
        def execute_query():
            try:
                vt_path = get_temp_bin_path()
                if not os.path.exists(vt_path):
                    raise ValueError("vt.exe CLI is not installed.")
                    
                if tab_key == "url":
                    cmd = [vt_path, 'url', query_val, '--format', 'json']
                elif tab_key == "domain":
                    cmd = [vt_path, 'domain', query_val, '--format', 'json']
                elif tab_key == "ip":
                    cmd = [vt_path, 'ip', query_val, '--format', 'json']
                elif tab_key == "search":
                    cmd = [vt_path, 'search', query_val, '--format', 'json']
                    
                import subprocess
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                if proc.returncode != 0:
                    err_msg = proc.stderr or proc.stdout
                    if "You are not authorized" in err_msg:
                        raise ValueError("Your API Key is not authorized for this operation (premium feature required).")
                    raise ValueError(err_msg.strip())
                    
                import json
                data = json.loads(proc.stdout)
                if isinstance(data, list) and len(data) > 0:
                    if tab_key != "search":
                        data = data[0]
                elif isinstance(data, list) and len(data) == 0:
                    data = None
                    
                state["results"] = data
                state["status"] = "success"
            except Exception as ex:
                state["status"] = "error"
                state["error"] = str(ex)
                
            thread_safe_build()
            
        threading.Thread(target=execute_query, daemon=True).start()

    def build_ui():
        nonlocal app_state
        cli_status, cli_hash = check_installed_binary()
        
        # Enforce install view if missing vt.exe
        if cli_status == 'missing' and app_state == "scanner":
            app_state = "install_cli"
            
        page.controls.clear()
        
        # Header Language Switcher
        def change_language(lang_code):
            nonlocal current_lang
            current_lang = lang_code
            write_env_var("LANGUAGE", lang_code)
            page.title = STRINGS[current_lang]["app_title"]
            build_ui()
            
        active_lang_name = "РУ" if current_lang == "ru" else "EN"
        
        language_menu = ft.PopupMenuButton(
            content=ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.LANGUAGE, color="#00F0FF", size=18),
                        ft.Text(active_lang_name, color="#FFFFFF", size=13, weight=ft.FontWeight.W_600),
                        ft.Icon(ft.Icons.ARROW_DROP_DOWN_ROUNDED, color="#94A3B8", size=16),
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                padding=ft.Padding(left=10, right=8, top=6, bottom=6),
                border=ft.Border.all(1, "#2E3C56"),
                border_radius=8,
                bgcolor="#151E33"
            ),
            tooltip="Select Language / Выбрать язык",
            items=[
                ft.PopupMenuItem(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.CHECK_ROUNDED, color="#00F0FF" if current_lang == "ru" else "transparent", size=16),
                            ft.Text("Русский", color="#E2E8F0", size=13),
                        ],
                        spacing=10
                    ),
                    on_click=lambda _: change_language("ru")
                ),
                ft.PopupMenuItem(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.CHECK_ROUNDED, color="#00F0FF" if current_lang == "en" else "transparent", size=16),
                            ft.Text("English", color="#E2E8F0", size=13),
                        ],
                        spacing=10
                    ),
                    on_click=lambda _: change_language("en")
                ),
            ]
        )
        
        # Settings Icon
        settings_button = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            icon_color="#94A3B8",
            on_click=lambda _: open_settings(page, current_lang, build_ui)
        )
        
        # Header Layout
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.SECURITY_ROUNDED, color="#00F0FF", size=30),
                        ft.Column([
                            ft.Text(STRINGS[current_lang]["app_title"], size=20, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                            ft.Text("Powered by VirusTotal V3 API", size=11, color="#94A3B8")
                        ], spacing=1)
                    ]),
                    ft.Row([
                        language_menu,
                        settings_button
                    ], spacing=5)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=ft.Padding(bottom=15),
            border=ft.Border.only(bottom=ft.BorderSide(1, "#1E293B"))
        )
        
        # Central view content switcher
        main_content = ft.Container(expand=True)
        
        if app_state == "install_cli":
            def on_auto_install_click(e):
                install_progress_bar.visible = True
                install_progress_bar.value = 0
                install_status_text.value = STRINGS[current_lang]["installing_cli"]
                page.update()
                
                def run_download():
                    def progress_cb(status_text, progress_val):
                        install_status_text.value = status_text
                        install_progress_bar.value = progress_val
                        thread_safe_update()
                        
                    try:
                        download_and_install_cli(progress_callback=progress_cb)
                        
                        # Verify installation status
                        cli_status, _ = check_installed_binary()
                        if cli_status in ('verified', 'custom'):
                            show_alert(STRINGS[current_lang]["app_title"], STRINGS[current_lang]["verify_success"])
                            nonlocal app_state
                            app_state = "scanner"
                            thread_safe_build()
                        else:
                            raise ValueError("Installation succeeded but verification failed.")
                    except Exception as ex:
                        # Reset progress elements
                        install_progress_bar.visible = False
                        install_status_text.value = ""
                        thread_safe_update()
                        show_alert(STRINGS[current_lang]["verify_fail"].format(e=""), str(ex))
                        
                threading.Thread(target=run_download, daemon=True).start()

            def on_manual_install_click(e):
                on_cli_click(e)
                
            main_content.content = build_install_view(
                cli_status,
                cli_hash,
                current_lang,
                install_status_text,
                install_progress_bar,
                on_auto_install_click,
                on_manual_install_click
            )
        elif app_state == "scans":
            tab_headers = []
            tab_contents = []
            for idx, scan in enumerate(active_scans):
                if scan["status"] == "scanning":
                    tab_content = build_scanning_view(
                        ft.ProgressRing(color="#00F0FF", width=48, height=48),
                        ft.Text(scan["status_text"], size=15, weight=ft.FontWeight.W_600, color="#00F0FF"),
                        ft.ProgressBar(value=scan["progress"], color="#00F0FF", bgcolor="#334155", height=6),
                        current_lang
                    )
                elif scan["status"] == "completed":
                    tab_content = build_results_view(
                        scan["results"],
                        scan["file_path"],
                        scan["sha256"],
                        current_lang,
                        page
                    )
                else:  # failed
                    def make_retry_callback(scan_idx, path):
                        def retry_scan(e):
                            active_scans[scan_idx]["status"] = "scanning"
                            active_scans[scan_idx]["status_text"] = STRINGS[current_lang]["computing_hash"]
                            active_scans[scan_idx]["progress"] = 0.0
                            active_scans[scan_idx]["error"] = None
                            build_ui()
                            threading.Thread(target=run_single_scan_pipeline, args=(scan_idx, path), daemon=True).start()
                        return retry_scan
                        
                    tab_content = ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color="#EF4444", size=48),
                                ft.Text(STRINGS[current_lang]["scan_failed"].format(e=""), size=16, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                                ft.Text(scan["error"], size=14, color="#EF4444", text_align=ft.TextAlign.CENTER),
                                ft.Container(height=10),
                                ft.Row(
                                    [
                                        ft.ElevatedButton(
                                            content=ft.Text("Retry / Повторить"),
                                            icon=ft.Icons.REFRESH_ROUNDED,
                                            on_click=make_retry_callback(idx, scan["file_path"]),
                                            bgcolor="#008DDA",
                                            color="#FFFFFF"
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=15
                        ),
                        alignment=ft.Alignment.CENTER,
                        expand=True
                    )
                
                icon = "⏳"
                if scan["status"] == "completed":
                    stats = scan["results"].get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                    if not stats and isinstance(scan["results"], list) and len(scan["results"]) > 0:
                        stats = scan["results"][0].get("last_analysis_stats", {})
                    malicious = stats.get("malicious", 0)
                    icon = "❌" if malicious > 0 else "✅"
                elif scan["status"] == "failed":
                    icon = "⚠️"
                    
                tab_headers.append(
                    ft.Tab(
                        label=f"{icon} {scan['filename']}"
                    )
                )
                tab_contents.append(
                    ft.Container(content=tab_content, padding=15)
                )
                
            def on_tab_change(e):
                nonlocal current_tab_index
                current_tab_index = int(e.control.selected_index)
                build_ui()
                
            tabs = ft.Tabs(
                selected_index=current_tab_index,
                on_change=on_tab_change,
                length=len(active_scans),
                expand=True,
                content=ft.Column(
                    expand=True,
                    controls=[
                        ft.TabBar(
                            tabs=tab_headers
                        ),
                        ft.TabBarView(
                            expand=True,
                            controls=tab_contents
                        )
                    ]
                )
            )
            
            # Check if current tab is completed and has a hash
            show_web_report_btn = False
            report_url = None
            if active_scans and current_tab_index < len(active_scans):
                current_scan = active_scans[current_tab_index]
                if current_scan["status"] == "completed" and current_scan["sha256"]:
                    show_web_report_btn = True
                    report_url = f"https://www.virustotal.com/gui/file/{current_scan['sha256']}"
            
            def go_back_to_scanner(e):
                nonlocal app_state, active_scans
                app_state = "scanner"
                active_scans = []
                build_ui()
                
            back_btn = ft.ElevatedButton(
                content=ft.Text(STRINGS[current_lang]["btn_back"]),
                icon=ft.Icons.ARROW_BACK_ROUNDED,
                on_click=go_back_to_scanner,
                bgcolor="#1E293B",
                color="#FFFFFF",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            )
            
            # Left side row with back button
            left_actions = ft.Row([back_btn], alignment=ft.MainAxisAlignment.START)
            
            # Right side actions (copy link & open web report)
            right_actions = ft.Row([], alignment=ft.MainAxisAlignment.END, spacing=10)
            
            if show_web_report_btn:
                def open_web_report(e, url=report_url):
                    import webbrowser
                    webbrowser.open(url)
                    
                def copy_web_report_link(e, url=report_url):
                    page.run_task(clipboard_service.set, url)
                    page.show_dialog(
                        ft.SnackBar(
                            content=ft.Text(STRINGS[current_lang]["link_copied"], color="#FFFFFF"),
                            bgcolor="#10B981"
                        )
                    )
                    
                copy_btn = ft.IconButton(
                    icon=ft.Icons.COPY_ROUNDED,
                    icon_color="#00F0FF",
                    tooltip=STRINGS[current_lang]["copy_link_tooltip"],
                    on_click=copy_web_report_link
                )
                
                web_btn = ft.ElevatedButton(
                    content=ft.Text(STRINGS[current_lang]["btn_open_web"]),
                    icon=ft.Icons.OPEN_IN_BROWSER_ROUNDED,
                    on_click=open_web_report,
                    bgcolor="#008DDA",
                    color="#FFFFFF",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                )
                right_actions.controls.extend([copy_btn, web_btn])
            
            top_buttons_row = ft.Row(
                [left_actions, right_actions],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=10
            )
            
            main_content.content = ft.Column(
                [
                    top_buttons_row,
                    tabs
                ],
                expand=True
            )
        else:
            files_view = build_scanner_view(cli_status, cli_hash, current_lang, file_picker_scan, on_scan_click)
            url_view = build_lookup_tab("url", STRINGS[current_lang]["url_placeholder"], STRINGS[current_lang]["url_helper"])
            domain_view = build_lookup_tab("domain", STRINGS[current_lang]["domain_placeholder"], STRINGS[current_lang]["domain_helper"])
            ip_view = build_lookup_tab("ip", STRINGS[current_lang]["ip_placeholder"], STRINGS[current_lang]["ip_helper"])
            search_view = build_lookup_tab("search", STRINGS[current_lang]["search_placeholder"], STRINGS[current_lang]["search_helper"])
            
            def on_active_tab_change(e):
                nonlocal active_scanner_tab_index
                active_scanner_tab_index = int(e.control.selected_index)
                build_ui()
                
            landing_tabs = ft.Tabs(
                selected_index=active_scanner_tab_index,
                on_change=on_active_tab_change,
                length=5,
                expand=True,
                content=ft.Column(
                    expand=True,
                    controls=[
                        ft.TabBar(
                            tabs=[
                                ft.Tab(label=STRINGS[current_lang]["tab_files"], icon=ft.Icons.ATTACH_FILE_ROUNDED),
                                ft.Tab(label=STRINGS[current_lang]["tab_urls"], icon=ft.Icons.LINK_ROUNDED),
                                ft.Tab(label=STRINGS[current_lang]["tab_domains"], icon=ft.Icons.LANGUAGE_ROUNDED),
                                ft.Tab(label=STRINGS[current_lang]["tab_ips"], icon=ft.Icons.CELL_TOWER_ROUNDED),
                                ft.Tab(label=STRINGS[current_lang]["tab_search"], icon=ft.Icons.SEARCH_ROUNDED),
                            ]
                        ),
                        ft.TabBarView(
                            expand=True,
                            controls=[
                                ft.Container(content=files_view, padding=10),
                                ft.Container(content=url_view, padding=10),
                                ft.Container(content=domain_view, padding=10),
                                ft.Container(content=ip_view, padding=10),
                                ft.Container(content=search_view, padding=10),
                            ]
                        )
                    ]
                )
            )
            main_content.content = landing_tabs
            
        # Build footer with social links
        footer = ft.Container(
            content=ft.Row(
                [
                    make_social_link(
                        "https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/youtube.svg",
                        "https://youtube.com/@avencores",
                        "YouTube"
                    ),
                    make_social_link(
                        "https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/telegram.svg",
                        "https://t.me/avencoresyt",
                        "Telegram"
                    ),
                    make_social_link(
                        "https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/github.svg",
                        "https://github.com/AvenCores",
                        "GitHub"
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20
            ),
            padding=ft.Padding(top=10, right=0, bottom=5, left=0),
            alignment=ft.Alignment(0, 0)
        )

        outer_container = ft.Container(
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#0B0F19", "#111827"]
            ),
            expand=True,
            padding=20,
            content=ft.Column(
                [
                    header,
                    ft.Container(height=10),
                    main_content,
                    footer
                ],
                expand=True
            )
        )
        
        page.add(outer_container)
        page.update()

    import asyncio
    _loop = asyncio.get_event_loop()

    def thread_safe_update():
        _loop.call_soon_threadsafe(page.update)

    def thread_safe_build():
        _loop.call_soon_threadsafe(build_ui)

    # ==============================================================================
    # BACKGROUND PIPELINE
    # ==============================================================================
    def run_single_scan_pipeline(idx, file_path):
        throttler = ProgressThrottler(0.15)
        
        def set_scan_status(text, progress_value):
            active_scans[idx]["status_text"] = text
            active_scans[idx]["progress"] = progress_value
            thread_safe_build()

        try:
            # 1. Compute Hash
            set_scan_status(STRINGS[current_lang]["computing_hash"], 0.1)
            sha256 = compute_sha256(file_path)
            if not sha256:
                raise ValueError("Could not compute target file SHA-256 hash.")
            active_scans[idx]["sha256"] = sha256
            
            # 2. Check API Key
            api_key = get_api_key()
            if not api_key:
                raise ValueError(STRINGS[current_lang]["api_key_missing"])
                
            # 3. Check Database
            set_scan_status(STRINGS[current_lang]["checking_vt"], 0.25)
            
            vt_path = get_temp_bin_path()
            if not os.path.exists(vt_path):
                raise ValueError("vt.exe was missing when scan was initiated.")
            existing_info = check_file_exists_vt(vt_path, sha256)
                
            if existing_info:
                # File already scanned! Fetch complete report.
                set_scan_status(STRINGS[current_lang]["scan_success"], 1.0)
                try:
                    web_info = check_file_exists_direct(sha256, api_key)
                    if web_info:
                        existing_info = web_info
                except Exception:
                    pass
                active_scans[idx]["results"] = existing_info
                active_scans[idx]["status"] = "completed"
                thread_safe_build()
                return
                
            # 4. Upload file
            set_scan_status(STRINGS[current_lang]["uploading_file"], 0.4)
            analysis_id = None
            
            vt_path = get_temp_bin_path()
            cmd = [vt_path, 'scan', 'file', file_path]
            import subprocess
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            if proc.returncode != 0:
                raise ValueError(f"vt.exe upload failed: {proc.stderr or proc.stdout}")
            
            stdout_lines = proc.stdout.strip().split('\n')
            for line in stdout_lines:
                if not line.strip():
                    continue
                parts = line.strip().rsplit(' ', 1)
                if len(parts) == 2:
                    analysis_id = parts[1]
                    break
            if not analysis_id and stdout_lines:
                last_line = stdout_lines[-1]
                if "analysis" in last_line:
                    analysis_id = last_line.split('/')[-1]
                        
            if not analysis_id:
                raise ValueError("Could not retrieve analysis ID from VirusTotal.")
                
            if analysis_id.startswith('http'):
                analysis_id = analysis_id.split('/')[-1]
                
            # 5. Poll Analysis status
            set_scan_status(STRINGS[current_lang]["waiting_analysis"], 0.7)
            start_time = time.time()
            
            while True:
                status = None
                vt_path = get_temp_bin_path()
                import subprocess
                status_cmd = [vt_path, 'analysis', analysis_id, '--format', 'json']
                status_proc = subprocess.run(
                    status_cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                if status_proc.returncode == 0:
                    try:
                        data = json.loads(status_proc.stdout)
                        if isinstance(data, list) and len(data) > 0:
                            data = data[0]
                        status = data.get('status')
                    except Exception:
                        pass
                            
                if status == "completed":
                    break
                    
                elapsed = int(time.time() - start_time)
                set_scan_status(f"{STRINGS[current_lang]['waiting_analysis']} ({elapsed}s)...", None)
                time.sleep(5)
                
            # 6. Success! Fetch final file details.
            set_scan_status(STRINGS[current_lang]["scan_success"], 1.0)
            
            final_report = check_file_exists_direct(sha256, api_key)
            if not final_report:
                final_report = check_file_exists_vt(vt_path, sha256)
                    
            if not final_report:
                raise ValueError("Analysis completed, but failed to fetch the file details.")
                
            active_scans[idx]["results"] = final_report
            active_scans[idx]["status"] = "completed"
            thread_safe_build()
            
        except ValueError as ve:
            err_text = str(ve)
            if err_text == "api_key_invalid_err":
                err_text = STRINGS[current_lang]["api_key_invalid_err"]
            active_scans[idx]["status"] = "failed"
            active_scans[idx]["error"] = err_text
            thread_safe_build()
        except Exception as ex:
            active_scans[idx]["status"] = "failed"
            active_scans[idx]["error"] = str(ex)
            thread_safe_build()

    # ==============================================================================
    # FILE PICKER HANDLERS
    # ==============================================================================
    def on_scan_file_selected(files):
        if not files:
            return
            
        nonlocal active_scans, app_state, current_tab_index
        active_scans = []
        current_tab_index = 0
        app_state = "scans"
        
        valid_files = []
        for f in files:
            if not f.path or not os.path.exists(f.path):
                continue
            if os.path.isdir(f.path):
                show_alert("Error / Ошибка", f"Scanning directories is not supported ({os.path.basename(f.path)}). Please choose files.")
                continue
            valid_files.append(f)
            
        if not valid_files:
            app_state = "scanner"
            build_ui()
            return
            
        for f in valid_files:
            active_scans.append({
                "file_path": f.path,
                "filename": os.path.basename(f.path),
                "status": "scanning",
                "status_text": STRINGS[current_lang]["computing_hash"],
                "progress": 0.0,
                "sha256": None,
                "results": None,
                "error": None
            })
            
        build_ui()
        
        # Start scanning for each file in a separate thread
        for idx, scan in enumerate(active_scans):
            threading.Thread(target=run_single_scan_pipeline, args=(idx, scan["file_path"]), daemon=True).start()

    async def on_scan_click(e):
        try:
            files = await file_picker_scan.pick_files(allow_multiple=True)
            on_scan_file_selected(files)
        except Exception as ex:
            show_alert("Error", str(ex))

    def on_cli_file_selected(files):
        nonlocal selected_installer_data, selected_installer_hash
        if not files:
            return
        file_path = files[0].path
        try:
            exe_hash, exe_data = process_selected_binary(file_path)
            selected_installer_data = exe_data
            selected_installer_hash = exe_hash
            
            from src.config import KNOWN_HASHES
            
            if exe_hash in KNOWN_HASHES:
                temp_bin = get_temp_bin_path()
                with open(temp_bin, "wb") as f:
                    f.write(exe_data)
                show_alert(STRINGS[current_lang]["app_title"], STRINGS[current_lang]["verify_success"])
                nonlocal app_state
                app_state = "scanner"
                build_ui()
            else:
                # Custom Hash Warning Dialog
                def approve_custom_binary(e):
                    page.pop_dialog()
                    temp_bin = get_temp_bin_path()
                    with open(temp_bin, "wb") as f:
                        f.write(selected_installer_data)
                    write_env_var(f"APPROVED_VT_HASH_{selected_installer_hash}", "True")
                    show_alert(STRINGS[current_lang]["app_title"], STRINGS[current_lang]["verify_success"])
                    nonlocal app_state
                    app_state = "scanner"
                    build_ui()
                    
                def reject_custom_binary(e):
                    page.pop_dialog()
                    
                dlg = ft.AlertDialog(
                    title=ft.Text(STRINGS[current_lang]["hash_warning_title"], color="#FFFFFF", weight=ft.FontWeight.BOLD),
                    content=ft.Text(STRINGS[current_lang]["hash_warning_text"].format(hash=exe_hash)),
                    actions=[
                        ft.TextButton(STRINGS[current_lang]["btn_no"], on_click=reject_custom_binary),
                        ft.ElevatedButton(STRINGS[current_lang]["btn_yes"], on_click=approve_custom_binary, bgcolor="#008DDA", color="#FFFFFF")
                    ],
                    bgcolor="#151E33"
                )
                page.show_dialog(dlg)
                
        except Exception as ex:
            show_alert(STRINGS[current_lang]["verify_fail"].format(e=""), str(ex))

    async def on_cli_click(e):
        try:
            files = await file_picker_cli.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["zip", "exe"]
            )
            on_cli_file_selected(files)
        except Exception as ex:
            show_alert("Error", str(ex))

    # Initialize file pickers
    file_picker_scan = ft.FilePicker()
    file_picker_cli = ft.FilePicker()
    page.services.extend([file_picker_scan, file_picker_cli, clipboard_service])
    
    build_ui()
    
    # Command line argument autostart scan
    if init_file_path and os.path.exists(init_file_path):
        api_key = get_api_key()
        cli_status, _ = check_installed_binary()
        
        if not api_key:
            show_alert("Error / Ошибка", STRINGS[current_lang]["api_key_missing"])
        elif cli_status == 'missing':
            show_alert("Error / Ошибка", STRINGS[current_lang]["download_instructions_title"])
        else:
            class PseudoFile:
                def __init__(self, path):
                    self.path = path
            on_scan_file_selected([PseudoFile(init_file_path)])

if __name__ == '__main__':
    ft.run(main, assets_dir="assets")
