import os
import sys

# ─────────────────────────────────────────────────────────────────────────────
# PyInstaller Subprocess & LD_LIBRARY_PATH Sanitization
# On Linux, PyInstaller sets LD_LIBRARY_PATH to sys._MEIPASS and saves the original
# value into LD_LIBRARY_PATH_ORIG. When launching child processes (e.g. Flet's
# Flutter desktop view executable, VirusTotal CLI binary, etc.), inheriting
# LD_LIBRARY_PATH pointing to _MEIPASS forces host system libraries (such as
# libsecret-1.so.0) to link against incompatible GLib libraries bundled from the
# build runner, causing symbol lookup errors (e.g. undefined symbol: g_variant_builder_init_).
# Restoring the original environment variables ensures all child processes run
# against the native host system libraries.
# ─────────────────────────────────────────────────────────────────────────────
for _var in ("LD_LIBRARY_PATH", "LIBPATH", "DYLD_LIBRARY_PATH"):
    _orig_var = f"{_var}_ORIG"
    if _orig_var in os.environ:
        os.environ[_var] = os.environ[_orig_var]
    elif _var in os.environ and getattr(sys, "frozen", False):
        os.environ.pop(_var, None)

import threading
import flet as ft

from app.core import (
    write_env_var,
    get_api_key,
    get_app_lang,
    get_app_theme,
    set_app_theme,
    IS_WINDOWS,
    STRINGS,
    KNOWN_HASHES,
    init_ssl_context,
)

# Initialize SSL CA certificates configuration for cross-distro compatibility
init_ssl_context()
from app.api import (
    check_installed_binary,
    get_temp_bin_path,
    get_installed_binary_path,
    process_selected_binary,
    download_and_install_cli,
    check_file_exists_direct,
    check_file_exists_vt,
)
from app.services import (
    ScanService,
    resolve_scan_status,
    update_scan_record_results,
    prompt_import_report,
)
from app.utils import safe_copy_to_clipboard
from app.ui import (
    build_header,
    build_footer,
    get_theme_palette,
    build_install_view,
    build_scanner_view,
    build_scanning_view,
    build_results_view,
    build_history_view,
    open_settings,
    open_api_key_dialog,
    IntelligenceView,
    ToolsView,
)

# Parse CLI arguments for context-menu invocation
init_file_path = None
if len(sys.argv) > 1:
    files = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
    if files:
        init_file_path = os.path.normpath(files[0])

def main(page: ft.Page):
    import asyncio
    try:
        main_loop = asyncio.get_running_loop()
    except RuntimeError:
        main_loop = asyncio.get_event_loop()

    native_show_dialog = getattr(page, 'show_dialog', None)

    def safe_show_dialog(dlg):
        def _do_show():
            if native_show_dialog and callable(native_show_dialog) and native_show_dialog != safe_show_dialog:
                try:
                    native_show_dialog(dlg)
                    return
                except Exception:
                    pass
            dlg.open = True
            if isinstance(dlg, ft.SnackBar):
                page.snack_bar = dlg
            else:
                page.dialog = dlg
                if dlg not in page.overlay:
                    page.overlay.append(dlg)
            try:
                page.update()
            except Exception:
                pass

        if main_loop and main_loop.is_running():
            main_loop.call_soon_threadsafe(_do_show)
        else:
            _do_show()

    page.show_dialog = safe_show_dialog

    if not (hasattr(page, 'pop_dialog') and callable(getattr(page, 'pop_dialog'))):
        def _pop_dialog_impl(dlg=None):
            target = dlg or getattr(page, 'dialog', None)
            if target:
                target.open = False
                if target in getattr(page, 'overlay', []):
                    try:
                        page.overlay.remove(target)
                    except Exception:
                        pass
                page.dialog = None
            try:
                page.update()
            except Exception:
                pass
        page.pop_dialog = _pop_dialog_impl

    # Load and sync API key from ~/.vt.toml on startup
    get_api_key()
    
    current_lang = get_app_lang()
    current_theme = get_app_theme()
    
    # Initialize and register clipboard service
    clipboard_service = ft.Clipboard()
    
    # Page setup
    current_theme = get_app_theme()
    initial_palette = get_theme_palette(current_theme)
    page.title = STRINGS[current_lang]["app_title"]
    page.theme_mode = ft.ThemeMode.DARK if current_theme == "dark" else ft.ThemeMode.LIGHT
    page.bgcolor = initial_palette["bg_gradient_colors"][0]
    page.window.bgcolor = initial_palette["bg_gradient_colors"][0]
    page.theme_animation_style = ft.AnimationStyle(duration=ft.Duration(milliseconds=250), curve=ft.AnimationCurve.EASE_IN_OUT)
    # Set window icon — use .ico on Windows, .png on other platforms if available
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_file = "icon.ico" if IS_WINDOWS else "icon.png"
    icon_full_path = os.path.join(_script_dir, "assets", icon_file)
    if os.path.exists(icon_full_path):
        page.window.icon = icon_full_path
    page.window.width = 1300
    page.window.height = 750
    page.window.min_width = 1300
    page.window.min_height = 750
    page.window.visible = False
    page.padding = 0

    # Use system font to prevent network loading and font layout shifts (jumping)
    if IS_WINDOWS:
        page.theme = ft.Theme(font_family="Segoe UI")
    elif sys.platform == "darwin":
        page.theme = ft.Theme(font_family="SF Pro Text")
    else:
        page.theme = ft.Theme(font_family="sans-serif")
    
    # State variables
    app_state = "scanner"  # scanner, scans, install_cli, history
    active_scans = []
    scan_service = None
    current_tab_index = 0
    _build_lock = threading.Lock()

    # Persistent root container — populated before first page.add()
    page_root = ft.Column(expand=True, spacing=0)
    
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
    
    # Persistent tools view instance to maintain comparison & YARA state across theme toggles
    tools_view_instance = None
    
    # Temporary variables for installer verification
    selected_installer_data = None
    selected_installer_hash = None
    
    # Helper to show alerts
    def show_alert(title, text):
        palette = get_theme_palette(current_theme)
        dlg = ft.AlertDialog(
            title=ft.Text(title, color=palette["text_primary"], weight=ft.FontWeight.BOLD),
            content=ft.Text(text, color=palette["text_secondary"]),
            actions=[ft.TextButton(STRINGS[current_lang]["btn_close"], style=ft.ButtonStyle(color=palette["accent"]), on_click=lambda _: page.pop_dialog())],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=palette["dialog_bg"]
        )
        page.show_dialog(dlg)

    # Note: Search and threat intelligence lookup views and handlers have been moved to src/ui/intelligence_view.py

    main_content = None

    def animate_back_navigation(on_finish):
        if main_content is not None and main_content.content is not None:
            main_content.opacity = 0.0
            main_content.offset = ft.Offset(0.03, 0)
            try:
                page.update()
            except Exception:
                pass

        def delayed_finish():
            import time
            time.sleep(0.04)
            _loop.call_soon_threadsafe(on_finish)

        threading.Thread(target=delayed_finish, daemon=True).start()

    def build_ui():
        if not _build_lock.acquire(blocking=False):
            return
        try:
            _do_build_ui()
        finally:
            _build_lock.release()

    def _do_build_ui():
        nonlocal app_state
        cli_status, cli_hash, cli_source = check_installed_binary()
        
        # Enforce install view if missing vt CLI
        if cli_status == 'missing':
            app_state = "install_cli"
        
        # Header Language Switcher
        def change_language(lang_code):
            nonlocal current_lang
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

        # Theme switcher callback
        def toggle_theme(target_theme=None):
            nonlocal current_theme
            if target_theme in ("dark", "light"):
                current_theme = target_theme
            else:
                current_theme = "light" if current_theme == "dark" else "dark"
            set_app_theme(current_theme)
            p = get_theme_palette(current_theme)
            page.bgcolor = p["bg_gradient_colors"][0]
            page.window.bgcolor = p["bg_gradient_colors"][0]
            page.theme_mode = ft.ThemeMode.DARK if current_theme == "dark" else ft.ThemeMode.LIGHT
            build_ui()

        # Settings CLI Reinstall callback
        def on_reinstall_cli(status_text_widget, status_icon, set_button_disabled):
            def run_reinstall():
                def progress_cb(status_text, progress_val):
                    status_text_widget.value = status_text
                    thread_safe_update()

                try:
                    download_and_install_cli(progress_callback=progress_cb, lang=current_lang)
                    cli_status, _, _ = check_installed_binary()
                    if cli_status in ('verified', 'custom'):
                        status_text_widget.value = STRINGS[current_lang]["reinstall_success"]
                        status_icon.color = "#10B981"
                        set_button_disabled(False)
                        thread_safe_update()
                        build_ui()
                    else:
                        raise ValueError("Reinstall succeeded but verification failed.")
                except Exception as ex:
                    status_text_widget.value = STRINGS[current_lang]["reinstall_fail"].format(e=str(ex))
                    status_icon.color = "#EF4444"
                    set_button_disabled(False)
                    thread_safe_update()

            threading.Thread(target=run_reinstall, daemon=True).start()

        palette = get_theme_palette(current_theme)

        header = build_header(
            current_lang=current_lang,
            on_language_change=change_language,
            on_settings_click=lambda _: open_settings(page, current_lang, build_ui, on_reinstall_cli, cli_source, theme_mode=current_theme, on_theme_change=toggle_theme),
            theme_mode=current_theme,
            on_theme_toggle=lambda _: toggle_theme()
        )
        
        # Central view content switcher with fast fade & slide transitions
        main_content = ft.Container(
            expand=True,
            opacity=1.0,
            offset=ft.Offset(0, 0),
            animate_opacity=ft.Animation(70, ft.AnimationCurve.EASE_OUT),
            animate_offset=ft.Animation(70, ft.AnimationCurve.EASE_OUT)
        )
        
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
                        download_and_install_cli(progress_callback=progress_cb, lang=current_lang)
                        
                        # Verify installation status
                        cli_status, _, _ = check_installed_binary()
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

            async def on_manual_install_click(e):
                await on_cli_click(e)
                
            current_view_body = build_install_view(
                cli_status,
                cli_hash,
                current_lang,
                install_status_text,
                install_progress_bar,
                on_auto_install_click,
                on_manual_install_click,
                theme_mode=current_theme
            )
        elif app_state == "scans":
            tab_headers = []
            tab_contents = []
            for idx, scan in enumerate(active_scans):
                if scan["status"] == "scanning":
                    scan_status_text = ft.Text(scan["status_text"], size=15, weight=ft.FontWeight.W_600, color=palette["accent"])
                    scan_progress_bar = ft.ProgressBar(value=scan["progress"], color=palette["accent"], bgcolor=palette["card_border"], height=6)
                    scan["_status_text_widget"] = scan_status_text
                    scan["_progress_bar_widget"] = scan_progress_bar
                    tab_content = build_scanning_view(
                        ft.ProgressRing(color=palette["accent"], width=48, height=48),
                        scan_status_text,
                        scan_progress_bar,
                        current_lang,
                        theme_mode=current_theme
                    )
                elif scan["status"] == "completed":
                    tab_content = build_results_view(
                        scan["results"],
                        scan["file_path"],
                        scan["sha256"],
                        current_lang,
                        page,
                        theme_mode=current_theme
                    )
                else:  # failed
                    def make_retry_callback(scan_idx, path):
                        def retry_scan(e):
                            nonlocal scan_service
                            active_scans[scan_idx]["status"] = "scanning"
                            active_scans[scan_idx]["status_text"] = STRINGS[current_lang]["computing_hash"]
                            active_scans[scan_idx]["progress"] = 0.0
                            active_scans[scan_idx]["error"] = None
                            if scan_service is None:
                                scan_service = ScanService(active_scans, current_lang, thread_safe_build, show_alert, page)
                            build_ui()
                            threading.Thread(target=scan_service.run_single_scan_pipeline, args=(scan_idx, path), daemon=True).start()
                        return retry_scan
                        
                    tab_content = ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color="#EF4444", size=48),
                                ft.Text(STRINGS[current_lang]["scan_failed"].format(e=""), size=16, weight=ft.FontWeight.BOLD, color=palette["text_primary"]),
                                ft.Text(scan["error"], size=14, color="#EF4444", text_align=ft.TextAlign.CENTER),
                                ft.Container(height=10),
                                ft.Row(
                                    [
                                        ft.Button(
                                            content=ft.Text("Retry / Повторить"),
                                            icon=ft.Icons.REFRESH_ROUNDED,
                                            on_click=make_retry_callback(idx, scan["file_path"]),
                                            bgcolor=palette["button_primary_bg"],
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
                    
                is_active = (current_tab_index == idx)
                
                def make_tab_btn(i, scan_icon, scan_name, is_act):
                    btn = ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(scan_icon, size=16),
                                ft.Text(scan_name, color=palette["text_primary"] if is_act else palette["text_muted"], size=12, weight=ft.FontWeight.W_600)
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=6
                        ),
                        padding=ft.Padding(left=12, right=12, top=8, bottom=8),
                        border_radius=8,
                        border=ft.Border.all(1, palette["accent"] if is_act else "transparent"),
                        bgcolor=palette["tab_active_bg"] if is_act else "transparent",
                        animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
                        on_click=lambda _, idx=i: on_tab_change(idx)
                    )
                    
                    def on_tab_hover(e):
                        if current_tab_index != i:
                            if e.data == "true":
                                btn.border = ft.Border.all(1, palette["tab_inactive_hover_border"])
                                btn.bgcolor = palette["tab_inactive_hover_bg"]
                            else:
                                btn.border = ft.Border.all(1, "transparent")
                                btn.bgcolor = "transparent"
                            try:
                                btn.update()
                            except Exception:
                                pass
                    
                    btn.on_hover = on_tab_hover
                    return btn
                
                tab_headers.append(make_tab_btn(idx, icon, scan['filename'], is_active))
                tab_contents.append(
                    ft.Container(content=tab_content, padding=15)
                )
                
            def on_tab_change(new_index):
                nonlocal current_tab_index
                if new_index != current_tab_index:
                    current_tab_index = new_index
                    build_ui()

            add_tab_btn = ft.IconButton(
                icon=ft.Icons.ADD_ROUNDED,
                icon_color=palette["accent"],
                tooltip=STRINGS[current_lang].get("add_file_tooltip", "Add file to scan"),
                on_click=on_add_scan_click,
                bgcolor=palette["button_secondary_bg"],
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            )
            
            tab_bar_row = ft.Row(
                [
                    ft.Container(
                        content=ft.Row(
                            controls=tab_headers,
                            scroll=ft.ScrollMode.AUTO,
                            spacing=8
                        ),
                        expand=True
                    ),
                    add_tab_btn
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            )
                
            tabs = ft.Container(
                expand=True,
                content=ft.Column(
                    expand=True,
                    controls=[
                        tab_bar_row,
                        ft.Container(
                            content=tab_contents[current_tab_index] if tab_contents else ft.Container(),
                            expand=True
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
                back_icon.offset = ft.Offset(-0.25, 0)
                back_btn_container.scale = 0.90
                try:
                    page.update()
                except Exception:
                    pass
                
                def perform_back():
                    nonlocal app_state, active_scans
                    if active_scanner_tab_index == 5:
                        app_state = "history"
                    else:
                        app_state = "scanner"
                    active_scans = []
                    build_ui()

                animate_back_navigation(perform_back)
                
            back_icon = ft.Icon(
                ft.Icons.ARROW_BACK_ROUNDED,
                color=palette["button_secondary_text"],
                size=18,
                offset=ft.Offset(0, 0),
                animate_offset=ft.Animation(50, ft.AnimationCurve.EASE_OUT)
            )
            
            back_btn_container = ft.Container(
                content=ft.Row([
                    back_icon,
                    ft.Text(STRINGS[current_lang]["btn_back"], color=palette["button_secondary_text"], size=14, weight=ft.FontWeight.W_500)
                ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.Padding(left=14, right=16, top=0, bottom=0),
                height=40,
                bgcolor=palette["button_secondary_bg"],
                border_radius=8,
                scale=1.0,
                animate_scale=ft.Animation(50, ft.AnimationCurve.EASE_OUT),
                on_click=go_back_to_scanner,
                ink=True,
                tooltip=STRINGS[current_lang]["btn_back"]
            )
            back_btn = back_btn_container
            
            # Left side row with back button
            left_actions = ft.Row([back_btn], alignment=ft.MainAxisAlignment.START)
            
            # Right side actions (copy link & open web report)
            right_actions = ft.Row([], alignment=ft.MainAxisAlignment.END, spacing=10)
            
            if show_web_report_btn:
                def open_web_report(e, url=report_url):
                    import webbrowser
                    webbrowser.open(url)
                    
                def copy_web_report_link(e, url=report_url):
                    page.run_task(safe_copy_to_clipboard, page, url, clipboard_service)
                    page.show_dialog(
                        ft.SnackBar(
                            content=ft.Text(STRINGS[current_lang]["link_copied"], color="#FFFFFF"),
                            bgcolor="#10B981"
                        )
                    )
                    
                copy_btn = ft.IconButton(
                    icon=ft.Icons.COPY_ROUNDED,
                    icon_color=palette["accent"],
                    tooltip=STRINGS[current_lang]["copy_link_tooltip"],
                    on_click=copy_web_report_link
                )
                
                web_btn = ft.Button(
                    content=ft.Text(STRINGS[current_lang]["btn_open_web"]),
                    icon=ft.Icons.OPEN_IN_BROWSER_ROUNDED,
                    on_click=open_web_report,
                    bgcolor=palette["button_primary_bg"],
                    color="#FFFFFF",
                    height=40,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                )
                right_actions.controls.extend([copy_btn, web_btn])
            
            top_buttons_row = ft.Row(
                [left_actions, right_actions],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=10
            )
            
            current_view_body = ft.Column(
                [
                    top_buttons_row,
                    tabs
                ],
                expand=True
            )
        else:
            def on_import_report_click(e=None):
                prompt_import_report(page, current_lang, on_history_open_in_app)

            files_view = build_scanner_view(cli_status, cli_hash, cli_source, current_lang, file_picker_scan, on_scan_click, on_folder_click, on_import_report_click, theme_mode=current_theme)
            intel_view = IntelligenceView(search_states, current_lang, show_alert, get_installed_binary_path, thread_safe_build, build_ui, page, theme_mode=current_theme)
            url_view = intel_view.build_lookup_tab("url", STRINGS[current_lang]["url_placeholder"], STRINGS[current_lang]["url_helper"])
            domain_view = intel_view.build_lookup_tab("domain", STRINGS[current_lang]["domain_placeholder"], STRINGS[current_lang]["domain_helper"])
            ip_view = intel_view.build_lookup_tab("ip", STRINGS[current_lang]["ip_placeholder"], STRINGS[current_lang]["ip_helper"])
            search_view = intel_view.build_lookup_tab("search", STRINGS[current_lang]["search_placeholder"], STRINGS[current_lang]["search_helper"])
            nonlocal tools_view_instance
            if tools_view_instance is None:
                tools_view_instance = ToolsView(current_lang, show_alert, page, theme_mode=current_theme)
            else:
                tools_view_instance.lang = current_lang
                tools_view_instance.theme_mode = current_theme
                tools_view_instance.palette = palette
            tools_view = tools_view_instance.build_tools_tab()

            def on_history_back():
                def perform_back():
                    nonlocal app_state, active_scanner_tab_index
                    active_scanner_tab_index = 0
                    app_state = "scanner"
                    build_ui()

                animate_back_navigation(perform_back)

            def on_history_rescan(item):
                nonlocal active_scans, app_state, current_tab_index, scan_service, active_scanner_tab_index
                if isinstance(item, dict) and item.get("type") == "lookup":
                    lookup_type = item.get("lookup_type", "url")
                    query = item.get("query", "")
                    if lookup_type in search_states:
                        search_states[lookup_type]["input"] = query
                    tab_indices = {"url": 1, "domain": 2, "ip": 3, "search": 4}
                    active_scanner_tab_index = tab_indices.get(lookup_type, 1)
                    app_state = "scanner"
                    build_ui()
                    intel_view.run_lookup_query(lookup_type)
                elif isinstance(item, dict) and item.get("type") == "file":
                    path = item.get("file_path", "")
                    if path and os.path.exists(path):
                        on_history_rescan(path)
                elif isinstance(item, str):
                    path = item
                    active_scans = []
                    current_tab_index = 0
                    app_state = "scans"
                    active_scans.append({
                        "file_path": path,
                        "filename": os.path.basename(path),
                        "status": "scanning",
                        "status_text": STRINGS[current_lang]["computing_hash"],
                        "progress": 0.0,
                        "sha256": None,
                        "results": None,
                        "error": None
                    })
                    build_ui()
                    scan_service = ScanService(active_scans, current_lang, thread_safe_build, show_alert, page)
                    threading.Thread(target=scan_service.run_single_scan_pipeline, args=(0, path), daemon=True).start()

            select_tab_ref = [None]

            def on_history_open_in_app(record):
                nonlocal active_scans, app_state, current_tab_index, active_scanner_tab_index
                record_type = record.get("type", "file")
                results = record.get("results")
                record_id = record.get("id")

                if record_type == "file":
                    file_path = record.get("file_path", "")
                    filename = record.get("filename", os.path.basename(file_path) if file_path else "Unknown")
                    sha256 = record.get("sha256", "")

                    if results:
                        active_scans = [{
                            "file_path": file_path,
                            "filename": filename,
                            "status": "completed",
                            "sha256": sha256,
                            "results": results,
                            "error": None
                        }]
                        current_tab_index = 0
                        active_scanner_tab_index = 0
                        app_state = "scans"
                        build_ui()
                    else:
                        if not sha256 and file_path and os.path.exists(file_path):
                            on_history_rescan(file_path)
                            return

                        active_scans = [{
                            "file_path": file_path,
                            "filename": filename,
                            "status": "scanning",
                            "status_text": STRINGS[current_lang].get("checking_vt", "Checking VirusTotal..."),
                            "progress": 0.5,
                            "sha256": sha256,
                            "results": None,
                            "error": None
                        }]
                        current_tab_index = 0
                        active_scanner_tab_index = 0
                        app_state = "scans"
                        build_ui()

                        def fetch_and_show():
                            nonlocal scan_service
                            try:
                                api_key = get_api_key()
                                vt_path = get_installed_binary_path()
                                info = None
                                if sha256:
                                    if api_key:
                                        try:
                                            info = check_file_exists_direct(sha256, api_key)
                                        except Exception:
                                            pass
                                    if not info and vt_path and os.path.exists(vt_path):
                                        info = check_file_exists_vt(vt_path, sha256)

                                if not info and file_path and os.path.exists(file_path):
                                    if scan_service is None:
                                        scan_service = ScanService(active_scans, current_lang, thread_safe_build, show_alert, page)
                                    scan_service.run_single_scan_pipeline(0, file_path)
                                    return

                                if info:
                                    active_scans[0]["results"] = info
                                    active_scans[0]["status"] = "completed"
                                    active_scans[0].pop("_status_text_widget", None)
                                    active_scans[0].pop("_progress_bar_widget", None)
                                    record["results"] = info
                                    update_scan_record_results(record_id, info)
                                else:
                                    active_scans[0]["status"] = "failed"
                                    active_scans[0]["error"] = STRINGS[current_lang].get(
                                        "history_no_local_results",
                                        "Для этой записи нет сохраненных локальных данных отчета."
                                    )
                            except Exception as ex:
                                active_scans[0]["status"] = "failed"
                                active_scans[0]["error"] = str(ex)
                            thread_safe_build()

                        threading.Thread(target=fetch_and_show, daemon=True).start()

                elif record_type == "lookup":
                    lookup_type = record.get("lookup_type", "url")
                    query = record.get("query", "")
                    if lookup_type in search_states:
                        search_states[lookup_type]["input"] = query
                        search_states[lookup_type]["results"] = results
                        search_states[lookup_type]["status"] = "success" if results else "idle"
                        search_states[lookup_type]["error"] = record.get("error")

                    tab_indices = {"url": 1, "domain": 2, "ip": 3, "search": 4}
                    target_tab_idx = tab_indices.get(lookup_type, 1)
                    active_scanner_tab_index = target_tab_idx
                    app_state = "scanner"
                    if select_tab_ref[0]:
                        select_tab_ref[0](target_tab_idx)
                    else:
                        build_ui()

                    if not results and query and lookup_type in search_states:
                        intel_view.run_lookup_query(lookup_type)

            history_view = build_history_view(current_lang, page, on_history_back, on_history_rescan, on_history_open_in_app, on_import_report_click, theme_mode=current_theme)

            def on_active_tab_change(e):
                nonlocal active_scanner_tab_index, app_state
                idx = int(e.control.selected_index)
                active_scanner_tab_index = idx
                if idx == 6:
                    app_state = "history"
                else:
                    app_state = "scanner"

            tab_definitions = [
                (0, STRINGS[current_lang]["tab_files"], ft.Icons.ATTACH_FILE_ROUNDED, files_view),
                (1, STRINGS[current_lang]["tab_urls"], ft.Icons.LINK_ROUNDED, url_view),
                (2, STRINGS[current_lang]["tab_domains"], ft.Icons.LANGUAGE_ROUNDED, domain_view),
                (3, STRINGS[current_lang]["tab_ips"], ft.Icons.CELL_TOWER_ROUNDED, ip_view),
                (4, STRINGS[current_lang]["tab_search"], ft.Icons.SEARCH_ROUNDED, search_view),
                (5, STRINGS[current_lang]["tab_tools"], ft.Icons.BUILD_ROUNDED, tools_view),
                (6, STRINGS[current_lang]["tab_history"], ft.Icons.HISTORY_ROUNDED, history_view),
            ]

            tab_views_map = {idx: v for idx, _, _, v in tab_definitions}

            animated_tab_content = ft.Container(
                content=ft.Container(
                    content=tab_views_map[active_scanner_tab_index],
                    padding=10,
                    expand=True
                ),
                expand=True
            )

            tab_buttons = []
            tab_buttons_map = {}

            def update_tab_buttons():
                for idx, btn in tab_buttons_map.items():
                    is_active = (active_scanner_tab_index == idx)
                    btn.border = ft.Border.all(1, palette["accent"] if is_active else "transparent")
                    btn.bgcolor = palette["tab_active_bg"] if is_active else "transparent"
                    col = btn.content
                    col.controls[0].color = palette["accent"] if is_active else palette["text_muted"]
                    col.controls[1].color = palette["text_primary"] if is_active else palette["text_muted"]
                    try:
                        btn.update()
                    except Exception:
                        pass

            def select_tab(idx):
                nonlocal active_scanner_tab_index, app_state
                active_scanner_tab_index = idx
                if idx == 6:
                    app_state = "history"
                else:
                    app_state = "scanner"

                update_tab_buttons()

                animated_tab_content.content = ft.Container(
                    content=tab_views_map[idx],
                    padding=10,
                    expand=True
                )
                try:
                    animated_tab_content.update()
                except Exception:
                    build_ui()

            select_tab_ref[0] = select_tab

            for idx, label, icon, _ in tab_definitions:
                is_active = (active_scanner_tab_index == idx)
                
                tab_btn = ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(icon, color=palette["accent"] if is_active else palette["text_muted"], size=20),
                            ft.Text(label, color=palette["text_primary"] if is_active else palette["text_muted"], size=12, weight=ft.FontWeight.W_600)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2
                    ),
                    padding=ft.Padding(left=12, right=12, top=6, bottom=6),
                    height=70,
                    border_radius=8,
                    border=ft.Border.all(1, palette["accent"] if is_active else "transparent"),
                    bgcolor=palette["tab_active_bg"] if is_active else "transparent",
                    animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
                    on_click=lambda _, i=idx: select_tab(i)
                )

                def make_hover_handler(btn, tab_idx):
                    def on_tab_hover(e):
                        if active_scanner_tab_index != tab_idx:
                            if e.data == "true":
                                btn.border = ft.Border.all(1, palette["tab_inactive_hover_border"])
                                btn.bgcolor = palette["tab_inactive_hover_bg"]
                            else:
                                btn.border = ft.Border.all(1, "transparent")
                                btn.bgcolor = "transparent"
                            try:
                                btn.update()
                            except Exception:
                                pass
                    return on_tab_hover

                tab_btn.on_hover = make_hover_handler(tab_btn, idx)
                tab_buttons.append(tab_btn)
                tab_buttons_map[idx] = tab_btn

            tab_header_row = ft.Row(
                tab_buttons,
                spacing=2,
                alignment=ft.MainAxisAlignment.START
            )

            landing_tabs = ft.Column(
                [
                    ft.Container(
                        content=tab_header_row,
                        padding=ft.Padding(left=4, right=4, top=5, bottom=15),
                        border=ft.Border(bottom=ft.BorderSide(1, palette["divider"]))
                    ),
                    animated_tab_content
                ],
                expand=True,
                spacing=10
            )
            current_view_body = landing_tabs
            
        main_content = ft.Container(
            content=current_view_body,
            expand=True
        )
            
        # Build footer with social links
        footer = build_footer(current_lang, page, theme_mode=current_theme)

        outer_container = ft.Container(
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=palette["bg_gradient_colors"]
            ),
            expand=True,
            padding=20,
            animate=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                [
                    header,
                    main_content,
                    footer
                ],
                expand=True
            )
        )
        
        page_root.controls = [outer_container]
        if not page.controls:
            # First render: add root with content already set — single render
            page.controls.append(page_root)
            page.update()
        else:
            # Subsequent renders: smoothly animates theme transition
            page_root.update()

    import asyncio
    try:
        _loop = asyncio.get_running_loop()
    except RuntimeError:
        _loop = asyncio.get_event_loop()

    def thread_safe_update():
        _loop.call_soon_threadsafe(page.update)

    def thread_safe_build():
        _loop.call_soon_threadsafe(build_ui)

    # ==============================================================================
    # BACKGROUND PIPELINE
    # ==============================================================================
    # Note: run_single_scan_pipeline logic has been moved to src/services/scan_service.py

    # ==============================================================================
    # FILE PICKER HANDLERS
    # ==============================================================================
    def on_scan_file_selected(files, append=False):
        if not files:
            return

        nonlocal active_scans, app_state, current_tab_index, scan_service

        cli_status, _, _ = check_installed_binary()
        if cli_status == 'missing':
            app_state = "install_cli"
            build_ui()
            return
            
        valid_files = []
        for f in files:
            if not f.path or not os.path.exists(f.path):
                continue
            if os.path.isdir(f.path):
                show_alert("Error / Ошибка", f"Scanning directories is not supported ({os.path.basename(f.path)}). Please choose files.")
                continue
            valid_files.append(f)
            
        if not valid_files:
            if not append and not active_scans:
                app_state = "scanner"
                build_ui()
            return
            
        start_idx = len(active_scans) if append else 0
        if not append:
            active_scans = []
            
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
            
        current_tab_index = start_idx
        app_state = "scans"
        build_ui()
        
        # Start scanning for each new file in a separate thread
        if scan_service is None or not append:
            scan_service = ScanService(active_scans, current_lang, thread_safe_build, show_alert, page)
        else:
            scan_service.active_scans = active_scans

        from concurrent.futures import ThreadPoolExecutor
        if not hasattr(page, "_scan_pool") or getattr(page, "_scan_pool_shutdown", False):
            page._scan_pool = ThreadPoolExecutor(max_workers=3)
            page._scan_pool_shutdown = False

        for idx in range(start_idx, len(active_scans)):
            scan = active_scans[idx]
            page._scan_pool.submit(scan_service.run_single_scan_pipeline, idx, scan["file_path"])

    async def on_scan_click(e):
        try:
            files = await file_picker_scan.pick_files(allow_multiple=True)
            on_scan_file_selected(files)
        except Exception as ex:
            show_alert("Error", str(ex))

    def on_folder_click(e):
        def worker():
            try:
                import tkinter as tk
                from tkinter import filedialog

                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                dir_path = filedialog.askdirectory(title=STRINGS[current_lang].get("btn_scan_folder", "Scan Folder"))
                root.destroy()

                if not dir_path:
                    return

                collected_files = []
                for root_dir, _, filenames in os.walk(dir_path):
                    for fname in filenames:
                        if fname.startswith("~$") or fname.startswith("."):
                            continue
                        full_p = os.path.join(root_dir, fname)
                        if os.path.isfile(full_p):
                            class FileObj:
                                def __init__(self, p):
                                    self.path = p
                            collected_files.append(FileObj(full_p))
                            if len(collected_files) >= 100:
                                break
                    if len(collected_files) >= 100:
                        break

                if collected_files:
                    on_scan_file_selected(collected_files)
                else:
                    show_alert(STRINGS[current_lang]["app_title"], "No readable files found in selected directory.")
            except Exception as ex:
                show_alert("Error", str(ex))

        threading.Thread(target=worker, daemon=True).start()

    async def on_add_scan_click(e):
        try:
            files = await file_picker_scan.pick_files(allow_multiple=True)
            on_scan_file_selected(files, append=True)
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
                    
                p = get_theme_palette(current_theme)
                dlg = ft.AlertDialog(
                    title=ft.Text(STRINGS[current_lang]["hash_warning_title"], color=p["text_primary"], weight=ft.FontWeight.BOLD),
                    content=ft.Text(STRINGS[current_lang]["hash_warning_text"].format(hash=exe_hash), color=p["text_secondary"]),
                    actions=[
                        ft.TextButton(STRINGS[current_lang]["btn_no"], style=ft.ButtonStyle(color=p["text_muted"]), on_click=reject_custom_binary),
                        ft.Button(STRINGS[current_lang]["btn_yes"], on_click=approve_custom_binary, bgcolor=p["button_primary_bg"], color="#FFFFFF")
                    ],
                    bgcolor=p["dialog_bg"]
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
    file_picker_folder = ft.FilePicker()
    page.services.extend([file_picker_scan, file_picker_cli, file_picker_folder, clipboard_service])

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
                    on_scan_file_selected([PseudoFile(p) for p in valid], append=(app_state == "scans"))
            except Exception:
                pass

    page.on_keyboard_event = on_paste_keyboard
    
    build_ui()

    async def _show_window_when_ready():
        try:
            await page.window.wait_until_ready_to_show()
            await page.window.center()
        except Exception:
            pass
        page.window.visible = True
        try:
            page.update()
        except Exception:
            pass

    page.run_task(_show_window_when_ready)

    # Show API key setup dialog on first launch if no key is configured
    if not get_api_key():
        def on_api_key_saved():
            build_ui()
        _, _, _cli_source = check_installed_binary()
        open_api_key_dialog(page, current_lang, on_api_key_saved, _cli_source, theme_mode=current_theme)
    elif init_file_path and os.path.exists(init_file_path):
        api_key = get_api_key()
        cli_status, _, _ = check_installed_binary()
        
        if not api_key:
            show_alert("Error / Ошибка", STRINGS[current_lang]["api_key_missing"])
        elif cli_status == 'missing':
            show_alert("Error / Ошибка", STRINGS[current_lang]["download_instructions_title"])
        else:
            class PseudoFile:
                def __init__(self, path):
                    self.path = path
            on_scan_file_selected([PseudoFile(init_file_path)])

def _setup_flet_environment():
    """
    Configures environment variables for Flet to locate bundled runtime binaries
    when running as a frozen PyInstaller application, preventing runtime downloads.
    """
    if not getattr(sys, 'frozen', False):
        return

    bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    os.chdir(bundle_dir)

    # If FLET_VIEW_PATH is already valid, nothing to do
    existing_view_path = os.environ.get("FLET_VIEW_PATH")
    if existing_view_path and os.path.exists(existing_view_path):
        return

    if sys.platform == "win32":
        candidates = [
            os.path.join(bundle_dir, "flet_desktop", "app", "flet"),
            os.path.join(bundle_dir, "flet_desktop", "app"),
            os.path.join(bundle_dir, "flet"),
            os.path.join(bundle_dir, "flet_desktop"),
            bundle_dir,
        ]
        for path in candidates:
            if os.path.isfile(os.path.join(path, "flet.exe")):
                os.environ["FLET_VIEW_PATH"] = path
                break
    elif sys.platform == "darwin":
        candidates = [
            os.path.join(bundle_dir, "flet_desktop", "app"),
            os.path.join(bundle_dir, "flet_desktop"),
            bundle_dir,
        ]
        for path in candidates:
            if os.path.isdir(path):
                try:
                    for item in os.listdir(path):
                        if item.endswith(".app"):
                            os.environ["FLET_VIEW_PATH"] = path
                            break
                except Exception:
                    pass
                if "FLET_VIEW_PATH" in os.environ:
                    break
    else:  # Linux / Unix
        import stat
        candidates = [
            os.path.join(bundle_dir, "flet_desktop", "app", "flet"),
            os.path.join(bundle_dir, "flet_desktop", "app"),
            os.path.join(bundle_dir, "flet"),
            os.path.join(bundle_dir, "flet_desktop"),
            bundle_dir,
        ]
        for path in candidates:
            exe_path = os.path.join(path, "flet")
            if os.path.isfile(exe_path):
                try:
                    st = os.stat(exe_path)
                    os.chmod(exe_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
                except Exception:
                    pass
                os.environ["FLET_VIEW_PATH"] = path
                break


if __name__ == '__main__':
    _setup_flet_environment()
    os.environ["FLET_HIDE_WINDOW_ON_START"] = "true"

    try:
        ft.run(main, view=ft.AppView.FLET_APP_HIDDEN, assets_dir="assets")
    except Exception as e:
        error_msg = (
            f"Failed to start VT GUI / Ошибка запуска VT GUI:\n\n{e}\n\n"
            "If this is your first launch, please ensure Internet access is allowed in Windows Firewall, "
            "or verify that all required system libraries are installed."
        )
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, error_msg, "VT GUI - Startup Error", 0x10)
            except Exception:
                print(error_msg, file=sys.stderr)
        else:
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("VT GUI - Startup Error", error_msg)
            except Exception:
                print(error_msg, file=sys.stderr)
        sys.exit(1)
