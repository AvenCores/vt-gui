import os
import shutil
import hashlib
import tempfile
import zipfile
from .config import KNOWN_HASHES, CLI_BINARY_NAME, IS_WINDOWS, load_env_vars

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
    Returns: status ('verified', 'custom', 'unapproved', 'missing') and the hash."""
    # Check our managed temp directory first
    path = get_temp_bin_path()
    if os.path.exists(path):
        return _validate_binary(path)

    # Fall back to system PATH
    path_in_path = _find_binary_in_path()
    if path_in_path:
        return _validate_binary(path_in_path)

    return 'missing', None

def _validate_binary(path):
    """Validates a binary at the given path. Returns (status, hash)."""
    try:
        with open(path, "rb") as f:
            data = f.read()
        file_hash = hashlib.sha256(data).hexdigest()

        if file_hash in KNOWN_HASHES:
            return 'verified', file_hash

        env_vars = load_env_vars()
        if env_vars.get(f"APPROVED_VT_HASH_{file_hash}") == "True":
            return 'custom', file_hash

        return 'unapproved', file_hash
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

def download_and_install_cli(progress_callback=None):
    """Downloads the official vt CLI zip for the current platform, verifies its hash, and extracts it.
    progress_callback signature: (status_text, progress_val)
    Raises Exception on error."""
    import urllib.request
    import io
    from .config import get_release_zip_name

    filename = get_release_zip_name()
    url = f"https://github.com/VirusTotal/vt-cli/releases/download/1.3.1/{filename}"

    if progress_callback:
        progress_callback("Connecting to GitHub...", 0.1)

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(req) as response:
            total_size = int(response.info().get('Content-Length', 0))
            downloaded = 0
            block_size = 8192
            data = b""

            while True:
                block = response.read(block_size)
                if not block:
                    break
                data += block
                downloaded += len(block)
                if total_size > 0 and progress_callback:
                    percent = downloaded / total_size
                    progress_callback(f"Downloading: {int(percent * 100)}%", 0.1 + percent * 0.7)

        if progress_callback:
            progress_callback("Extracting CLI binary...", 0.85)

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
            progress_callback("Verifying binary hash...", 0.9)

        exe_hash = hashlib.sha256(exe_data).hexdigest()
        if exe_hash not in KNOWN_HASHES:
            raise ValueError(f"Extracted binary hash is not recognized as an official release: {exe_hash}")

        if progress_callback:
            progress_callback("Installing...", 0.95)

        temp_bin = get_temp_bin_path()
        with open(temp_bin, "wb") as f:
            f.write(exe_data)

        # On non-Windows, make the binary executable
        if not IS_WINDOWS:
            os.chmod(temp_bin, 0o755)

        if progress_callback:
            progress_callback("Done!", 1.0)

        return True
    except Exception as e:
        raise e
