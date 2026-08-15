import flet as ft
import webbrowser
import urllib.request
import json
import asyncio

from ...core.config import STRINGS
from ...utils.clipboard import safe_copy_to_clipboard
from .theme import get_theme_palette

APP_VERSION = "V1.0.8"
GITHUB_REPO = "AvenCores/vt-gui"
RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def _parse_version(version_str):
    """Parse version string like 'V1.0.0' or '1.0.0' into tuple of ints."""
    v = version_str.lstrip("Vv")
    try:
        return tuple(int(x) for x in v.split("."))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def _check_for_update():
    """Check GitHub for the latest release. Returns (latest_tag, html_url) or None."""
    try:
        req = urllib.request.Request(
            API_URL,
            headers={"User-Agent": "VT-GUI", "Accept": "application/vnd.github.v3+json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            tag = data.get("tag_name", "")
            html_url = data.get("html_url", RELEASES_URL)
            return tag, html_url
    except Exception:
        return None


def build_footer(lang="en", page=None, theme_mode="dark"):
    """Builds a sticky, premium footer containing social links with hover animations and theming support."""
    S = STRINGS.get(lang, STRINGS.get("en", {}))
    palette = get_theme_palette(theme_mode)
    is_dark = (theme_mode == "dark")

    def make_social_link(icon_name, dest_url, tooltip):
        img = ft.Image(
            src=icon_name,
            width=24,
            height=24,
            color=palette["text_muted"]
        )

        def on_hover(e):
            img.color = palette["accent"] if e.data == "true" else palette["text_muted"]
            img.update()

        return ft.Container(
            content=img,
            tooltip=tooltip,
            on_click=lambda _: webbrowser.open(dest_url),
            on_hover=on_hover,
            padding=5,
            border_radius=4
        )

    about_text = S.get("footer_about", "About")
    donate_text = S.get("footer_support_author", "Support the author")
    copy_text = S.get("footer_copy_card", "Copy card number")
    copied_text = S.get("footer_card_copied", "Card number copied!")
    close_text = S.get("btn_close", "Close")
    powered_by_text = S.get("footer_powered_by", "Powered by VirusTotal V3 API")
    author_text = S.get("footer_author", "Author:")
    card_number = "2202 2050 1464 4675"

    def on_about_click(e):
        def open_repo(_):
            webbrowser.open("https://github.com/AvenCores/vt-gui")

        app_desc_text = S.get("app_desc", "Modern GUI application for fast scanning of files, URLs, domains, IP addresses, and YARA rules via official VirusTotal API & CLI.")

        def make_tag_pill(text, icon):
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(icon, color=palette["accent"], size=13),
                        ft.Text(text, color=palette["text_secondary"], size=11, weight=ft.FontWeight.W_600)
                    ],
                    spacing=4,
                    tight=True
                ),
                padding=ft.Padding(left=8, right=8, top=4, bottom=4),
                bgcolor=palette["accent_bg"] if not is_dark else "#1E2A47",
                border=ft.Border.all(1, palette["card_border"]),
                border_radius=12
            )

        tags_row = ft.Row(
            [
                make_tag_pill("VirusTotal V3 API", ft.Icons.API_ROUNDED),
                make_tag_pill("vt-cli Engine", ft.Icons.TERMINAL_ROUNDED),
                make_tag_pill("Cross-Platform", ft.Icons.DEVICES_ROUNDED),
                make_tag_pill("12 Languages", ft.Icons.TRANSLATE_ROUNDED),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            wrap=True,
            spacing=6,
            run_spacing=6
        )

        repo_button = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CODE_ROUNDED, color=palette["accent"], size=16),
                    ft.Text("github.com/AvenCores/vt-gui", color=palette["text_primary"], size=12, weight=ft.FontWeight.W_600),
                    ft.Icon(ft.Icons.OPEN_IN_NEW_ROUNDED, color=palette["text_muted"], size=14)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8
            ),
            padding=ft.Padding(left=14, right=14, top=10, bottom=10),
            bgcolor=palette["card_bg_secondary"],
            border=ft.Border.all(1, palette["accent"]),
            border_radius=10,
            on_click=open_repo,
            alignment=ft.Alignment.CENTER
        )

        info_box = ft.Container(
            content=ft.Column(
                [
                    ft.Text(f"{author_text} AvenCores", color=palette["text_secondary"], size=12, weight=ft.FontWeight.W_600),
                    ft.Text(powered_by_text, color=palette["text_muted"], size=11),
                    ft.Text("License: GNU GPL v3", color=palette["text_muted"], size=11)
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.Padding(left=14, right=14, top=10, bottom=10),
            bgcolor=palette["card_bg_secondary"],
            border=ft.Border.all(1, palette["card_border_subtle"]),
            border_radius=10,
            alignment=ft.Alignment.CENTER
        )

        modal_header = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Icon(ft.Icons.SECURITY_ROUNDED, color=palette["accent"], size=36),
                        padding=12,
                        bgcolor=palette["dialog_header_bg"],
                        border=ft.Border.all(1.5, palette["accent"]),
                        shape=ft.BoxShape.CIRCLE
                    ),
                    ft.Text(
                        S.get("app_title", "VirusTotal File Scanner"),
                        color=palette["text_primary"],
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(
                        content=ft.Text(f"{APP_VERSION}", color=palette["accent"], size=12, weight=ft.FontWeight.BOLD),
                        padding=ft.Padding(left=10, right=10, top=3, bottom=3),
                        bgcolor=palette["card_bg_secondary"],
                        border=ft.Border.all(1, palette["accent"]),
                        border_radius=12
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            ),
            padding=ft.Padding(top=10, bottom=10, left=10, right=10),
            alignment=ft.Alignment.CENTER
        )

        dialog_content = ft.Container(
            width=420,
            content=ft.Column(
                [
                    modal_header,
                    tags_row,
                    ft.Text(
                        app_desc_text,
                        color=palette["text_muted"],
                        size=12,
                        text_align=ft.TextAlign.CENTER
                    ),
                    repo_button,
                    info_box
                ],
                spacing=14,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )

        dlg = ft.AlertDialog(
            content=dialog_content,
            content_padding=ft.Padding(left=20, right=20, top=16, bottom=16),
            actions=[
                ft.Button(
                    close_text,
                    on_click=lambda _: e.control.page.pop_dialog(),
                    bgcolor=palette["button_primary_bg"],
                    color=palette["button_primary_text"],
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                )
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            bgcolor=palette["dialog_bg"]
        )
        e.control.page.show_dialog(dlg)

    def on_donate_click(e):
        clipboard = ft.Clipboard()
        if clipboard not in e.control.page.services:
            e.control.page.services.append(clipboard)

        def copy_card(_):
            e.control.page.run_task(safe_copy_to_clipboard, e.control.page, card_number, clipboard)
            e.control.page.show_dialog(
                ft.SnackBar(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color="#FFFFFF", size=18),
                        ft.Text(copied_text, color="#FFFFFF", weight=ft.FontWeight.W_600)
                    ], spacing=8),
                    bgcolor="#10B981"
                )
            )

        modal_header = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Icon(ft.Icons.FAVORITE_ROUNDED, color="#EC4899", size=36),
                        padding=12,
                        bgcolor="#FDF2F8" if not is_dark else "#3B1527",
                        border=ft.Border.all(1.5, "#EC4899"),
                        shape=ft.BoxShape.CIRCLE
                    ),
                    ft.Text(
                        donate_text,
                        color=palette["text_primary"],
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        S.get("donate_desc", "Your support helps develop the project and add new features!"),
                        color=palette["text_muted"],
                        size=12,
                        text_align=ft.TextAlign.CENTER
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            ),
            padding=ft.Padding(top=10, bottom=10, left=10, right=10),
            alignment=ft.Alignment.CENTER
        )

        card_box = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Image(src="sber.svg", width=22, height=22),
                                    ft.Text("Сбербанк / SBER", color=palette["text_secondary"], size=13, weight=ft.FontWeight.BOLD)
                                ],
                                spacing=8
                            ),
                            ft.Container(
                                content=ft.Text("MIR", color="#10B981", size=10, weight=ft.FontWeight.BOLD),
                                padding=ft.Padding(left=6, right=6, top=2, bottom=2),
                                bgcolor="#ECFDF5" if not is_dark else "#064E3B",
                                border_radius=4
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(card_number, color=palette["accent"], size=16, weight=ft.FontWeight.BOLD),
                                ft.IconButton(
                                    icon=ft.Icons.CONTENT_COPY_ROUNDED,
                                    icon_color=palette["accent"],
                                    icon_size=18,
                                    tooltip=copy_text,
                                    on_click=copy_card
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=ft.Padding(left=12, right=8, top=6, bottom=6),
                        bgcolor=palette["card_bg_secondary"],
                        border=ft.Border.all(1, palette["accent"]),
                        border_radius=8
                    ),
                    ft.Button(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.COPY_ROUNDED, color="#FFFFFF", size=16),
                                ft.Text(copy_text, color="#FFFFFF", size=13, weight=ft.FontWeight.W_600)
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8
                        ),
                        on_click=copy_card,
                        bgcolor=palette["button_primary_bg"],
                        color="#FFFFFF",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    )
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.Padding(left=16, right=16, top=14, bottom=14),
            bgcolor=palette["card_bg_secondary"],
            border=ft.Border.all(1, palette["card_border"]),
            border_radius=12
        )

        thank_you_box = ft.Text(
            S.get("donate_thank_you", "❤️ Thank you for using and supporting the app!"),
            color=palette["text_muted"],
            size=11,
            text_align=ft.TextAlign.CENTER
        )

        dialog_content = ft.Container(
            width=400,
            content=ft.Column(
                [
                    modal_header,
                    card_box,
                    thank_you_box
                ],
                spacing=14,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )

        dlg = ft.AlertDialog(
            content=dialog_content,
            content_padding=ft.Padding(left=20, right=20, top=16, bottom=16),
            actions=[
                ft.Button(
                    close_text,
                    on_click=lambda _: e.control.page.pop_dialog(),
                    bgcolor=palette["button_secondary_bg"],
                    color=palette["button_secondary_text"],
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                )
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            bgcolor=palette["dialog_bg"]
        )
        e.control.page.show_dialog(dlg)

    update_text = S.get("footer_check_update", "Check for updates")
    update_available_text = S.get("footer_update_available", "Update available")
    update_latest_text = S.get("footer_up_to_date", "Up to date")
    update_error_text = S.get("footer_update_error", "Could not check")
    checking_text = S.get("footer_checking", "Checking...")

    version_label = ft.Container(
        content=ft.Text(APP_VERSION, color=palette["text_secondary"], size=12, weight=ft.FontWeight.W_600),
        padding=ft.Padding(left=5, right=0, top=0, bottom=0),
        tooltip=APP_VERSION
    )

    update_btn_icon = ft.Icon(ft.Icons.UPDATE_ROUNDED, size=14, color=palette["text_muted"])
    update_btn_label = ft.Text(update_text, color=palette["text_muted"], size=11)
    update_btn = ft.Container(
        content=ft.Row([update_btn_icon, update_btn_label], spacing=4),
        padding=ft.Padding(left=4, right=4, top=2, bottom=2),
        border_radius=4,
        tooltip=update_text,
        on_hover=lambda e: _on_update_hover(e),
    )

    def _on_update_hover(e):
        if update_btn.data != "checking" and update_btn.data != "update":
            update_btn.bgcolor = palette["card_bg_hover"] if e.data == "true" else None
            update_btn.update()

    def on_update_click(e):
        update_btn.data = "checking"
        update_btn_label.value = checking_text
        update_btn_label.color = "#F59E0B"
        update_btn_icon.color = "#F59E0B"
        update_btn.update()

        def _show_vpn_dialog(e_event=None):
            target_page = page or (e_event.control.page if e_event and hasattr(e_event, "control") else None)
            if not target_page:
                return

            vpn_title_text = S.get("update_error_title", "Update Check Failed")
            vpn_msg_text = S.get("update_error_vpn_desc", "Could not connect to GitHub. Please check your internet connection or turn on a VPN.")
            vpn_promo_text = S.get("update_error_vpn_promo", "Free VPN configs available here:")
            btn_vpn_text = S.get("btn_free_vpn", "Free GOIDA VPN Configs")

            def open_vpn(_):
                webbrowser.open("https://github.com/AvenCores/goida-vpn-configs")

            modal_header = ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Icon(ft.Icons.VPN_LOCK_ROUNDED, color="#F59E0B", size=36),
                            padding=12,
                            bgcolor="#FEF3C7" if not is_dark else "#2D1F07",
                            border=ft.Border.all(1.5, "#F59E0B"),
                            shape=ft.BoxShape.CIRCLE
                        ),
                        ft.Text(
                            vpn_title_text,
                            color=palette["text_primary"],
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            vpn_msg_text,
                            color=palette["text_muted"],
                            size=12,
                            text_align=ft.TextAlign.CENTER
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8
                ),
                padding=ft.Padding(top=10, bottom=10, left=10, right=10),
                alignment=ft.Alignment.CENTER
            )

            vpn_box = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            vpn_promo_text,
                            color=palette["text_muted"],
                            size=12,
                            weight=ft.FontWeight.W_500,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Button(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.KEY_ROUNDED, size=16, color="#FFFFFF"),
                                    ft.Text(btn_vpn_text, color="#FFFFFF", size=13, weight=ft.FontWeight.BOLD),
                                    ft.Icon(ft.Icons.OPEN_IN_NEW_ROUNDED, size=14, color="#FFFFFF"),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=8,
                                tight=True,
                            ),
                            on_click=open_vpn,
                            bgcolor=palette["button_primary_bg"],
                            color="#FFFFFF",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                        ),
                    ],
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding(left=16, right=16, top=14, bottom=14),
                bgcolor=palette["card_bg_secondary"],
                border=ft.Border.all(1, palette["card_border"]),
                border_radius=12
            )

            dialog_content = ft.Container(
                width=400,
                content=ft.Column(
                    [
                        modal_header,
                        vpn_box,
                    ],
                    spacing=14,
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

            dlg = ft.AlertDialog(
                content=dialog_content,
                content_padding=ft.Padding(left=20, right=20, top=16, bottom=16),
                actions=[
                    ft.Button(
                        close_text,
                        on_click=lambda _: target_page.pop_dialog(),
                        bgcolor=palette["button_secondary_bg"],
                        color=palette["button_secondary_text"],
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.CENTER,
                on_dismiss=lambda _: _reset_btn(None),
                bgcolor=palette["dialog_bg"],
            )
            target_page.show_dialog(dlg)

        async def _do_check():
            result = await asyncio.to_thread(_check_for_update)
            if result is None:
                update_btn_label.value = update_error_text
                update_btn_label.color = "#EF4444"
                update_btn_icon.color = "#EF4444"
                update_btn.data = "error"
                update_btn.update()
                _show_vpn_dialog(e)
                return

            latest_tag, html_url = result
            current = _parse_version(APP_VERSION)
            latest = _parse_version(latest_tag)

            if latest > current:
                update_btn_label.value = f"{update_available_text} ({latest_tag})"
                update_btn_label.color = "#10B981"
                update_btn_icon.color = "#10B981"
                update_btn_icon.name = ft.Icons.NEW_RELEASES_ROUNDED
                update_btn.data = "update"
                update_btn.on_click = lambda _: webbrowser.open(html_url)
                update_btn.tooltip = f"{update_available_text}: {latest_tag}"
                update_btn.update()
            else:
                update_btn_label.value = update_latest_text
                update_btn_label.color = "#10B981"
                update_btn_icon.color = "#10B981"
                update_btn_icon.name = ft.Icons.CHECK_CIRCLE_ROUNDED
                update_btn.data = "latest"
                update_btn.update()
                await asyncio.sleep(3)
                _reset_btn(None)

        def _reset_btn(_=None):
            update_btn_label.value = update_text
            update_btn_label.color = palette["text_muted"]
            update_btn_icon.color = palette["text_muted"]
            update_btn_icon.name = ft.Icons.UPDATE_ROUNDED
            update_btn.data = None
            update_btn.on_click = on_update_click
            update_btn.bgcolor = None
            update_btn.tooltip = update_text
            update_btn.update()

        page.run_task(_do_check)

    update_btn.on_click = on_update_click
    update_btn.data = None
    donate_btn = make_social_link("donate.svg", "#", donate_text)
    donate_btn.on_click = on_donate_click

    about_btn = make_social_link("info.svg", "#", about_text)
    about_btn.on_click = on_about_click

    social_icons = ft.Row(
        [
            make_social_link("youtube.svg", "https://www.youtube.com/@avencores/", "YouTube"),
            make_social_link("telegram.svg", "https://t.me/avencoresyt", "Telegram"),
            make_social_link("vk.svg", "https://vk.ru/avencoresreuploads", "VK"),
            make_social_link("dzen.svg", "https://dzen.ru/avencores", "Dzen"),
            make_social_link("github.svg", "https://github.com/AvenCores", "GitHub"),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20,
    )

    left_part = ft.Container(
        content=ft.Row([version_label, update_btn], spacing=8),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        expand=True,
    )

    right_part = ft.Container(
        content=ft.Row([donate_btn, about_btn], spacing=8, alignment=ft.MainAxisAlignment.END),
        expand=True,
    )

    center_part = ft.Container(
        content=social_icons,
        expand=True,
        alignment=ft.Alignment.CENTER,
    )

    return ft.Container(
        content=ft.Row(
            [left_part, center_part, right_part],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(top=10, right=10, bottom=5, left=10)
    )
