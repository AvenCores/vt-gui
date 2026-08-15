import flet as ft
import os
import threading

from ...core.config import STRINGS, get_api_key
from ...api.vt_api import reanalyze_item, get_file_behaviours, get_comments, add_comment, delete_comment, vote_item, get_user_vote
from ...services.export_service import prompt_export_report
from ..components.theme import make_stat_card, make_file_details_card, make_engine_row, make_loading_card, get_theme_palette

# Module-level state caches to preserve UI state across theme toggles and rerenders
_VOTE_CACHE = {}
_ACTIVE_RES_TAB = {}
_ENGINES_EXPANDED = {}
_BEHAVIORS_CACHE = {}
_COMMENTS_CACHE = {}


def build_results_view(current_scan_results, selected_target_file, last_completed_sha256, lang, page, theme_mode="dark"):
    """Builds the enhanced results dashboard, showing detections, behaviors, comments, voting, and export options with theme support."""
    palette = get_theme_palette(theme_mode)
    
    def safe_update_control(control=None):
        def _apply():
            try:
                if control is not None and getattr(control, "page", None) is not None:
                    control.update()
                else:
                    page.update()
            except Exception:
                try:
                    page.update()
                except Exception:
                    pass

        if hasattr(page, "loop") and page.loop and page.loop.is_running():
            try:
                page.loop.call_soon_threadsafe(_apply)
                return
            except Exception:
                pass
        _apply()

    def get_stats_and_results(data_dict):
        if not isinstance(data_dict, dict):
            if isinstance(data_dict, list) and len(data_dict) > 0 and isinstance(data_dict[0], dict):
                data_dict = data_dict[0]
            else:
                data_dict = {}

        data = data_dict.get("data") if isinstance(data_dict, dict) else {}
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            data = data[0]

        attributes = None
        if isinstance(data, dict):
            attributes = data.get("attributes")
        if not isinstance(attributes, dict):
            attributes = data_dict.get("attributes") if isinstance(data_dict, dict) else {}
        if not isinstance(attributes, dict):
            attributes = data_dict if isinstance(data_dict, dict) else {}

        stats = attributes.get("last_analysis_stats") if isinstance(attributes, dict) else None
        if not isinstance(stats, dict) and isinstance(data_dict, dict):
            stats = data_dict.get("last_analysis_stats")
        if not isinstance(stats, dict):
            stats = {}

        results = attributes.get("last_analysis_results") if isinstance(attributes, dict) else None
        if not isinstance(results, dict) and isinstance(data_dict, dict):
            results = data_dict.get("last_analysis_results")
        if not isinstance(results, dict):
            results = {}

        names = attributes.get("names", []) if isinstance(attributes, dict) else []
        if not isinstance(names, list) and isinstance(data_dict, dict):
            names = data_dict.get("names", [])
        if not isinstance(names, list):
            names = []

        size = attributes.get("size", 0) if isinstance(attributes, dict) else 0
        if not size and isinstance(data_dict, dict):
            size = data_dict.get("size", 0)

        return stats, results, names, size, attributes

    stats, results_dict, names, size, attributes = get_stats_and_results(current_scan_results)
    
    filename = selected_target_file if selected_target_file else "Unknown_File"
    if names and isinstance(names, list) and len(names) > 0 and isinstance(names[0], str):
        filename = names[0]
    else:
        filename = os.path.basename(filename)
        
    malicious = stats.get("malicious", 0) if isinstance(stats, dict) else 0
    suspicious = stats.get("suspicious", 0) if isinstance(stats, dict) else 0
    harmless = stats.get("harmless", 0) if isinstance(stats, dict) else 0
    undetected = stats.get("undetected", 0) if isinstance(stats, dict) else 0

    # 1. Verdict Banner
    if malicious > 0:
        banner_text = STRINGS[lang]["verdict_malicious"].format(malicious=malicious)
        banner_color = "#FF3131"
        banner_icon = ft.Icons.GPP_BAD_ROUNDED
    elif suspicious > 0:
        banner_text = STRINGS[lang]["verdict_suspicious"].format(suspicious=suspicious)
        banner_color = "#FFD700" if theme_mode == "dark" else "#D97706"
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
        shadow=ft.BoxShadow(blur_radius=8, color=palette["shadow_color"], offset=ft.Offset(0, 2))
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

    target_sha256 = last_completed_sha256 or ""
    if not target_sha256 and isinstance(attributes, dict):
        target_sha256 = attributes.get("sha256") or attributes.get("md5") or ""
    if not target_sha256 and isinstance(current_scan_results, dict):
        target_sha256 = current_scan_results.get("sha256") or ""
        data_val = current_scan_results.get("data")
        if not target_sha256 and isinstance(data_val, dict):
            target_sha256 = data_val.get("id") or ""
        elif not target_sha256 and isinstance(data_val, str) and len(data_val) == 64:
            target_sha256 = data_val

    # Persistent user vote state from cache
    user_vote_state = [_VOTE_CACHE.get(target_sha256)]
    is_voting_state = [False]

    def handle_vote(verdict):
        def vote_action(e):
            if is_voting_state[0]:
                return
            api_key = get_api_key()
            if not api_key:
                page.show_dialog(ft.SnackBar(content=ft.Text(STRINGS[lang]["api_key_missing"])))
                return
            if not target_sha256:
                page.show_dialog(ft.SnackBar(content=ft.Text(STRINGS[lang].get("vote_sha_missing", "SHA-256 is missing for voting.")), bgcolor="#EF4444"))
                return

            if user_vote_state[0] == verdict:
                verdict_word = STRINGS[lang].get(f"verdict_{verdict}_word", verdict)
                msg = STRINGS[lang].get("already_voted", "Already voted '{verdict}' for this file.").format(verdict=verdict_word)
                page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor=palette["button_primary_bg"]))
                return

            is_voting_state[0] = True
            update_vote_ui()

            def worker():
                try:
                    vote_item("files", target_sha256, verdict, api_key)
                    user_vote_state[0] = verdict
                    _VOTE_CACHE[target_sha256] = verdict
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

    def build_vote_controls():
        if is_voting_state[0]:
            return [
                ft.Container(
                    content=ft.Row([
                        ft.ProgressRing(width=14, height=14, stroke_width=2, color=palette["accent"]),
                        ft.Text(STRINGS[lang].get("voting_progress", "Sending vote..."), color=palette["text_muted"], size=11)
                    ], spacing=6),
                    padding=ft.Padding(left=8, right=8, top=4, bottom=4),
                    bgcolor=palette["card_bg"],
                    border_radius=8,
                    border=ft.Border.all(1, palette["accent"])
                )
            ]
        else:
            is_harmless = (user_vote_state[0] == "harmless")
            is_malicious = (user_vote_state[0] == "malicious")

            harmless_label = STRINGS[lang].get("vote_harmless", "Vote Harmless") if not is_harmless else STRINGS[lang].get("voted_harmless", "Voted Harmless")
            malicious_label = STRINGS[lang].get("vote_malicious", "Vote Malicious") if not is_malicious else STRINGS[lang].get("voted_malicious", "Voted Malicious")

            harmless_btn = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.THUMBS_UP_DOWN_ROUNDED, color="#10B981" if is_harmless else ("#39FF14" if theme_mode == "dark" else "#16A34A"), size=18),
                    ft.Text(harmless_label, color="#10B981" if is_harmless else palette["text_secondary"], size=11, weight=ft.FontWeight.BOLD if is_harmless else ft.FontWeight.NORMAL)
                ], spacing=4),
                padding=ft.Padding(left=10, right=10, top=6, bottom=6),
                border_radius=8,
                bgcolor="#10B98122" if is_harmless else palette["button_secondary_bg"],
                border=ft.Border.all(1, "#10B981" if is_harmless else palette["card_border"]),
                on_click=handle_vote("harmless"),
                tooltip=STRINGS[lang].get("vote_harmless", "Vote Harmless")
            )

            malicious_btn = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.THUMB_DOWN_ALT_ROUNDED, color="#EF4444", size=18),
                    ft.Text(malicious_label, color="#EF4444" if is_malicious else palette["text_secondary"], size=11, weight=ft.FontWeight.BOLD if is_malicious else ft.FontWeight.NORMAL)
                ], spacing=4),
                padding=ft.Padding(left=10, right=10, top=6, bottom=6),
                border_radius=8,
                bgcolor="#EF444422" if is_malicious else palette["button_secondary_bg"],
                border=ft.Border.all(1, "#EF4444" if is_malicious else palette["card_border"]),
                on_click=handle_vote("malicious"),
                tooltip=STRINGS[lang].get("vote_malicious", "Vote Malicious")
            )

            return [harmless_btn, malicious_btn]

    vote_buttons_container = ft.Row(controls=build_vote_controls(), spacing=6)

    def update_vote_ui():
        vote_buttons_container.controls = build_vote_controls()
        safe_update_control(vote_buttons_container)

    def load_user_vote():
        if target_sha256 in _VOTE_CACHE:
            return

        api_key = get_api_key()
        if not api_key or not target_sha256:
            return
        def worker():
            try:
                v = get_user_vote("files", target_sha256, api_key)
                if v:
                    _VOTE_CACHE[target_sha256] = v
                    user_vote_state[0] = v
                    update_vote_ui()
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    load_user_vote()

    actions_row = ft.Row([
        ft.Button(STRINGS[lang].get("btn_reanalyze", "Re-analyze"), icon=ft.Icons.REFRESH_ROUNDED, on_click=handle_reanalyze, bgcolor=palette["button_secondary_bg"], color=palette["accent"]),
        ft.Button(STRINGS[lang].get("btn_export_report", "Export Report"), icon=ft.Icons.DOWNLOAD_ROUNDED, on_click=handle_export, bgcolor=palette["button_secondary_bg"], color=palette["button_secondary_text"]),
        vote_buttons_container
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    details_card = make_file_details_card(filename, size, last_completed_sha256, STRINGS, lang, theme_mode=theme_mode)
    
    stats_row = ft.Row(
        [
            make_stat_card(STRINGS[lang]["stats_malicious"], malicious, "#FF3131", ft.Icons.REPORT_PROBLEM_ROUNDED, theme_mode=theme_mode),
            make_stat_card(STRINGS[lang]["stats_suspicious"], suspicious, "#FFD700" if theme_mode == "dark" else "#D97706", ft.Icons.WARNING_AMBER_ROUNDED, theme_mode=theme_mode),
            make_stat_card(STRINGS[lang]["stats_harmless"], harmless, "#39FF14" if theme_mode == "dark" else "#16A34A", ft.Icons.CHECK_CIRCLE_ROUNDED, theme_mode=theme_mode),
            make_stat_card(STRINGS[lang]["stats_undetected"], undetected, palette["text_muted"], ft.Icons.HELP_OUTLINE_ROUNDED, theme_mode=theme_mode)
        ],
        spacing=10,
        alignment=ft.MainAxisAlignment.SPACE_EVENLY
    )

    # Tab 1: Detections
    detections_list = ft.Column(spacing=5, expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    mal_susp_list = []
    clean_list = []
    if isinstance(results_dict, dict):
        for engine, info in results_dict.items():
            if isinstance(info, dict):
                category = info.get("category", "undetected")
                res = info.get("result")
                method = info.get("method", "unknown")
            elif isinstance(info, str):
                category = "malicious" if info.lower() in ("malicious", "suspicious", "detected") else ("harmless" if info.lower() in ("clean", "harmless", "undetected") else info)
                res = info
                method = "export"
            else:
                category = "undetected"
                res = None
                method = "unknown"

            if category in ("malicious", "suspicious"):
                mal_susp_list.append((engine, category, res, method))
            else:
                clean_list.append((engine, category, res, method))
                
    if mal_susp_list:
        detections_list.controls.append(
            ft.Text(f"{STRINGS[lang]['detections_title']} ({len(mal_susp_list)})", size=16, weight=ft.FontWeight.BOLD, color=palette["text_primary"])
        )
        for engine, category, res, method in mal_susp_list:
            detections_list.controls.append(make_engine_row(engine, category, res, method, theme_mode=theme_mode))
    else:
        detections_list.controls.append(
            ft.Text(STRINGS[lang]["verdict_safe"], size=14, color=palette["text_muted"])
        )
        
    is_engines_expanded = _ENGINES_EXPANDED.get(target_sha256, False)
    full_list_column = ft.Column(spacing=5, visible=is_engines_expanded, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    for engine, category, res, method in sorted(clean_list + mal_susp_list, key=lambda x: x[0].lower()):
        full_list_column.controls.append(make_engine_row(engine, category, res, method, theme_mode=theme_mode))
        
    toggle_button = ft.Ref[ft.TextButton]()
    
    def toggle_full_list(e):
        full_list_column.visible = not full_list_column.visible
        _ENGINES_EXPANDED[target_sha256] = full_list_column.visible
        if full_list_column.visible:
            toggle_button.current.content = STRINGS[lang]["hide_all_engines"]
            toggle_button.current.icon = ft.Icons.KEYBOARD_ARROW_UP_ROUNDED
        else:
            toggle_button.current.content = STRINGS[lang]["show_all_engines"].format(count=len(clean_list) + len(mal_susp_list))
            toggle_button.current.icon = ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED
        safe_update_control()
        
    total_engines_count = len(clean_list) + len(mal_susp_list)
    show_all_btn = ft.TextButton(
        ref=toggle_button,
        content=STRINGS[lang]["hide_all_engines"] if is_engines_expanded else STRINGS[lang]["show_all_engines"].format(count=total_engines_count),
        icon=ft.Icons.KEYBOARD_ARROW_UP_ROUNDED if is_engines_expanded else ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED,
        icon_color=palette["accent"],
        style=ft.ButtonStyle(color=palette["accent"]),
        on_click=toggle_full_list
    )
    
    detections_tab_view = ft.Column([
        detections_list,
        ft.Container(height=10),
        show_all_btn,
        full_list_column
    ], scroll=ft.ScrollMode.ALWAYS, expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    # Tab 2: Behavior & Sandbox Reports
    def build_behavior_item_controls(behaviours):
        if not behaviours:
            return [ft.Text(STRINGS[lang].get("behavior_empty", "No sandbox execution reports available for this file."), color=palette["text_muted"])]
        items = []
        for idx, b in enumerate(behaviours):
            attrs = b.get("attributes", {})
            sandbox_name = attrs.get("sandbox_name", f"Sandbox #{idx+1}")
            tags = attrs.get("tags", [])
            mitre = attrs.get("mitre_attack_techniques", [])
            
            details = [
                ft.Text(f"Sandbox: {sandbox_name.upper()}", weight=ft.FontWeight.BOLD, color=palette["accent"], size=14),
                ft.Text(f"Tags: {', '.join(tags) if tags else 'None'}", color=palette["text_muted"], size=11)
            ]
            
            if mitre:
                details.append(ft.Text(f"MITRE ATT&CK Techniques: {len(mitre)} detected", weight=ft.FontWeight.W_600, color="#FFD700" if theme_mode == "dark" else "#D97706", size=12))
                for m in mitre[:5]:
                    tech_id = m.get("signature_description", m.get("id", ""))
                    details.append(ft.Text(f" • {tech_id}", color=palette["text_secondary"], size=11))

            items.append(ft.Container(
                content=ft.Column(details, spacing=4, horizontal_alignment=ft.CrossAxisAlignment.START),
                padding=12,
                border_radius=10,
                bgcolor=palette["card_bg"],
                border=ft.Border.all(1, palette["card_border"]),
                alignment=ft.Alignment.CENTER_LEFT
            ))
        return items

    behavior_loading_card = make_loading_card(STRINGS[lang].get("behavior_loading", "Loading sandbox execution reports..."), theme_mode=theme_mode)
    
    if target_sha256 in _BEHAVIORS_CACHE:
        behavior_container = ft.Column(controls=build_behavior_item_controls(_BEHAVIORS_CACHE[target_sha256]), spacing=8, scroll=ft.ScrollMode.ALWAYS, expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    else:
        behavior_container = ft.Column(controls=[behavior_loading_card], spacing=8, scroll=ft.ScrollMode.ALWAYS, expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def load_behavior(e=None):
        if target_sha256 in _BEHAVIORS_CACHE:
            return

        behavior_container.controls = [behavior_loading_card]
        safe_update_control(behavior_container)
        
        def worker():
            api_key = get_api_key()
            if not api_key:
                behavior_container.controls = [ft.Text(STRINGS[lang].get("api_key_missing", "API key required."), color="#EF4444")]
                safe_update_control(behavior_container)
                return
            behaviours = get_file_behaviours(last_completed_sha256, api_key)
            _BEHAVIORS_CACHE[target_sha256] = behaviours
            behavior_container.controls = build_behavior_item_controls(behaviours)
            safe_update_control(behavior_container)

        threading.Thread(target=worker, daemon=True).start()

    if target_sha256 not in _BEHAVIORS_CACHE:
        load_behavior()

    # Tab 3: Comments
    def build_comment_item_controls(comms):
        if not comms:
            return [ft.Text(STRINGS[lang].get("comments_empty", "No community comments yet."), color=palette["text_muted"])]
        items = []
        for c in comms:
            cid = c.get("id")
            attrs = c.get("attributes", {})
            txt = attrs.get("text", "")
            date_val = attrs.get("date")
            
            date_str = ""
            if date_val:
                try:
                    from datetime import datetime
                    date_str = datetime.fromtimestamp(date_val).strftime("%d.%m.%Y %H:%M")
                except Exception:
                    pass

            delete_btn = ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                icon_color="#EF4444",
                icon_size=18,
                tooltip=STRINGS[lang].get("btn_delete_comment", "Delete comment"),
                on_click=lambda e, comment_id=cid: confirm_delete_comment(comment_id)
            ) if cid else ft.Container()

            content_controls = []
            if date_str:
                content_controls.append(ft.Text(date_str, color=palette["text_muted"], size=10))
            content_controls.append(ft.Text(txt, color=palette["text_secondary"], size=12, selectable=True))

            items.append(ft.Container(
                content=ft.Row([
                    ft.Column(content_controls, spacing=2, expand=True, horizontal_alignment=ft.CrossAxisAlignment.START),
                    delete_btn
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding(left=12, right=8, top=8, bottom=8),
                border_radius=8,
                bgcolor=palette["card_bg"],
                border=ft.Border.all(1, palette["card_border"])
            ))
        return items

    comments_loading_card = make_loading_card(STRINGS[lang].get("comments_loading", "Loading community comments..."), theme_mode=theme_mode)
    
    if target_sha256 in _COMMENTS_CACHE:
        comments_container = ft.Column(controls=build_comment_item_controls(_COMMENTS_CACHE[target_sha256]), spacing=8, scroll=ft.ScrollMode.ALWAYS, expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    else:
        comments_container = ft.Column(controls=[comments_loading_card], spacing=8, scroll=ft.ScrollMode.ALWAYS, expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    send_progress = ft.ProgressRing(width=20, height=20, stroke_width=2.5, color=palette["accent"], visible=False)
    send_button = ft.IconButton(
        icon=ft.Icons.SEND_ROUNDED,
        icon_color=palette["accent"],
        on_click=lambda e: post_comment(e),
        tooltip=STRINGS[lang].get("btn_send_comment", "Send comment")
    )

    comment_input = ft.TextField(
        hint_text=STRINGS[lang].get("post_comment_hint", "Write a community note or comment..."),
        border_color=palette["input_border"],
        focused_border_color=palette["accent"],
        bgcolor=palette["input_bg"],
        color=palette["text_primary"],
        hint_style=ft.TextStyle(color=palette["text_muted"]),
        expand=True,
        on_submit=lambda e: post_comment(e)
    )

    def set_sending_state(is_sending):
        comment_input.disabled = is_sending
        send_button.visible = not is_sending
        send_progress.visible = is_sending
        safe_update_control()

    def post_comment(e=None):
        txt = comment_input.value.strip()
        if not txt:
            return
        api_key = get_api_key()
        if not api_key:
            page.show_dialog(ft.SnackBar(content=ft.Text(STRINGS[lang]["api_key_missing"])))
            return
            
        set_sending_state(True)

        def worker():
            try:
                add_comment("files", last_completed_sha256, txt, api_key)
                comment_input.value = ""
                load_comments(force=True)
                page.show_dialog(ft.SnackBar(content=ft.Text(STRINGS[lang].get("toast_comment_success", "Comment posted!")), bgcolor="#10B981"))
            except Exception as ex:
                msg = STRINGS[lang].get("toast_comment_fail", "Failed to post comment: {e}").format(e=str(ex))
                page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor="#EF4444"))
            finally:
                set_sending_state(False)

        threading.Thread(target=worker, daemon=True).start()

    def confirm_delete_comment(cid):
        overlay_holder = [None]
        is_deleting = False

        def close_overlay():
            ov = overlay_holder[0]
            if ov is not None and ov in page.overlay:
                page.overlay.remove(ov)
                safe_update_control()
            overlay_holder[0] = None

        def on_backdrop_click(e):
            if not is_deleting:
                close_overlay()

        cancel_btn = ft.TextButton(
            content=ft.Text(STRINGS[lang].get("btn_cancel", "Cancel"), color=palette["text_muted"], size=13),
            on_click=lambda _: close_overlay()
        )

        delete_btn = ft.Button(
            content=ft.Text(STRINGS[lang].get("btn_delete", "Delete"), weight=ft.FontWeight.W_600),
            on_click=lambda e: start_deletion(),
            bgcolor="#EF4444",
            color="#FFFFFF",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )

        loading_indicator = ft.Row([
            ft.ProgressRing(width=16, height=16, stroke_width=2, color="#EF4444"),
            ft.Text(
                STRINGS[lang].get("deleting_comment", "Deleting comment..."),
                color="#EF4444",
                size=13,
                weight=ft.FontWeight.W_500
            )
        ], spacing=10, alignment=ft.MainAxisAlignment.END, visible=False)

        actions_row_del = ft.Row([cancel_btn, delete_btn], alignment=ft.MainAxisAlignment.END, spacing=10)

        panel = ft.Container(
            width=420,
            bgcolor=palette["dialog_bg"],
            border_radius=12,
            padding=ft.Padding(left=24, right=24, top=20, bottom=20),
            border=ft.Border.all(1, palette["card_border"]),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.DELETE_ROUNDED, color="#EF4444", size=22),
                    ft.Text(
                        STRINGS[lang].get("dlg_delete_comment_title", "Delete comment"),
                        color=palette["text_primary"],
                        weight=ft.FontWeight.BOLD,
                        size=16
                    )
                ], spacing=8),
                ft.Container(height=8),
                ft.Text(
                    STRINGS[lang].get("dlg_delete_comment_confirm", "Are you sure you want to delete this comment?"),
                    color=palette["text_secondary"],
                    size=13
                ),
                ft.Container(height=16),
                actions_row_del,
                loading_indicator
            ], tight=True)
        )

        overlay = ft.Container(
            expand=True,
            bgcolor="#88000000",
            alignment=ft.Alignment.CENTER,
            on_click=on_backdrop_click,
            content=panel
        )
        overlay_holder[0] = overlay

        def start_deletion():
            nonlocal is_deleting
            api_key = get_api_key()
            if not api_key:
                page.show_dialog(ft.SnackBar(content=ft.Text(STRINGS[lang].get("api_key_missing", "API key required."))))
                return

            is_deleting = True
            actions_row_del.visible = False
            loading_indicator.visible = True
            safe_update_control()

            def worker():
                try:
                    delete_comment(cid, api_key)
                    close_overlay()
                    load_comments(force=True)
                    page.show_dialog(ft.SnackBar(
                        content=ft.Text(STRINGS[lang].get("toast_comment_delete_success", "Comment deleted!")),
                        bgcolor="#10B981"
                    ))
                except Exception as ex:
                    close_overlay()
                    msg = STRINGS[lang].get("toast_comment_delete_fail", "Failed to delete comment: {e}").format(e=str(ex))
                    page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor="#EF4444"))

            threading.Thread(target=worker, daemon=True).start()

        page.overlay.append(overlay)
        safe_update_control()

    def load_comments(e=None, force=False):
        if not force and target_sha256 in _COMMENTS_CACHE:
            return

        api_key = get_api_key()
        if not api_key:
            comments_container.controls = [ft.Text(STRINGS[lang].get("api_key_missing", "API key required."), color=palette["text_muted"])]
            safe_update_control(comments_container)
            return
            
        def worker():
            comms = get_comments("files", last_completed_sha256, api_key)
            _COMMENTS_CACHE[target_sha256] = comms
            comments_container.controls = build_comment_item_controls(comms)
            safe_update_control(comments_container)

        threading.Thread(target=worker, daemon=True).start()

    if target_sha256 not in _COMMENTS_CACHE:
        load_comments()

    comments_tab_view = ft.Column([
        ft.Row([
            comment_input,
            ft.Container(
                content=ft.Stack([send_button, send_progress], alignment=ft.Alignment.CENTER),
                alignment=ft.Alignment.CENTER,
                padding=ft.Padding(right=6, left=0, top=0, bottom=0)
            )
        ]),
        ft.Divider(color=palette["divider"]),
        comments_container
    ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    res_tab_defs = [
        (0, STRINGS[lang].get("tab_detections", "Detections"), ft.Icons.SECURITY_ROUNDED, detections_tab_view),
        (1, STRINGS[lang].get("tab_behavior", "Behavior / Sandbox"), ft.Icons.MISCELLANEOUS_SERVICES_ROUNDED, behavior_container),
        (2, STRINGS[lang].get("tab_comments", "Comments"), ft.Icons.COMMENT_ROUNDED, comments_tab_view),
    ]

    active_res_tab = [_ACTIVE_RES_TAB.get(target_sha256, 0)]
    res_tab_views_map = {idx: v for idx, _, _, v in res_tab_defs}

    res_tab_content_container = ft.Container(
        content=res_tab_views_map[active_res_tab[0]],
        padding=5,
        expand=True,
        alignment=ft.Alignment.TOP_LEFT
    )

    res_tab_buttons = []
    res_tab_buttons_map = {}

    def update_res_tab_buttons():
        for idx, btn in res_tab_buttons_map.items():
            is_active = (active_res_tab[0] == idx)
            btn.border = ft.Border.all(1, palette["accent"] if is_active else "transparent")
            btn.bgcolor = palette["tab_active_bg"] if is_active else "transparent"
            col = btn.content
            col.controls[0].color = palette["accent"] if is_active else palette["text_muted"]
            col.controls[1].color = palette["text_primary"] if is_active else palette["text_muted"]
            safe_update_control(btn)

    def select_res_tab(idx):
        if active_res_tab[0] == idx:
            return
        active_res_tab[0] = idx
        _ACTIVE_RES_TAB[target_sha256] = idx
        if idx == 1:
            load_behavior(None)
        update_res_tab_buttons()
        res_tab_content_container.content = res_tab_views_map[idx]
        safe_update_control(res_tab_content_container)

    for idx, label, icon, _ in res_tab_defs:
        is_active = (active_res_tab[0] == idx)
        
        tab_btn = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, color=palette["accent"] if is_active else palette["text_muted"], size=20),
                    ft.Text(label, color=palette["text_primary"] if is_active else palette["text_muted"], size=12, weight=ft.FontWeight.W_600, text_align=ft.TextAlign.CENTER)
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
            on_click=lambda _, i=idx: select_res_tab(i)
        )

        def make_res_hover_handler(btn, tab_idx):
            def on_tab_hover(e):
                if active_res_tab[0] != tab_idx:
                    if e.data == "true":
                        btn.border = ft.Border.all(1, palette["tab_inactive_hover_border"])
                        btn.bgcolor = palette["tab_inactive_hover_bg"]
                    else:
                        btn.border = ft.Border.all(1, "transparent")
                        btn.bgcolor = "transparent"
                    safe_update_control(btn)
            return on_tab_hover

        tab_btn.on_hover = make_res_hover_handler(tab_btn, idx)
        res_tab_buttons.append(tab_btn)
        res_tab_buttons_map[idx] = tab_btn

    res_tab_header_row = ft.Row(
        res_tab_buttons,
        spacing=2,
        alignment=ft.MainAxisAlignment.START
    )

    tabs = ft.Column(
        [
            ft.Container(
                content=res_tab_header_row,
                padding=ft.Padding(left=4, right=4, top=10, bottom=10),
                border=ft.Border(
                    top=ft.BorderSide(1, palette["divider"]),
                    bottom=ft.BorderSide(1, palette["divider"])
                )
            ),
            res_tab_content_container
        ],
        expand=True,
        height=480,
        spacing=10
    )
    
    return ft.Column([
        verdict_banner,
        actions_row,
        details_card,
        stats_row,
        tabs
    ], expand=True, spacing=10, scroll=ft.ScrollMode.AUTO)
