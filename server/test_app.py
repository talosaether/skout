import pytest
import tempfile
import shutil
import json
import io
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock the database connection before importing app
with patch('db.get_conn'), patch('app.ensure_schema'):
    from app import app
from storage import save_file, get_file_hash

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_db():
    """Mock database operations."""
    with patch('app.get_conn') as mock_get_conn, \
         patch('app.tx') as mock_tx:

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_tx.return_value.__enter__.return_value = mock_cur

        yield mock_cur

def test_health_endpoint(client):
    """Test the health endpoint."""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json == {"ok": True}

@patch('app.save_file')
def test_create_asset_success(mock_save_file, client, mock_db):
    """Test successful asset creation."""
    # Setup mocks
    test_data = b"fake image data"
    test_hash = "abcd1234"
    mock_save_file.return_value = test_hash
    mock_db.fetchone.return_value = ("test-id", datetime(2023, 1, 1))

    # Create test file
    data = {
        'file': (io.BytesIO(test_data), 'test.jpg', 'image/jpeg')
    }

    response = client.post('/api/assets', data=data)

    assert response.status_code == 201
    assert response.json == {
        "id": "test-id",
        "created_at": "2023-01-01T00:00:00"
    }

    # Verify save_file was called with correct data
    mock_save_file.assert_called_once_with(test_data)

def test_create_asset_missing_file(client):
    """Test asset creation without file."""
    response = client.post('/api/assets')
    assert response.status_code == 400

def test_create_asset_wrong_mimetype(client):
    """Test asset creation with non-image file."""
    data = {
        'file': (io.BytesIO(b"text content"), 'test.txt', 'text/plain')
    }
    response = client.post('/api/assets', data=data)
    assert response.status_code == 415

def test_create_asset_too_large(client):
    """Test asset creation with file too large."""
    large_data = b"x" * (8 * 1024 * 1024)  # 8MB > 7MB limit
    data = {
        'file': (io.BytesIO(large_data), 'large.jpg', 'image/jpeg')
    }
    response = client.post('/api/assets', data=data)
    assert response.status_code == 413

@patch('app.load_file')
def test_get_asset_success(mock_load_file, client, mock_db):
    """Test successful asset retrieval."""
    test_data = b"fake image data"
    test_hash = "abcd1234"

    mock_db.fetchone.return_value = ("test.jpg", "image/jpeg", test_hash)
    mock_load_file.return_value = test_data

    response = client.get('/api/assets/test-id')

    assert response.status_code == 200
    assert response.data == test_data
    assert response.headers['Content-Type'] == 'image/jpeg'

    mock_load_file.assert_called_once_with(test_hash)

def test_get_asset_not_found_in_db(client, mock_db):
    """Test asset retrieval when asset not in database."""
    mock_db.fetchone.return_value = None

    response = client.get('/api/assets/nonexistent-id')
    assert response.status_code == 404

@patch('app.load_file')
def test_get_asset_file_not_found_on_disk(mock_load_file, client, mock_db):
    """Test asset retrieval when file not found on disk."""
    mock_db.fetchone.return_value = ("test.jpg", "image/jpeg", "abcd1234")
    mock_load_file.side_effect = FileNotFoundError()

    response = client.get('/api/assets/test-id')
    assert response.status_code == 404

@patch('app.delete_file')
def test_delete_asset_success_with_file_deletion(mock_delete_file, client, mock_db):
    """Test successful asset deletion when file should be deleted."""
    # Setup mock responses for database queries
    mock_db.fetchone.side_effect = [
        ("abcd1234",),  # file_hash query
        (0,)  # ref_count query (no other references)
    ]

    response = client.delete('/api/assets/test-id')

    assert response.status_code == 200
    assert response.json == {"deleted": "test-id"}

    # Verify file deletion was called
    mock_delete_file.assert_called_once_with("abcd1234")

@patch('app.delete_file')
def test_delete_asset_success_without_file_deletion(mock_delete_file, client, mock_db):
    """Test successful asset deletion when file should NOT be deleted (other references exist)."""
    # Setup mock responses
    mock_db.fetchone.side_effect = [
        ("abcd1234",),  # file_hash query
        (1,)  # ref_count query (other references exist)
    ]

    response = client.delete('/api/assets/test-id')

    assert response.status_code == 200
    assert response.json == {"deleted": "test-id"}

    # Verify file deletion was NOT called
    mock_delete_file.assert_not_called()

def test_delete_asset_not_found(client, mock_db):
    """Test asset deletion when asset not found."""
    mock_db.fetchone.return_value = None

    response = client.delete('/api/assets/nonexistent-id')
    assert response.status_code == 404

def test_list_assets_success(client, mock_db):
    """Test successful asset listing."""
    # Setup mock responses
    mock_db.fetchone.return_value = (2,)  # total count
    mock_db.fetchall.return_value = [
        ("id1", datetime(2023, 1, 1), "file1.jpg", "image/jpeg", 1024),
        ("id2", datetime(2023, 1, 2), "file2.png", "image/png", 2048)
    ]

    response = client.get('/api/assets')

    assert response.status_code == 200
    data = response.json
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == "id1"
    assert data["items"][0]["filename"] == "file1.jpg"