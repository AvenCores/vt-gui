import os
import hashlib
import tempfile
import zipfile
from .config import KNOWN_HASHES, load_env_vars

def get_temp_bin_path():
    """Returns the immutable temp directory binary file path."""
    temp_dir = os.path.join(tempfile.gettempdir(), "vt_cli_immutable")
    os.makedirs(temp_dir, exist_ok=True)
    return os.path.join(temp_dir, "vt.exe")

def check_installed_binary():
    """Checks if vt.exe is installed and validates its hash.
    Returns: status ('verified', 'custom', 'unapproved', 'missing') and the hash."""
    path = get_temp_bin_path()
    if not os.path.exists(path):
        return 'missing', None
        
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
    """Parses ZIP or vt.exe directly to compute vt.exe's hash and extracts data."""
    is_zip = zipfile.is_zipfile(file_path)
    
    if is_zip:
        with zipfile.ZipFile(file_path) as z:
            vt_name = None
            for name in z.namelist():
                if name.endswith("vt.exe") or name == "vt.exe":
                    vt_name = name
                    break
            if not vt_name:
                raise ValueError("vt.exe not found inside the ZIP archive.")
            exe_data = z.read(vt_name)
    else:
        if not file_path.endswith("vt.exe"):
            raise ValueError("Selected file is not vt.exe or a ZIP archive.")
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
    """Downloads the official vt.exe zip, verifies its hash, and extracts it.
    progress_callback signature: (status_text, progress_val)
    Raises Exception on error."""
    import struct
    import urllib.request
    import io
    
    is_64bit = struct.calcsize("P") * 8 == 64
    filename = "Windows64.zip" if is_64bit else "Windows32.zip"
    url = f"https://github.com/VirusTotal/vt-cli/releases/download/1.3.1/{filename}"
    
    if progress_callback:
        progress_callback("Connecting to GitHub...", 0.1)
        
    try:
        # Create a request
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        
        # Download file
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
            progress_callback("Extracting vt.exe...", 0.85)
            
        # Extract vt.exe from ZIP in memory
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            vt_name = None
            for name in z.namelist():
                if name.endswith("vt.exe") or name == "vt.exe":
                    vt_name = name
                    break
            if not vt_name:
                raise ValueError("vt.exe not found inside the ZIP archive.")
            exe_data = z.read(vt_name)
            
        if progress_callback:
            progress_callback("Verifying binary hash...", 0.9)
            
        # Verify hash of the extracted binary against known official hashes
        exe_hash = hashlib.sha256(exe_data).hexdigest()
        if exe_hash not in KNOWN_HASHES:
            raise ValueError(f"Extracted binary hash is not recognized as an official release: {exe_hash}")
            
        if progress_callback:
            progress_callback("Installing...", 0.95)
            
        # Write to destination
        temp_bin = get_temp_bin_path()
        with open(temp_bin, "wb") as f:
            f.write(exe_data)
            
        if progress_callback:
            progress_callback("Done!", 1.0)
            
        return True
    except Exception as e:
        raise e

