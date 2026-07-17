import flet as ft
import webbrowser

APP_VERSION = "V1.0.0"

def build_footer(lang="en"):
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

    def on_about_click(e):
        dlg = ft.AlertDialog(
            title=ft.Text("VirusTotal File Scanner", color="#FFFFFF", weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Text(f"{APP_VERSION}", color="#00F0FF", size=14, weight=ft.FontWeight.BOLD),
                ft.Text("Powered by VirusTotal V3 API", color="#94A3B8", size=12),
                ft.Text("github.com/AvenCores", color="#94A3B8", size=11),
            ], spacing=8),
            actions=[ft.TextButton("OK", on_click=lambda _: e.control.page.pop_dialog())],
            bgcolor="#151E33"
        )
        e.control.page.show_dialog(dlg)

    version_label = ft.Container(
        content=ft.Text(APP_VERSION, color="#E2E8F0", size=12, weight=ft.FontWeight.W_600),
        padding=ft.Padding(left=5, right=0, top=0, bottom=0),
        tooltip=APP_VERSION
    )
    about_btn = make_social_link(
        "info.svg",
        "#",
        about_text
    )
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
                    about_btn
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
        ]),
        padding=ft.Padding(top=10, right=10, bottom=5, left=10)
    )
