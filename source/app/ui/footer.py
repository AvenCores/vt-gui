import flet as ft
import webbrowser
import urllib.request
import json
import asyncio
from ..config import STRINGS

APP_VERSION = "V1.0.0"
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

def build_footer(lang="en", page=None):
    """Builds a sticky, premium footer containing social links with hover animations."""
    S = STRINGS.get(lang, STRINGS.get("en", {}))

    def make_social_link(icon_name, dest_url, tooltip):
        img = ft.Image(
            src=icon_name,
            width=24,
            height=24,
            color="#94A3B8"
        )

        def on_hover(e):
            img.color = "#00F0FF" if e.data == "true" else "#94A3B8"
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

        dlg = ft.AlertDialog(
            title=ft.Text(S.get("app_title", "VirusTotal File Scanner"), color="#FFFFFF", weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Text(f"{APP_VERSION}", color="#00F0FF", size=14, weight=ft.FontWeight.BOLD),
                ft.Text(powered_by_text, color="#94A3B8", size=12),
                ft.ElevatedButton(
                    content=ft.Text("github.com/AvenCores/vt-gui", color="#FFFFFF", size=12),
                    icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                    on_click=open_repo,
                    bgcolor="#2E3C56",
                    color="#FFFFFF",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                ),
                ft.Text(f"{author_text} AvenCores", color="#94A3B8", size=11)
            ], spacing=6, height=100, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[ft.TextButton("OK", on_click=lambda _: e.control.page.pop_dialog())],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#151E33"
        )
        e.control.page.show_dialog(dlg)

    def on_donate_click(e):
        clipboard = ft.Clipboard()
        e.control.page.services.append(clipboard)

        def copy_card(_):
            e.control.page.run_task(clipboard.set, card_number)
            e.control.page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(copied_text, color="#FFFFFF"),
                    bgcolor="#10B981"
                )
            )

        dlg = ft.AlertDialog(
            title=ft.Text(donate_text, color="#FFFFFF", weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Row([
                    ft.Image(src="sber.svg", width=28, height=28),
                    ft.Text("SBER", color="#FFFFFF", size=15, weight=ft.FontWeight.BOLD)
                ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(
                    content=ft.Text(card_number, color="#FFFFFF", size=15, weight=ft.FontWeight.BOLD),
                    alignment=ft.Alignment.CENTER,
                    padding=ft.Padding(top=10, bottom=10, left=15, right=15),
                    border=ft.Border.all(1, "#2E3C56"),
                    border_radius=8,
                    bgcolor="#0B0F19"
                ),
                ft.ElevatedButton(
                    content=ft.Text(copy_text, color="#FFFFFF", size=13),
                    icon=ft.Icons.COPY_ROUNDED,
                    on_click=copy_card,
                    bgcolor="#008DDA",
                    color="#FFFFFF",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                )
            ], spacing=10, height=160, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[ft.TextButton(close_text, on_click=lambda _: e.control.page.pop_dialog())],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#151E33"
        )
        e.control.page.show_dialog(dlg)

    update_text = S.get("footer_check_update", "Check for updates")
    update_available_text = S.get("footer_update_available", "Update available")
    update_latest_text = S.get("footer_up_to_date", "Up to date")
    update_error_text = S.get("footer_update_error", "Could not check")
    checking_text = S.get("footer_checking", "Checking...")

    version_label = ft.Container(
        content=ft.Text(APP_VERSION, color="#E2E8F0", size=12, weight=ft.FontWeight.W_600),
        padding=ft.Padding(left=5, right=0, top=0, bottom=0),
        tooltip=APP_VERSION
    )

    update_btn_icon = ft.Icon(ft.Icons.UPDATE_ROUNDED, size=14, color="#94A3B8")
    update_btn_label = ft.Text(update_text, color="#94A3B8", size=11)
    update_btn = ft.Container(
        content=ft.Row([update_btn_icon, update_btn_label], spacing=4),
        padding=ft.Padding(left=4, right=4, top=2, bottom=2),
        border_radius=4,
        tooltip=update_text,
        on_hover=lambda e: _on_update_hover(e),
    )

    def _on_update_hover(e):
        if update_btn.data != "checking" and update_btn.data != "update":
            update_btn.bgcolor = "#1E293B" if e.data == "true" else None
            update_btn.update()

    def on_update_click(e):
        update_btn.data = "checking"
        update_btn_label.value = checking_text
        update_btn_label.color = "#FACC15"
        update_btn_icon.color = "#FACC15"
        update_btn.update()

        async def _do_check():
            result = await asyncio.to_thread(_check_for_update)
            if result is None:
                update_btn_label.value = update_error_text
                update_btn_label.color = "#EF4444"
                update_btn_icon.color = "#EF4444"
                update_btn.data = "error"
                update_btn.update()
                await asyncio.sleep(3)
                _reset_btn(None)
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
            update_btn_label.color = "#94A3B8"
            update_btn_icon.color = "#94A3B8"
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

    return ft.Container(
        content=ft.Column([
            ft.Row(
                [
                    ft.Row([version_label, update_btn], spacing=8),
                    ft.Row(
                        [
                            make_social_link("youtube.svg", "https://www.youtube.com/@avencores/", "YouTube"),
                            make_social_link("telegram.svg", "https://t.me/avencoresyt", "Telegram"),
                            make_social_link("vk.svg", "https://vk.ru/avencoresreuploads", "VK"),
                            make_social_link("dzen.svg", "https://dzen.ru/avencores", "Dzen"),
                            make_social_link("github.svg", "https://github.com/AvenCores", "GitHub"),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20
                    ),
                    ft.Row(
                        [
                            donate_btn,
                            about_btn
                        ],
                        spacing=8
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
        ]),
        padding=ft.Padding(top=10, right=10, bottom=5, left=10)
    )
