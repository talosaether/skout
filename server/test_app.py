import pytest
import tempfile
import shutil
import json
import io
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# Set test JWT secret before importing
os.environ['JWT_SECRET'] = 'test-secret-key-for-integration-tests'

# Mock the database connection before importing app
with patch('db.get_conn'), patch('app.ensure_schema'):
    from app import app
from storage import save_file, get_file_hash
from auth import generate_jwt_token, hash_password

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

@pytest.fixture
def test_user():
    """Create a test user and return user_id and auth token."""
    user_id = "test-user-id-123"
    token = generate_jwt_token(user_id)
    return {"id": user_id, "token": token}

def get_auth_headers(token):
    """Helper to create auth headers."""
    return {"Authorization": f"Bearer {token}"}

def test_health_endpoint(client):
    """Test the health endpoint (no auth required)."""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json == {"ok": True}

# Authentication Endpoint Tests
@patch('app.hash_password')
def test_register_success(mock_hash, client, mock_db):
    """Test successful user registration."""
    mock_hash.return_value = "hashed_password"
    mock_db.fetchone.side_effect = [
        None,  # Email doesn't exist
        ("new-user-id", datetime(2023, 1, 1))  # User creation
    ]

    response = client.post('/api/auth/register',
                          json={"email": "test@example.com", "password": "ValidPass123"})

    assert response.status_code == 201
    data = response.json
    assert "token" in data
    assert data["user"]["email"] == "test@example.com"

def test_register_duplicate_email(client, mock_db):
    """Test registration with duplicate email."""
    mock_db.fetchone.return_value = ("existing-id",)  # Email exists

    response = client.post('/api/auth/register',
                          json={"email": "existing@example.com", "password": "ValidPass123"})

    assert response.status_code == 409

def test_register_invalid_email(client):
    """Test registration with invalid email."""
    response = client.post('/api/auth/register',
                          json={"email": "invalid-email", "password": "ValidPass123"})
    assert response.status_code == 400

def test_register_weak_password(client):
    """Test registration with weak password."""
    response = client.post('/api/auth/register',
                          json={"email": "test@example.com", "password": "weak"})
    assert response.status_code == 400

@patch('app.verify_password')
def test_login_success(mock_verify, client, mock_db):
    """Test successful login."""
    mock_verify.return_value = True
    mock_db.fetchone.return_value = (
        "user-id-123",
        "test@example.com",
        "hashed_password",
        datetime(2023, 1, 1)
    )

    response = client.post('/api/auth/login',
                          json={"email": "test@example.com", "password": "Password123"})

    assert response.status_code == 200
    data = response.json
    assert "token" in data
    assert data["user"]["id"] == "user-id-123"

def test_login_invalid_email(client, mock_db):
    """Test login with non-existent email."""
    mock_db.fetchone.return_value = None

    response = client.post('/api/auth/login',
                          json={"email": "nonexistent@example.com", "password": "Password123"})

    assert response.status_code == 401

@patch('app.verify_password')
def test_login_wrong_password(mock_verify, client, mock_db):
    """Test login with wrong password."""
    mock_verify.return_value = False
    mock_db.fetchone.return_value = ("user-id", "test@example.com", "hashed_password", datetime(2023, 1, 1))

    response = client.post('/api/auth/login',
                          json={"email": "test@example.com", "password": "WrongPassword"})

    assert response.status_code == 401

def test_get_current_user_success(client, mock_db, test_user):
    """Test getting current user info."""
    mock_db.fetchone.return_value = (test_user["id"], "test@example.com", datetime(2023, 1, 1))

    response = client.get('/api/auth/me', headers=get_auth_headers(test_user["token"]))

    assert response.status_code == 200
    data = response.json
    assert data["id"] == test_user["id"]
    assert data["email"] == "test@example.com"

def test_get_current_user_no_token(client):
    """Test getting current user without token."""
    response = client.get('/api/auth/me')
    assert response.status_code == 401

def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token."""
    response = client.get('/api/auth/me', headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401

# Asset Endpoint Tests (require authentication)
@patch('app.save_file')
def test_create_asset_success(mock_save_file, client, mock_db, test_user):
    """Test successful asset creation with authentication."""
    # Setup mocks
    test_data = b"fake image data"
    test_hash = "abcd1234"
    mock_save_file.return_value = test_hash
    mock_db.fetchone.return_value = ("test-id", datetime(2023, 1, 1))

    # Create test file
    data = {
        'file': (io.BytesIO(test_data), 'test.jpg', 'image/jpeg')
    }

    response = client.post('/api/assets', data=data, headers=get_auth_headers(test_user["token"]))

    assert response.status_code == 201
    assert "id" in response.json
    assert "created_at" in response.json

    # Verify save_file was called with correct data
    mock_save_file.assert_called_once_with(test_data)

def test_create_asset_no_auth(client):
    """Test asset creation without authentication."""
    data = {
        'file': (io.BytesIO(b"test data"), 'test.jpg', 'image/jpeg')
    }
    response = client.post('/api/assets', data=data)
    assert response.status_code == 401

def test_create_asset_missing_file(client, test_user):
    """Test asset creation without file."""
    response = client.post('/api/assets', headers=get_auth_headers(test_user["token"]))
    assert response.status_code == 400

def test_create_asset_wrong_mimetype(client, test_user):
    """Test asset creation with non-image file."""
    data = {
        'file': (io.BytesIO(b"text content"), 'test.txt', 'text/plain')
    }
    response = client.post('/api/assets', data=data, headers=get_auth_headers(test_user["token"]))
    assert response.status_code == 415

def test_create_asset_too_large(client, test_user):
    """Test asset creation with file too large."""
    large_data = b"x" * (8 * 1024 * 1024)  # 8MB > 7MB limit
    data = {
        'file': (io.BytesIO(large_data), 'large.jpg', 'image/jpeg')
    }
    response = client.post('/api/assets', data=data, headers=get_auth_headers(test_user["token"]))
    assert response.status_code == 413

@patch('app.load_file')
def test_get_asset_success(mock_load_file, client, mock_db, test_user):
    """Test successful asset retrieval with authentication."""
    test_data = b"fake image data"
    test_hash = "abcd1234"

    mock_db.fetchone.return_value = ("test.jpg", "image/jpeg", test_hash)
    mock_load_file.return_value = test_data

    response = client.get('/api/assets/test-uuid-123', headers=get_auth_headers(test_user["token"]))

    assert response.status_code == 200
    assert response.data == test_data
    assert response.headers['Content-Type'] == 'image/jpeg'

    mock_load_file.assert_called_once_with(test_hash)

def test_get_asset_no_auth(client):
    """Test asset retrieval without authentication."""
    response = client.get('/api/assets/test-uuid-123')
    assert response.status_code == 401

def test_get_asset_not_found_in_db(client, mock_db, test_user):
    """Test asset retrieval when asset not in database or not owned by user."""
    mock_db.fetchone.return_value = None

    response = client.get('/api/assets/550e8400-e29b-41d4-a716-446655440000',
                         headers=get_auth_headers(test_user["token"]))
    assert response.status_code == 404

@patch('app.load_file')
def test_get_asset_file_not_found_on_disk(mock_load_file, client, mock_db, test_user):
    """Test asset retrieval when file not found on disk."""
    mock_db.fetchone.return_value = ("test.jpg", "image/jpeg", "abcd1234")
    mock_load_file.side_effect = FileNotFoundError()

    response = client.get('/api/assets/550e8400-e29b-41d4-a716-446655440000',
                         headers=get_auth_headers(test_user["token"]))
    assert response.status_code == 404

@patch('app.delete_file')
def test_delete_asset_success_with_file_deletion(mock_delete_file, client, mock_db, test_user):
    """Test successful asset deletion when file should be deleted."""
    # Setup mock responses for database queries
    mock_db.fetchone.side_effect = [
        ("abcd1234",),  # file_hash query
        (0,)  # ref_count query (no other references)
    ]

    response = client.delete('/api/assets/550e8400-e29b-41d4-a716-446655440000',
                            headers=get_auth_headers(test_user["token"]))

    assert response.status_code == 200
    assert "deleted" in response.json

    # Verify file deletion was called
    mock_delete_file.assert_called_once_with("abcd1234")

def test_delete_asset_no_auth(client):
    """Test asset deletion without authentication."""
    response = client.delete('/api/assets/550e8400-e29b-41d4-a716-446655440000')
    assert response.status_code == 401

@patch('app.delete_file')
def test_delete_asset_success_without_file_deletion(mock_delete_file, client, mock_db, test_user):
    """Test successful asset deletion when file should NOT be deleted (other references exist)."""
    # Setup mock responses
    mock_db.fetchone.side_effect = [
        ("abcd1234",),  # file_hash query
        (1,)  # ref_count query (other references exist)
    ]

    response = client.delete('/api/assets/550e8400-e29b-41d4-a716-446655440000',
                            headers=get_auth_headers(test_user["token"]))

    assert response.status_code == 200
    assert "deleted" in response.json

    # Verify file deletion was NOT called
    mock_delete_file.assert_not_called()

def test_delete_asset_not_found(client, mock_db, test_user):
    """Test asset deletion when asset not found or not owned by user."""
    mock_db.fetchone.return_value = None

    response = client.delete('/api/assets/550e8400-e29b-41d4-a716-446655440000',
                            headers=get_auth_headers(test_user["token"]))
    assert response.status_code == 404

def test_list_assets_success(client, mock_db, test_user):
    """Test successful asset listing (only shows user's assets)."""
    # Setup mock responses
    mock_db.fetchone.return_value = (2,)  # total count
    mock_db.fetchall.return_value = [
        ("id1", datetime(2023, 1, 1), "file1.jpg", "image/jpeg", 1024),
        ("id2", datetime(2023, 1, 2), "file2.png", "image/png", 2048)
    ]

    response = client.get('/api/assets', headers=get_auth_headers(test_user["token"]))

    assert response.status_code == 200
    data = response.json
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == "id1"
    assert data["items"][0]["filename"] == "file1.jpg"

def test_list_assets_no_auth(client):
    """Test asset listing without authentication."""
    response = client.get('/api/assets')
    assert response.status_code == 401