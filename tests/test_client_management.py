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
async def admin_token(client, clean_db):
    """Create admin and get token"""
    user_doc = {
        "email": "admin@test.com",
        "name": "Admin User",
        "role": "admin",
        "client_id": None,
        "password_hash": hash_password("admin123"),
        "created_at": "2025-01-01T00:00:00"
    }
    await clean_db.users.insert_one(user_doc)
    
    response = await client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "admin123"
    })
    return response.json()["access_token"]

@pytest_asyncio.fixture
async def recruiter_token(client, clean_db):
    """Create recruiter and get token"""
    user_doc = {
        "email": "recruiter@test.com",
        "name": "Recruiter User",
        "role": "recruiter",
        "client_id": None,
        "password_hash": hash_password("rec123"),
        "created_at": "2025-01-01T00:00:00"
    }
    await clean_db.users.insert_one(user_doc)
    
    response = await client.post("/api/auth/login", json={
        "email": "recruiter@test.com",
        "password": "rec123"
    })
    return response.json()["access_token"]

@pytest_asyncio.fixture
async def client_user_token(client, seed_test_client):
    """Create client user and get token"""
    user_doc = {
        "email": "clientuser@test.com",
        "name": "Client User",
        "role": "client_user",
        "client_id": "test_client_001",
        "password_hash": hash_password("client123"),
        "created_at": "2025-01-01T00:00:00"
    }
    await seed_test_client.users.insert_one(user_doc)
    
    response = await client.post("/api/auth/login", json={
        "email": "clientuser@test.com",
        "password": "client123"
    })
    return response.json()["access_token"]

@pytest_asyncio.fixture
async def sample_client(clean_db):
    """Create a sample client for testing"""
    client_doc = {
        "client_id": "test_client_sample",
        "company_name": "Sample Company",
        "status": "active",
        "created_at": "2025-01-01T00:00:00",
        "created_by": "admin@test.com"
    }
    await clean_db.clients.insert_one(client_doc)
    return client_doc


class TestClientListEndpoint:
    """Tests for GET /api/clients endpoint"""
    
    @pytest.mark.asyncio
    async def test_list_clients_admin_success(self, client, admin_token, sample_client):
        """Test admin can list clients"""
        response = await client.get(
            "/api/clients",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(c["client_id"] == "test_client_sample" for c in data)
    
    @pytest.mark.asyncio
    async def test_list_clients_recruiter_success(self, client, recruiter_token, sample_client):
        """Test recruiter can list clients"""
        response = await client.get(
            "/api/clients",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_list_clients_client_user_forbidden(self, client, client_user_token):
        """Test client user cannot list clients"""
        response = await client.get(
            "/api/clients",
            headers={"Authorization": f"Bearer {client_user_token}"}
        )
        
        assert response.status_code == 403
        assert "Admin or recruiter" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_list_clients_no_auth(self, client):
        """Test unauthenticated request fails"""
        response = await client.get("/api/clients")
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_list_clients_with_search(self, client, admin_token, clean_db):
        """Test client list search functionality"""
        # Create multiple clients
        await clean_db.clients.insert_one({
            "client_id": "client_alpha",
            "company_name": "Alpha Corp",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        await clean_db.clients.insert_one({
            "client_id": "client_beta",
            "company_name": "Beta Industries",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        
        # Search for "Alpha"
        response = await client.get(
            "/api/clients?search=Alpha",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["company_name"] == "Alpha Corp"
    
    @pytest.mark.asyncio
    async def test_list_clients_pagination(self, client, admin_token, clean_db):
        """Test pagination parameters"""
        # Create multiple clients
        for i in range(5):
            await clean_db.clients.insert_one({
                "client_id": f"client_{i}",
                "company_name": f"Company {i}",
                "status": "active",
                "created_at": "2025-01-01T00:00:00"
            })
        
        # Test skip and limit
        response = await client.get(
            "/api/clients?skip=0&limit=2",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    @pytest.mark.asyncio
    async def test_list_clients_includes_user_count(self, client, admin_token, seed_test_client):
        """Test that client list includes user count"""
        response = await client.get(
            "/api/clients",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        for client_data in data:
            assert "user_count" in client_data
            assert isinstance(client_data["user_count"], int)


class TestClientCreateEndpoint:
    """Tests for POST /api/clients endpoint"""
    
    @pytest.mark.asyncio
    async def test_create_client_admin_success(self, client, admin_token, clean_db):
        """Test admin can create client"""
        response = await client.post(
            "/api/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"company_name": "New Test Company", "status": "active"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["company_name"] == "New Test Company"
        assert data["status"] == "active"
        assert "client_id" in data
        assert data["client_id"].startswith("client_")
        assert data["user_count"] == 0
    
    @pytest.mark.asyncio
    async def test_create_client_recruiter_success(self, client, recruiter_token, clean_db):
        """Test recruiter can create client"""
        response = await client.post(
            "/api/clients",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json={"company_name": "Recruiter Created Co", "status": "active"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["company_name"] == "Recruiter Created Co"
    
    @pytest.mark.asyncio
    async def test_create_client_client_user_forbidden(self, client, client_user_token):
        """Test client user cannot create client"""
        response = await client.post(
            "/api/clients",
            headers={"Authorization": f"Bearer {client_user_token}"},
            json={"company_name": "Unauthorized Co"}
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_create_client_duplicate_name(self, client, admin_token, sample_client):
        """Test creating client with duplicate name fails"""
        response = await client.post(
            "/api/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"company_name": "Sample Company"}  # Same as sample_client
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_client_default_status(self, client, admin_token, clean_db):
        """Test client created with default status"""
        response = await client.post(
            "/api/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"company_name": "Default Status Co"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "active"


class TestClientDetailEndpoints:
    """Tests for GET, PUT, PATCH /api/clients/{client_id}"""
    
    @pytest.mark.asyncio
    async def test_get_client_success(self, client, admin_token, sample_client):
        """Test getting client details"""
        response = await client.get(
            f"/api/clients/{sample_client['client_id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["client_id"] == sample_client["client_id"]
        assert data["company_name"] == sample_client["company_name"]
        assert "user_count" in data
    
    @pytest.mark.asyncio
    async def test_get_client_not_found(self, client, admin_token):
        """Test getting non-existent client"""
        response = await client.get(
            "/api/clients/nonexistent_client_id",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_client_success(self, client, admin_token, sample_client):
        """Test updating client"""
        response = await client.put(
            f"/api/clients/{sample_client['client_id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"company_name": "Updated Company Name"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["company_name"] == "Updated Company Name"
    
    @pytest.mark.asyncio
    async def test_update_client_status(self, client, admin_token, sample_client):
        """Test updating client status"""
        response = await client.put(
            f"/api/clients/{sample_client['client_id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "inactive"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "inactive"
    
    @pytest.mark.asyncio
    async def test_update_client_duplicate_name(self, client, admin_token, clean_db):
        """Test updating to duplicate name fails"""
        # Create two clients
        await clean_db.clients.insert_one({
            "client_id": "client_1",
            "company_name": "Company One",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        await clean_db.clients.insert_one({
            "client_id": "client_2",
            "company_name": "Company Two",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        
        # Try to update client_2 to same name as client_1
        response = await client.put(
            "/api/clients/client_2",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"company_name": "Company One"}
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_update_client_no_data(self, client, admin_token, sample_client):
        """Test update with no data fails"""
        response = await client.put(
            f"/api/clients/{sample_client['client_id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={}
        )
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_disable_client_success(self, client, admin_token, sample_client):
        """Test disabling client"""
        response = await client.patch(
            f"/api/clients/{sample_client['client_id']}/disable",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert "disabled successfully" in response.json()["message"]
        
        # Verify status changed
        get_response = await client.get(
            f"/api/clients/{sample_client['client_id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.json()["status"] == "inactive"
    
    @pytest.mark.asyncio
    async def test_disable_nonexistent_client(self, client, admin_token):
        """Test disabling non-existent client"""
        response = await client.patch(
            "/api/clients/nonexistent/disable",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404


class TestClientUserManagement:
    """Tests for client user creation and listing"""
    
    @pytest.mark.asyncio
    async def test_list_client_users_empty(self, client, admin_token, sample_client):
        """Test listing users for client with no users"""
        response = await client.get(
            f"/api/clients/{sample_client['client_id']}/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert response.json() == []
    
    @pytest.mark.asyncio
    async def test_list_client_users_with_data(self, client, admin_token, clean_db):
        """Test listing users for client"""
        # Create client and users
        await clean_db.clients.insert_one({
            "client_id": "client_with_users",
            "company_name": "Test Co",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        
        await clean_db.users.insert_one({
            "email": "user1@test.com",
            "name": "User 1",
            "role": "client_user",
            "client_id": "client_with_users",
            "password_hash": hash_password("pass"),
            "created_at": "2025-01-01T00:00:00"
        })
        
        response = await client.get(
            "/api/clients/client_with_users/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == "user1@test.com"
        assert "password_hash" not in data[0]  # Should be excluded
    
    @pytest.mark.asyncio
    async def test_create_client_user_admin_success(self, client, admin_token, sample_client):
        """Test admin can create user for client"""
        response = await client.post(
            f"/api/clients/{sample_client['client_id']}/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "newuser@test.com",
                "name": "New User",
                "password": "password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["name"] == "New User"
        assert data["role"] == "client_user"
        assert data["client_id"] == sample_client["client_id"]
    
    @pytest.mark.asyncio
    async def test_create_client_user_recruiter_success(self, client, recruiter_token, sample_client):
        """Test recruiter can create user for client"""
        response = await client.post(
            f"/api/clients/{sample_client['client_id']}/users",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json={
                "email": "recruiter.added@test.com",
                "name": "Recruiter Added",
                "password": "pass123"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["role"] == "client_user"
    
    @pytest.mark.asyncio
    async def test_create_client_user_forbidden_for_client_user(self, client, client_user_token, sample_client):
        """Test client user cannot create users"""
        response = await client.post(
            f"/api/clients/{sample_client['client_id']}/users",
            headers={"Authorization": f"Bearer {client_user_token}"},
            json={
                "email": "unauthorized@test.com",
                "name": "Unauthorized",
                "password": "pass"
            }
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_create_user_nonexistent_client(self, client, admin_token):
        """Test creating user for non-existent client"""
        response = await client.post(
            "/api/clients/nonexistent_client/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "user@test.com",
                "name": "User",
                "password": "pass"
            }
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, client, admin_token, sample_client, clean_db):
        """Test creating user with duplicate email"""
        # Create first user
        await clean_db.users.insert_one({
            "email": "existing@test.com",
            "name": "Existing User",
            "role": "client_user",
            "client_id": sample_client["client_id"],
            "password_hash": hash_password("pass"),
            "created_at": "2025-01-01T00:00:00"
        })
        
        # Try to create with same email
        response = await client.post(
            f"/api/clients/{sample_client['client_id']}/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "existing@test.com",
                "name": "Duplicate",
                "password": "pass"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_user_always_client_role(self, client, admin_token, sample_client):
        """Test that created users always have client_user role"""
        response = await client.post(
            f"/api/clients/{sample_client['client_id']}/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "forced.role@test.com",
                "name": "Force Role",
                "password": "pass"
            }
        )
        
        assert response.status_code == 200
        # Role should always be client_user regardless of any attempt to specify otherwise
        assert response.json()["role"] == "client_user"
    
    @pytest.mark.asyncio
    async def test_list_users_nonexistent_client(self, client, admin_token):
        """Test listing users for non-existent client"""
        response = await client.get(
            "/api/clients/nonexistent/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404


class TestMultiTenantEnforcement:
    """Tests for multi-tenant data isolation"""
    
    @pytest.mark.asyncio
    async def test_client_user_cannot_list_all_clients(self, client, client_user_token):
        """Test client user cannot list all clients"""
        response = await client.get(
            "/api/clients",
            headers={"Authorization": f"Bearer {client_user_token}"}
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_client_user_cannot_view_other_client(self, client, clean_db):
        """Test client user cannot view another client's details"""
        # Create two clients
        await clean_db.clients.insert_one({
            "client_id": "client_A",
            "company_name": "Client A",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        await clean_db.clients.insert_one({
            "client_id": "client_B",
            "company_name": "Client B",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        
        # Create user for client_A
        await clean_db.users.insert_one({
            "email": "userA@test.com",
            "name": "User A",
            "role": "client_user",
            "client_id": "client_A",
            "password_hash": hash_password("pass"),
            "created_at": "2025-01-01T00:00:00"
        })
        
        # Login as client_A user
        login_response = await client.post("/api/auth/login", json={
            "email": "userA@test.com",
            "password": "pass"
        })
        token = login_response.json()["access_token"]
        
        # Try to view client_B
        response = await client.get(
            "/api/clients/client_B",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_admin_can_access_all_clients(self, client, admin_token, clean_db):
        """Test admin can access any client"""
        await clean_db.clients.insert_one({
            "client_id": "any_client",
            "company_name": "Any Client",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        
        response = await client.get(
            "/api/clients/any_client",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_recruiter_can_access_all_clients(self, client, recruiter_token, clean_db):
        """Test recruiter can access any client"""
        await clean_db.clients.insert_one({
            "client_id": "any_client_rec",
            "company_name": "Any Client Rec",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        
        response = await client.get(
            "/api/clients/any_client_rec",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        
        assert response.status_code == 200
    
    # TODO: Phase 3+ - Add tests for job/candidate data isolation
    # When jobs and candidates are implemented:
    # - Client user can only see their own client's jobs
    # - Client user cannot create job for another client
    # - Admin/recruiter can see all jobs across clients
