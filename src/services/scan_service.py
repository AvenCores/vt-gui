import os
import time
import json
import subprocess
import threading
from ..config import STRINGS, get_api_key
from ..cli_manager import get_temp_bin_path, compute_sha256
from ..vt_api import check_file_exists_direct, check_file_exists_vt

class ScanService:
    def __init__(self, active_scans, current_lang, thread_safe_build_fn, show_alert_fn, page):
        self.active_scans = active_scans
        self.current_lang = current_lang
        self.thread_safe_build_fn = thread_safe_build_fn
        self.show_alert_fn = show_alert_fn
        self.page = page

    def run_single_scan_pipeline(self, idx, file_path):
        def set_scan_status(text, progress_value):
            self.active_scans[idx]["status_text"] = text
            self.active_scans[idx]["progress"] = progress_value
            self.thread_safe_build_fn()

        try:
            # 1. Compute Hash
            set_scan_status(STRINGS[self.current_lang]["computing_hash"], 0.1)
            sha256 = compute_sha256(file_path)
            if not sha256:
                raise ValueError("Could not compute target file SHA-256 hash.")
            self.active_scans[idx]["sha256"] = sha256
            
            # 2. Check API Key
            api_key = get_api_key()
            if not api_key:
                raise ValueError(STRINGS[self.current_lang]["api_key_missing"])
                
            # 3. Check Database
            set_scan_status(STRINGS[self.current_lang]["checking_vt"], 0.25)
            
            vt_path = get_temp_bin_path()
            if not os.path.exists(vt_path):
                raise ValueError("vt.exe was missing when scan was initiated.")
            existing_info = check_file_exists_vt(vt_path, sha256)
                
            if existing_info:
                # File already scanned! Fetch complete report.
                set_scan_status(STRINGS[self.current_lang]["scan_success"], 1.0)
                try:
                    web_info = check_file_exists_direct(sha256, api_key)
                    if web_info:
                        existing_info = web_info
                except Exception:
                    pass
                self.active_scans[idx]["results"] = existing_info
                self.active_scans[idx]["status"] = "completed"
                self.thread_safe_build_fn()
                return
                
            # 4. Upload file
            set_scan_status(STRINGS[self.current_lang]["uploading_file"], 0.4)
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
            set_scan_status(STRINGS[self.current_lang]["waiting_analysis"], 0.7)
            start_time = time.time()
            
            while True:
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
                set_scan_status(f"{STRINGS[self.current_lang]['waiting_analysis']} ({elapsed}s)...", None)
                time.sleep(5)
                
            # 6. Success! Fetch final file details.
            set_scan_status(STRINGS[self.current_lang]["scan_success"], 1.0)
            
            final_report = check_file_exists_direct(sha256, api_key)
            if not final_report:
                final_report = check_file_exists_vt(vt_path, sha256)
                    
            if not final_report:
                raise ValueError("Analysis completed, but failed to fetch the file details.")
                
            self.active_scans[idx]["results"] = final_report
            self.active_scans[idx]["status"] = "completed"
            self.thread_safe_build_fn()
            
        except ValueError as ve:
            err_text = str(ve)
            if err_text == "api_key_invalid_err":
                err_text = STRINGS[self.current_lang]["api_key_invalid_err"]
            self.active_scans[idx]["status"] = "failed"
            self.active_scans[idx]["error"] = err_text
            self.thread_safe_build_fn()
        except Exception as ex:
            self.active_scans[idx]["status"] = "failed"
            self.active_scans[idx]["error"] = str(ex)
            self.thread_safe_build_fn()
