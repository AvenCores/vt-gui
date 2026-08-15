"""
Core package containing application configuration, platform constants, and bundling utilities.
"""

from .constants import (
    IS_WINDOWS,
    CLI_BINARY_NAME,
    KNOWN_HASHES,
    LANG_NAMES,
    LANG_FLAGS,
)
from .config import (
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
    get_app_theme,
    set_app_theme,
)
from .bundle_runtime import prepare_flet_runtime
from .ssl_helper import get_ca_bundle_path, get_ssl_context, init_ssl_context

__all__ = [
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
    "get_app_theme",
    "set_app_theme",
    "prepare_flet_runtime",
    "get_ca_bundle_path",
    "get_ssl_context",
    "init_ssl_context",
]
