import flet as ft
from ...core.config import STRINGS, get_available_langs, get_lang_flag
from .theme import get_theme_palette


def build_header(
    current_lang: str,
    on_language_change,
    on_settings_click,
    theme_mode: str = "dark",
    on_theme_toggle=None,
) -> ft.Container:
    """
    Builds the top header bar with application branding,
    language selector dropdown, animated theme switch button, and settings button.
    """
    palette = get_theme_palette(theme_mode)
    available_langs = get_available_langs()
    active_lang_name = dict([(c, n) for c, n, f in available_langs]).get(current_lang, current_lang.upper())
    active_lang_flag = get_lang_flag(current_lang)

    language_menu = ft.PopupMenuButton(
        content=ft.Container(
            content=ft.Row(
                [
                    ft.Image(src=active_lang_flag, width=20, height=14, fit=ft.BoxFit.CONTAIN, border_radius=2),
                    ft.Text(active_lang_name, color=palette["text_primary"], size=13, weight=ft.FontWeight.W_600),
                    ft.Icon(ft.Icons.ARROW_DROP_DOWN_ROUNDED, color=palette["text_muted"], size=16),
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            padding=ft.Padding(left=10, right=8, top=6, bottom=6),
            border=ft.Border.all(1, palette["card_border"]),
            border_radius=8,
            bgcolor=palette["card_bg"]
        ),
        tooltip="Select Language / Выбрать язык",
        items=[
            ft.PopupMenuItem(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.CHECK_ROUNDED, color=palette["accent"] if current_lang == code else "transparent", size=16),
                        ft.Image(src=flag, width=20, height=14, fit=ft.BoxFit.CONTAIN, border_radius=2),
                        ft.Text(name, color=palette["text_secondary"], size=13),
                    ],
                    spacing=8
                ),
                on_click=lambda _, c=code: on_language_change(c)
            )
            for code, name, flag in available_langs
        ]
    )

    is_dark = (theme_mode == "dark")
    theme_icon = ft.Icons.LIGHT_MODE_ROUNDED if is_dark else ft.Icons.DARK_MODE_ROUNDED
    theme_icon_color = "#F59E0B" if is_dark else "#3B82F6"
    theme_tooltip = STRINGS.get(current_lang, {}).get(
        "theme_toggle_light" if is_dark else "theme_toggle_dark",
        "Switch to Light Theme" if is_dark else "Switch to Dark Theme"
    )

    theme_icon_widget = ft.Icon(
        theme_icon,
        color=theme_icon_color,
        size=19
    )

    icon_wrapper = ft.Container(
        content=theme_icon_widget,
        alignment=ft.Alignment.CENTER,
        rotate=0.0,
        scale=1.0,
        animate_rotation=ft.Animation(400, ft.AnimationCurve.EASE_OUT_BACK),
        animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )

    theme_button = ft.Container(
        content=icon_wrapper,
        width=38,
        height=38,
        border_radius=8,
        border=ft.Border.all(1, palette["card_border"]),
        bgcolor=palette["card_bg"],
        alignment=ft.Alignment.CENTER,
        tooltip=theme_tooltip,
        animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
    )

    def on_theme_click(e):
        icon_wrapper.rotate = (icon_wrapper.rotate or 0.0) + 3.14159
        icon_wrapper.scale = 0.75
        try:
            icon_wrapper.update()
        except Exception:
            pass
        if on_theme_toggle:
            on_theme_toggle(e)

    def on_theme_hover(e):
        if e.data == "true":
            theme_button.bgcolor = palette["card_bg_hover"]
            theme_button.border = ft.Border.all(1, palette["accent"])
            icon_wrapper.scale = 1.12
        else:
            theme_button.bgcolor = palette["card_bg"]
            theme_button.border = ft.Border.all(1, palette["card_border"])
            icon_wrapper.scale = 1.0
        try:
            theme_button.update()
            icon_wrapper.update()
        except Exception:
            pass

    theme_button.on_click = on_theme_click
    theme_button.on_hover = on_theme_hover

    settings_button = ft.IconButton(
        icon=ft.Icons.SETTINGS_ROUNDED,
        icon_color=palette["text_muted"],
        tooltip=STRINGS.get(current_lang, {}).get("settings_title", "Settings"),
        on_click=on_settings_click
    )

    return ft.Container(
        content=ft.Row(
            [
                ft.Row([
                    ft.Icon(ft.Icons.SECURITY_ROUNDED, color=palette["accent"], size=30),
                    ft.Column([
                        ft.Text(STRINGS[current_lang]["app_title"], size=20, weight=ft.FontWeight.BOLD, color=palette["text_primary"]),
                        ft.Text("Powered by VirusTotal V3 API", size=11, color=palette["text_muted"])
                    ], spacing=1)
                ]),
                ft.Row([
                    language_menu,
                    theme_button,
                    settings_button
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        padding=ft.Padding(bottom=15),
        border=ft.Border.only(bottom=ft.BorderSide(1, palette["divider"]))
    )
