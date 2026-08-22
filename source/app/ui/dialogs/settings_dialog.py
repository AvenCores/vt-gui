import flet as ft
import webbrowser

from ...core.config import write_env_var, STRINGS, get_api_key, get_app_theme, set_app_theme
from ...api.vt_api import get_local_usage_periods
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

    # API usage section (fully local: today / week / month counters)
    quota_click_text = STRINGS[lang].get("api_quota_click", "API Quota: Click 'Check API' to fetch usage")
    quota_icon = ft.Icon(ft.Icons.DATA_USAGE_ROUNDED, color=palette["accent"], size=16)
    quota_prompt = ft.Text(quota_click_text, size=12, color=palette["text_muted"])
    usage_values = {
        name: ft.Text("0", size=12, weight=ft.FontWeight.W_600, color=palette["text_primary"])
        for name in ("daily", "weekly", "monthly")
    }

    def quota_separator():
        return ft.Container(width=1, height=12, bgcolor=palette["divider"], border_radius=1)

    quota_segments = ft.Row(
        [
            ft.Text(STRINGS[lang].get("usage_title", "API usage"), size=11, weight=ft.FontWeight.W_600, color=palette["text_muted"]),
            quota_separator(),
            ft.Text(STRINGS[lang].get("usage_today", "Today"), size=11, color=palette["text_muted"]),
            usage_values["daily"],
            quota_separator(),
            ft.Text(STRINGS[lang].get("usage_7days", "7 days"), size=11, color=palette["text_muted"]),
            usage_values["weekly"],
            quota_separator(),
            ft.Text(STRINGS[lang].get("usage_month", "Month"), size=11, color=palette["text_muted"]),
            usage_values["monthly"],
        ],
        spacing=5,
    )
    quota_segments.visible = False
    quota_holder = ft.Column([quota_prompt, quota_segments], spacing=0, tight=True)

    def show_quota_segments():
        quota_prompt.visible = False
        quota_segments.visible = True

    def apply_local_quota():
        periods = get_local_usage_periods()
        usage_values["daily"].value = str(periods["daily"])
        usage_values["weekly"].value = str(periods["weekly"])
        usage_values["monthly"].value = str(periods["monthly"])

    def is_plausible_api_key(key):
        return len(key) == 64 and all(c in "0123456789abcdefABCDEF" for c in key)

    def set_key_status(ok):
        if ok:
            api_check_text.value = STRINGS[lang].get("api_check_local_ok", "Key format is valid (local check)")
            api_check_text.color = "#10B981"
            api_check_icon.color = "#10B981"
            api_check_icon.name = ft.Icons.CHECK_CIRCLE_ROUNDED
        else:
            api_check_text.value = STRINGS[lang]["api_key_hint"]
            api_check_text.color = "#F59E0B"
            api_check_icon.color = "#F59E0B"
            api_check_icon.name = ft.Icons.WARNING_ROUNDED
        page.update()

    def on_check_api_click(e):
        key = api_key_field.value.strip()
        ok = is_plausible_api_key(key)
        if ok:
            show_quota_segments()
            apply_local_quota()
        set_key_status(ok)

    if api_key:
        show_quota_segments()
        apply_local_quota()

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
        ft.Row([quota_icon, quota_holder], spacing=6),
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
