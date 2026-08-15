import sys

# Platform-aware binary name
IS_WINDOWS = sys.platform == "win32"
CLI_BINARY_NAME = "vt.exe" if IS_WINDOWS else "vt"

# Official SHA-256 hashes of the vt CLI binary itself
KNOWN_HASHES = {
    # Version 1.3.1 — Windows
    "1f46c735b74a0a094b10faa3c58fee84577e767e2c7df3c2b0799ec8ff85c404": "1.3.1 (Windows 64-bit)",
    "b8a1acb1a5e857046852f9ca806099a9c48faedfc690ec3c8233659a6c8cc1e7": "1.3.1 (Windows 32-bit)",
    # Version 1.3.1 — Linux
    "600b19a99dced17d9e8d075f76a719ff30d7b6e3b18884d1eac670b128c34f8c": "1.3.1 (Linux 64-bit)",
    "1310faa6e352a22e3a95c8c82e3ff69ced1f507a7be2d2de3dc7a2c4e1465dee": "1.3.1 (Linux 32-bit)",
    # Version 1.3.1 — macOS
    "d32449caf0cb059c9331e3f2dfce7703823ff0faf8a40270a20f68ebb618a970": "1.3.1 (macOS)",
    # Version 1.3.1 — FreeBSD
    "87edffbd677e81083c4d0954383ad314f76ef3e3b58c01d471c3a152d2b80c56": "1.3.1 (FreeBSD 64-bit)",
    "516fbd51c01aaa086d71a34eb5bc0c5032eb2b1c7c55778b100952e5339573d0": "1.3.1 (FreeBSD 32-bit)",
}

# Display names for each language code
LANG_NAMES = {
    "en": "English",
    "ru": "Русский",
    "es": "Español",
    "de": "Deutsch",
    "fr": "Français",
    "pt": "Português",
    "tr": "Türkçe",
    "uk": "Українська",
    "zh": "中文",
    "ja": "日本語",
    "ko": "한국어",
    "ar": "العربية",
}

# Country flag image asset paths for each language code
LANG_FLAGS = {
    "en": "flags/en.png",
    "ru": "flags/ru.png",
    "es": "flags/es.png",
    "de": "flags/de.png",
    "fr": "flags/fr.png",
    "pt": "flags/pt.png",
    "tr": "flags/tr.png",
    "uk": "flags/uk.png",
    "zh": "flags/zh.png",
    "ja": "flags/ja.png",
    "ko": "flags/ko.png",
    "ar": "flags/ar.png",
}
