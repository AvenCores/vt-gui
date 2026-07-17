import flet as ft
from ..config import write_env_var, STRINGS, get_api_key

def open_settings(page, lang, on_settings_saved):
    """Opens a beautiful modal settings dialog with configuration options."""
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
        text_style=ft.TextStyle(color="#E2E8F0")
    )
    
    def save_settings(e):
        write_env_var("VT_APIKEY", api_key_field.value.strip())
        
        # Close settings dialog
        page.pop_dialog()
        
        # Call completion callback to reload parent UI
        on_settings_saved()
        
    settings_content = ft.Column(
        [
            api_key_field
        ],
        spacing=15,
        height=80,
        width=400
    )
    
    dlg = ft.AlertDialog(
        title=ft.Text(STRINGS[lang]["settings_title"], color="#FFFFFF", weight=ft.FontWeight.BOLD),
        content=settings_content,
        actions=[
            ft.TextButton(STRINGS[lang]["btn_no"], on_click=lambda _: page.pop_dialog()),
            ft.ElevatedButton(STRINGS[lang]["btn_save"], on_click=save_settings, bgcolor="#008DDA", color="#FFFFFF")
        ],
        bgcolor="#151E33"
    )
    
    page.show_dialog(dlg)
