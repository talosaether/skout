import os
import hashlib
from pathlib import Path

def get_file_hash(data: bytes) -> str:
    """Generate SHA-256 hash of file data."""
    return hashlib.sha256(data).hexdigest()

def get_storage_path(file_hash: str, base_dir: str = "/app/data") -> Path:
    """
    Generate storage path using hash-based directory structure.
    Uses first 2 chars for first level, next 2 chars for second level.
    Example: hash abc123... -> /app/data/ab/c1/abc123...
    """
    return Path(base_dir) / file_hash[:2] / file_hash[2:4] / file_hash

def save_file(data: bytes, base_dir: str = "/app/data") -> str:
    """
    Save file data to disk using hash-based storage.
    Returns the file hash.
    """
    file_hash = get_file_hash(data)
    file_path = get_storage_path(file_hash, base_dir)

    # Create directories if they don't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Only write if file doesn't already exist (deduplication)
    if not file_path.exists():
        with open(file_path, 'wb') as f:
            f.write(data)

    return file_hash

def load_file(file_hash: str, base_dir: str = "/app/data") -> bytes:
    """Load file data from disk using hash."""
    file_path = get_storage_path(file_hash, base_dir)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_hash}")

    with open(file_path, 'rb') as f:
        return f.read()

def delete_file(file_hash: str, base_dir: str = "/app/data") -> bool:
    """
    Delete file from disk using hash.
    Returns True if file was deleted, False if it didn't exist.
    """
    file_path = get_storage_path(file_hash, base_dir)

    if file_path.exists():
        file_path.unlink()

        # Clean up empty directories
        try:
            file_path.parent.rmdir()  # Remove second level dir if empty
            file_path.parent.parent.rmdir()  # Remove first level dir if empty
        except OSError:
            pass  # Directory not empty, which is fine

        return True
    return False

def file_exists(file_hash: str, base_dir: str = "/app/data") -> bool:
    """Check if file exists in storage."""
    file_path = get_storage_path(file_hash, base_dir)
    return file_path.exists()