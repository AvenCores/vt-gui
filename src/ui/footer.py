import flet as ft
import webbrowser

APP_VERSION = "V1.0.0"

def build_footer(lang="en", page=None):
    """Builds a sticky, premium footer containing social links with hover animations."""
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

    about_text = "О программе" if lang == "ru" else "About"
    donate_text = "Поддержать автора" if lang == "ru" else "Support the author"
    copy_text = "Скопировать номер карты" if lang == "ru" else "Copy card number"
    copied_text = "Номер карты скопирован!" if lang == "ru" else "Card number copied!"
    close_text = "Закрыть" if lang == "ru" else "Close"
    card_number = "2202 2050 1464 4675"

    def on_about_click(e):
        dlg = ft.AlertDialog(
            title=ft.Text("VirusTotal File Scanner", color="#FFFFFF", weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Text(f"{APP_VERSION}", color="#00F0FF", size=14, weight=ft.FontWeight.BOLD),
                ft.Text("Powered by VirusTotal V3 API", color="#94A3B8", size=12),
                ft.Text("github.com/AvenCores", color="#94A3B8", size=11),
            ], spacing=6, height=80),
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

    version_label = ft.Container(
        content=ft.Text(APP_VERSION, color="#E2E8F0", size=12, weight=ft.FontWeight.W_600),
        padding=ft.Padding(left=5, right=0, top=0, bottom=0),
        tooltip=APP_VERSION
    )
    donate_btn = make_social_link("donate.svg", "#", donate_text)
    donate_btn.on_click = on_donate_click

    about_btn = make_social_link("info.svg", "#", about_text)
    about_btn.on_click = on_about_click

    return ft.Container(
        content=ft.Column([
            ft.Row(
                [
                    version_label,
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
