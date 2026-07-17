import os
import flet as ft
import webbrowser
from ..config import write_env_var, STRINGS

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
        expand=True
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

    content = ft.Column(
        [
            ft.Row([
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color="#FFD700", size=24),
                ft.Column([
                    ft.Text(STRINGS[lang]["api_key_required_text"], color="#E2E8F0", size=13, selectable=True)
                ], spacing=0, expand=True)
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START),
            api_key_field,
            ft.TextButton(
                content=ft.Text(STRINGS[lang]["btn_get_api_key"], color="#00F0FF", size=13),
                icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                on_click=open_get_key
            )
        ],
        spacing=12,
        height=160,
        width=420
    )

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(STRINGS[lang]["api_key_setup_title"], color="#FFFFFF", weight=ft.FontWeight.BOLD),
        content=content,
        actions=[save_btn],
        actions_alignment=ft.MainAxisAlignment.END,
        bgcolor="#151E33"
    )

    page.show_dialog(dlg)
