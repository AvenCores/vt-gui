import os
import threading
import flet as ft
import webbrowser
from ..config import write_env_var, STRINGS, get_api_key
from ..cli_manager import check_installed_binary, download_and_install_cli

def open_api_key_dialog(page, lang, on_saved):
    """Opens a non-dismissable dialog for entering an API key on first launch."""
    api_key_field = ft.TextField(
        label=STRINGS[lang]["api_key_label"],
        hint_text=STRINGS[lang]["api_key_hint"],
        password=True,
        can_reveal_password=True,
        border_color="#2E3C56",
        focused_border_color="#00F0FF",
        label_style=ft.TextStyle(color="#94A3B8"),
        text_style=ft.TextStyle(color="#E2E8F0"),
        expand=True,
    )

    save_btn = ft.ElevatedButton(
        STRINGS[lang]["btn_save"],
        on_click=lambda _: None,
        bgcolor="#008DDA",
        color="#FFFFFF",
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
    api_check_text = ft.Text(" ", size=12, color="#94A3B8")
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

    # --- Reinstall VT CLI (same style as settings_dialog.py) ---
    reinstall_status_icon = ft.Icon(ft.Icons.SYNC_ROUNDED, color="transparent", size=14)
    reinstall_status_text = ft.Text(" ", size=12, color="#94A3B8")
    reinstall_status_row = ft.Row([reinstall_status_icon, reinstall_status_text], spacing=6, height=20)

    def set_reinstall_disabled(disabled):
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
        set_reinstall_disabled(True)
        reinstall_status_text.value = STRINGS[lang]["reinstalling_cli"]
        reinstall_status_icon.color = "#F59E0B"
        page.update()

        def run_reinstall():
            try:
                download_and_install_cli(lang=lang)
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
            reinstall_container.bgcolor = "#1E2A47"
            reinstall_container.border = ft.Border.all(1, "#F59E0B")
        else:
            reinstall_container.bgcolor = "#151E33"
            reinstall_container.border = ft.Border.all(1, "#2E3C56")
        reinstall_container.update()

    reinstall_icon = ft.Icon(ft.Icons.REFRESH_ROUNDED, color="#F59E0B", size=20)
    reinstall_label = ft.Text(STRINGS[lang]["btn_reinstall_cli"], color="#F59E0B", size=14, weight=ft.FontWeight.W_600)

    reinstall_container = ft.Container(
        content=ft.Row(
            [reinstall_icon, reinstall_label],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
        ),
        on_click=on_reinstall_click,
        on_hover=on_reinstall_hover,
        border=ft.Border.all(1, "#2E3C56"),
        border_radius=12,
        bgcolor="#151E33",
        padding=ft.Padding(left=16, right=16, top=12, bottom=12),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )
    reinstall_container.data_on_click = on_reinstall_click
    reinstall_container.data_on_hover = on_reinstall_hover

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

    # --- Layout ---
    content = ft.Column(
        [
            ft.Text(STRINGS[lang]["api_key_required_text"], color="#E2E8F0", size=12),
            api_key_field,
            ft.Row([api_check_btn, api_check_row], alignment=ft.MainAxisAlignment.START, spacing=5),
            ft.TextButton(
                content=ft.Text(STRINGS[lang]["btn_get_api_key"], color="#00F0FF", size=13),
                icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                on_click=open_get_key
            ),
            ft.Divider(height=1, color="#2E3C56"),
            reinstall_row,
            reinstall_status_row,
        ],
        spacing=8,
        width=400,
        height=260,
        alignment=ft.MainAxisAlignment.START,
    )

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(STRINGS[lang]["api_key_setup_title"], color="#FFFFFF", weight=ft.FontWeight.BOLD),
        content=content,
        actions=[save_btn],
        actions_alignment=ft.MainAxisAlignment.END,
        bgcolor="#151E33",
        content_padding=ft.Padding(left=24, right=24, top=10, bottom=10),
    )

    page.show_dialog(dlg)
