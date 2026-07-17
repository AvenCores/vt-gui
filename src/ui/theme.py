import flet as ft

def make_stat_card(label, count, color_hex, icon):
    """Creates a beautiful, glowing stat card control."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(icon, color=color_hex, size=24),
                ft.Text(str(count), size=20, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                ft.Text(label, size=11, color="#94A3B8", weight=ft.FontWeight.W_600),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5
        ),
        bgcolor="#151E33",
        border=ft.Border.all(1, "#2E3C56"),
        border_radius=12,
        padding=12,
        alignment=ft.Alignment.CENTER,
        expand=True,
        shadow=ft.BoxShadow(blur_radius=8, color="#000000", offset=ft.Offset(0, 3))
    )

def make_file_details_card(filename, size, sha256, strings, lang):
    """Creates a clean metadata display card for the scanned file."""
    size_mb = size / (1024 * 1024) if size else 0
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(strings[lang]["file_details"], size=15, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                ft.Divider(color="#1E293B", height=1),
                ft.Row([
                    ft.Text(f"{strings[lang]['file_name']}:", size=13, color="#94A3B8"),
                    ft.Text(filename, size=13, color="#E2E8F0", weight=ft.FontWeight.W_600),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text(f"{strings[lang]['file_size']}:", size=13, color="#94A3B8"),
                    ft.Text(f"{size_mb:.2f} MB ({size} bytes)" if size else strings[lang]["unknown"], size=13, color="#E2E8F0"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text(f"{strings[lang]['file_hash']}:", size=13, color="#94A3B8"),
                    ft.Text(sha256, size=11, color="#00F0FF", selectable=True),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ],
            spacing=6
        ),
        bgcolor="#151E33",
        border=ft.Border.all(1, "#2E3C56"),
        border_radius=12,
        padding=15
    )

def make_engine_row(name, category, result, method):
    """Creates a highly-styled row for antivirus verdicts with semantic colors."""
    if category == "malicious":
        icon = ft.Icons.REPORT_PROBLEM_ROUNDED
        icon_color = "#FF3131"
        bg_color = "#2A1821"
        border_color = "#4D1F2D"
    elif category == "suspicious":
        icon = ft.Icons.WARNING_AMBER_ROUNDED
        icon_color = "#FFD700"
        bg_color = "#2A2318"
        border_color = "#4D3D1F"
    elif category in ("harmless", "undetected"):
        icon = ft.Icons.CHECK_CIRCLE_ROUNDED
        icon_color = "#39FF14"
        bg_color = "#182A1B"
        border_color = "#1F4D25"
    else:
        icon = ft.Icons.HELP_OUTLINE_ROUNDED
        icon_color = "#94A3B8"
        bg_color = "#151E33"
        border_color = "#2E3C56"
        
    return ft.Container(
        content=ft.Row(
            [
                ft.Row([
                    ft.Icon(icon, color=icon_color, size=18),
                    ft.Text(name, weight=ft.FontWeight.BOLD, size=13, color="#E2E8F0"),
                ], spacing=10),
                ft.Column([
                    ft.Text(result or "Clean", size=13, weight=ft.FontWeight.W_600, color=icon_color),
                    ft.Text(f"Method: {method}", size=9, color="#94A3B8")
                ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.END)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        bgcolor=bg_color,
        border=ft.Border.all(1, border_color),
        border_radius=10,
        padding=ft.Padding(left=15, right=15, top=8, bottom=8),
    )
