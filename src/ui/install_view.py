import flet as ft
import webbrowser
from ..config import STRINGS

def build_install_view(cli_status, cli_hash, lang, file_picker_cli, on_direct_mode_changed, direct_mode_init, on_cli_click):
    """Builds the Flet container for the vt.exe CLI manual installation screen."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Row([
                    ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, color="#F59E0B", size=24),
                    ft.Text(STRINGS[lang]["download_instructions_title"], size=18, weight=ft.FontWeight.BOLD, color="#FFFFFF")
                ], spacing=10),
                ft.Text(STRINGS[lang]["download_instructions_text"], size=14, color="#E2E8F0"),
                ft.Container(height=10),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            content=STRINGS[lang]["open_releases"],
                            icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                            icon_color="#FFFFFF",
                            color="#FFFFFF",
                            bgcolor="#008DDA",
                            on_click=lambda _: webbrowser.open("https://github.com/VirusTotal/vt-cli/releases"),
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                        ),
                        ft.OutlinedButton(
                            content=STRINGS[lang]["select_file_zip"],
                            icon=ft.Icons.FOLDER_OPEN_ROUNDED,
                            on_click=on_cli_click,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=8),
                                side=ft.BorderSide(1, "#00F0FF"),
                                color="#00F0FF"
                            )
                        )
                    ],
                    spacing=15
                ),
                ft.Divider(color="#1E293B"),
                ft.Row(
                    [
                        ft.Text(STRINGS[lang]["direct_mode_label"], size=13, color="#E2E8F0", weight=ft.FontWeight.BOLD),
                        ft.Switch(
                            value=direct_mode_init,
                            active_color="#00F0FF",
                            on_change=on_direct_mode_changed
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Text(STRINGS[lang]["direct_mode_hint"], size=11, color="#94A3B8")
            ],
            spacing=15
        ),
        bgcolor="#151E33",
        border=ft.Border.all(1, "#2E3C56"),
        border_radius=16,
        padding=25
    )
