import json
import os
import sys
import threading
import time
import webbrowser
import flet as ft

from app.config import (
    load_env_vars,
    write_env_var,
    get_api_key,
    get_app_lang,
    get_available_langs,
    IS_WINDOWS,
    STRINGS
)
from app.cli_manager import (
    check_installed_binary,
    get_temp_bin_path,
    process_selected_binary,
    compute_sha256,
    download_and_install_cli
)
from app.vt_api import (
    check_file_exists_direct,
    check_file_exists_vt
)
from app.ui.install_view import build_install_view
from app.ui.scanner_view import build_scanner_view
from app.ui.scanning_view import build_scanning_view
from app.ui.results_view import build_results_view
from app.ui.settings_dialog import open_settings
from app.ui.api_key_dialog import open_api_key_dialog
from app.ui.intelligence_view import IntelligenceView
from app.ui.footer import build_footer
from app.services.scan_service import ScanService, resolve_scan_status

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
    # Set window icon — use .ico on Windows, .png on other platforms if available
    icon_path = "icon.ico" if IS_WINDOWS else "icon.png"
    if os.path.exists(os.path.join("assets", icon_path)):
        page.window.icon = icon_path
    page.window_width = 800
    page.window_height = 700
    page.window_min_width = 650
    page.window_min_height = 600
    page.padding = 0

    # Use system font to prevent network loading and font layout shifts (jumping)
    if IS_WINDOWS:
        page.theme = ft.Theme(font_family="Segoe UI")
    elif sys.platform == "darwin":
        page.theme = ft.Theme(font_family="SF Pro Text")
    else:
        page.theme = ft.Theme(font_family="sans-serif")
    
    # State variables
    app_state = "scanner"  # scanner, scans, install_cli
    active_scans = []
    scan_service = None
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

    # Note: Search and threat intelligence lookup views and handlers have been moved to src/ui/intelligence_view.py

    def build_ui():
        nonlocal app_state
        cli_status, cli_hash = check_installed_binary()
        
        # Enforce install view if missing vt CLI
        if cli_status == 'missing' and app_state == "scanner":
            app_state = "install_cli"
            
        page.controls.clear()
        
        # Header Language Switcher
        def change_language(lang_code):
            nonlocal current_lang, scan_service
            current_lang = lang_code
            write_env_var("LANGUAGE", lang_code)
            page.title = STRINGS[current_lang]["app_title"]
            # Re-translate active scan statuses for the new language
            for scan in active_scans:
                if scan["status"] == "scanning":
                    resolve_scan_status(scan, lang_code)
            if scan_service is not None:
                scan_service.current_lang = lang_code
            build_ui()

        available_langs = get_available_langs()
        active_lang_name = dict(available_langs).get(current_lang, current_lang.upper())

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
                            ft.Icon(ft.Icons.CHECK_ROUNDED, color="#00F0FF" if current_lang == code else "transparent", size=16),
                            ft.Text(name, color="#E2E8F0", size=13),
                        ],
                        spacing=10
                    ),
                    on_click=lambda _, c=code: change_language(c)
                )
                for code, name in available_langs
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
                    scan_status_text = ft.Text(scan["status_text"], size=15, weight=ft.FontWeight.W_600, color="#00F0FF")
                    scan_progress_bar = ft.ProgressBar(value=scan["progress"], color="#00F0FF", bgcolor="#334155", height=6)
                    scan["_status_text_widget"] = scan_status_text
                    scan["_progress_bar_widget"] = scan_progress_bar
                    tab_content = build_scanning_view(
                        ft.ProgressRing(color="#00F0FF", width=48, height=48),
                        scan_status_text,
                        scan_progress_bar,
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
                
            back_btn = ft.Button(
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
                
                web_btn = ft.Button(
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
            intel_view = IntelligenceView(search_states, current_lang, show_alert, get_temp_bin_path, thread_safe_build, build_ui, page)
            url_view = intel_view.build_lookup_tab("url", STRINGS[current_lang]["url_placeholder"], STRINGS[current_lang]["url_helper"])
            domain_view = intel_view.build_lookup_tab("domain", STRINGS[current_lang]["domain_placeholder"], STRINGS[current_lang]["domain_helper"])
            ip_view = intel_view.build_lookup_tab("ip", STRINGS[current_lang]["ip_placeholder"], STRINGS[current_lang]["ip_helper"])
            search_view = intel_view.build_lookup_tab("search", STRINGS[current_lang]["search_placeholder"], STRINGS[current_lang]["search_helper"])
            
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
        footer = build_footer(current_lang, page)

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
    # ==============================================================================
    # BACKGROUND PIPELINE
    # ==============================================================================
    # Note: run_single_scan_pipeline logic has been moved to src/services/scan_service.py

    # ==============================================================================
    # FILE PICKER HANDLERS
    # ==============================================================================
    def on_scan_file_selected(files):
        if not files:
            return
            
        nonlocal active_scans, app_state, current_tab_index, scan_service
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
        scan_service = ScanService(active_scans, current_lang, thread_safe_build, show_alert, page)
        for idx, scan in enumerate(active_scans):
            threading.Thread(target=scan_service.run_single_scan_pipeline, args=(idx, scan["file_path"]), daemon=True).start()

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
            
            from app.config import KNOWN_HASHES
            
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
            allowed_exts = ["zip", "exe"] if IS_WINDOWS else ["zip"]
            files = await file_picker_cli.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=allowed_exts
            )
            on_cli_file_selected(files)
        except Exception as ex:
            show_alert("Error", str(ex))

    # Initialize file pickers
    file_picker_scan = ft.FilePicker()
    file_picker_cli = ft.FilePicker()
    page.services.extend([file_picker_scan, file_picker_cli, clipboard_service])

    # Ctrl+V handler: paste file path from clipboard
    async def on_paste_keyboard(e):
        if e.key == "v" and (e.ctrl or e.meta):
            try:
                clip_text = clipboard_service.get()
                if not clip_text or not clip_text.strip():
                    return
                paths = [p.strip().strip('"').strip("'") for p in clip_text.splitlines() if p.strip()]
                valid = [p for p in paths if os.path.exists(p) and not os.path.isdir(p)]
                if valid:
                    class PseudoFile:
                        def __init__(self, path):
                            self.path = path
                    on_scan_file_selected([PseudoFile(p) for p in valid])
            except Exception:
                pass

    page.on_keyboard_event = on_paste_keyboard
    
    build_ui()

    # Show API key setup dialog on first launch if no key is configured
    if not get_api_key():
        def on_api_key_saved():
            build_ui()
        open_api_key_dialog(page, current_lang, on_api_key_saved)
    elif init_file_path and os.path.exists(init_file_path):
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
    # When frozen by PyInstaller, set CWD to the bundle dir so assets/ is found
    if getattr(sys, 'frozen', False):
        os.chdir(sys._MEIPASS)
    ft.run(main, assets_dir="assets")
