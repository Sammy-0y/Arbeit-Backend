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
async def second_client_user_token(client, clean_db):
    """Create second client user for cross-tenant tests"""
    # Create second client
    await clean_db.clients.insert_one({
        "client_id": "test_client_002",
        "company_name": "Second Client Co",
        "status": "active",
        "created_at": "2025-01-01T00:00:00"
    })
    
    user_doc = {
        "email": "clientuser2@test.com",
        "name": "Client User 2",
        "role": "client_user",
        "client_id": "test_client_002",
        "password_hash": hash_password("client123"),
        "created_at": "2025-01-01T00:00:00"
    }
    await clean_db.users.insert_one(user_doc)
    
    response = await client.post("/api/auth/login", json={
        "email": "clientuser2@test.com",
        "password": "client123"
    })
    return response.json()["access_token"]

@pytest_asyncio.fixture
async def sample_job(seed_test_client):
    """Create a sample job for testing"""
    job_doc = {
        "job_id": "job_sample_001",
        "client_id": "test_client_001",
        "title": "Software Engineer",
        "location": "San Francisco",
        "employment_type": "Full-time",
        "experience_range": {"min_years": 2, "max_years": 5},
        "salary_range": {"min_amount": 100000, "max_amount": 150000, "currency": "USD"},
        "work_model": "Hybrid",
        "required_skills": ["Python", "React", "AWS"],
        "description": "Great opportunity to work with our team",
        "status": "Active",
        "created_at": "2025-01-01T00:00:00",
        "created_by": "clientuser@test.com"
    }
    await seed_test_client.jobs.insert_one(job_doc)
    return job_doc


class TestJobCreateEndpoint:
    """Tests for POST /api/jobs endpoint"""
    
    @pytest.mark.asyncio
    async def test_create_job_client_user_success(self, client, client_user_token, seed_test_client):
        """Test client user can create job (client_id auto-assigned)"""
        job_data = {
            "title": "Senior Developer",
            "location": "New York",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 3, "max_years": 7},
            "work_model": "Remote",
            "required_skills": ["JavaScript", "Node.js"],
            "description": "Looking for experienced developer",
            "status": "Active"
        }
        
        response = await client.post(
            "/api/jobs",
            headers={"Authorization": f"Bearer {client_user_token}"},
            json=job_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Senior Developer"
        assert data["client_id"] == "test_client_001"  # Auto-assigned
        assert data["job_id"].startswith("job_")
        assert data["status"] == "Active"
    
    @pytest.mark.asyncio
    async def test_create_job_admin_with_client_id(self, client, admin_token, seed_test_client):
        """Test admin can create job for specific client"""
        job_data = {
            "title": "Data Scientist",
            "location": "Boston",
            "employment_type": "Contract",
            "experience_range": {"min_years": 5, "max_years": 10},
            "work_model": "Onsite",
            "required_skills": ["Python", "Machine Learning"],
            "description": "Data science role",
            "status": "Active",
            "client_id": "test_client_001"
        }
        
        response = await client.post(
            "/api/jobs",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=job_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["client_id"] == "test_client_001"
    
    @pytest.mark.asyncio
    async def test_create_job_recruiter_with_client_id(self, client, recruiter_token, seed_test_client):
        """Test recruiter can create job for specific client"""
        job_data = {
            "title": "Product Manager",
            "location": "Seattle",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 2, "max_years": 5},
            "work_model": "Hybrid",
            "required_skills": ["Product Management", "Agile"],
            "description": "PM role",
            "status": "Draft",
            "client_id": "test_client_001"
        }
        
        response = await client.post(
            "/api/jobs",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json=job_data
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "Draft"
    
    @pytest.mark.asyncio
    async def test_create_job_admin_missing_client_id(self, client, admin_token):
        """Test admin must provide client_id"""
        job_data = {
            "title": "Test Job",
            "location": "NYC",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 1, "max_years": 3},
            "work_model": "Remote",
            "required_skills": ["Testing"],
            "description": "Test",
            "status": "Active"
        }
        
        response = await client.post(
            "/api/jobs",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=job_data
        )
        
        assert response.status_code == 400
        assert "client_id is required" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_job_invalid_client_id(self, client, admin_token):
        """Test creating job with non-existent client fails"""
        job_data = {
            "title": "Test Job",
            "location": "NYC",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 1, "max_years": 3},
            "work_model": "Remote",
            "required_skills": ["Testing"],
            "description": "Test",
            "status": "Active",
            "client_id": "nonexistent_client"
        }
        
        response = await client.post(
            "/api/jobs",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=job_data
        )
        
        assert response.status_code == 404
        assert "Client not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_job_with_salary_range(self, client, client_user_token):
        """Test job creation with optional salary range"""
        job_data = {
            "title": "Engineer",
            "location": "LA",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 2, "max_years": 4},
            "salary_range": {"min_amount": 80000, "max_amount": 120000, "currency": "USD"},
            "work_model": "Onsite",
            "required_skills": ["Java"],
            "description": "Java developer",
            "status": "Active"
        }
        
        response = await client.post(
            "/api/jobs",
            headers={"Authorization": f"Bearer {client_user_token}"},
            json=job_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["salary_range"]["min_amount"] == 80000
        assert data["salary_range"]["currency"] == "USD"
    
    @pytest.mark.asyncio
    async def test_create_job_no_auth(self, client):
        """Test job creation requires authentication"""
        job_data = {
            "title": "Test",
            "location": "NYC",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 1, "max_years": 3},
            "work_model": "Remote",
            "required_skills": ["Test"],
            "description": "Test",
            "status": "Active"
        }
        
        response = await client.post("/api/jobs", json=job_data)
        assert response.status_code == 403


class TestJobListEndpoint:
    """Tests for GET /api/jobs endpoint"""
    
    @pytest.mark.asyncio
    async def test_list_jobs_client_user_filtered(self, client, client_user_token, sample_job):
        """Test client user only sees their own jobs"""
        response = await client.get(
            "/api/jobs",
            headers={"Authorization": f"Bearer {client_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All jobs should belong to test_client_001
        for job in data:
            assert job["client_id"] == "test_client_001"
    
    @pytest.mark.asyncio
    async def test_list_jobs_admin_sees_all(self, client, admin_token, clean_db):
        """Test admin sees jobs from all clients"""
        # Create jobs for different clients
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
        
        await clean_db.jobs.insert_one({
            "job_id": "job_A",
            "client_id": "client_A",
            "title": "Job A",
            "location": "NYC",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 1, "max_years": 3},
            "work_model": "Remote",
            "required_skills": ["Python"],
            "description": "Job A",
            "status": "Active",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "admin@test.com"
        })
        await clean_db.jobs.insert_one({
            "job_id": "job_B",
            "client_id": "client_B",
            "title": "Job B",
            "location": "LA",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 1, "max_years": 3},
            "work_model": "Remote",
            "required_skills": ["Java"],
            "description": "Job B",
            "status": "Active",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "admin@test.com"
        })
        
        response = await client.get(
            "/api/jobs",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        client_ids = [job["client_id"] for job in data]
        assert "client_A" in client_ids
        assert "client_B" in client_ids
    
    @pytest.mark.asyncio
    async def test_list_jobs_filter_by_client(self, client, admin_token, clean_db):
        """Test admin can filter jobs by client_id"""
        await clean_db.clients.insert_one({
            "client_id": "filter_client",
            "company_name": "Filter Client",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        
        await clean_db.jobs.insert_one({
            "job_id": "filter_job",
            "client_id": "filter_client",
            "title": "Filtered Job",
            "location": "NYC",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 1, "max_years": 3},
            "work_model": "Remote",
            "required_skills": ["Python"],
            "description": "Test",
            "status": "Active",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "admin@test.com"
        })
        
        response = await client.get(
            "/api/jobs?client_id=filter_client",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["client_id"] == "filter_client"
    
    @pytest.mark.asyncio
    async def test_list_jobs_search_by_title(self, client, admin_token, clean_db):
        """Test search by job title"""
        await clean_db.clients.insert_one({
            "client_id": "search_client",
            "company_name": "Search Client",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        
        await clean_db.jobs.insert_one({
            "job_id": "search_job",
            "client_id": "search_client",
            "title": "Senior Python Developer",
            "location": "NYC",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 5, "max_years": 8},
            "work_model": "Remote",
            "required_skills": ["Python", "Django"],
            "description": "Test",
            "status": "Active",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "admin@test.com"
        })
        
        response = await client.get(
            "/api/jobs?search=Python",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert any("Python" in job["title"] for job in data)
    
    @pytest.mark.asyncio
    async def test_list_jobs_search_by_skill(self, client, admin_token, clean_db):
        """Test search by required skills"""
        await clean_db.clients.insert_one({
            "client_id": "skill_client",
            "company_name": "Skill Client",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        
        await clean_db.jobs.insert_one({
            "job_id": "skill_job",
            "client_id": "skill_client",
            "title": "Developer",
            "location": "NYC",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 2, "max_years": 5},
            "work_model": "Remote",
            "required_skills": ["React", "TypeScript", "GraphQL"],
            "description": "Test",
            "status": "Active",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "admin@test.com"
        })
        
        response = await client.get(
            "/api/jobs?search=GraphQL",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert any("GraphQL" in job["required_skills"] for job in data)
    
    @pytest.mark.asyncio
    async def test_list_jobs_filter_by_status(self, client, admin_token, clean_db):
        """Test filter jobs by status"""
        await clean_db.clients.insert_one({
            "client_id": "status_client",
            "company_name": "Status Client",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        
        await clean_db.jobs.insert_one({
            "job_id": "draft_job",
            "client_id": "status_client",
            "title": "Draft Job",
            "location": "NYC",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 1, "max_years": 3},
            "work_model": "Remote",
            "required_skills": ["Test"],
            "description": "Test",
            "status": "Draft",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "admin@test.com"
        })
        
        response = await client.get(
            "/api/jobs?status=Draft",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        for job in data:
            assert job["status"] == "Draft"
    
    @pytest.mark.asyncio
    async def test_list_jobs_pagination(self, client, admin_token, clean_db):
        """Test pagination with skip and limit"""
        await clean_db.clients.insert_one({
            "client_id": "page_client",
            "company_name": "Page Client",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        
        # Create multiple jobs
        for i in range(5):
            await clean_db.jobs.insert_one({
                "job_id": f"page_job_{i}",
                "client_id": "page_client",
                "title": f"Job {i}",
                "location": "NYC",
                "employment_type": "Full-time",
                "experience_range": {"min_years": 1, "max_years": 3},
                "work_model": "Remote",
                "required_skills": ["Test"],
                "description": "Test",
                "status": "Active",
                "created_at": "2025-01-01T00:00:00",
                "created_by": "admin@test.com"
            })
        
        response = await client.get(
            "/api/jobs?skip=0&limit=2",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2


class TestJobDetailEndpoint:
    """Tests for GET /api/jobs/{job_id} endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_job_success(self, client, client_user_token, sample_job):
        """Test getting job details"""
        response = await client.get(
            f"/api/jobs/{sample_job['job_id']}",
            headers={"Authorization": f"Bearer {client_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == sample_job["job_id"]
        assert data["title"] == sample_job["title"]
        assert "company_name" in data
    
    @pytest.mark.asyncio
    async def test_get_job_not_found(self, client, admin_token):
        """Test getting non-existent job"""
        response = await client.get(
            "/api/jobs/nonexistent_job_id",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_job_cross_tenant_forbidden(self, client, second_client_user_token, sample_job):
        """Test client user cannot view other client's job"""
        response = await client.get(
            f"/api/jobs/{sample_job['job_id']}",
            headers={"Authorization": f"Bearer {second_client_user_token}"}
        )
        
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_job_admin_can_view_any(self, client, admin_token, sample_job):
        """Test admin can view any job"""
        response = await client.get(
            f"/api/jobs/{sample_job['job_id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200


class TestJobUpdateEndpoint:
    """Tests for PUT /api/jobs/{job_id} endpoint"""
    
    @pytest.mark.asyncio
    async def test_update_job_client_user_success(self, client, client_user_token, sample_job):
        """Test client user can update their own job"""
        update_data = {
            "title": "Updated Software Engineer",
            "location": "Los Angeles"
        }
        
        response = await client.put(
            f"/api/jobs/{sample_job['job_id']}",
            headers={"Authorization": f"Bearer {client_user_token}"},
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Software Engineer"
        assert data["location"] == "Los Angeles"
    
    @pytest.mark.asyncio
    async def test_update_job_admin_success(self, client, admin_token, sample_job):
        """Test admin can update any job"""
        update_data = {
            "status": "Closed"
        }
        
        response = await client.put(
            f"/api/jobs/{sample_job['job_id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=update_data
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "Closed"
    
    @pytest.mark.asyncio
    async def test_update_job_cross_tenant_forbidden(self, client, second_client_user_token, sample_job):
        """Test client user cannot update other client's job"""
        update_data = {
            "title": "Hacked Title"
        }
        
        response = await client.put(
            f"/api/jobs/{sample_job['job_id']}",
            headers={"Authorization": f"Bearer {second_client_user_token}"},
            json=update_data
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_update_job_not_found(self, client, admin_token):
        """Test updating non-existent job"""
        response = await client.put(
            "/api/jobs/nonexistent_job",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "New Title"}
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_job_no_data(self, client, admin_token, sample_job):
        """Test update with no data fails"""
        response = await client.put(
            f"/api/jobs/{sample_job['job_id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={}
        )
        
        assert response.status_code == 400


class TestJobCloseEndpoint:
    """Tests for PATCH /api/jobs/{job_id}/close endpoint"""
    
    @pytest.mark.asyncio
    async def test_close_job_client_user_own_job(self, client, client_user_token, sample_job):
        """Test client user can close their own job"""
        response = await client.patch(
            f"/api/jobs/{sample_job['job_id']}/close",
            headers={"Authorization": f"Bearer {client_user_token}"}
        )
        
        assert response.status_code == 200
        assert "closed successfully" in response.json()["message"].lower()
        
        # Verify status changed
        get_response = await client.get(
            f"/api/jobs/{sample_job['job_id']}",
            headers={"Authorization": f"Bearer {client_user_token}"}
        )
        assert get_response.json()["status"] == "Closed"
    
    @pytest.mark.asyncio
    async def test_close_job_admin_success(self, client, admin_token, sample_job):
        """Test admin can close any job"""
        response = await client.patch(
            f"/api/jobs/{sample_job['job_id']}/close",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_close_job_recruiter_success(self, client, recruiter_token, sample_job):
        """Test recruiter can close any job"""
        response = await client.patch(
            f"/api/jobs/{sample_job['job_id']}/close",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_close_job_cross_tenant_forbidden(self, client, second_client_user_token, sample_job):
        """Test client user cannot close other client's job"""
        response = await client.patch(
            f"/api/jobs/{sample_job['job_id']}/close",
            headers={"Authorization": f"Bearer {second_client_user_token}"}
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_close_job_not_found(self, client, admin_token):
        """Test closing non-existent job"""
        response = await client.patch(
            "/api/jobs/nonexistent_job/close",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404


class TestJobTenantIsolation:
    """Tests for multi-tenant data isolation in job management"""
    
    @pytest.mark.asyncio
    async def test_client_user_cannot_list_other_jobs(self, client, clean_db):
        """Test client users only see their own jobs in list"""
        # Create two clients with jobs
        await clean_db.clients.insert_one({
            "client_id": "tenant_A",
            "company_name": "Tenant A",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        await clean_db.clients.insert_one({
            "client_id": "tenant_B",
            "company_name": "Tenant B",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        
        # Create jobs for each tenant
        await clean_db.jobs.insert_one({
            "job_id": "job_tenant_A",
            "client_id": "tenant_A",
            "title": "Job A",
            "location": "NYC",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 1, "max_years": 3},
            "work_model": "Remote",
            "required_skills": ["Python"],
            "description": "Job A",
            "status": "Active",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "userA@test.com"
        })
        await clean_db.jobs.insert_one({
            "job_id": "job_tenant_B",
            "client_id": "tenant_B",
            "title": "Job B",
            "location": "LA",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 1, "max_years": 3},
            "work_model": "Remote",
            "required_skills": ["Java"],
            "description": "Job B",
            "status": "Active",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "userB@test.com"
        })
        
        # Create user for tenant_A
        await clean_db.users.insert_one({
            "email": "userA@test.com",
            "name": "User A",
            "role": "client_user",
            "client_id": "tenant_A",
            "password_hash": hash_password("pass"),
            "created_at": "2025-01-01T00:00:00"
        })
        
        # Login as tenant_A user
        login_response = await client.post("/api/auth/login", json={
            "email": "userA@test.com",
            "password": "pass"
        })
        token = login_response.json()["access_token"]
        
        # List jobs
        response = await client.get(
            "/api/jobs",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        jobs = response.json()
        # Should only see tenant_A jobs
        assert all(job["client_id"] == "tenant_A" for job in jobs)
        assert not any(job["client_id"] == "tenant_B" for job in jobs)
    
    @pytest.mark.asyncio
    async def test_admin_recruiter_bypass_tenant_filter(self, client, admin_token, clean_db):
        """Test admin and recruiter can see all jobs regardless of tenant"""
        # Create jobs for different tenants
        await clean_db.clients.insert_one({
            "client_id": "multi_tenant_A",
            "company_name": "Multi A",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        await clean_db.clients.insert_one({
            "client_id": "multi_tenant_B",
            "company_name": "Multi B",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        
        await clean_db.jobs.insert_one({
            "job_id": "multi_job_A",
            "client_id": "multi_tenant_A",
            "title": "Multi Job A",
            "location": "NYC",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 1, "max_years": 3},
            "work_model": "Remote",
            "required_skills": ["Test"],
            "description": "Test",
            "status": "Active",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "admin@test.com"
        })
        await clean_db.jobs.insert_one({
            "job_id": "multi_job_B",
            "client_id": "multi_tenant_B",
            "title": "Multi Job B",
            "location": "LA",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 1, "max_years": 3},
            "work_model": "Remote",
            "required_skills": ["Test"],
            "description": "Test",
            "status": "Active",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "admin@test.com"
        })
        
        response = await client.get(
            "/api/jobs",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        jobs = response.json()
        client_ids = [job["client_id"] for job in jobs]
        assert "multi_tenant_A" in client_ids
        assert "multi_tenant_B" in client_ids
