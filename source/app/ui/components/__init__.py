"""
UI components package providing layout headers, footers, and shared theme widgets.
"""

from .header import build_header
from .footer import build_footer
from .theme import (
    get_theme_palette,
    make_loading_card,
    make_stat_card,
    make_file_details_card,
    make_engine_row,
)

__all__ = [
    "build_header",
    "build_footer",
    "get_theme_palette",
    "make_loading_card",
    "make_stat_card",
    "make_file_details_card",
    "make_engine_row",
]
