"""
UI package providing user interface components, dialogs, and views.
"""

from .components import (
    build_header,
    build_footer,
    get_theme_palette,
    make_loading_card,
    make_stat_card,
    make_file_details_card,
    make_engine_row,
)
from .dialogs import (
    open_api_key_dialog,
    open_settings,
)
from .views import (
    build_install_view,
    build_scanner_view,
    build_scanning_view,
    build_results_view,
    build_history_view,
    IntelligenceView,
    ToolsView,
)

__all__ = [
    "build_header",
    "build_footer",
    "get_theme_palette",
    "make_loading_card",
    "make_stat_card",
    "make_file_details_card",
    "make_engine_row",
    "open_api_key_dialog",
    "open_settings",
    "build_install_view",
    "build_scanner_view",
    "build_scanning_view",
    "build_results_view",
    "build_history_view",
    "IntelligenceView",
    "ToolsView",
]
