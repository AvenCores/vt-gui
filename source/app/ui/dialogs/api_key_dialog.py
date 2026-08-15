import os
import threading
import flet as ft
import webbrowser

from ...core.config import write_env_var, STRINGS
from ...api.cli_manager import download_and_install_cli
from ...api.vt_api import verify_api_key
from ..components.theme import get_theme_palette


def open_api_key_dialog(page, lang, on_saved, cli_source=None, theme_mode="dark"):
    """Opens a non-dismissable dialog for entering an API key on first launch with theme support."""
    palette = get_theme_palette(theme_mode)

    api_key_field = ft.TextField(
        label=STRINGS[lang]["api_key_label"],
        hint_text=STRINGS[lang]["api_key_hint"],
        password=True,
        can_reveal_password=True,
        border_color=palette["input_border"],
        focused_border_color=palette["accent"],
        label_style=ft.TextStyle(color=palette["text_muted"]),
        text_style=ft.TextStyle(color=palette["text_primary"]),
        bgcolor=palette["input_bg"],
    )

    save_btn = ft.Button(
        STRINGS[lang]["btn_save"],
        on_click=lambda _: None,
        bgcolor=palette["button_primary_bg"],
        color=palette["button_primary_text"],
        disabled=True
    )

    def on_input_change(e):
        save_btn.disabled = not api_key_field.value or not api_key_field.value.strip()
        page.update()

    api_key_field.on_change = on_input_change

    def do_save(e):
        key = api_key_field.value.strip()
        if not key:
            return
        write_env_var("VT_APIKEY", key)
        os.environ["VTCLI_APIKEY"] = key
        page.pop_dialog()
        on_saved()

    save_btn.on_click = do_save

    def open_get_key(e):
        webbrowser.open("https://docs.virustotal.com/docs/please-give-me-an-api-key")

    # --- Check API Key ---
    api_check_icon = ft.Icon(ft.Icons.VERIFIED_ROUNDED, color="transparent", size=16)
    api_check_text = ft.Text(" ", size=12, color=palette["text_muted"])
    api_check_row = ft.Row([api_check_icon, api_check_text], spacing=6, height=20)

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

    # --- Reinstall VT CLI ---
    reinstall_status_icon = ft.Icon(ft.Icons.SYNC_ROUNDED, color="transparent", size=14)
    reinstall_status_text = ft.Text(" ", size=12, color=palette["text_muted"])
    reinstall_status_row = ft.Row([reinstall_status_icon, reinstall_status_text], spacing=6, height=20)

    def set_reinstall_disabled(disabled):
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
        set_reinstall_disabled(True)
        reinstall_status_text.value = STRINGS[lang]["reinstalling_cli"]
        reinstall_status_icon.color = "#F59E0B"
        page.update()

        def run_reinstall():
            def progress_cb(status_text, progress_val):
                reinstall_status_text.value = status_text
                try:
                    page.update()
                except Exception:
                    pass

            try:
                download_and_install_cli(progress_callback=progress_cb, lang=lang)
                reinstall_status_text.value = STRINGS[lang]["reinstall_success"]
                reinstall_status_text.color = "#10B981"
                reinstall_status_icon.color = "#10B981"
                reinstall_status_icon.name = ft.Icons.CHECK_CIRCLE_ROUNDED
            except Exception as ex:
                reinstall_status_text.value = STRINGS[lang]["reinstall_fail"].format(e=str(ex))
                reinstall_status_text.color = "#EF4444"
                reinstall_status_icon.color = "#EF4444"
                reinstall_status_icon.name = ft.Icons.ERROR_ROUNDED
            set_reinstall_disabled(False)
            page.update()

        threading.Thread(target=run_reinstall, daemon=True).start()

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

    content = ft.Column(
        [
            ft.Text(STRINGS[lang]["api_key_required_text"], color=palette["text_secondary"], size=12),
            api_key_field,
            ft.Row([api_check_btn, api_check_row], alignment=ft.MainAxisAlignment.START, spacing=5),
            ft.TextButton(
                content=ft.Text(STRINGS[lang]["btn_get_api_key"], color=palette["accent"], size=13),
                icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                icon_color=palette["accent"],
                on_click=open_get_key
            ),
            ft.Divider(height=1, color=palette["divider"]),
            reinstall_row,
            system_warning_row,
            reinstall_status_row,
        ],
        spacing=8,
        width=400,
        height=280,
        alignment=ft.MainAxisAlignment.START,
    )

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(STRINGS[lang]["api_key_setup_title"], color=palette["text_primary"], weight=ft.FontWeight.BOLD),
        content=content,
        actions=[save_btn],
        actions_alignment=ft.MainAxisAlignment.END,
        bgcolor=palette["dialog_bg"],
        content_padding=ft.Padding(left=24, right=24, top=10, bottom=10),
    )

    page.show_dialog(dlg)
