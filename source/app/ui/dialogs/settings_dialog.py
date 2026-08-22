import flet as ft
import webbrowser
import threading

from ...core.config import write_env_var, STRINGS, get_api_key, get_app_theme, set_app_theme
from ...api.vt_api import get_user_quota, verify_api_key, get_cached_quota, get_local_usage
from ..components.theme import get_theme_palette


def open_settings(page, lang, on_settings_saved, on_reinstall_cli=None, cli_source=None, theme_mode="dark", on_theme_change=None):
    """Opens a beautiful modal settings dialog with configuration options, theme selection, and API quota display."""
    palette = get_theme_palette(theme_mode)
    is_dark = (theme_mode == "dark")
    api_key = get_api_key() or ""

    api_key_field = ft.TextField(
        label=STRINGS[lang]["api_key_label"],
        hint_text=STRINGS[lang]["api_key_hint"],
        value=api_key,
        password=True,
        can_reveal_password=True,
        border_color=palette["input_border"],
        focused_border_color=palette["accent"],
        label_style=ft.TextStyle(color=palette["text_muted"]),
        text_style=ft.TextStyle(color=palette["text_primary"]),
        bgcolor=palette["input_bg"],
    )

    get_api_key_btn = ft.TextButton(
        content=ft.Text(STRINGS[lang]["btn_get_api_key"], color=palette["accent"], size=13),
        icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
        icon_color=palette["accent"],
        on_click=lambda _: webbrowser.open("https://docs.virustotal.com/docs/please-give-me-an-api-key")
    )

    api_check_icon = ft.Icon(ft.Icons.VERIFIED_ROUNDED, color="transparent", size=16)
    api_check_text = ft.Text(" ", size=12, color=palette["text_muted"])

    # API Quota progress section (local/cached value renders instantly, refreshed in background)
    quota_click_text = STRINGS[lang].get("api_quota_click", "API Quota: Click 'Check API' to fetch usage")
    quota_text = ft.Text(quota_click_text, size=12, color=palette["text_muted"])
    quota_progress = ft.ProgressBar(value=0.0, color=palette["accent"], bgcolor=palette["card_border"], height=4, visible=False)
    quota_shown = {"value": False}

    def apply_quota(q):
        used = q.get("daily_used", 0)
        allowed = q.get("daily_allowed", 0)
        quota_shown["value"] = True
        quota_text.color = palette["text_muted"]
        if allowed > 0:
            percent = min(used / allowed, 1.0)
            quota_progress.value = percent
            quota_progress.color = "#FF3131" if percent > 0.9 else palette["accent"]
            quota_progress.visible = True
            quota_text.value = STRINGS[lang].get("api_quota_daily", "Daily API Quota: {used} / {allowed} requests ({percent}%)").format(used=used, allowed=allowed, percent=int(percent*100))
        else:
            quota_text.value = STRINGS[lang].get("api_quota_usage", "Daily API Usage: {used} requests used").format(used=used)

    def update_quota_display(key):
        try:
            q = get_user_quota(key)
            if q:
                apply_quota(q)
                page.update()
            elif not quota_shown["value"]:
                quota_text.value = quota_click_text
                quota_text.color = "#EF4444"
                page.update()
        except Exception:
            if not quota_shown["value"]:
                quota_text.value = quota_click_text
                quota_text.color = "#EF4444"
                page.update()

    def refresh_quota_async():
        key = api_key_field.value.strip()
        if key:
            threading.Thread(target=update_quota_display, args=(key,), daemon=True).start()

    def local_quota_snapshot():
        used = get_local_usage()
        return {
            "daily_used": used,
            "daily_allowed": 0,
            "monthly_used": used,
            "monthly_allowed": 0,
            "free_tier": True,
        }

    cached_quota = get_cached_quota() if api_key else None
    if cached_quota and cached_quota.get("free_tier"):
        used_now = get_local_usage()
        cached_quota["daily_used"] = used_now
        cached_quota["monthly_used"] = used_now
    if api_key:
        apply_quota(cached_quota or local_quota_snapshot())

    def on_check_api_click(e):
        key = api_key_field.value.strip()
        if not key:
            api_check_text.value = STRINGS[lang]["api_key_hint"]
            api_check_text.color = "#F59E0B"
            api_check_icon.color = "#F59E0B"
            api_check_icon.name = ft.Icons.WARNING_ROUNDED
            page.update()
            return

        api_check_btn.disabled = True
        api_check_text.value = STRINGS[lang]["api_checking"]
        api_check_text.color = palette["text_muted"]
        api_check_icon.color = "transparent"
        page.update()

        def run_check():
            try:
                success, error = verify_api_key(key)
                if success:
                    api_check_text.value = STRINGS[lang]["api_check_success"]
                    api_check_text.color = "#10B981"
                    api_check_icon.color = "#10B981"
                    api_check_icon.name = ft.Icons.CHECK_CIRCLE_ROUNDED
                    update_quota_display(key)
                else:
                    api_check_text.value = STRINGS[lang]["api_check_fail"].format(e=error)
                    api_check_text.color = "#EF4444"
                    api_check_icon.color = "#EF4444"
                    api_check_icon.name = ft.Icons.ERROR_ROUNDED
            except Exception as ex:
                api_check_text.value = STRINGS[lang]["api_check_fail"].format(e=str(ex))
                api_check_text.color = "#EF4444"
                api_check_icon.color = "#EF4444"
                api_check_icon.name = ft.Icons.ERROR_ROUNDED
            api_check_btn.disabled = False
            page.update()

        threading.Thread(target=run_check, daemon=True).start()

    api_check_btn = ft.TextButton(
        content=ft.Text(STRINGS[lang]["btn_check_api"], color=palette["accent"], size=13),
        icon=ft.Icons.HELP_OUTLINE_ROUNDED,
        icon_color=palette["accent"],
        on_click=on_check_api_click,
    )

    api_check_row = ft.Row(
        [api_check_icon, api_check_text],
        spacing=6,
        height=20,
    )

    def save_settings(e):
        write_env_var("VT_APIKEY", api_key_field.value.strip())
        page.pop_dialog()
        on_settings_saved()

    # Reinstall CLI section
    status_icon = ft.Icon(ft.Icons.SYNC_ROUNDED, color="transparent", size=14)
    status_text = ft.Text(" ", size=12, color=palette["text_muted"])
    status_row = ft.Row(
        [status_icon, status_text],
        spacing=6,
        height=20,
    )

    def set_button_disabled(disabled):
        if disabled:
            reinstall_container.border = ft.Border.all(1, palette["card_border_subtle"])
            reinstall_container.on_click = None
            reinstall_container.on_hover = None
            reinstall_icon.color = palette["text_muted"]
            reinstall_label.color = palette["text_muted"]
        else:
            reinstall_container.border = ft.Border.all(1, palette["card_border"])
            reinstall_container.on_click = reinstall_container.data_on_click
            reinstall_container.on_hover = reinstall_container.data_on_hover
            reinstall_icon.color = "#F59E0B"
            reinstall_label.color = "#F59E0B"

    def on_reinstall_click(e):
        if on_reinstall_cli:
            set_button_disabled(True)
            status_text.value = STRINGS[lang]["reinstalling_cli"]
            status_icon.color = "#F59E0B"
            page.update()
            on_reinstall_cli(status_text, status_icon, set_button_disabled)

    def on_reinstall_hover(e):
        if reinstall_container.on_click is None:
            return
        if e.data == "true":
            reinstall_container.bgcolor = palette["card_bg_hover"]
            reinstall_container.border = ft.Border.all(1, "#F59E0B")
        else:
            reinstall_container.bgcolor = palette["card_bg_secondary"]
            reinstall_container.border = ft.Border.all(1, palette["card_border"])
        reinstall_container.update()

    reinstall_icon = ft.Icon(ft.Icons.REFRESH_ROUNDED, color="#F59E0B", size=20)
    reinstall_label = ft.Text(STRINGS[lang]["btn_reinstall_cli"], color="#F59E0B", size=14, weight=ft.FontWeight.W_600)

    system_binary_active = (cli_source == 'system')

    reinstall_container = ft.Container(
        content=ft.Row(
            [reinstall_icon, reinstall_label],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
        ),
        on_click=None if system_binary_active else on_reinstall_click,
        on_hover=None if system_binary_active else on_reinstall_hover,
        border=ft.Border.all(1, palette["card_border_subtle"] if system_binary_active else palette["card_border"]),
        border_radius=12,
        bgcolor=palette["card_bg_secondary"],
        padding=ft.Padding(left=16, right=16, top=12, bottom=12),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        tooltip=STRINGS[lang].get("reinstall_disabled_system", "Disabled: using system VT CLI") if system_binary_active else None,
    )
    reinstall_container.data_on_click = on_reinstall_click
    reinstall_container.data_on_hover = on_reinstall_hover

    if system_binary_active:
        reinstall_icon.color = palette["text_muted"]
        reinstall_label.color = palette["text_muted"]

    vt_cli_link_btn = ft.IconButton(
        icon=ft.Icons.LANGUAGE_ROUNDED,
        icon_color=palette["text_muted"],
        icon_size=20,
        tooltip="GitHub",
        on_click=lambda _: webbrowser.open("https://github.com/virustotal/vt-cli"),
    )

    reinstall_row = ft.Row(
        [reinstall_container, vt_cli_link_btn],
        alignment=ft.MainAxisAlignment.START,
        spacing=5,
    )

    system_warning_row = ft.Container()
    if system_binary_active:
        system_warning_row = ft.Row(
            [
                ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, color="#6366F1", size=14),
                ft.Text(
                    STRINGS[lang].get("reinstall_disabled_system", "Disabled: using system VT CLI from PATH"),
                    color="#6366F1", size=11
                )
            ],
            spacing=6,
        )

    column_controls = [
        api_key_field,
        get_api_key_btn,
        ft.Row([api_check_btn, api_check_row], alignment=ft.MainAxisAlignment.START, spacing=5),
        ft.Column([quota_text, quota_progress], spacing=4),
        ft.Divider(height=1, color=palette["divider"]),
        reinstall_row,
        system_warning_row,
        status_row,
    ]

    settings_content = ft.Container(
        width=440,
        content=ft.Column(
            column_controls,
            spacing=8,
            tight=True,
        )
    )

    modal_header = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.SETTINGS_ROUNDED, color=palette["accent"], size=36),
                    padding=12,
                    bgcolor=palette["dialog_header_bg"],
                    border=ft.Border.all(1.5, palette["accent"]),
                    shape=ft.BoxShape.CIRCLE
                ),
                ft.Text(
                    STRINGS[lang]["settings_title"],
                    color=palette["text_primary"],
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8
        ),
        padding=ft.Padding(top=4, bottom=4, left=10, right=10),
        alignment=ft.Alignment.CENTER
    )

    dlg = ft.AlertDialog(
        title=modal_header,
        title_padding=ft.Padding(left=16, right=16, top=16, bottom=4),
        content_padding=ft.Padding(left=16, right=16, top=8, bottom=8),
        actions_padding=ft.Padding(left=16, right=16, top=4, bottom=12),
        content=settings_content,
        actions=[
            ft.TextButton(
                STRINGS[lang]["btn_no"],
                on_click=lambda _: page.pop_dialog(),
                style=ft.ButtonStyle(color=palette["text_muted"])
            ),
            ft.Button(
                STRINGS[lang]["btn_save"],
                on_click=save_settings,
                bgcolor=palette["button_primary_bg"],
                color=palette["button_primary_text"],
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        bgcolor=palette["dialog_bg"]
    )

    page.show_dialog(dlg)
    refresh_quota_async()
