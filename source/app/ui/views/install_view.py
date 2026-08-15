import flet as ft
from ...core.config import STRINGS
from ..components.theme import get_theme_palette


def build_install_view(cli_status, cli_hash, lang, install_status_text, install_progress_bar, on_auto_install_click, on_manual_install_click, theme_mode="dark"):
    """Builds the Flet container for the vt CLI automatic and manual installation screen with theme support."""
    palette = get_theme_palette(theme_mode)
    
    auto_install_btn = ft.Button(
        content=ft.Text(STRINGS[lang]["btn_auto_install"], weight=ft.FontWeight.BOLD),
        icon=ft.Icons.DOWNLOAD_ROUNDED,
        icon_color="#FFFFFF",
        color="#FFFFFF",
        bgcolor=palette["button_primary_bg"],
        height=45,
        on_click=on_auto_install_click,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    )
    
    manual_install_btn = ft.OutlinedButton(
        content=ft.Text(STRINGS[lang]["btn_manual_install"]),
        icon=ft.Icons.FOLDER_OPEN_ROUNDED,
        height=45,
        on_click=on_manual_install_click,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            side=ft.BorderSide(1, palette["card_border"]),
            color=palette["text_muted"]
        )
    )
    
    card = ft.Container(
        content=ft.Column(
            [
                ft.Row([
                    ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, color="#F59E0B", size=24),
                    ft.Text(STRINGS[lang]["download_instructions_title"], size=18, weight=ft.FontWeight.BOLD, color=palette["text_primary"])
                ], spacing=10),
                ft.Text(STRINGS[lang]["install_desc"], size=14, color=palette["text_secondary"]),
                ft.Container(height=10),
                ft.Column(
                    [
                        auto_install_btn,
                        manual_install_btn
                    ],
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    tight=True
                ),
                ft.Container(height=10),
                ft.Column(
                    [
                        install_status_text,
                        install_progress_bar
                    ],
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    tight=True
                )
            ],
            spacing=15,
            tight=True
        ),
        bgcolor=palette["card_bg"],
        border=ft.Border.all(1, palette["card_border"]),
        border_radius=16,
        padding=25,
        width=550
    )

    return ft.Container(
        content=card,
        alignment=ft.Alignment.CENTER,
        expand=True
    )
