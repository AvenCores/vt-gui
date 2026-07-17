import flet as ft
import webbrowser

def build_footer():
    """Builds a sticky, premium footer containing social links with hover animations."""
    def make_social_link(icon_url, dest_url, tooltip):
        img = ft.Image(
            src=icon_url,
            width=20,
            height=20,
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

    return ft.Container(
        content=ft.Row(
            [
                make_social_link(
                    "https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/youtube.svg",
                    "https://youtube.com/@avencores",
                    "YouTube"
                ),
                make_social_link(
                    "https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/telegram.svg",
                    "https://t.me/avencoresyt",
                    "Telegram"
                ),
                make_social_link(
                    "https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/github.svg",
                    "https://github.com/AvenCores",
                    "GitHub"
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20
        ),
        padding=ft.Padding(top=10, right=0, bottom=5, left=0),
        alignment=ft.Alignment(0, 0)
    )
