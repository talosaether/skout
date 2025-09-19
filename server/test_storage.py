import pytest
import tempfile
import shutil
from pathlib import Path
from storage import get_file_hash, get_storage_path, save_file, load_file, delete_file, file_exists

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_get_file_hash():
    """Test file hash generation."""
    data1 = b"Hello, World!"
    data2 = b"Hello, World!"
    data3 = b"Different content"

    hash1 = get_file_hash(data1)
    hash2 = get_file_hash(data2)
    hash3 = get_file_hash(data3)

    # Same content should produce same hash
    assert hash1 == hash2
    # Different content should produce different hash
    assert hash1 != hash3
    # Hash should be 64 chars (SHA-256 hex)
    assert len(hash1) == 64

def test_get_storage_path():
    """Test storage path generation."""
    file_hash = "abcd1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab"
    base_dir = "/test/data"

    path = get_storage_path(file_hash, base_dir)
    expected = Path("/test/data/ab/cd/abcd1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab")

    assert path == expected

def test_save_and_load_file(temp_dir):
    """Test saving and loading files."""
    test_data = b"This is test file content"

    # Save file
    file_hash = save_file(test_data, temp_dir)

    # Verify hash is correct
    expected_hash = get_file_hash(test_data)
    assert file_hash == expected_hash

    # Load file and verify content
    loaded_data = load_file(file_hash, temp_dir)
    assert loaded_data == test_data

def test_file_deduplication(temp_dir):
    """Test that identical files are deduplicated."""
    test_data = b"Duplicate content test"

    # Save the same data twice
    hash1 = save_file(test_data, temp_dir)
    hash2 = save_file(test_data, temp_dir)

    # Should get same hash
    assert hash1 == hash2

    # File should exist only once
    file_path = get_storage_path(hash1, temp_dir)
    assert file_path.exists()

def test_file_exists(temp_dir):
    """Test file existence check."""
    test_data = b"Existence test"

    # File shouldn't exist initially
    file_hash = get_file_hash(test_data)
    assert not file_exists(file_hash, temp_dir)

    # Save file
    save_file(test_data, temp_dir)

    # File should exist now
    assert file_exists(file_hash, temp_dir)

def test_delete_file(temp_dir):
    """Test file deletion."""
    test_data = b"Delete test"

    # Save file
    file_hash = save_file(test_data, temp_dir)
    assert file_exists(file_hash, temp_dir)

    # Delete file
    result = delete_file(file_hash, temp_dir)
    assert result is True
    assert not file_exists(file_hash, temp_dir)

    # Try to delete non-existent file
    result = delete_file(file_hash, temp_dir)
    assert result is False

def test_load_nonexistent_file(temp_dir):
    """Test loading a file that doesn't exist."""
    fake_hash = "0123456789abcdef" * 4  # 64 char hash

    with pytest.raises(FileNotFoundError):
        load_file(fake_hash, temp_dir)

def test_directory_structure(temp_dir):
    """Test that the directory structure is created correctly."""
    test_data = b"Directory structure test"
    file_hash = save_file(test_data, temp_dir)

    # Check directory structure
    expected_path = get_storage_path(file_hash, temp_dir)
    assert expected_path.exists()
    assert expected_path.parent.exists()  # Second level dir
    assert expected_path.parent.parent.exists()  # First level dir
    assert expected_path.parent.parent.parent == Path(temp_dir)

def test_directory_cleanup_on_delete(temp_dir):
    """Test that empty directories are cleaned up when deleting files."""
    test_data = b"Cleanup test"
    file_hash = save_file(test_data, temp_dir)
    file_path = get_storage_path(file_hash, temp_dir)

    # Verify directories exist
    second_level_dir = file_path.parent
    first_level_dir = second_level_dir.parent

    assert second_level_dir.exists()
    assert first_level_dir.exists()

    # Delete file
    delete_file(file_hash, temp_dir)

    # Directories should be cleaned up if empty
    assert not second_level_dir.exists()
    assert not first_level_dir.exists()