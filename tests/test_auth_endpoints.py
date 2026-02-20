import pytest
import pytest_asyncio
import sys
from pathlib import Path
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from server import app, db as server_db, hash_password
import os

# Override database for testing
from motor.motor_asyncio import AsyncIOMotorClient

@pytest_asyncio.fixture
async def test_app(test_db):
    """Override app database with test database"""
    # Replace the db in server module
    import server
    original_db = server.db
    server.db = test_db
    
    yield app
    
    # Restore original db
    server.db = original_db

@pytest_asyncio.fixture
async def client(test_app):
    """HTTP client for testing"""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestAuthRegister:
    """Integration tests for /api/auth/register endpoint"""
    
    @pytest.mark.asyncio
    async def test_register_admin_success(self, client, clean_db):
        """Test successful admin registration"""
        response = await client.post("/api/auth/register", json={
            "email": "new_admin@test.com",
            "password": "admin123",
            "name": "New Admin",
            "role": "admin",
            "client_id": None
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "new_admin@test.com"
        assert data["name"] == "New Admin"
        assert data["role"] == "admin"
        assert "password" not in data  # Password should not be returned
    
    @pytest.mark.asyncio
    async def test_register_recruiter_success(self, client, clean_db):
        """Test successful recruiter registration"""
        response = await client.post("/api/auth/register", json={
            "email": "new_recruiter@test.com",
            "password": "rec123",
            "name": "New Recruiter",
            "role": "recruiter",
            "client_id": None
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "recruiter"
    
    @pytest.mark.asyncio
    async def test_register_client_user_success(self, client, seed_test_client):
        """Test successful client user registration"""
        response = await client.post("/api/auth/register", json={
            "email": "new_client@test.com",
            "password": "client123",
            "name": "New Client",
            "role": "client_user",
            "client_id": "test_client_001"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "client_user"
        assert data["client_id"] == "test_client_001"
    
    @pytest.mark.asyncio
    async def test_register_client_user_missing_client_id(self, client, clean_db):
        """Test client user registration fails without client_id"""
        response = await client.post("/api/auth/register", json={
            "email": "client@test.com",
            "password": "pass123",
            "name": "Client",
            "role": "client_user",
            "client_id": None
        })
        
        assert response.status_code == 400
        assert "client_id is required" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_client_user_invalid_client_id(self, client, clean_db):
        """Test client user registration fails with non-existent client_id"""
        response = await client.post("/api/auth/register", json={
            "email": "client@test.com",
            "password": "pass123",
            "name": "Client",
            "role": "client_user",
            "client_id": "non_existent_client"
        })
        
        assert response.status_code == 400
        assert "Invalid client_id" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, clean_db):
        """Test registration fails with duplicate email"""
        user_data = {
            "email": "duplicate@test.com",
            "password": "pass123",
            "name": "User",
            "role": "admin"
        }
        
        # First registration
        response1 = await client.post("/api/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Second registration with same email
        response2 = await client.post("/api/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"].lower()


class TestAuthLogin:
    """Integration tests for /api/auth/login endpoint"""
    
    async def create_test_user(self, db, email, password, role, client_id=None):
        """Helper to create a test user"""
        user_doc = {
            "email": email,
            "name": "Test User",
            "role": role,
            "client_id": client_id,
            "password_hash": hash_password(password),
            "created_at": "2025-01-01T00:00:00"
        }
        await db.users.insert_one(user_doc)
    
    @pytest.mark.asyncio
    async def test_login_success_admin(self, client, clean_db):
        """Test successful login with admin credentials"""
        await self.create_test_user(clean_db, "admin@test.com", "admin123", "admin")
        
        response = await client.post("/api/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "admin@test.com"
        assert data["user"]["role"] == "admin"
    
    @pytest.mark.asyncio
    async def test_login_success_client_user(self, client, seed_test_client):
        """Test successful login with client user credentials"""
        await self.create_test_user(
            seed_test_client,
            "client@test.com",
            "client123",
            "client_user",
            "test_client_001"
        )
        
        response = await client.post("/api/auth/login", json={
            "email": "client@test.com",
            "password": "client123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["client_id"] == "test_client_001"
    
    @pytest.mark.asyncio
    async def test_login_failure_wrong_password(self, client, clean_db):
        """Test login failure with incorrect password"""
        await self.create_test_user(clean_db, "user@test.com", "correct_pass", "admin")
        
        response = await client.post("/api/auth/login", json={
            "email": "user@test.com",
            "password": "wrong_pass"
        })
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_failure_unregistered_email(self, client, clean_db):
        """Test login failure with unregistered email"""
        response = await client.post("/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "any_password"
        })
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_invalid_email_format(self, client, clean_db):
        """Test login with invalid email format"""
        response = await client.post("/api/auth/login", json={
            "email": "not-an-email",
            "password": "password123"
        })
        
        assert response.status_code == 422  # Validation error


class TestAuthMe:
    """Integration tests for /api/auth/me endpoint"""
    
    async def get_auth_token(self, client, db, email, password, role, client_id=None):
        """Helper to create user and get auth token"""
        user_doc = {
            "email": email,
            "name": "Test User",
            "role": role,
            "client_id": client_id,
            "password_hash": hash_password(password),
            "created_at": "2025-01-01T00:00:00"
        }
        await db.users.insert_one(user_doc)
        
        response = await client.post("/api/auth/login", json={
            "email": email,
            "password": password
        })
        return response.json()["access_token"]
    
    @pytest.mark.asyncio
    async def test_auth_me_success(self, client, clean_db):
        """Test /api/auth/me returns current user with valid token"""
        token = await self.get_auth_token(
            client, clean_db, "test@test.com", "pass123", "admin"
        )
        
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@test.com"
        assert data["role"] == "admin"
    
    @pytest.mark.asyncio
    async def test_auth_me_no_token(self, client, clean_db):
        """Test /api/auth/me fails without token"""
        response = await client.get("/api/auth/me")
        
        assert response.status_code == 403  # No credentials provided
    
    @pytest.mark.asyncio
    async def test_auth_me_invalid_token(self, client, clean_db):
        """Test /api/auth/me fails with invalid token"""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_auth_me_client_user_has_client_id(self, client, seed_test_client):
        """Test /api/auth/me returns client_id for client users"""
        token = await self.get_auth_token(
            client, seed_test_client, "client@test.com", "pass123",
            "client_user", "test_client_001"
        )
        
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["client_id"] == "test_client_001"