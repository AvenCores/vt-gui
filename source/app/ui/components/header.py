import flet as ft
from ...core.config import STRINGS, get_available_langs, get_lang_flag


def build_header(current_lang: str, on_language_change, on_settings_click) -> ft.Container:
    """
    Builds the top header bar with application branding,
    language selector dropdown, and settings button.
    """
    available_langs = get_available_langs()
    active_lang_name = dict([(c, n) for c, n, f in available_langs]).get(current_lang, current_lang.upper())
    active_lang_flag = get_lang_flag(current_lang)

    language_menu = ft.PopupMenuButton(
        content=ft.Container(
            content=ft.Row(
                [
                    ft.Image(src=active_lang_flag, width=20, height=14, fit=ft.BoxFit.CONTAIN, border_radius=2),
                    ft.Text(active_lang_name, color="#FFFFFF", size=13, weight=ft.FontWeight.W_600),
                    ft.Icon(ft.Icons.ARROW_DROP_DOWN_ROUNDED, color="#94A3B8", size=16),
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            padding=ft.Padding(left=10, right=8, top=6, bottom=6),
            border=ft.Border.all(1, "#2E3C56"),
            border_radius=8,
            bgcolor="#151E33"
        ),
        tooltip="Select Language / Выбрать язык",
        items=[
            ft.PopupMenuItem(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.CHECK_ROUNDED, color="#00F0FF" if current_lang == code else "transparent", size=16),
                        ft.Image(src=flag, width=20, height=14, fit=ft.BoxFit.CONTAIN, border_radius=2),
                        ft.Text(name, color="#E2E8F0", size=13),
                    ],
                    spacing=8
                ),
                on_click=lambda _, c=code: on_language_change(c)
            )
            for code, name, flag in available_langs
        ]
    )

    settings_button = ft.IconButton(
        icon=ft.Icons.SETTINGS,
        icon_color="#94A3B8",
        on_click=on_settings_click
    )

    return ft.Container(
        content=ft.Row(
            [
                ft.Row([
                    ft.Icon(ft.Icons.SECURITY_ROUNDED, color="#00F0FF", size=30),
                    ft.Column([
                        ft.Text(STRINGS[current_lang]["app_title"], size=20, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                        ft.Text("Powered by VirusTotal V3 API", size=11, color="#94A3B8")
                    ], spacing=1)
                ]),
                ft.Row([
                    language_menu,
                    settings_button
                ], spacing=5)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        padding=ft.Padding(bottom=15),
        border=ft.Border.only(bottom=ft.BorderSide(1, "#1E293B"))
    )
