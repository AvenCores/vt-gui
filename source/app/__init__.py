"""
VT GUI Application Package
~~~~~~~~~~~~~~~~~~~~~~~~~~

A modern cross-platform GUI for VirusTotal built with Python and Flet.

Modules:
    - config: Configuration, environment (.env/~/.vt.toml), language and strings.
    - vt_api: VirusTotal v3 REST API client.
    - cli_manager: vt CLI binary installation, verification and update manager.
    - history_manager: Local scan and search history storage.
    - exporter: JSON report export and import utilities.
    - clipboard_utils: Cross-platform clipboard helper.
    - bundle_runtime: Packaging helper for bundling Flet desktop runtime.
    - services: Business logic and scan pipelines (ScanService).
    - ui: User interface components, views, and modal dialogs.
"""

from .config import STRINGS, get_api_key, get_app_lang, write_env_var
from .vt_api import check_file_exists_direct, check_file_exists_vt
from .cli_manager import check_installed_binary, download_and_install_cli
from .history_manager import update_scan_record_results, load_history, clear_history
from .exporter import prompt_export_report, prompt_import_report
from .clipboard_utils import safe_copy_to_clipboard

__all__ = [
    "STRINGS",
    "get_api_key",
    "get_app_lang",
    "write_env_var",
    "check_file_exists_direct",
    "check_file_exists_vt",
    "check_installed_binary",
    "download_and_install_cli",
    "update_scan_record_results",
    "load_history",
    "clear_history",
    "prompt_export_report",
    "prompt_import_report",
    "safe_copy_to_clipboard",
]
