import pytest
import pytest_asyncio
import sys
from pathlib import Path
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from server import app, hash_password

@pytest_asyncio.fixture
async def test_app(test_db):
    """Override app database with test database"""
    import server
    original_db = server.db
    server.db = test_db
    yield app
    server.db = original_db

@pytest_asyncio.fixture
async def client(test_app):
    """HTTP client for testing"""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def users_with_tokens(client, seed_test_client):
    """Create users of all roles and return their tokens"""
    users = [
        {"email": "admin@test.com", "password": "pass", "role": "admin", "client_id": None},
        {"email": "recruiter@test.com", "password": "pass", "role": "recruiter", "client_id": None},
        {"email": "client@test.com", "password": "pass", "role": "client_user", "client_id": "test_client_001"},
    ]
    
    tokens = {}
    
    for user in users:
        # Create user
        user_doc = {
            "email": user["email"],
            "name": f"Test {user['role']}",
            "role": user["role"],
            "client_id": user["client_id"],
            "password_hash": hash_password(user["password"]),
            "created_at": "2025-01-01T00:00:00"
        }
        await seed_test_client.users.insert_one(user_doc)
        
        # Get token
        response = await client.post("/api/auth/login", json={
            "email": user["email"],
            "password": user["password"]
        })
        tokens[user["role"]] = response.json()["access_token"]
    
    return tokens


class TestRoleBasedAccess:
    """Tests for role-based access control"""
    
    @pytest.mark.asyncio
    async def test_admin_token_contains_correct_role(self, client, users_with_tokens):
        """Test that admin token contains correct role information"""
        token = users_with_tokens["admin"]
        
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
        assert data["client_id"] is None
    
    @pytest.mark.asyncio
    async def test_recruiter_token_contains_correct_role(self, client, users_with_tokens):
        """Test that recruiter token contains correct role information"""
        token = users_with_tokens["recruiter"]
        
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "recruiter"
        assert data["client_id"] is None
    
    @pytest.mark.asyncio
    async def test_client_user_token_contains_correct_role_and_client_id(self, client, users_with_tokens):
        """Test that client user token contains role and client_id"""
        token = users_with_tokens["client_user"]
        
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "client_user"
        assert data["client_id"] == "test_client_001"
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_requires_authentication(self, client, clean_db):
        """Test that protected endpoints reject requests without token"""
        response = await client.get("/api/auth/me")
        assert response.status_code == 403  # Forbidden (no credentials)
    
    @pytest.mark.asyncio
    async def test_all_roles_can_access_own_profile(self, client, users_with_tokens):
        """Test that all roles can access their own profile via /api/auth/me"""
        for role, token in users_with_tokens.items():
            response = await client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            assert response.json()["role"] == role


class TestMultiTenantFoundation:
    """Tests for multi-tenant isolation foundation"""
    
    @pytest.mark.asyncio
    async def test_client_user_has_client_id_in_token(self, client, seed_test_client):
        """Test that client_user JWT token includes client_id"""
        # Create client user
        user_doc = {
            "email": "tenant@test.com",
            "name": "Tenant User",
            "role": "client_user",
            "client_id": "test_client_001",
            "password_hash": hash_password("pass123"),
            "created_at": "2025-01-01T00:00:00"
        }
        await seed_test_client.users.insert_one(user_doc)
        
        # Login and get token
        login_response = await client.post("/api/auth/login", json={
            "email": "tenant@test.com",
            "password": "pass123"
        })
        
        assert login_response.status_code == 200
        token_data = login_response.json()
        assert token_data["user"]["client_id"] == "test_client_001"
        
        # Verify token content via /me endpoint
        me_response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        
        assert me_response.status_code == 200
        assert me_response.json()["client_id"] == "test_client_001"
    
    @pytest.mark.asyncio
    async def test_admin_and_recruiter_have_no_client_id(self, client, clean_db):
        """Test that admin and recruiter users don't have client_id"""
        for role in ["admin", "recruiter"]:
            # Create user
            user_doc = {
                "email": f"{role}@test.com",
                "name": f"Test {role}",
                "role": role,
                "client_id": None,
                "password_hash": hash_password("pass123"),
                "created_at": "2025-01-01T00:00:00"
            }
            await clean_db.users.insert_one(user_doc)
            
            # Login
            response = await client.post("/api/auth/login", json={
                "email": f"{role}@test.com",
                "password": "pass123"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["user"]["client_id"] is None
    
    @pytest.mark.asyncio
    async def test_different_clients_have_different_client_ids(self, client, clean_db):
        """Test that users from different clients have different client_ids"""
        # Create two clients
        await clean_db.clients.insert_one({
            "client_id": "client_A",
            "company_name": "Company A",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        await clean_db.clients.insert_one({
            "client_id": "client_B",
            "company_name": "Company B",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        
        # Create users for each client
        test_users = [
            {"email": "userA@test.com", "client_id": "client_A"},
            {"email": "userB@test.com", "client_id": "client_B"}
        ]
        
        for user_info in test_users:
            user_doc = {
                "email": user_info["email"],
                "name": f"User {user_info['client_id']}",
                "role": "client_user",
                "client_id": user_info["client_id"],
                "password_hash": hash_password("pass123"),
                "created_at": "2025-01-01T00:00:00"
            }
            await clean_db.users.insert_one(user_doc)
            
            # Login and verify client_id
            response = await client.post("/api/auth/login", json={
                "email": user_info["email"],
                "password": "pass123"
            })
            
            assert response.status_code == 200
            assert response.json()["user"]["client_id"] == user_info["client_id"]
    
    # TODO: Phase 3+ - Add tests for actual data isolation in queries
    # When jobs and candidates are implemented, test that:
    # - client_user can only query their own client's data
    # - client_user cannot access other clients' data even with direct API calls
    # - admin/recruiter can access all data
    @pytest.mark.asyncio
    async def test_tenant_isolation_placeholder(self):
        """Placeholder for future tenant isolation tests with actual data"""
        # TODO: Implement in Phase 3 when jobs/candidates exist
        # Test scenarios:
        # 1. Client A user tries to access Client B's job (should fail)
        # 2. Client A user lists jobs (should only see Client A jobs)
        # 3. Admin/recruiter can see all jobs
        pass