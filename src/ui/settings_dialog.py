import flet as ft
from ..config import load_env_vars, write_env_var, STRINGS
from ..context_menu import register_context_menu, unregister_context_menu

def open_settings(page, lang, on_settings_saved):
    """Opens a beautiful modal settings dialog with configuration options."""
    env_vars = load_env_vars()
    api_key = env_vars.get("VT_APIKEY", "")
    is_direct = env_vars.get("DIRECT_MODE") == "True"
    
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
    
    direct_switch = ft.Switch(
        value=is_direct,
        label=STRINGS[lang]["direct_mode_label"],
        active_color="#00F0FF",
        label_style=ft.TextStyle(color="#E2E8F0", size=13)
    )
    
    # Helper to show alerts inside settings
    def show_settings_alert(text):
        def close_inner_dlg(e):
            page.dialog.open = False
            page.update()
            
        page.dialog = ft.AlertDialog(
            title=ft.Text(STRINGS[lang]["settings_title"], color="#FFFFFF", weight=ft.FontWeight.BOLD),
            content=ft.Text(text, color="#E2E8F0"),
            actions=[ft.TextButton(STRINGS[lang]["btn_close"], on_click=close_inner_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#1E293B",
            border=ft.Border.all(1, "#334155")
        )
        page.dialog.open = True
        page.update()

    def register_menu(e):
        ok, err = register_context_menu()
        if ok:
            show_settings_alert(STRINGS[lang]["context_menu_success"])
        else:
            show_settings_alert(STRINGS[lang]["context_menu_fail"].format(e=err))
            
    def unregister_menu(e):
        ok, err = unregister_context_menu()
        if ok:
            show_settings_alert(STRINGS[lang]["context_menu_removed"])
        else:
            show_settings_alert(STRINGS[lang]["context_menu_fail"].format(e=err))
            
    register_btn = ft.ElevatedButton(
        text=STRINGS[lang]["context_menu_register"],
        icon=ft.Icons.ADD_LINK_ROUNDED,
        color="#FFFFFF",
        bgcolor="#10B981",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=register_menu
    )
    
    unregister_btn = ft.OutlinedButton(
        text=STRINGS[lang]["context_menu_unregister"],
        icon=ft.Icons.LINK_OFF_ROUNDED,
        color="#EF4444",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=unregister_menu
    )
    
    def save_settings(e):
        write_env_var("VT_APIKEY", api_key_field.value.strip())
        write_env_var("DIRECT_MODE", str(direct_switch.value))
        
        # Close dialog
        page.dialog.open = False
        page.update()
        
        # Call completion callback to reload parent UI
        on_settings_saved()
        
    settings_content = ft.Column(
        [
            api_key_field,
            ft.Divider(color="#2E3C56"),
            direct_switch,
            ft.Text(STRINGS[lang]["direct_mode_hint"], size=10, color="#94A3B8"),
            ft.Divider(color="#2E3C56"),
            ft.Text(STRINGS[lang]["context_menu_label"], weight=ft.FontWeight.BOLD, size=13, color="#FFFFFF"),
            ft.Row([register_btn, unregister_btn], spacing=10)
        ],
        spacing=15,
        height=320,
        width=400
    )
    
    page.dialog = ft.AlertDialog(
        title=ft.Text(STRINGS[lang]["settings_title"], color="#FFFFFF", weight=ft.FontWeight.BOLD),
        content=settings_content,
        actions=[
            ft.TextButton(STRINGS[lang]["btn_no"], on_click=lambda _: close_dlg()),
            ft.ElevatedButton(STRINGS[lang]["btn_save"], on_click=save_settings, bgcolor="#008DDA", color="#FFFFFF")
        ],
        bgcolor="#151E33",
        border=ft.Border.all(1, "#2E3C56")
    )
    
    def close_dlg():
        page.dialog.open = False
        page.update()
        
    page.dialog.open = True
    page.update()
