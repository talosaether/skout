import pytest
import os
from auth import (
    hash_password,
    verify_password,
    generate_jwt_token,
    verify_jwt_token,
    validate_email,
    validate_password
)

# Set test JWT secret
os.environ['JWT_SECRET'] = 'test-secret-key-for-unit-tests-only'

class TestPasswordHashing:
    def test_hash_password_generates_different_hashes(self):
        """Test that same password generates different hashes (salt is random)"""
        password = "TestPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_verify_password_succeeds_with_correct_password(self):
        """Test password verification succeeds with correct password"""
        password = "CorrectPassword123"
        password_hash = hash_password(password)
        assert verify_password(password, password_hash) is True

    def test_verify_password_fails_with_incorrect_password(self):
        """Test password verification fails with incorrect password"""
        password = "CorrectPassword123"
        wrong_password = "WrongPassword123"
        password_hash = hash_password(password)
        assert verify_password(wrong_password, password_hash) is False

    def test_hash_contains_bcrypt_prefix(self):
        """Test that hash uses bcrypt format"""
        password = "TestPassword123"
        password_hash = hash_password(password)
        assert password_hash.startswith('$2b$')


class TestJWTTokens:
    def test_generate_token_returns_string(self):
        """Test token generation returns a string"""
        token = generate_jwt_token('test-user-id-123')
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token_succeeds(self):
        """Test valid token verification succeeds"""
        user_id = 'test-user-id-456'
        token = generate_jwt_token(user_id)
        payload = verify_jwt_token(token)

        assert payload is not None
        assert payload['user_id'] == user_id
        assert 'iat' in payload
        assert 'exp' in payload

    def test_verify_invalid_token_fails(self):
        """Test invalid token verification fails"""
        invalid_token = 'invalid.token.string'
        payload = verify_jwt_token(invalid_token)
        assert payload is None

    def test_verify_tampered_token_fails(self):
        """Test tampered token verification fails"""
        token = generate_jwt_token('test-user-id')
        # Tamper with token by changing a character
        tampered_token = token[:-5] + 'XXXXX'
        payload = verify_jwt_token(tampered_token)
        assert payload is None

    def test_token_contains_user_id(self):
        """Test token payload contains correct user_id"""
        user_id = 'specific-test-user-id'
        token = generate_jwt_token(user_id)
        payload = verify_jwt_token(token)
        assert payload['user_id'] == user_id

    def test_custom_expiry_hours(self):
        """Test token generation with custom expiry"""
        token = generate_jwt_token('test-user', expiry_hours=1)
        payload = verify_jwt_token(token)

        assert payload is not None
        # Verify expiry is set (would need more complex test to verify exact time)
        assert 'exp' in payload
        assert payload['exp'] > payload['iat']


class TestValidation:
    def test_validate_email_accepts_valid_emails(self):
        """Test email validation accepts valid email addresses"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            'first.last@sub.domain.com'
        ]
        for email in valid_emails:
            assert validate_email(email) is True, f"Should accept {email}"

    def test_validate_email_rejects_invalid_emails(self):
        """Test email validation rejects invalid email addresses"""
        invalid_emails = [
            'notanemail',
            '@example.com',
            'user@',
            'user @example.com',
            '',
            'a' * 255 + '@example.com',  # Too long
        ]
        for email in invalid_emails:
            assert validate_email(email) is False, f"Should reject {email}"

    def test_validate_password_accepts_strong_passwords(self):
        """Test password validation accepts strong passwords"""
        strong_passwords = [
            'Password123',
            'MySecure1Pass',
            'Welcome2023',
            'Test1234Test'
        ]
        for password in strong_passwords:
            is_valid, error_msg = validate_password(password)
            assert is_valid is True, f"Should accept {password}: {error_msg}"
            assert error_msg == ""

    def test_validate_password_rejects_short_passwords(self):
        """Test password validation rejects passwords under 8 characters"""
        is_valid, error_msg = validate_password('Short1')
        assert is_valid is False
        assert 'at least 8 characters' in error_msg

    def test_validate_password_rejects_no_uppercase(self):
        """Test password validation rejects passwords without uppercase"""
        is_valid, error_msg = validate_password('password123')
        assert is_valid is False
        assert 'uppercase' in error_msg.lower()

    def test_validate_password_rejects_no_lowercase(self):
        """Test password validation rejects passwords without lowercase"""
        is_valid, error_msg = validate_password('PASSWORD123')
        assert is_valid is False
        assert 'lowercase' in error_msg.lower()

    def test_validate_password_rejects_no_digit(self):
        """Test password validation rejects passwords without digit"""
        is_valid, error_msg = validate_password('PasswordOnly')
        assert is_valid is False
        assert 'digit' in error_msg.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
