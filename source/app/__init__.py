"""
VT GUI Application Package
~~~~~~~~~~~~~~~~~~~~~~~~~~

A modern cross-platform GUI for VirusTotal built with Python and Flet.

Subpackages:
    - app.core: Application configuration, constants, localization, and packaging utilities.
    - app.api: VirusTotal v3 REST API client and vt CLI binary manager.
    - app.services: Application business logic (scan pipelines, history storage, report import/export).
    - app.utils: General helper utilities (clipboard, hashing).
    - app.ui: User interface components, views, and modal dialogs.
"""

from .core import (
    IS_WINDOWS,
    CLI_BINARY_NAME,
    KNOWN_HASHES,
    LANG_NAMES,
    LANG_FLAGS,
    STRINGS,
    get_release_zip_name,
    get_lang_flag,
    get_available_langs,
    load_env_vars,
    get_env_file_path,
    get_vt_toml_path,
    read_key_from_vt_toml,
    write_key_to_vt_toml,
    write_env_var,
    get_api_key,
    get_app_lang,
    prepare_flet_runtime,
)

from .api import (
    check_file_exists_direct,
    verify_api_key,
    check_file_exists_vt,
    get_user_quota,
    reanalyze_item,
    submit_url_scan,
    get_file_behaviours,
    get_subdomains,
    get_dns_resolutions,
    get_comments,
    add_comment,
    delete_comment,
    vote_item,
    get_user_vote,
    diff_files,
    get_yara_rulesets,
    get_temp_bin_path,
    check_installed_binary,
    get_installed_binary_path,
    process_selected_binary,
    download_and_install_cli,
)

from .services import (
    ScanService,
    resolve_scan_status,
    load_history,
    save_history,
    add_scan_record,
    add_lookup_record,
    delete_scan_record,
    update_scan_record_results,
    clear_history,
    get_history,
    export_report_to_path,
    export_report_to_file,
    prompt_export_report,
    parse_imported_report,
    prompt_import_report,
)

from .utils import (
    set_clipboard_win32,
    safe_copy_to_clipboard,
    compute_sha256,
)

from .ui import (
    build_header,
    build_footer,
    make_loading_card,
    make_stat_card,
    make_file_details_card,
    make_engine_row,
    open_api_key_dialog,
    open_settings,
    build_install_view,
    build_scanner_view,
    build_scanning_view,
    build_results_view,
    build_history_view,
    IntelligenceView,
    ToolsView,
)

__all__ = [
    # Core
    "IS_WINDOWS",
    "CLI_BINARY_NAME",
    "KNOWN_HASHES",
    "LANG_NAMES",
    "LANG_FLAGS",
    "STRINGS",
    "get_release_zip_name",
    "get_lang_flag",
    "get_available_langs",
    "load_env_vars",
    "get_env_file_path",
    "get_vt_toml_path",
    "read_key_from_vt_toml",
    "write_key_to_vt_toml",
    "write_env_var",
    "get_api_key",
    "get_app_lang",
    "prepare_flet_runtime",
    # API
    "check_file_exists_direct",
    "verify_api_key",
    "check_file_exists_vt",
    "get_user_quota",
    "reanalyze_item",
    "submit_url_scan",
    "get_file_behaviours",
    "get_subdomains",
    "get_dns_resolutions",
    "get_comments",
    "add_comment",
    "delete_comment",
    "vote_item",
    "get_user_vote",
    "diff_files",
    "get_yara_rulesets",
    "get_temp_bin_path",
    "check_installed_binary",
    "get_installed_binary_path",
    "process_selected_binary",
    "download_and_install_cli",
    # Services
    "ScanService",
    "resolve_scan_status",
    "load_history",
    "save_history",
    "add_scan_record",
    "add_lookup_record",
    "delete_scan_record",
    "update_scan_record_results",
    "clear_history",
    "get_history",
    "export_report_to_path",
    "export_report_to_file",
    "prompt_export_report",
    "parse_imported_report",
    "prompt_import_report",
    # Utils
    "set_clipboard_win32",
    "safe_copy_to_clipboard",
    "compute_sha256",
    # UI
    "build_header",
    "build_footer",
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
