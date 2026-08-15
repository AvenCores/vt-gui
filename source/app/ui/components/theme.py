import flet as ft

THEME_PALETTES = {
    "dark": {
        "bg_gradient_colors": ["#0B0F19", "#111827"],
        "page_bg": "#0B0F19",
        "card_bg": "#151E33",
        "card_bg_secondary": "#1E293B",
        "card_bg_hover": "#1E2A47",
        "card_border": "#2E3C56",
        "card_border_subtle": "#1E293B",
        "divider": "#1E293B",
        "text_primary": "#FFFFFF",
        "text_secondary": "#E2E8F0",
        "text_muted": "#94A3B8",
        "accent": "#00F0FF",
        "accent_secondary": "#008DDA",
        "accent_bg": "#1E2A47",
        "input_bg": "#151E33",
        "input_border": "#2E3C56",
        "input_border_focus": "#00F0FF",
        "dialog_bg": "#151E33",
        "dialog_header_bg": "#1E2A47",
        "tab_active_bg": "#1E293B",
        "tab_active_border": "#00F0FF",
        "tab_inactive_hover_bg": "#152035",
        "tab_inactive_hover_border": "#00F0FF",
        "button_primary_bg": "#008DDA",
        "button_primary_text": "#FFFFFF",
        "button_secondary_bg": "#1E293B",
        "button_secondary_text": "#FFFFFF",
        "button_secondary_border": "#2E3C56",
        "stat_card_bg": "#151E33",
        "stat_card_border": "#2E3C56",
        "stat_card_shadow": "#000000",
        "shadow_color": "#000000",
        "code_bg": "#0F172A",
    },
    "light": {
        "bg_gradient_colors": ["#F8FAFC", "#EEF2F6"],
        "page_bg": "#F8FAFC",
        "card_bg": "#FFFFFF",
        "card_bg_secondary": "#F1F5F9",
        "card_bg_hover": "#E2E8F0",
        "card_border": "#CBD5E1",
        "card_border_subtle": "#E2E8F0",
        "divider": "#E2E8F0",
        "text_primary": "#0F172A",
        "text_secondary": "#334155",
        "text_muted": "#64748B",
        "accent": "#0284C7",
        "accent_secondary": "#0284C7",
        "accent_bg": "#E0F2FE",
        "input_bg": "#FFFFFF",
        "input_border": "#CBD5E1",
        "input_border_focus": "#0284C7",
        "dialog_bg": "#FFFFFF",
        "dialog_header_bg": "#E0F2FE",
        "tab_active_bg": "#E0F2FE",
        "tab_active_border": "#0284C7",
        "tab_inactive_hover_bg": "#F1F5F9",
        "tab_inactive_hover_border": "#CBD5E1",
        "button_primary_bg": "#0284C7",
        "button_primary_text": "#FFFFFF",
        "button_secondary_bg": "#F1F5F9",
        "button_secondary_text": "#0F172A",
        "button_secondary_border": "#CBD5E1",
        "stat_card_bg": "#FFFFFF",
        "stat_card_border": "#E2E8F0",
        "stat_card_shadow": "#0F172A15",
        "shadow_color": "#0F172A10",
        "code_bg": "#F1F5F9",
    }
}


def get_theme_palette(theme_mode="dark"):
    """Returns the color dictionary for the specified theme mode ('dark' or 'light')."""
    mode = "light" if str(theme_mode).lower().strip() == "light" else "dark"
    return THEME_PALETTES[mode]


def make_loading_card(message, height=140, theme_mode="dark"):
    """Creates a premium glowing loading card for async data fetching."""
    palette = get_theme_palette(theme_mode)
    accent = palette["accent"]
    is_dark = (theme_mode == "dark")
    return ft.Container(
        content=ft.Column(
            [
                ft.ProgressRing(width=28, height=28, stroke_width=2.5, color=accent),
                ft.Text(message, color=accent, size=12, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        ),
        alignment=ft.Alignment(0, 0),
        padding=15,
        height=height,
        bgcolor="#151E33aa" if is_dark else "#FFFFFFdd",
        border_radius=12,
        border=ft.Border.all(1, f"{accent}33"),
        shadow=ft.BoxShadow(blur_radius=10, color=f"{accent}10", offset=ft.Offset(0, 2))
    )


def make_stat_card(label, count, color_hex, icon, theme_mode="dark"):
    """Creates a glowing stat card control."""
    palette = get_theme_palette(theme_mode)
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(icon, color=color_hex, size=24),
                ft.Text(str(count), size=20, weight=ft.FontWeight.BOLD, color=palette["text_primary"]),
                ft.Text(label, size=11, color=palette["text_muted"], weight=ft.FontWeight.W_600),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5
        ),
        bgcolor=palette["stat_card_bg"],
        border=ft.Border.all(1, palette["stat_card_border"]),
        border_radius=12,
        padding=12,
        alignment=ft.Alignment.CENTER,
        expand=True,
        shadow=ft.BoxShadow(blur_radius=8, color=palette["stat_card_shadow"], offset=ft.Offset(0, 3))
    )


def make_file_details_card(filename, size, sha256, strings, lang, theme_mode="dark"):
    """Creates a clean metadata display card for the scanned file."""
    palette = get_theme_palette(theme_mode)
    safe_size = size if isinstance(size, (int, float)) else 0
    size_mb = safe_size / (1024 * 1024) if safe_size else 0
    filename_str = str(filename or "Unknown_File")
    sha256_str = str(sha256 or "")
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(strings[lang]["file_details"], size=15, weight=ft.FontWeight.BOLD, color=palette["text_primary"]),
                ft.Divider(color=palette["divider"], height=1),
                ft.Row([
                    ft.Text(f"{strings[lang]['file_name']}:", size=13, color=palette["text_muted"]),
                    ft.Text(filename_str, size=13, color=palette["text_secondary"], weight=ft.FontWeight.W_600),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text(f"{strings[lang]['file_size']}:", size=13, color=palette["text_muted"]),
                    ft.Text(f"{size_mb:.2f} MB ({safe_size} bytes)" if safe_size else strings[lang]["unknown"], size=13, color=palette["text_secondary"]),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text(f"{strings[lang]['file_hash']}:", size=13, color=palette["text_muted"]),
                    ft.Text(sha256_str, size=11, color=palette["accent"], selectable=True),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ],
            spacing=6
        ),
        bgcolor=palette["card_bg"],
        border=ft.Border.all(1, palette["card_border"]),
        border_radius=12,
        padding=15
    )


def make_engine_row(name, category, result, method, theme_mode="dark"):
    """Creates a styled row for antivirus verdicts with semantic colors."""
    palette = get_theme_palette(theme_mode)
    is_dark = (theme_mode == "dark")
    if category == "malicious":
        icon = ft.Icons.REPORT_PROBLEM_ROUNDED
        icon_color = "#FF3131" if is_dark else "#DC2626"
        bg_color = "#2A1821" if is_dark else "#FEF2F2"
        border_color = "#4D1F2D" if is_dark else "#FECACA"
    elif category == "suspicious":
        icon = ft.Icons.WARNING_AMBER_ROUNDED
        icon_color = "#FFD700" if is_dark else "#D97706"
        bg_color = "#2A2318" if is_dark else "#FFFBEB"
        border_color = "#4D3D1F" if is_dark else "#FDE68A"
    elif category in ("harmless", "undetected"):
        icon = ft.Icons.CHECK_CIRCLE_ROUNDED
        icon_color = "#39FF14" if is_dark else "#16A34A"
        bg_color = "#182A1B" if is_dark else "#F0FDF4"
        border_color = "#1F4D25" if is_dark else "#BBF7D0"
    else:
        icon = ft.Icons.HELP_OUTLINE_ROUNDED
        icon_color = palette["text_muted"]
        bg_color = palette["card_bg"]
        border_color = palette["card_border"]
        
    return ft.Container(
        content=ft.Row(
            [
                ft.Row([
                    ft.Icon(icon, color=icon_color, size=18),
                    ft.Text(name, weight=ft.FontWeight.BOLD, size=13, color=palette["text_secondary"]),
                ], spacing=10),
                ft.Column([
                    ft.Text(result or "Clean", size=13, weight=ft.FontWeight.W_600, color=icon_color),
                    ft.Text(f"Method: {method}", size=9, color=palette["text_muted"])
                ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.END)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        bgcolor=bg_color,
        border=ft.Border.all(1, border_color),
        border_radius=10,
        padding=ft.Padding(left=15, right=15, top=8, bottom=8),
    )
