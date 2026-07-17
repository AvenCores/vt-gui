import flet as ft
from ..config import STRINGS, get_cli_display_name

def build_install_view(cli_status, cli_hash, lang, install_status_text, install_progress_bar, on_auto_install_click, on_manual_install_click):
    """Builds the Flet container for the vt CLI automatic and manual installation screen."""
    
    # Auto install primary action
    auto_install_btn = ft.ElevatedButton(
        content=ft.Text(STRINGS[lang]["btn_auto_install"], weight=ft.FontWeight.BOLD),
        icon=ft.Icons.DOWNLOAD_ROUNDED,
        icon_color="#FFFFFF",
        color="#FFFFFF",
        bgcolor="#008DDA",
        height=45,
        on_click=on_auto_install_click,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    )
    
    # Manual install secondary action
    manual_install_btn = ft.OutlinedButton(
        content=ft.Text(STRINGS[lang]["btn_manual_install"]),
        icon=ft.Icons.FOLDER_OPEN_ROUNDED,
        height=45,
        on_click=on_manual_install_click,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            side=ft.BorderSide(1, "#94A3B8"),
            color="#94A3B8"
        )
    )
    
    return ft.Container(
        content=ft.Column(
            [
                ft.Row([
                    ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, color="#F59E0B", size=24),
                    ft.Text(STRINGS[lang]["download_instructions_title"], size=18, weight=ft.FontWeight.BOLD, color="#FFFFFF")
                ], spacing=10),
                ft.Text(STRINGS[lang]["install_desc"], size=14, color="#E2E8F0"),
                ft.Container(height=10),
                ft.Column(
                    [
                        auto_install_btn,
                        manual_install_btn
                    ],
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                ),
                ft.Container(height=10),
                ft.Column(
                    [
                        install_status_text,
                        install_progress_bar
                    ],
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                )
            ],
            spacing=15
        ),
        bgcolor="#151E33",
        border=ft.Border.all(1, "#2E3C56"),
        border_radius=16,
        padding=25,
        width=550
    )
