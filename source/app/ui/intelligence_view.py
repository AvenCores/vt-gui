import os
import sys
import threading
import subprocess
import json
import webbrowser
import flet as ft
from ..config import STRINGS, get_api_key, CLI_BINARY_NAME
from ..vt_api import submit_url_scan, get_subdomains, get_dns_resolutions, reanalyze_item
from ..exporter import export_report_to_file, prompt_export_report
from ..history_manager import add_lookup_record
from .theme import make_stat_card, make_engine_row

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

class IntelligenceView:
    def __init__(self, search_states, current_lang, show_alert_fn, get_installed_binary_path_fn, thread_safe_build_fn, build_ui_fn, page: ft.Page):
        self.search_states = search_states
        self.current_lang = current_lang
        self.show_alert_fn = show_alert_fn
        self.get_installed_binary_path_fn = get_installed_binary_path_fn
        self.thread_safe_build_fn = thread_safe_build_fn
        self.build_ui_fn = build_ui_fn
        self.page = page

    def build_lookup_results_view(self, data_dict, item_type, item_id):
        stats = data_dict.get("last_analysis_stats", {})
        results = data_dict.get("last_analysis_results", {})
        
        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        harmless = stats.get("harmless", 0)
        undetected = stats.get("undetected", 0)
        
        if malicious > 0:
            banner_text = STRINGS[self.current_lang]["verdict_malicious"].format(malicious=malicious)
            banner_color = "#FF3131"
            banner_icon = ft.Icons.GPP_BAD_ROUNDED
        elif suspicious > 0:
            banner_text = STRINGS[self.current_lang]["verdict_suspicious"].format(suspicious=suspicious)
            banner_color = "#FFD700"
            banner_icon = ft.Icons.WARNING_ROUNDED
        else:
            banner_text = STRINGS[self.current_lang]["verdict_safe"]
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
        
        stats_row = ft.Row(
            [
                make_stat_card(STRINGS[self.current_lang]["stats_malicious"], malicious, "#FF3131", ft.Icons.REPORT_PROBLEM_ROUNDED),
                make_stat_card(STRINGS[self.current_lang]["stats_suspicious"], suspicious, "#FFD700", ft.Icons.WARNING_AMBER_ROUNDED),
                make_stat_card(STRINGS[self.current_lang]["stats_harmless"], harmless, "#39FF14", ft.Icons.CHECK_CIRCLE_ROUNDED),
                make_stat_card(STRINGS[self.current_lang]["stats_undetected"], undetected, "#94A3B8", ft.Icons.HELP_OUTLINE_ROUNDED)
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY
        )

        def handle_export(e):
            prompt_export_report(self.page, data_dict, f"{item_type}_{item_id}", self.current_lang)

        def handle_reanalyze(e):
            api_key = get_api_key()
            if not api_key:
                self.page.show_dialog(ft.SnackBar(content=ft.Text(STRINGS[self.current_lang]["api_key_missing"])))
                return
            def worker():
                try:
                    reanalyze_item(item_type, item_id, api_key)
                    self.page.show_dialog(ft.SnackBar(content=ft.Text(STRINGS[self.current_lang].get("toast_reanalyze_success", "Re-analysis requested on VirusTotal!")), bgcolor="#10B981"))
                except Exception as ex:
                    msg = STRINGS[self.current_lang].get("toast_reanalyze_fail", "Re-analysis failed: {e}").format(e=str(ex))
                    self.page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor="#EF4444"))
            threading.Thread(target=worker, daemon=True).start()

        action_buttons = ft.Row([
            ft.ElevatedButton(STRINGS[self.current_lang].get("btn_reanalyze", "Re-analyze"), icon=ft.Icons.REFRESH_ROUNDED, on_click=handle_reanalyze, bgcolor="#1E293B", color="#00F0FF"),
            ft.ElevatedButton(STRINGS[self.current_lang].get("btn_export_report", "Export Report"), icon=ft.Icons.DOWNLOAD_ROUNDED, on_click=handle_export, bgcolor="#1E293B", color="#FFFFFF")
        ], alignment=ft.MainAxisAlignment.START, spacing=8)
        
        details_items = [
            ft.Row([ft.Text(STRINGS[self.current_lang]["lbl_type"], color="#94A3B8", size=12), ft.Text(item_type.upper(), color="#FFFFFF", size=12, weight=ft.FontWeight.BOLD)]),
            ft.Row([ft.Text(STRINGS[self.current_lang]["lbl_target"], color="#94A3B8", size=12), ft.Text(item_id, color="#FFFFFF", size=12, weight=ft.FontWeight.BOLD)])
        ]
        
        if item_type == "domain":
            registrar = data_dict.get("registrar")
            if registrar:
                details_items.append(ft.Row([ft.Text(STRINGS[self.current_lang]["lbl_registrar"], color="#94A3B8", size=12), ft.Text(registrar, color="#FFFFFF", size=12)]))
            reputation = data_dict.get("reputation")
            if reputation is not None:
                details_items.append(ft.Row([ft.Text(STRINGS[self.current_lang]["lbl_reputation"], color="#94A3B8", size=12), ft.Text(str(reputation), color="#FFFFFF", size=12)]))
        elif item_type == "ip":
            reputation = data_dict.get("reputation")
            if reputation is not None:
                details_items.append(ft.Row([ft.Text(STRINGS[self.current_lang]["lbl_reputation"], color="#94A3B8", size=12), ft.Text(str(reputation), color="#FFFFFF", size=12)]))
                
        details_card = ft.Container(
            content=ft.Column(details_items, spacing=6),
            padding=15,
            border=ft.Border.all(1, "#2E3C56"),
            border_radius=12,
            bgcolor="#151E33"
        )
        
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
                ft.Text(f"{STRINGS[self.current_lang]['detections_title']} ({len(mal_susp_list)})", size=15, weight=ft.FontWeight.BOLD, color="#FFFFFF")
            )
            for engine, category, res, method in mal_susp_list:
                detections_list.controls.append(make_engine_row(engine, category, res, method))
        else:
            detections_list.controls.append(
                ft.Text(STRINGS[self.current_lang]["verdict_safe"], size=13, color="#94A3B8")
            )
            
        if item_type == "domain":
            web_url = f"https://www.virustotal.com/gui/domain/{item_id}"
        elif item_type == "ip":
            web_url = f"https://www.virustotal.com/gui/ip/{item_id}"
        elif item_type == "url":
            url_id = data_dict.get("_id", "")
            web_url = f"https://www.virustotal.com/gui/url/{url_id}"
        else:
            web_url = f"https://www.virustotal.com/gui/search/{item_id}"
            
        web_btn = ft.ElevatedButton(
            content=ft.Text(STRINGS[self.current_lang]["btn_open_web"]),
            icon=ft.Icons.OPEN_IN_BROWSER_ROUNDED,
            on_click=lambda _: webbrowser.open(web_url),
            bgcolor="#008DDA",
            color="#FFFFFF",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )

        # Extended relations view for Domain & IP
        relations_view = None
        if item_type in ("domain", "ip"):
            loading_indicator = ft.Row([
                ft.ProgressRing(width=14, height=14, stroke_width=2, color="#00F0FF"),
                ft.Text(STRINGS[self.current_lang].get("dns_loading", "Загрузка DNS-резолвинга и поддоменов..."), color="#94A3B8", size=12)
            ], spacing=8)
            rel_container = ft.Column([loading_indicator], spacing=6)
            
            def load_relations():
                api_key = get_api_key()
                if not api_key:
                    rel_container.controls = [ft.Text(STRINGS[self.current_lang]["api_key_missing"], color="#F59E0B", size=12)]
                    return
                def worker():
                    items = []
                    if item_type == "domain":
                        subs = get_subdomains(item_id, api_key)
                        if subs:
                            items.append(ft.Text(STRINGS[self.current_lang].get("lbl_subdomains", "Subdomains:"), weight=ft.FontWeight.BOLD, color="#00F0FF"))
                            for s in subs[:10]:
                                sub_id = s.get("id", "")
                                items.append(ft.Text(f" • {sub_id}", color="#E2E8F0", size=12))
                    res = get_dns_resolutions(item_type, item_id, api_key)
                    if res:
                        items.append(ft.Text(STRINGS[self.current_lang].get("lbl_dns_resolutions", "DNS Resolutions:"), weight=ft.FontWeight.BOLD, color="#00F0FF"))
                        for r in res[:10]:
                            attrs = r.get("attributes", {})
                            host = attrs.get("host_name", attrs.get("ip_address", ""))
                            items.append(ft.Text(f" • {host}", color="#E2E8F0", size=12))
                    
                    if items:
                        rel_container.controls = items
                    else:
                        rel_container.controls = [ft.Text(STRINGS[self.current_lang].get("dns_no_data", "DNS-резолвинг и поддомены не найдены."), color="#64748B", size=12)]
                    
                    try:
                        self.page.update()
                    except Exception:
                        pass
                threading.Thread(target=worker, daemon=True).start()
            load_relations()
            relations_view = ft.Container(content=rel_container, padding=12, bgcolor="#151E33", border_radius=10, border=ft.Border.all(1, "#2E3C56"))

        main_items = [
            verdict_banner,
            ft.Row([action_buttons, web_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=5),
            details_card,
            stats_row,
            ft.Divider(color="#1E293B"),
            detections_list
        ]
        
        if relations_view:
            main_items.append(ft.Divider(color="#1E293B"))
            main_items.append(relations_view)
        
        return ft.Column(
            main_items,
            spacing=10,
            scroll=ft.ScrollMode.ALWAYS,
            expand=True
        )

    def build_search_results_view(self, results_list):
        if not results_list:
            return ft.Container(
                content=ft.Text(STRINGS[self.current_lang]["no_results"], color="#94A3B8", size=13),
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
                            vt_path = self.get_installed_binary_path_fn()
                            if not vt_path or not os.path.exists(vt_path):
                                raise ValueError(f"{CLI_BINARY_NAME} CLI is not installed.")
                            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
                            cmd = [vt_path, 'download', file_hash, '-o', downloads_dir]
                            proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', creationflags=_NO_WINDOW)
                            if proc.returncode == 0:
                                self.page.show_dialog(
                                    ft.SnackBar(
                                        content=ft.Text(STRINGS[self.current_lang]["download_success"], color="#FFFFFF"),
                                        bgcolor="#10B981"
                                    )
                                )
                            else:
                                raise ValueError(proc.stderr or proc.stdout)
                        except Exception as ex:
                            err_title = "Error" if self.current_lang == "en" else "Ошибка"
                            self.show_alert_fn(err_title, f"Download failed (requires premium API key): {str(ex)}")
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
                                ft.Text(f"{STRINGS[self.current_lang]['lbl_size']} {size_str}", color="#E2E8F0", size=11),
                                ft.Text(f"{STRINGS[self.current_lang]['lbl_detections']} {malicious}/{total}", color="#FF3131" if malicious > 0 else "#10B981", size=11, weight=ft.FontWeight.W_600)
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Row(
                            [
                                ft.TextButton(
                                    STRINGS[self.current_lang]["btn_download_sample"],
                                    icon=ft.Icons.DOWNLOAD_ROUNDED,
                                    on_click=make_download_handler(sha256),
                                    style=ft.ButtonStyle(color="#00F0FF")
                                ),
                                ft.TextButton(
                                    STRINGS[self.current_lang]["btn_web_report"],
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

    def build_lookup_tab(self, tab_key, placeholder_text, helper_desc):
        state = self.search_states[tab_key]
        
        input_field = ft.TextField(
            hint_text=placeholder_text,
            value=state["input"],
            on_submit=lambda e: self.run_lookup_query(tab_key),
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
            on_click=lambda e: self.run_lookup_query(tab_key),
            height=48,
            width=48
        )

        buttons_row = [input_field, search_btn]

        if tab_key == "url":
            def trigger_live_scan(e):
                val = state["input"].strip()
                if not val:
                    return
                api_key = get_api_key()
                if not api_key:
                    self.show_alert_fn("Error", STRINGS[self.current_lang]["api_key_missing"])
                    return
                state["status"] = "loading"
                self.build_ui_fn()
                def worker():
                    try:
                        submit_url_scan(val, api_key)
                        self.run_lookup_query("url")
                    except Exception as ex:
                        state["status"] = "error"
                        state["error"] = str(ex)
                        self.thread_safe_build_fn()
                threading.Thread(target=worker, daemon=True).start()

            live_scan_btn = ft.ElevatedButton(
                STRINGS[self.current_lang].get("btn_live_scan_url", "Scan Live URL"),
                icon=ft.Icons.TRAVEL_EXPLORE_ROUNDED,
                on_click=trigger_live_scan,
                bgcolor="#008DDA",
                color="#FFFFFF"
            )
            buttons_row.append(live_scan_btn)
        
        results_area = ft.Container(expand=True, alignment=ft.Alignment.CENTER)
        
        if state["status"] == "loading":
            results_area.content = ft.Column(
                [
                    ft.ProgressRing(color="#00F0FF", width=36, height=36),
                    ft.Text(STRINGS[self.current_lang]["querying_vt"], color="#00F0FF", size=13)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            )
        elif state["status"] == "error":
            error_items = [
                ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color="#EF4444", size=32),
                ft.Text(state["error"], color="#EF4444", size=13, text_align=ft.TextAlign.CENTER),
                ft.ElevatedButton(
                    content=ft.Text(STRINGS[self.current_lang]["btn_upgrade_premium"], color="#FFFFFF", size=13),
                    icon=ft.Icons.OPEN_IN_BROWSER_ROUNDED,
                    on_click=lambda _: webbrowser.open("https://www.virustotal.com/gui/contact-us/premium-services"),
                    bgcolor="#008DDA",
                    color="#FFFFFF",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                )
            ]
            results_area.content = ft.Column(
                error_items,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            )
        elif state["status"] == "success" and state["results"] is not None:
            if tab_key == "search":
                results_area.content = self.build_search_results_view(state["results"])
            else:
                results_area.content = self.build_lookup_results_view(state["results"], tab_key, state["input"].strip())
        else:
            results_area.content = ft.Container(
                content=ft.Text(helper_desc, color="#94A3B8", size=13, text_align=ft.TextAlign.CENTER),
                alignment=ft.Alignment(0, 0)
            )
            
        return ft.Column(
            [
                ft.Row(buttons_row, spacing=10),
                ft.Divider(color="#2E3C56", height=1),
                results_area
            ],
            spacing=10,
            expand=True
        )

    def run_lookup_query(self, tab_key):
        state = self.search_states[tab_key]
        query_val = state["input"].strip()
        if not query_val:
            return
            
        state["status"] = "loading"
        state["error"] = None
        state["results"] = None
        self.build_ui_fn()
        
        def execute_query():
            try:
                vt_path = self.get_installed_binary_path_fn()
                if not vt_path or not os.path.exists(vt_path):
                    raise ValueError(f"{CLI_BINARY_NAME} CLI is not installed.")
                    
                if tab_key == "url":
                    cmd = [vt_path, 'url', query_val, '--format', 'json']
                elif tab_key == "domain":
                    cmd = [vt_path, 'domain', query_val, '--format', 'json']
                elif tab_key == "ip":
                    cmd = [vt_path, 'ip', query_val, '--format', 'json']
                elif tab_key == "search":
                    cmd = [vt_path, 'search', query_val, '--format', 'json']
                    
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=_NO_WINDOW
                )
                if proc.returncode != 0:
                    err_msg = proc.stderr or proc.stdout
                    if "You are not authorized" in err_msg:
                        raise ValueError(STRINGS[self.current_lang]["premium_required_err"])
                    raise ValueError(err_msg.strip())
                    
                stdout = proc.stdout.strip()
                if not stdout:
                    raise ValueError("Empty response from VirusTotal. The URL may not have been analyzed yet.")
                    
                data = json.loads(stdout)
                if isinstance(data, list) and len(data) > 0:
                    if tab_key != "search":
                        data = data[0]
                elif isinstance(data, list) and len(data) == 0:
                    data = None
                    
                state["results"] = data
                state["status"] = "success"
                add_lookup_record(
                    lookup_type=tab_key,
                    query=query_val,
                    status="completed",
                    results=data
                )
            except Exception as ex:
                state["status"] = "error"
                state["error"] = str(ex)
                add_lookup_record(
                    lookup_type=tab_key,
                    query=query_val,
                    status="failed",
                    error=str(ex)
                )
                
            self.thread_safe_build_fn()
            
        threading.Thread(target=execute_query, daemon=True).start()
