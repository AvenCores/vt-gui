import flet as ft
import webbrowser
import threading
from ..config import write_env_var, STRINGS, get_api_key
from ..vt_api import get_user_quota

def open_settings(page, lang, on_settings_saved, on_reinstall_cli=None, cli_source=None):
    """Opens a beautiful modal settings dialog with configuration options and API quota display."""
    api_key = get_api_key() or ""

    api_key_field = ft.TextField(
        label=STRINGS[lang]["api_key_label"],
        hint_text=STRINGS[lang]["api_key_hint"],
        value=api_key,
        password=True,
        can_reveal_password=True,
        border_color="#2E3C56",
        focused_border_color="#00F0FF",
        label_style=ft.TextStyle(color="#94A3B8"),
        text_style=ft.TextStyle(color="#E2E8F0"),
    )

    get_api_key_btn = ft.TextButton(
        content=ft.Text(STRINGS[lang]["btn_get_api_key"], color="#00F0FF", size=13),
        icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
        on_click=lambda _: webbrowser.open("https://docs.virustotal.com/docs/please-give-me-an-api-key")
    )

    api_check_icon = ft.Icon(ft.Icons.VERIFIED_ROUNDED, color="transparent", size=16)
    api_check_text = ft.Text(" ", size=12, color="#94A3B8")

    # API Quota progress section
    quota_text = ft.Text(STRINGS[lang].get("api_quota_click", "API Quota: Click 'Check API' to fetch usage"), size=12, color="#94A3B8")
    quota_progress = ft.ProgressBar(value=0.0, color="#00F0FF", bgcolor="#334155", height=4, visible=False)

    def update_quota_display(key):
        try:
            q = get_user_quota(key)
            if q:
                used = q.get("daily_used", 0)
                allowed = q.get("daily_allowed", 0)
                if allowed > 0:
                    percent = min(used / allowed, 1.0)
                    quota_progress.value = percent
                    quota_progress.color = "#FF3131" if percent > 0.9 else "#00F0FF"
                    quota_progress.visible = True
                    quota_text.value = STRINGS[lang].get("api_quota_daily", "Daily API Quota: {used} / {allowed} requests ({percent}%)").format(used=used, allowed=allowed, percent=int(percent*100))
                else:
                    quota_text.value = STRINGS[lang].get("api_quota_usage", "Daily API Usage: {used} requests used").format(used=used)
                page.update()
        except Exception:
            pass

    if api_key:
        threading.Thread(target=lambda: update_quota_display(api_key), daemon=True).start()

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
        api_check_text.color = "#94A3B8"
        api_check_icon.color = "transparent"
        page.update()

        def run_check():
            from ..vt_api import verify_api_key
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
        content=ft.Text(STRINGS[lang]["btn_check_api"], color="#00F0FF", size=13),
        icon=ft.Icons.HELP_OUTLINE_ROUNDED,
        icon_color="#00F0FF",
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
    status_text = ft.Text(" ", size=12, color="#94A3B8")
    status_row = ft.Row(
        [status_icon, status_text],
        spacing=6,
        height=20,
    )

    def set_button_disabled(disabled):
        if disabled:
            reinstall_container.border = ft.Border.all(1, "#1E293B")
            reinstall_container.on_click = None
            reinstall_container.on_hover = None
            reinstall_icon.color = "#4B5563"
            reinstall_label.color = "#4B5563"
        else:
            reinstall_container.border = ft.Border.all(1, "#2E3C56")
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
            reinstall_container.bgcolor = "#1E2A47"
            reinstall_container.border = ft.Border.all(1, "#F59E0B")
        else:
            reinstall_container.bgcolor = "#151E33"
            reinstall_container.border = ft.Border.all(1, "#2E3C56")
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
        border=ft.Border.all(1, "#1E293B" if system_binary_active else "#2E3C56"),
        border_radius=12,
        bgcolor="#151E33",
        padding=ft.Padding(left=16, right=16, top=12, bottom=12),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        tooltip=STRINGS[lang].get("reinstall_disabled_system", "Disabled: using system VT CLI") if system_binary_active else None,
    )
    reinstall_container.data_on_click = on_reinstall_click
    reinstall_container.data_on_hover = on_reinstall_hover

    if system_binary_active:
        reinstall_icon.color = "#4B5563"
        reinstall_label.color = "#4B5563"

    vt_cli_link_btn = ft.IconButton(
        icon=ft.Icons.LANGUAGE_ROUNDED,
        icon_color="#94A3B8",
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
        ft.Divider(height=1, color="#2E3C56"),
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

    settings_title_container = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.SETTINGS_ROUNDED, color="#00F0FF", size=22),
                ft.Text(STRINGS[lang]["settings_title"], color="#FFFFFF", size=17, weight=ft.FontWeight.BOLD)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8
        ),
        padding=ft.Padding(top=6, bottom=12, left=10, right=10),
        border=ft.Border.only(bottom=ft.BorderSide(1, "#2E3C56")),
        alignment=ft.Alignment.CENTER
    )

    dlg = ft.AlertDialog(
        title=settings_title_container,
        content=settings_content,
        actions=[
            ft.TextButton(STRINGS[lang]["btn_no"], on_click=lambda _: page.pop_dialog()),
            ft.ElevatedButton(STRINGS[lang]["btn_save"], on_click=save_settings, bgcolor="#008DDA", color="#FFFFFF")
        ],
        bgcolor="#151E33"
    )

    page.show_dialog(dlg)
