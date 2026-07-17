import os
import time
import json
import subprocess
import threading
from ..config import STRINGS, get_api_key, CLI_BINARY_NAME
from ..cli_manager import get_temp_bin_path, compute_sha256
from ..vt_api import check_file_exists_direct, check_file_exists_vt


def resolve_scan_status(scan, lang):
    """Re-resolve a scan's status_text using the given language code."""
    resolver = scan.get("status_resolver")
    if resolver is None:
        return
    new_text = resolver(lang)
    scan["status_text"] = new_text
    widget = scan.get("_status_text_widget")
    if widget is not None:
        widget.value = new_text


class ScanService:
    def __init__(self, active_scans, current_lang, thread_safe_build_fn, show_alert_fn, page):
        self.active_scans = active_scans
        self._current_lang = current_lang
        self.thread_safe_build_fn = thread_safe_build_fn
        self.show_alert_fn = show_alert_fn
        self.page = page

    @property
    def current_lang(self):
        return self._current_lang

    @current_lang.setter
    def current_lang(self, value):
        self._current_lang = value

    def run_single_scan_pipeline(self, idx, file_path):
        def set_scan_status(text, progress_value, rebuild=False, resolver=None):
            self.active_scans[idx]["status_text"] = text
            if resolver is not None:
                self.active_scans[idx]["status_resolver"] = resolver
            if progress_value is not None:
                self.active_scans[idx]["progress"] = progress_value
            # Update widgets directly if references exist, avoiding full UI rebuild
            status_text_w = self.active_scans[idx].get("_status_text_widget")
            progress_bar_w = self.active_scans[idx].get("_progress_bar_widget")
            if status_text_w is not None:
                status_text_w.value = text
            if progress_bar_w is not None and progress_value is not None:
                progress_bar_w.value = progress_value
            if rebuild or status_text_w is None:
                self.thread_safe_build_fn()
            else:
                # Lightweight update: just push changed values to the client
                try:
                    self.page.update()
                except Exception:
                    pass

        try:
            # 1. Compute Hash
            set_scan_status(STRINGS[self.current_lang]["computing_hash"], 0.1,
                            resolver=lambda lang: STRINGS[lang]["computing_hash"])
            sha256 = compute_sha256(file_path)
            if not sha256:
                raise ValueError("Could not compute target file SHA-256 hash.")
            self.active_scans[idx]["sha256"] = sha256
            
            # 2. Check API Key
            api_key = get_api_key()
            if not api_key:
                raise ValueError(STRINGS[self.current_lang]["api_key_missing"])
                
            # 3. Check Database
            set_scan_status(STRINGS[self.current_lang]["checking_vt"], 0.25,
                            resolver=lambda lang: STRINGS[lang]["checking_vt"])
            
            vt_path = get_temp_bin_path()
            if not os.path.exists(vt_path):
                raise ValueError(f"{CLI_BINARY_NAME} was missing when scan was initiated.")
            existing_info = check_file_exists_vt(vt_path, sha256)
                
            if existing_info:
                # File already scanned! Fetch complete report.
                set_scan_status(STRINGS[self.current_lang]["scan_success"], 1.0, rebuild=True)
                try:
                    web_info = check_file_exists_direct(sha256, api_key)
                    if web_info:
                        existing_info = web_info
                except Exception:
                    pass
                self.active_scans[idx]["results"] = existing_info
                self.active_scans[idx]["status"] = "completed"
                self.active_scans[idx].pop("_status_text_widget", None)
                self.active_scans[idx].pop("_progress_bar_widget", None)
                self.thread_safe_build_fn()
                return
                
            # 4. Upload file
            set_scan_status(STRINGS[self.current_lang]["uploading_file"], 0.4,
                            resolver=lambda lang: STRINGS[lang]["uploading_file"])
            analysis_id = None
            
            vt_path = get_temp_bin_path()
            cmd = [vt_path, 'scan', 'file', file_path]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            if proc.returncode != 0:
                raise ValueError(f"vt CLI upload failed: {proc.stderr or proc.stdout}")
            
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
            set_scan_status(STRINGS[self.current_lang]["waiting_analysis"], 0.7,
                            resolver=lambda lang: STRINGS[lang]["waiting_analysis"])
            start_time = time.time()
            max_wait = 300  # 5 minutes timeout
            
            while True:
                elapsed = time.time() - start_time
                if elapsed >= max_wait:
                    raise ValueError(STRINGS[self.current_lang]["scan_timeout_err"].format(timeout=max_wait))
                    
                status = None
                vt_path = get_temp_bin_path()
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
                # Animate progress from 0.7 to 0.95 over the timeout window
                progress = 0.7 + 0.25 * min(elapsed / max_wait, 1.0)
                def _waiting_resolver(lang, _el=elapsed):
                    return f"{STRINGS[lang]['waiting_analysis']} ({_el}s)..."
                set_scan_status(f"{STRINGS[self.current_lang]['waiting_analysis']} ({elapsed}s)...", progress,
                                resolver=_waiting_resolver)
                time.sleep(5)
                
            # 6. Success! Fetch final file details.
            set_scan_status(STRINGS[self.current_lang]["scan_success"], 1.0, rebuild=True)
            
            final_report = check_file_exists_direct(sha256, api_key)
            if not final_report:
                final_report = check_file_exists_vt(vt_path, sha256)
                    
            if not final_report:
                raise ValueError("Analysis completed, but failed to fetch the file details.")
                
            self.active_scans[idx]["results"] = final_report
            self.active_scans[idx]["status"] = "completed"
            self.active_scans[idx].pop("_status_text_widget", None)
            self.active_scans[idx].pop("_progress_bar_widget", None)
            self.thread_safe_build_fn()

        except ValueError as ve:
            err_text = str(ve)
            if err_text == "api_key_invalid_err":
                err_text = STRINGS[self.current_lang]["api_key_invalid_err"]
            self.active_scans[idx]["status"] = "failed"
            self.active_scans[idx]["error"] = err_text
            self.active_scans[idx].pop("_status_text_widget", None)
            self.active_scans[idx].pop("_progress_bar_widget", None)
            self.thread_safe_build_fn()
        except Exception as ex:
            self.active_scans[idx]["status"] = "failed"
            self.active_scans[idx]["error"] = str(ex)
            self.active_scans[idx].pop("_status_text_widget", None)
            self.active_scans[idx].pop("_progress_bar_widget", None)
            self.thread_safe_build_fn()
