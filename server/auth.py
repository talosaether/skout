import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, g, abort

# JWT configuration from environment
JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable must be set")

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt with work factor 12.
    Returns bcrypt hash string.
    """
    salt = bcrypt.gensalt(rounds=12)
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify password against bcrypt hash.
    Uses constant-time comparison to prevent timing attacks.
    """
    password_bytes = password.encode('utf-8')
    hash_bytes = password_hash.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hash_bytes)

def generate_jwt_token(user_id: str, expiry_hours: int = None) -> str:
    """
    Generate JWT token for user.

    Args:
        user_id: UUID of the user
        expiry_hours: Token expiry in hours (defaults to JWT_EXPIRY_HOURS)

    Returns:
        JWT token string
    """
    if expiry_hours is None:
        expiry_hours = JWT_EXPIRY_HOURS

    now = datetime.now(timezone.utc)
    expiry = now + timedelta(hours=expiry_hours)

    payload = {
        'user_id': user_id,
        'iat': now,
        'exp': expiry
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return token

def verify_jwt_token(token: str) -> dict | None:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dict on success, None on failure
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

def require_auth(f):
    """
    Decorator for routes that require authentication.
    Extracts and validates JWT token from Authorization header.
    Attaches user_id to g.user_id on success.
    Returns 401 if authentication fails.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({'error': 'Missing authorization header'}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': 'Invalid authorization header format. Expected: Bearer <token>'}), 401

        token = parts[1]
        payload = verify_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Attach user_id to request context
        g.user_id = payload.get('user_id')

        return f(*args, **kwargs)

    return decorated_function

def validate_email(email: str) -> bool:
    """
    Validate email format.
    Basic validation - more comprehensive validation in database constraint.
    """
    if not email or '@' not in email:
        return False
    if len(email) < 3 or len(email) > 254:
        return False
    return True

def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)

    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain at least one uppercase letter, one lowercase letter, and one digit"

    return True, ""
