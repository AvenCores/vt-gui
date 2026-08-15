import hashlib


def compute_sha256(file_path: str) -> str:
    """Computes the SHA-256 hash of a local file in 64KB blocks."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return None
