import os
import shutil
import hashlib
import tempfile
import zipfile
from .config import KNOWN_HASHES, CLI_BINARY_NAME, IS_WINDOWS, load_env_vars

# Cache for binary validation to avoid repeated SHA-256 computation
_validation_cache = {}  # {path: (mtime, size, status, hash)}

def get_temp_bin_path():
    """Returns the immutable temp directory binary file path."""
    temp_dir = os.path.join(tempfile.gettempdir(), "vt_cli_immutable")
    os.makedirs(temp_dir, exist_ok=True)
    return os.path.join(temp_dir, CLI_BINARY_NAME)

def _find_binary_in_path():
    """Checks if vt CLI is available in the system PATH."""
    found = shutil.which("vt")
    if found:
        return found
    # On Windows, also check for vt.exe explicitly
    if IS_WINDOWS:
        found = shutil.which("vt.exe")
        if found:
            return found
    return None

def check_installed_binary():
    """Checks if the vt CLI binary is installed and validates its hash.
    First checks the temp directory, then falls back to system PATH.
    Returns: (status, hash, source) where source is 'app', 'system', or None."""
    # Check our managed temp directory first
    path = get_temp_bin_path()
    if os.path.exists(path):
        status, file_hash = _validate_binary(path)
        return status, file_hash, 'app'

    # Fall back to system PATH
    path_in_path = _find_binary_in_path()
    if path_in_path and os.path.exists(path_in_path):
        status, file_hash = _validate_binary(path_in_path)
        return status, file_hash, 'system'

    return 'missing', None, None

def get_installed_binary_path():
    """Returns absolute path to the valid installed vt CLI binary, or None if missing."""
    path = get_temp_bin_path()
    if os.path.exists(path):
        status, _ = _validate_binary(path)
        if status != 'missing':
            return path

    path_in_path = _find_binary_in_path()
    if path_in_path and os.path.exists(path_in_path):
        status, _ = _validate_binary(path_in_path)
        if status != 'missing':
            return path_in_path

    return None

def _validate_binary(path):
    """Validates a binary at the given path. Returns (status, hash).
    Uses a cache keyed on (mtime, size) to avoid redundant hashing."""
    try:
        stat = os.stat(path)
        cache_key = path
        cached = _validation_cache.get(cache_key)
        if cached and cached[0] == stat.st_mtime and cached[1] == stat.st_size:
            return cached[2], cached[3]

        with open(path, "rb") as f:
            data = f.read()
        file_hash = hashlib.sha256(data).hexdigest()

        if file_hash in KNOWN_HASHES:
            status = 'verified'
        else:
            env_vars = load_env_vars()
            if env_vars.get(f"APPROVED_VT_HASH_{file_hash}") == "True":
                status = 'custom'
            else:
                status = 'unapproved'

        _validation_cache[cache_key] = (stat.st_mtime, stat.st_size, status, file_hash)
        return status, file_hash
    except Exception:
        return 'missing', None

def process_selected_binary(file_path):
    """Parses ZIP or vt binary directly to compute hash and extract data.
    Accepts platform-appropriate binaries (vt.exe on Windows, vt on other platforms)."""
    is_zip = zipfile.is_zipfile(file_path)

    if is_zip:
        with zipfile.ZipFile(file_path) as z:
            vt_name = None
            for name in z.namelist():
                basename = os.path.basename(name)
                if basename in ("vt.exe", "vt"):
                    vt_name = name
                    break
            if not vt_name:
                raise ValueError(f"CLI binary ({CLI_BINARY_NAME}) not found inside the ZIP archive.")
            exe_data = z.read(vt_name)
    else:
        basename = os.path.basename(file_path)
        if basename not in ("vt.exe", "vt"):
            raise ValueError("Selected file is not a vt CLI binary or a ZIP archive.")
        with open(file_path, "rb") as f:
            exe_data = f.read()

    exe_hash = hashlib.sha256(exe_data).hexdigest()
    return exe_hash, exe_data

def compute_sha256(file_path):
    """Computes the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return None

def download_and_install_cli(progress_callback=None, lang="en"):
    """Downloads the official vt CLI zip for the current platform, verifies its hash, and extracts it.
    progress_callback signature: (status_text, progress_val)
    Raises Exception on error."""
    import urllib.request
    import io
    from .config import get_release_zip_name, STRINGS

    strings = STRINGS.get(lang, STRINGS.get("en", {}))
    filename = get_release_zip_name()
    url = f"https://github.com/VirusTotal/vt-cli/releases/download/1.3.1/{filename}"

    if progress_callback:
        progress_callback(strings.get("cli_connecting", "Connecting to GitHub..."), 0.1)

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(req) as response:
            total_size = int(response.info().get('Content-Length', 0))
            downloaded = 0
            block_size = 65536
            chunks = []

            while True:
                block = response.read(block_size)
                if not block:
                    break
                chunks.append(block)
                downloaded += len(block)
                if total_size > 0 and progress_callback:
                    percent = downloaded / total_size
                    progress_callback(strings.get("cli_downloading", "Downloading: {percent}%").format(percent=int(percent * 100)), 0.1 + percent * 0.7)

            data = b"".join(chunks)

        if progress_callback:
            progress_callback(strings.get("cli_extracting", "Extracting CLI binary..."), 0.85)

        with zipfile.ZipFile(io.BytesIO(data)) as z:
            vt_name = None
            for name in z.namelist():
                basename = os.path.basename(name)
                if basename in ("vt.exe", "vt"):
                    vt_name = name
                    break
            if not vt_name:
                raise ValueError(f"CLI binary ({CLI_BINARY_NAME}) not found inside the ZIP archive.")
            exe_data = z.read(vt_name)

        if progress_callback:
            progress_callback(strings.get("cli_verifying", "Verifying binary hash..."), 0.9)

        exe_hash = hashlib.sha256(exe_data).hexdigest()
        if exe_hash not in KNOWN_HASHES:
            raise ValueError(f"Extracted binary hash is not recognized as an official release: {exe_hash}")

        if progress_callback:
            progress_callback(strings.get("cli_installing", "Installing..."), 0.95)

        temp_bin = get_temp_bin_path()
        with open(temp_bin, "wb") as f:
            f.write(exe_data)

        # On non-Windows, make the binary executable
        if not IS_WINDOWS:
            os.chmod(temp_bin, 0o755)

        if progress_callback:
            progress_callback(strings.get("cli_done", "Done!"), 1.0)

        return True
    except Exception as e:
        raise e
