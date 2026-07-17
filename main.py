import json
import os
import sys
import threading
import time
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
    
    # Page setup
    page.title = STRINGS[current_lang]["app_title"]
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 800
    page.window_height = 700
    page.window_min_width = 650
    page.window_min_height = 600
    page.padding = 0
    
    # Load fonts
    page.fonts = {
        "Outfit": "https://github.com/google/fonts/raw/main/ofl/outfit/Outfit%5Bwght%5D.ttf"
    }
    page.theme = ft.Theme(font_family="Outfit")
    
    # State variables
    app_state = "scanner"  # scanner, scanning, results, install_cli
    selected_target_file = None
    current_scan_results = None
    last_completed_sha256 = None
    
    # GUI references
    scan_status_text = ft.Text("", size=15, weight=ft.FontWeight.W_600, color="#00F0FF")
    scan_progress_bar = ft.ProgressBar(value=0, color="#00F0FF", bgcolor="#334155", height=6)
    scan_progress_ring = ft.ProgressRing(color="#00F0FF", width=48, height=48)
    
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
            
        language_menu = ft.PopupMenuButton(
            icon=ft.Icons.LANGUAGE,
            icon_color="#00F0FF",
            tooltip="Язык / Language",
            items=[
                ft.PopupMenuItem(content=ft.Text("Русский"), on_click=lambda _: change_language("ru")),
                ft.PopupMenuItem(content=ft.Text("English"), on_click=lambda _: change_language("en")),
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
        elif app_state == "scanning":
            main_content.content = build_scanning_view(scan_progress_ring, scan_status_text, scan_progress_bar)
        elif app_state == "results":
            def back_to_scanner(e):
                nonlocal app_state, selected_target_file, current_scan_results
                app_state = "scanner"
                selected_target_file = None
                current_scan_results = None
                build_ui()
                
            main_content.content = build_results_view(
                current_scan_results,
                selected_target_file,
                last_completed_sha256,
                current_lang,
                back_to_scanner,
                page
            )
        else:
            main_content.content = build_scanner_view(cli_status, cli_hash, current_lang, file_picker_scan, on_scan_click)
            
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
                    main_content
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
    def set_scan_status(text, progress_value):
        scan_status_text.value = text
        if progress_value is None:
            scan_progress_bar.value = None
        else:
            scan_progress_bar.value = progress_value
        thread_safe_update()

    def show_scan_error(err_msg):
        nonlocal app_state
        app_state = "scanner"
        thread_safe_build()
        show_alert(STRINGS[current_lang]["scan_failed"].format(e=""), err_msg)

    def show_results(results_data, file_hash, file_path):
        nonlocal app_state, current_scan_results, last_completed_sha256, selected_target_file
        current_scan_results = results_data
        last_completed_sha256 = file_hash
        selected_target_file = file_path
        app_state = "results"
        thread_safe_build()

    def run_scan_pipeline(file_path):
        nonlocal app_state
        app_state = "scanning"
        thread_safe_build()
        
        throttler = ProgressThrottler(0.12)
        
        def on_upload_progress(current, total):
            if throttler.should_update() or current == total:
                percent = current / total if total > 0 else 0
                scan_progress_bar.value = percent
                current_mb = current / (1024 * 1024)
                total_mb = total / (1024 * 1024)
                scan_status_text.value = STRINGS[current_lang]["upload_progress"].format(
                    percent=int(percent * 100),
                    current=current_mb,
                    total=total_mb
                )
                thread_safe_update()

        try:
            # 1. Compute Hash
            set_scan_status(STRINGS[current_lang]["computing_hash"], 0.1)
            sha256 = compute_sha256(file_path)
            if not sha256:
                raise ValueError("Could not compute target file SHA-256 hash.")
                
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
                show_results(existing_info, sha256, file_path)
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
                
            show_results(final_report, sha256, file_path)
            
        except ValueError as ve:
            err_text = str(ve)
            if err_text == "api_key_invalid_err":
                err_text = STRINGS[current_lang]["api_key_invalid_err"]
            show_scan_error(err_text)
        except Exception as ex:
            show_scan_error(str(ex))

    # ==============================================================================
    # FILE PICKER HANDLERS
    # ==============================================================================
    def on_scan_file_selected(files):
        if not files:
            return
        file_path = files[0].path
        if not os.path.exists(file_path):
            return
        if os.path.isdir(file_path):
            show_alert("Error / Ошибка", "Scanning directories is not supported. Please choose a file.")
            return
        threading.Thread(target=run_scan_pipeline, args=(file_path,), daemon=True).start()

    async def on_scan_click(e):
        try:
            files = await file_picker_scan.pick_files(allow_multiple=False)
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
    page.services.extend([file_picker_scan, file_picker_cli])
    
    build_ui()
    
    # Context menu autostart scan
    if init_file_path and os.path.exists(init_file_path):
        api_key = get_api_key()
        cli_status, _ = check_installed_binary()
        
        if not api_key:
            show_alert("Error / Ошибка", STRINGS[current_lang]["api_key_missing"])
        elif cli_status == 'missing':
            show_alert("Error / Ошибка", STRINGS[current_lang]["download_instructions_title"])
        else:
            threading.Thread(target=run_scan_pipeline, args=(init_file_path,), daemon=True).start()

if __name__ == '__main__':
    ft.run(main)
