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
)
from .bundle_runtime import prepare_flet_runtime

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
    "prepare_flet_runtime",
]
