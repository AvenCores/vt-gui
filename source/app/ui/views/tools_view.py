import sys
import json
import threading
import subprocess
import flet as ft

from ...core.config import STRINGS, get_api_key
from ...api.vt_api import check_file_exists_direct, check_file_exists_vt, get_yara_rulesets
from ...api.cli_manager import get_installed_binary_path
from ...services.history_service import add_lookup_record
from ..components.theme import get_theme_palette

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


class ToolsView:
    def __init__(self, lang, show_alert_fn, page: ft.Page, theme_mode="dark"):
        self.lang = lang
        self.show_alert_fn = show_alert_fn
        self.page = page
        self.theme_mode = theme_mode
        self.palette = get_theme_palette(theme_mode)
        self.active_subtab_index = 0
        
        # State for File Diff
        self.diff_hash1 = ""
        self.diff_hash2 = ""
        self.diff_status = "idle"
        self.diff_results = None
        self.diff_error = None
        
        # State for YARA
        self.yara_rulesets = []
        self.yara_status = "idle"
        self.yara_error = None

    def build_tools_tab(self):
        diff_card = self._build_diff_card()
        yara_card = self._build_yara_card()
        
        subtab_definitions = [
            (0, STRINGS[self.lang].get("tab_diff", "File Comparison (vt diff)"), ft.Icons.COMPARE_ARROWS_ROUNDED, diff_card),
            (1, STRINGS[self.lang].get("tab_yara", "YARA Rulesets (Livehunt)"), ft.Icons.BUG_REPORT_ROUNDED, yara_card),
        ]

        subtab_views_map = {idx: v for idx, _, _, v in subtab_definitions}

        animated_subtab_content = ft.AnimatedSwitcher(
            content=ft.Container(
                key=f"subtab_container_{self.active_subtab_index}",
                content=subtab_views_map[self.active_subtab_index],
                padding=10,
                expand=True
            ),
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=250,
            reverse_duration=200,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
            switch_out_curve=ft.AnimationCurve.EASE_IN,
            expand=True
        )

        subtab_buttons = []
        subtab_buttons_map = {}

        def update_subtab_buttons():
            for idx, btn in subtab_buttons_map.items():
                is_active = (self.active_subtab_index == idx)
                btn.border = ft.Border.all(1, self.palette["accent"] if is_active else "transparent")
                btn.bgcolor = self.palette["tab_active_bg"] if is_active else "transparent"
                col = btn.content
                col.controls[0].color = self.palette["accent"] if is_active else self.palette["text_muted"]
                col.controls[1].color = self.palette["text_primary"] if is_active else self.palette["text_muted"]
                try:
                    btn.update()
                except Exception:
                    pass

        def select_subtab(idx):
            if self.active_subtab_index == idx:
                return
            self.active_subtab_index = idx
            update_subtab_buttons()
            animated_subtab_content.content = ft.Container(
                key=f"subtab_container_{idx}",
                content=subtab_views_map[idx],
                padding=10,
                expand=True
            )
            try:
                animated_subtab_content.update()
            except Exception:
                pass

        for idx, label, icon, _ in subtab_definitions:
            is_active = (self.active_subtab_index == idx)
            
            subtab_btn = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(icon, color=self.palette["accent"] if is_active else self.palette["text_muted"], size=20),
                        ft.Text(label, color=self.palette["text_primary"] if is_active else self.palette["text_muted"], size=12, weight=ft.FontWeight.W_600)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2
                ),
                padding=ft.Padding(left=12, right=12, top=6, bottom=6),
                height=70,
                border_radius=8,
                border=ft.Border.all(1, self.palette["accent"] if is_active else "transparent"),
                bgcolor=self.palette["tab_active_bg"] if is_active else "transparent",
                animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
                on_click=lambda _, i=idx: select_subtab(i)
            )

            def make_hover_handler(btn, tab_idx):
                def on_tab_hover(e):
                    if self.active_subtab_index != tab_idx:
                        if e.data == "true":
                            btn.border = ft.Border.all(1, self.palette["tab_inactive_hover_border"])
                            btn.bgcolor = self.palette["tab_inactive_hover_bg"]
                        else:
                            btn.border = ft.Border.all(1, "transparent")
                            btn.bgcolor = "transparent"
                        try:
                            btn.update()
                        except Exception:
                            pass
                return on_tab_hover

            subtab_btn.on_hover = make_hover_handler(subtab_btn, idx)
            subtab_buttons.append(subtab_btn)
            subtab_buttons_map[idx] = subtab_btn

        subtab_header_row = ft.Row(
            subtab_buttons,
            spacing=2,
            alignment=ft.MainAxisAlignment.START
        )

        return ft.Column(
            [
                ft.Container(
                    content=subtab_header_row,
                    padding=ft.Padding(left=4, right=4, top=0, bottom=20),
                    border=ft.Border(bottom=ft.BorderSide(1, self.palette["divider"]))
                ),
                animated_subtab_content
            ],
            expand=True,
            spacing=10
        )

    def _build_diff_card(self):
        hash1_field = ft.TextField(
            label=STRINGS[self.lang].get("hash_1_label", "SHA-256 Hash #1"),
            hint_text=STRINGS[self.lang].get("hash_1_hint", "First hash to compare"),
            value=self.diff_hash1,
            border_color=self.palette["input_border"],
            focused_border_color=self.palette["accent"],
            bgcolor=self.palette["input_bg"],
            color=self.palette["text_primary"],
            label_style=ft.TextStyle(color=self.palette["text_muted"]),
            expand=True,
            on_change=lambda e: setattr(self, 'diff_hash1', e.control.value.strip())
        )
        
        hash2_field = ft.TextField(
            label=STRINGS[self.lang].get("hash_2_label", "SHA-256 Hash #2"),
            hint_text=STRINGS[self.lang].get("hash_2_hint", "Second hash to compare"),
            value=self.diff_hash2,
            border_color=self.palette["input_border"],
            focused_border_color=self.palette["accent"],
            bgcolor=self.palette["input_bg"],
            color=self.palette["text_primary"],
            label_style=ft.TextStyle(color=self.palette["text_muted"]),
            expand=True,
            on_change=lambda e: setattr(self, 'diff_hash2', e.control.value.strip())
        )
        
        results_container = ft.Container(expand=True, alignment=ft.Alignment.CENTER)

        def update_diff_ui():
            if self.diff_status == "loading":
                results_container.content = ft.Column([
                    ft.ProgressRing(color=self.palette["accent"]),
                    ft.Text(STRINGS[self.lang].get("diff_comparing", "Comparing hashes via VirusTotal CLI..."), color=self.palette["accent"])
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            elif self.diff_status == "error":
                results_container.content = ft.Column([
                    ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color="#EF4444", size=32),
                    ft.Text(f"Diff Error: {self.diff_error}", color="#EF4444", text_align=ft.TextAlign.CENTER)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            elif self.diff_status == "success" and self.diff_results:
                f1 = self.diff_results.get("file1", {})
                f2 = self.diff_results.get("file2", {})
                
                a1 = f1.get("attributes", f1.get("data", {}).get("attributes", {})) if isinstance(f1, dict) else {}
                a2 = f2.get("attributes", f2.get("data", {}).get("attributes", {})) if isinstance(f2, dict) else {}

                is_same = (self.diff_hash1.lower() == self.diff_hash2.lower())
                
                # Extract properties
                name1 = (a1.get("names", [self.diff_hash1[:12]]) or [self.diff_hash1[:12]])[0]
                name2 = (a2.get("names", [self.diff_hash2[:12]]) or [self.diff_hash2[:12]])[0]
                
                size1 = f"{a1.get('size', 0) / 1024:.1f} KB" if a1.get('size') else "N/A"
                size2 = f"{a2.get('size', 0) / 1024:.1f} KB" if a2.get('size') else "N/A"
                
                det1 = str(a1.get("last_analysis_stats", {}).get("malicious", "0"))
                det2 = str(a2.get("last_analysis_stats", {}).get("malicious", "0"))
                
                type1 = a1.get("type_description", a1.get("type_tag", "Unknown"))
                type2 = a2.get("type_description", a2.get("type_tag", "Unknown"))
                
                imp1 = a1.get("pe_info", {}).get("imphash", "N/A")
                imp2 = a2.get("pe_info", {}).get("imphash", "N/A")

                banner = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED if is_same else ft.Icons.COMPARE_ARROWS_ROUNDED, color="#10B981" if is_same else self.palette["accent"], size=22),
                        ft.Text(
                            STRINGS[self.lang].get("diff_same_hashes", "Identical Hashes: Files match 100%") if is_same else STRINGS[self.lang].get("diff_different_hashes", "Comparison Breakdown between File #1 and File #2:"),
                            weight=ft.FontWeight.BOLD,
                            color="#10B981" if is_same else self.palette["text_primary"],
                            size=13
                        )
                    ], spacing=8),
                    padding=10, border_radius=8, bgcolor="#10B98122" if is_same else self.palette["accent_bg"], border=ft.Border.all(1, "#10B981" if is_same else self.palette["accent"])
                )

                def make_row(prop_name, v1, v2):
                    match = (v1 == v2)
                    st_text = STRINGS[self.lang].get("status_match", "Match") if match else STRINGS[self.lang].get("status_differ", "Differ")
                    st_color = "#10B981" if match else "#EF4444"
                    
                    return ft.Container(
                        content=ft.Row([
                            ft.Text(prop_name, weight=ft.FontWeight.BOLD, color=self.palette["text_muted"], width=130, size=11),
                            ft.Text(str(v1), color=self.palette["text_secondary"], width=220, size=11, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(str(v2), color=self.palette["text_secondary"], width=220, size=11, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Container(
                                content=ft.Text(st_text, color="#FFFFFF", size=10, weight=ft.FontWeight.BOLD),
                                padding=ft.Padding(left=8, top=2, right=8, bottom=2),
                                border_radius=4,
                                bgcolor=st_color
                            )
                        ], alignment=ft.MainAxisAlignment.START, spacing=10),
                        padding=8,
                        border=ft.Border(bottom=ft.BorderSide(1, self.palette["divider"]))
                    )

                lbl_prop = STRINGS[self.lang].get("attr_property", "Property")
                lbl_f1 = STRINGS[self.lang].get("card_file_hash_1", "File Hash #1")
                lbl_f2 = STRINGS[self.lang].get("card_file_hash_2", "File Hash #2")
                lbl_st = STRINGS[self.lang].get("attr_status", "Status")
                
                header_row = ft.Container(
                    content=ft.Row([
                        ft.Text(lbl_prop, weight=ft.FontWeight.BOLD, color=self.palette["accent"], width=130, size=12),
                        ft.Text(lbl_f1, weight=ft.FontWeight.BOLD, color=self.palette["accent"], width=220, size=12),
                        ft.Text(lbl_f2, weight=ft.FontWeight.BOLD, color=self.palette["accent"], width=220, size=12),
                        ft.Text(lbl_st, weight=ft.FontWeight.BOLD, color=self.palette["accent"], size=12)
                    ], alignment=ft.MainAxisAlignment.START, spacing=10),
                    padding=8,
                    bgcolor=self.palette["card_bg_secondary"],
                    border_radius=6
                )

                h1_str = (self.diff_hash1[:16] + "...") if len(self.diff_hash1) > 16 else self.diff_hash1
                h2_str = (self.diff_hash2[:16] + "...") if len(self.diff_hash2) > 16 else self.diff_hash2

                table_rows = [
                    banner,
                    header_row,
                    make_row("SHA-256", h1_str, h2_str),
                    make_row(STRINGS[self.lang].get("lbl_file_name", "Name:").replace(":", ""), name1, name2),
                    make_row(STRINGS[self.lang].get("lbl_size_card", "Size:").replace(":", ""), size1, size2),
                    make_row(STRINGS[self.lang].get("lbl_detections_card", "Detections:").replace(":", ""), det1, det2),
                    make_row("Type / Format", type1, type2)
                ]

                md5_1 = a1.get("md5", "N/A")
                md5_2 = a2.get("md5", "N/A")
                if md5_1 != "N/A" or md5_2 != "N/A":
                    table_rows.append(make_row("MD5", md5_1[:12]+"..." if len(md5_1)>12 else md5_1, md5_2[:12]+"..." if len(md5_2)>12 else md5_2))

                if imp1 != "N/A" or imp2 != "N/A":
                    table_rows.append(make_row("Imphash", imp1, imp2))

                auth1 = a1.get("authentihash", "N/A")
                auth2 = a2.get("authentihash", "N/A")
                if auth1 != "N/A" or auth2 != "N/A":
                    table_rows.append(make_row("Authentihash", auth1[:12]+"...", auth2[:12]+"..."))

                results_container.content = ft.Column(table_rows, spacing=4, scroll=ft.ScrollMode.ALWAYS, expand=True)
            else:
                results_container.content = ft.Text(STRINGS[self.lang].get("diff_prompt", "Enter two file hashes above to compare detections, PE headers, and metadata."), color=self.palette["text_muted"])
            
            try:
                self.page.update()
            except Exception:
                pass

        update_diff_ui()
        
        def run_diff(e):
            if not self.diff_hash1 or not self.diff_hash2:
                err_msg = STRINGS[self.lang].get("compare_hashes_prompt", "Please enter both SHA-256 hashes to compare.")
                err_title = STRINGS[self.lang].get("error_title", "Error")
                self.show_alert_fn(err_title, err_msg)
                return
                
            self.diff_status = "loading"
            self.diff_results = None
            self.diff_error = None
            update_diff_ui()
            
            def worker():
                vt_path = get_installed_binary_path()
                api_key = get_api_key()
                
                try:
                    f1 = check_file_exists_direct(self.diff_hash1, api_key) or (check_file_exists_vt(vt_path, self.diff_hash1) if vt_path else None) or {}
                    f2 = check_file_exists_direct(self.diff_hash2, api_key) or (check_file_exists_vt(vt_path, self.diff_hash2) if vt_path else None) or {}
                    
                    self.diff_results = {"file1": f1, "file2": f2}
                    self.diff_status = "success"
                except Exception as ex:
                    self.diff_status = "error"
                    self.diff_error = str(ex)
                
                add_lookup_record(
                    "diff",
                    f"{self.diff_hash1[:8]}... vs {self.diff_hash2[:8]}...",
                    "completed" if self.diff_status == "success" else "failed",
                    results=self.diff_results,
                    error=self.diff_error
                )

                update_diff_ui()

            threading.Thread(target=worker, daemon=True).start()

        diff_btn = ft.Button(
            STRINGS[self.lang].get("btn_compare_hashes", "Compare Hashes"),
            icon=ft.Icons.COMPARE_ARROWS_ROUNDED,
            on_click=run_diff,
            bgcolor=self.palette["button_primary_bg"],
            color="#FFFFFF"
        )

        return ft.Column([
            ft.Row([hash1_field, hash2_field], spacing=10),
            ft.Row([diff_btn], alignment=ft.MainAxisAlignment.END),
            ft.Divider(color=self.palette["divider"]),
            results_container
        ], expand=True, spacing=10)

    def _build_yara_card(self):
        yara_body_container = ft.Container(expand=True, alignment=ft.Alignment.CENTER)
        
        def update_yara_ui():
            if self.yara_status == "loading":
                yara_body_container.content = ft.Column([ft.ProgressRing(color=self.palette["accent"]), ft.Text(STRINGS[self.lang].get("yara_loading", "Loading YARA Rulesets..."), color=self.palette["accent"])], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            elif self.yara_status == "error":
                yara_body_container.content = ft.Column([
                    ft.Icon(ft.Icons.LOCK_ROUNDED, color="#FFD700" if self.theme_mode == "dark" else "#D97706", size=32),
                    ft.Text(self.yara_error or "Could not fetch YARA rulesets", color=self.palette["text_secondary"], text_align=ft.TextAlign.CENTER)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            elif self.yara_rulesets:
                items = []
                for r in self.yara_rulesets:
                    name = r.get("name", r.get("id", "Ruleset"))
                    items.append(ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.CODE_ROUNDED, color=self.palette["accent"]),
                            ft.Text(name, color=self.palette["text_primary"], weight=ft.FontWeight.BOLD)
                        ]),
                        padding=10, border_radius=8, bgcolor=self.palette["card_bg"], border=ft.Border.all(1, self.palette["card_border"])
                    ))
                yara_body_container.content = ft.Column(items, scroll=ft.ScrollMode.ALWAYS, expand=True)
            else:
                yara_body_container.content = ft.Text(STRINGS[self.lang].get("yara_load_prompt", "Click refresh to load your VirusTotal Livehunt YARA rulesets."), color=self.palette["text_muted"])
            
            try:
                self.page.update()
            except Exception:
                pass

        update_yara_ui()

        def refresh_yara(e=None):
            self.yara_status = "loading"
            update_yara_ui()
            
            def worker():
                api_key = get_api_key()
                vt_path = get_installed_binary_path()
                
                # Method 1: VirusTotal API v3
                if api_key:
                    try:
                        rules = get_yara_rulesets(api_key)
                        if rules:
                            self.yara_rulesets = rules
                            self.yara_status = "success"
                            update_yara_ui()
                            return
                    except Exception as ex:
                        if "Premium" in str(ex) or "403" in str(ex):
                            msg = STRINGS[self.lang].get("yara_premium_required", "YARA Livehunt rulesets require a VirusTotal Premium API key.")
                            self.yara_status = "error"
                            self.yara_error = msg
                            update_yara_ui()
                            return

                # Method 2: VT CLI binary fallback
                if vt_path:
                    try:
                        cmd = [vt_path, 'yara', 'list', '--format', 'json']
                        proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', creationflags=_NO_WINDOW)
                        if proc.returncode == 0 and proc.stdout.strip():
                            data = json.loads(proc.stdout)
                            self.yara_rulesets = data if isinstance(data, list) else [data]
                            self.yara_status = "success"
                            update_yara_ui()
                            return
                        else:
                            err = proc.stderr or proc.stdout
                            if "You are not authorized" in err or "403" in err:
                                err = STRINGS[self.lang].get("yara_premium_required", "YARA Livehunt rulesets require a VirusTotal Premium API key.")
                            self.yara_status = "error"
                            self.yara_error = err or STRINGS[self.lang].get("yara_no_rules", "No YARA rulesets available.")
                            update_yara_ui()
                            return
                    except Exception as ex:
                        self.yara_status = "error"
                        self.yara_error = str(ex)
                        update_yara_ui()
                        return

                add_lookup_record(
                    "yara",
                    f"YARA Rules ({len(self.yara_rulesets)} rulesets)" if self.yara_status == "success" else "YARA Livehunt",
                    "completed" if self.yara_status == "success" else "failed",
                    results=self.yara_rulesets,
                    error=self.yara_error
                )

                update_yara_ui()

            threading.Thread(target=worker, daemon=True).start()

        refresh_btn = ft.IconButton(ft.Icons.REFRESH_ROUNDED, icon_color=self.palette["accent"], on_click=refresh_yara, tooltip=STRINGS[self.lang].get("yara_refresh_tooltip", "Refresh Rulesets"))

        return ft.Column([
            ft.Row([
                ft.Text(STRINGS[self.lang].get("tab_yara", "YARA Rulesets (Livehunt)"), size=16, weight=ft.FontWeight.BOLD, color=self.palette["text_primary"]),
                refresh_btn
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(color=self.palette["divider"]),
            yara_body_container
        ], expand=True)
