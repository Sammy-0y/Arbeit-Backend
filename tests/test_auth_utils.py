import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from server import hash_password, verify_password, create_access_token, decode_token
from fastapi import HTTPException
import jwt
from datetime import datetime, timezone, timedelta
import os

JWT_SECRET = os.environ.get('JWT_SECRET', 'arbeit-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'

class TestPasswordHashing:
    """Unit tests for password hashing utilities"""
    
    def test_hash_password_creates_hash(self):
        """Test that hash_password creates a valid bcrypt hash"""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password  # Hash should be different from password
    
    def test_hash_password_different_each_time(self):
        """Test that hashing the same password produces different hashes (salt)"""
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2  # Different salts
    
    def test_verify_password_correct(self):
        """Test that verify_password returns True for correct password"""
        password = "correct_password"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test that verify_password returns False for incorrect password"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty(self):
        """Test that verify_password handles empty passwords"""
        password = "test"
        hashed = hash_password(password)
        
        assert verify_password("", hashed) is False


class TestJWTTokens:
    """Unit tests for JWT token utilities"""
    
    def test_create_access_token(self):
        """Test that create_access_token generates a valid JWT"""
        data = {
            "email": "test@test.com",
            "role": "admin"
        }
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_token_valid(self):
        """Test that decode_token successfully decodes a valid token"""
        data = {
            "email": "test@test.com",
            "role": "recruiter",
            "client_id": None
        }
        token = create_access_token(data)
        decoded = decode_token(token)
        
        assert decoded["email"] == data["email"]
        assert decoded["role"] == data["role"]
        assert "exp" in decoded  # Expiration should be added
    
    def test_decode_token_with_client_id(self):
        """Test token includes client_id for client users"""
        data = {
            "email": "client@test.com",
            "role": "client_user",
            "client_id": "client_123"
        }
        token = create_access_token(data)
        decoded = decode_token(token)
        
        assert decoded["client_id"] == "client_123"
    
    def test_decode_token_expired(self):
        """Test that decode_token raises exception for expired token"""
        data = {"email": "test@test.com", "role": "admin"}
        
        # Create expired token
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) - timedelta(hours=1)  # Expired 1 hour ago
        to_encode.update({"exp": expire})
        expired_token = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token(expired_token)
        
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()
    
    def test_decode_token_invalid(self):
        """Test that decode_token raises exception for invalid token"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token(invalid_token)
        
        assert exc_info.value.status_code == 401
        assert "invalid" in exc_info.value.detail.lower()
    
    def test_decode_token_wrong_secret(self):
        """Test that token signed with wrong secret is rejected"""
        data = {"email": "test@test.com", "role": "admin"}
        
        # Create token with wrong secret
        wrong_secret_token = jwt.encode(data, "wrong_secret", algorithm=JWT_ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token(wrong_secret_token)
        
        assert exc_info.value.status_code == 401