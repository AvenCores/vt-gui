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
