import flet as ft
import os
import threading
from ..config import STRINGS, get_api_key
from ..vt_api import reanalyze_item, get_file_behaviours, get_comments, add_comment, vote_item, get_user_vote
from ..exporter import export_report_to_file, prompt_export_report
from .theme import make_stat_card, make_file_details_card, make_engine_row

def build_results_view(current_scan_results, selected_target_file, last_completed_sha256, lang, page):
    """Builds the enhanced results dashboard, showing detections, behaviors, comments, voting, and export options."""
    
    def get_stats_and_results(data_dict):
        data = data_dict.get("data", {})
        attributes = data.get("attributes")
        if attributes:
            stats = attributes.get("last_analysis_stats")
            results = attributes.get("last_analysis_results")
            names = attributes.get("names", [])
            size = attributes.get("size", 0)
            return stats, results, names, size, attributes
            
        if isinstance(data_dict, list) and len(data_dict) > 0:
            data_dict = data_dict[0]
            
        stats = data_dict.get("last_analysis_stats")
        results = data_dict.get("last_analysis_results")
        names = data_dict.get("names", [])
        attrs = data_dict.get("attributes", {})
        size = attrs.get("size", data_dict.get("size", 0))
        return stats, results, names, size, attrs

    stats, results_dict, names, size, attributes = get_stats_and_results(current_scan_results)
    
    filename = selected_target_file if selected_target_file else "Unknown_File"
    if names:
        filename = names[0]
    else:
        filename = os.path.basename(filename)
        
    malicious = stats.get("malicious", 0) if stats else 0
    suspicious = stats.get("suspicious", 0) if stats else 0
    harmless = stats.get("harmless", 0) if stats else 0
    undetected = stats.get("undetected", 0) if stats else 0
    
    # 1. Verdict Banner
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
    
    # 2. Action Bar (Re-analyze, Export, Vote)
    def handle_reanalyze(e):
        api_key = get_api_key()
        if not api_key:
            page.show_dialog(ft.SnackBar(content=ft.Text(STRINGS[lang]["api_key_missing"])))
            return
            
        def worker():
            try:
                reanalyze_item("file", last_completed_sha256, api_key)
                page.show_dialog(ft.SnackBar(content=ft.Text(STRINGS[lang].get("toast_reanalyze_success", "Re-analysis requested on VirusTotal!")), bgcolor="#10B981"))
            except Exception as ex:
                msg = STRINGS[lang].get("toast_reanalyze_fail", "Re-analysis failed: {e}").format(e=str(ex))
                page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor="#EF4444"))
        threading.Thread(target=worker, daemon=True).start()

    def handle_export(e):
        prompt_export_report(page, current_scan_results, filename, lang)

    target_sha256 = (
        last_completed_sha256
        or attributes.get("sha256")
        or attributes.get("md5")
        or current_scan_results.get("sha256")
        or current_scan_results.get("data", {}).get("id")
        or current_scan_results.get("data", {}).get("attributes", {}).get("sha256")
        or ""
    )

    user_vote_state = [None]  # "harmless", "malicious", or None
    is_voting_state = [False]

    vote_buttons_container = ft.Row(spacing=6)

    def handle_vote(verdict):
        def vote_action(e):
            if is_voting_state[0]:
                return
            api_key = get_api_key()
            if not api_key:
                page.show_dialog(ft.SnackBar(content=ft.Text(STRINGS[lang]["api_key_missing"])))
                return
            if not target_sha256:
                page.show_dialog(ft.SnackBar(content=ft.Text("SHA-256 is missing for voting."), bgcolor="#EF4444"))
                return

            if user_vote_state[0] == verdict:
                verdict_word = STRINGS[lang].get(f"verdict_{verdict}_word", verdict)
                msg = STRINGS[lang].get("already_voted", "Already voted '{verdict}' for this file.").format(verdict=verdict_word)
                page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor="#008DDA"))
                return

            is_voting_state[0] = True
            update_vote_ui()

            def worker():
                try:
                    vote_item("files", target_sha256, verdict, api_key)
                    user_vote_state[0] = verdict
                    is_voting_state[0] = False
                    update_vote_ui()
                    verdict_word = STRINGS[lang].get(f"verdict_{verdict}_word", verdict)
                    msg = STRINGS[lang].get("toast_vote_success", "Voted '{verdict}' successfully!").format(verdict=verdict_word)
                    page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor="#10B981"))
                except Exception as ex:
                    is_voting_state[0] = False
                    update_vote_ui()
                    msg = STRINGS[lang].get("toast_vote_fail", "Vote failed: {e}").format(e=str(ex))
                    page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor="#EF4444"))
            threading.Thread(target=worker, daemon=True).start()
        return vote_action

    def update_vote_ui():
        controls = []
        if is_voting_state[0]:
            controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.ProgressRing(width=14, height=14, stroke_width=2, color="#00F0FF"),
                        ft.Text(STRINGS[lang].get("voting_progress", "Sending vote..."), color="#94A3B8", size=11)
                    ], spacing=6),
                    padding=ft.Padding(left=8, right=8, top=4, bottom=4),
                    bgcolor="#151E33",
                    border_radius=8,
                    border=ft.Border.all(1, "#00F0FF")
                )
            )
        else:
            is_harmless = (user_vote_state[0] == "harmless")
            is_malicious = (user_vote_state[0] == "malicious")

            harmless_label = STRINGS[lang].get("vote_harmless", "Vote Harmless") if not is_harmless else STRINGS[lang].get("voted_harmless", "Voted Harmless")
            malicious_label = STRINGS[lang].get("vote_malicious", "Vote Malicious") if not is_malicious else STRINGS[lang].get("voted_malicious", "Voted Malicious")

            harmless_btn = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.THUMBS_UP_DOWN_ROUNDED, color="#10B981" if is_harmless else "#39FF14", size=18),
                    ft.Text(harmless_label, color="#10B981" if is_harmless else "#E2E8F0", size=11, weight=ft.FontWeight.BOLD if is_harmless else ft.FontWeight.NORMAL)
                ], spacing=4),
                padding=ft.Padding(left=10, right=10, top=6, bottom=6),
                border_radius=8,
                bgcolor="#10B98122" if is_harmless else "#1E293B",
                border=ft.Border.all(1, "#10B981" if is_harmless else "#2E3C56"),
                on_click=handle_vote("harmless"),
                tooltip=STRINGS[lang].get("vote_harmless", "Vote Harmless")
            )

            malicious_btn = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.THUMB_DOWN_ALT_ROUNDED, color="#EF4444", size=18),
                    ft.Text(malicious_label, color="#EF4444" if is_malicious else "#E2E8F0", size=11, weight=ft.FontWeight.BOLD if is_malicious else ft.FontWeight.NORMAL)
                ], spacing=4),
                padding=ft.Padding(left=10, right=10, top=6, bottom=6),
                border_radius=8,
                bgcolor="#EF444422" if is_malicious else "#1E293B",
                border=ft.Border.all(1, "#EF4444" if is_malicious else "#2E3C56"),
                on_click=handle_vote("malicious"),
                tooltip=STRINGS[lang].get("vote_malicious", "Vote Malicious")
            )

            controls.extend([harmless_btn, malicious_btn])

        vote_buttons_container.controls = controls
        try:
            page.update()
        except Exception:
            pass

    def load_user_vote():
        api_key = get_api_key()
        if not api_key or not target_sha256:
            return
        def worker():
            v = get_user_vote("files", target_sha256, api_key)
            if v:
                user_vote_state[0] = v
                update_vote_ui()
        threading.Thread(target=worker, daemon=True).start()

    load_user_vote()
    update_vote_ui()

    actions_row = ft.Row([
        ft.ElevatedButton(STRINGS[lang].get("btn_reanalyze", "Re-analyze"), icon=ft.Icons.REFRESH_ROUNDED, on_click=handle_reanalyze, bgcolor="#1E293B", color="#00F0FF"),
        ft.ElevatedButton(STRINGS[lang].get("btn_export_report", "Export Report"), icon=ft.Icons.DOWNLOAD_ROUNDED, on_click=handle_export, bgcolor="#1E293B", color="#FFFFFF"),
        vote_buttons_container
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    details_card = make_file_details_card(filename, size, last_completed_sha256, STRINGS, lang)
    
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

    # Tab 1: Detections
    detections_list = ft.Column(spacing=5, expand=True)
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
    
    detections_tab_view = ft.Column([
        detections_list,
        ft.Container(height=10),
        show_all_btn,
        full_list_column
    ], scroll=ft.ScrollMode.ALWAYS, expand=True)

    # Tab 2: Behavior & Sandbox Reports
    behavior_container = ft.Column(spacing=8, scroll=ft.ScrollMode.ALWAYS, expand=True)
    behavior_loaded = False

    def load_behavior(e=None):
        nonlocal behavior_loaded
        if behavior_loaded:
            return
        behavior_container.controls = [ft.ProgressRing(color="#00F0FF"), ft.Text(STRINGS[lang].get("behavior_loading", "Loading sandbox reports..."), color="#00F0FF")]
        page.update()
        
        def worker():
            nonlocal behavior_loaded
            api_key = get_api_key()
            if not api_key:
                behavior_container.controls = [ft.Text(STRINGS[lang].get("api_key_missing", "API key required."), color="#EF4444")]
                page.update()
                return
            behaviours = get_file_behaviours(last_completed_sha256, api_key)
            behavior_loaded = True
            behavior_container.controls.clear()
            
            if not behaviours:
                behavior_container.controls.append(ft.Text(STRINGS[lang].get("behavior_empty", "No sandbox execution reports available for this file."), color="#94A3B8"))
            else:
                for idx, b in enumerate(behaviours):
                    attrs = b.get("attributes", {})
                    sandbox_name = attrs.get("sandbox_name", f"Sandbox #{idx+1}")
                    tags = attrs.get("tags", [])
                    mitre = attrs.get("mitre_attack_techniques", [])
                    
                    details = [
                        ft.Text(f"Sandbox: {sandbox_name.upper()}", weight=ft.FontWeight.BOLD, color="#00F0FF", size=14),
                        ft.Text(f"Tags: {', '.join(tags) if tags else 'None'}", color="#94A3B8", size=11)
                    ]
                    
                    if mitre:
                        details.append(ft.Text(f"MITRE ATT&CK Techniques: {len(mitre)} detected", weight=ft.FontWeight.W_600, color="#FFD700", size=12))
                        for m in mitre[:5]:
                            tech_id = m.get("signature_description", m.get("id", ""))
                            details.append(ft.Text(f" • {tech_id}", color="#E2E8F0", size=11))

                    behavior_container.controls.append(ft.Container(
                        content=ft.Column(details, spacing=4),
                        padding=12, border_radius=10, bgcolor="#151E33", border=ft.Border.all(1, "#2E3C56")
                    ))
            page.update()
        threading.Thread(target=worker, daemon=True).start()

    # Tab 3: Comments
    comments_container = ft.Column(spacing=8, scroll=ft.ScrollMode.ALWAYS, expand=True)
    comment_input = ft.TextField(hint_text=STRINGS[lang].get("post_comment_hint", "Write a community note or comment..."), border_color="#2E3C56", expand=True)
    
    def post_comment(e):
        txt = comment_input.value.strip()
        if not txt:
            return
        api_key = get_api_key()
        if not api_key:
            page.show_dialog(ft.SnackBar(content=ft.Text(STRINGS[lang]["api_key_missing"])))
            return
        def worker():
            try:
                add_comment("files", last_completed_sha256, txt, api_key)
                comment_input.value = ""
                load_comments()
                page.show_dialog(ft.SnackBar(content=ft.Text(STRINGS[lang].get("toast_comment_success", "Comment posted!")), bgcolor="#10B981"))
            except Exception as ex:
                msg = STRINGS[lang].get("toast_comment_fail", "Failed to post comment: {e}").format(e=str(ex))
                page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor="#EF4444"))
        threading.Thread(target=worker, daemon=True).start()

    def load_comments(e=None):
        api_key = get_api_key()
        if not api_key:
            comments_container.controls = [ft.Text(STRINGS[lang].get("api_key_missing", "API key required."), color="#94A3B8")]
            page.update()
            return
            
        def worker():
            comms = get_comments("files", last_completed_sha256, api_key)
            comments_container.controls.clear()
            if not comms:
                comments_container.controls.append(ft.Text(STRINGS[lang].get("comments_empty", "No community comments yet."), color="#94A3B8"))
            else:
                for c in comms:
                    attrs = c.get("attributes", {})
                    txt = attrs.get("text", "")
                    date_val = attrs.get("date", 0)
                    comments_container.controls.append(ft.Container(
                        content=ft.Column([
                            ft.Text(txt, color="#E2E8F0", size=12),
                        ], spacing=3),
                        padding=10, border_radius=8, bgcolor="#151E33", border=ft.Border.all(1, "#2E3C56")
                    ))
            page.update()
        threading.Thread(target=worker, daemon=True).start()

    load_comments()

    comments_tab_view = ft.Column([
        ft.Row([comment_input, ft.IconButton(ft.Icons.SEND_ROUNDED, icon_color="#00F0FF", on_click=post_comment)]),
        ft.Divider(color="#2E3C56"),
        comments_container
    ], expand=True)

    tabs = ft.Tabs(
        length=3,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label=STRINGS[lang].get("tab_detections", "Detections"), icon=ft.Icons.SECURITY_ROUNDED),
                        ft.Tab(label=STRINGS[lang].get("tab_behavior", "Behavior / Sandbox"), icon=ft.Icons.MISCELLANEOUS_SERVICES_ROUNDED),
                        ft.Tab(label=STRINGS[lang].get("tab_comments", "Comments"), icon=ft.Icons.COMMENT_ROUNDED)
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        ft.Container(content=detections_tab_view, padding=5),
                        ft.Container(content=behavior_container, padding=5, on_hover=load_behavior),
                        ft.Container(content=comments_tab_view, padding=5)
                    ]
                )
            ]
        )
    )
    
    return ft.Column([
        verdict_banner,
        actions_row,
        details_card,
        stats_row,
        ft.Divider(color="#1E293B"),
        tabs
    ], expand=True, spacing=10)
