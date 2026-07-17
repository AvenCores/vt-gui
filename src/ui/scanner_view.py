import flet as ft
from ..config import STRINGS, KNOWN_HASHES

def build_scanner_view(cli_status, cli_hash, is_direct, lang, file_picker_scan, on_scan_file_selected):
    """Builds the main File Scanner view with drag-and-drop simulated click zone and badges."""
    # Build Status Badge for CLI
    if is_direct:
        badge_text = STRINGS[lang]["direct_mode_label"]
        badge_color = "#008DDA"
        badge_icon = ft.Icons.HTTP_ROUNDED
    elif cli_status == 'verified':
        version_str = KNOWN_HASHES.get(cli_hash, "CLI")
        badge_text = STRINGS[lang]["vt_exe_verified"].format(version=version_str)
        badge_color = "#10B981"
        badge_icon = ft.Icons.CHECK_CIRCLE_ROUNDED
    elif cli_status == 'custom':
        badge_text = STRINGS[lang]["vt_exe_custom"]
        badge_color = "#10B981"
        badge_icon = ft.Icons.CHECK_CIRCLE_ROUNDED
    elif cli_status == 'unapproved':
        badge_text = STRINGS[lang]["vt_exe_unapproved"].format(hash=cli_hash[:8] + "...")
        badge_color = "#EF4444"
        badge_icon = ft.Icons.GPP_BAD_ROUNDED
    else:
        badge_text = STRINGS[lang]["vt_exe_missing"]
        badge_color = "#F59E0B"
        badge_icon = ft.Icons.WARNING_ROUNDED
        
    status_badge = ft.Container(
        content=ft.Row([
            ft.Icon(badge_icon, color="#FFFFFF", size=14),
            ft.Text(badge_text, color="#FFFFFF", size=12, weight=ft.FontWeight.BOLD)
        ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=badge_color,
        padding=ft.Padding(left=12, right=12, top=6, bottom=6),
        border_radius=15,
    )
    
    # Dashed-look click area
    dashed_area = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.CLOUD_UPLOAD_ROUNDED, size=56, color="#00F0FF"),
                ft.Text(STRINGS[lang]["drag_drop_text"], size=16, color="#E2E8F0", weight=ft.FontWeight.W_600, text_align=ft.TextAlign.CENTER),
                ft.Text("Max size: 650 MB", size=12, color="#94A3B8")
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        ),
        border=ft.Border.all(2, "#2E3C56"),
        border_radius=16,
        bgcolor="#151E33",
        height=250,
        alignment=ft.Alignment.CENTER,
        on_click=lambda _: on_scan_file_selected(file_picker_scan.pick_files(allow_multiple=False)),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT)
    )
    
    def on_hover_dashed(e):
        dashed_area.border = ft.Border.all(2, "#00F0FF" if e.data == "true" else "#2E3C56")
        dashed_area.bgcolor = "#1E2A47" if e.data == "true" else "#151E33"
        dashed_area.update()
        
    dashed_area.on_hover = on_hover_dashed
    
    return ft.Column(
        [
            ft.Row([
                ft.Text(STRINGS[lang]["vt_exe_status"] + ":", size=14, color="#94A3B8", weight=ft.FontWeight.BOLD),
                status_badge
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=10),
            dashed_area
        ],
        spacing=15,
        expand=True
    )
