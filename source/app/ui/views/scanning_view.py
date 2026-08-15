import flet as ft
from ...core.config import STRINGS
from ..components.theme import get_theme_palette


def build_scanning_view(scan_progress_ring, scan_status_text, scan_progress_bar, lang, theme_mode="dark"):
    """Builds the progress indicator view for ongoing file scans with theme support."""
    palette = get_theme_palette(theme_mode)
    return ft.Container(
        content=ft.Column(
            [
                scan_progress_ring,
                ft.Text(STRINGS[lang]["scan_in_progress"], size=12, weight=ft.FontWeight.BOLD, color=palette["text_muted"]),
                scan_status_text,
                ft.Container(content=scan_progress_bar, width=450, padding=ft.Padding(top=10))
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15
        ),
        expand=True,
        alignment=ft.Alignment.CENTER
    )
