"""
UI Dialogs package providing modal dialogs for settings and API key management.
"""

from .api_key_dialog import open_api_key_dialog
from .settings_dialog import open_settings

__all__ = [
    "open_api_key_dialog",
    "open_settings",
]
