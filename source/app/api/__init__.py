"""
API package providing VirusTotal v3 REST API interactions and vt CLI management.
"""

from .vt_api import (
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
)

from .cli_manager import (
    get_temp_bin_path,
    check_installed_binary,
    get_installed_binary_path,
    process_selected_binary,
    download_and_install_cli,
)

__all__ = [
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
]
