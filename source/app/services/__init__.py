"""
Services package providing business logic pipelines (scanning, history tracking, report import/export).
"""

from .scan_service import ScanService, resolve_scan_status
from .history_service import (
    load_history,
    save_history,
    add_scan_record,
    add_lookup_record,
    delete_scan_record,
    update_scan_record_results,
    clear_history,
    get_history,
)
from .export_service import (
    export_report_to_path,
    export_report_to_file,
    prompt_export_report,
    parse_imported_report,
    prompt_import_report,
)

__all__ = [
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
]
