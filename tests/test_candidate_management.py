import pytest
import pytest_asyncio
import sys
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock
import io

sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from server import app, hash_password, redact_text, ParsedResume, CandidateStory

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
        "job_id": "job_test_001",
        "client_id": "test_client_001",
        "title": "Software Engineer",
        "location": "San Francisco",
        "employment_type": "Full-time",
        "experience_range": {"min_years": 2, "max_years": 5},
        "work_model": "Hybrid",
        "required_skills": ["Python", "React"],
        "description": "Great role",
        "status": "Active",
        "created_at": "2025-01-01T00:00:00",
        "created_by": "admin@test.com"
    }
    await seed_test_client.jobs.insert_one(job_doc)
    return job_doc

@pytest_asyncio.fixture
async def second_client_job(clean_db):
    """Create job for second client"""
    job_doc = {
        "job_id": "job_test_002",
        "client_id": "test_client_002",
        "title": "Data Scientist",
        "location": "NYC",
        "employment_type": "Full-time",
        "experience_range": {"min_years": 3, "max_years": 7},
        "work_model": "Remote",
        "required_skills": ["Python", "ML"],
        "description": "ML role",
        "status": "Active",
        "created_at": "2025-01-01T00:00:00",
        "created_by": "admin@test.com"
    }
    await clean_db.jobs.insert_one(job_doc)
    return job_doc

@pytest_asyncio.fixture
async def mock_ai_functions():
    """Mock AI parsing and story generation"""
    mock_parsed_resume = ParsedResume(
        name="John Doe",
        current_role="Senior Developer",
        email="john.doe@example.com",
        phone="555-1234",
        linkedin="linkedin.com/in/johndoe",
        skills=["Python", "React", "AWS"],
        experience=[
            {"company": "Tech Corp", "role": "Developer", "duration": "2020-2023", "achievements": ["Built API"]}
        ],
        education=[
            {"degree": "BS Computer Science", "institution": "MIT", "year": "2019"}
        ],
        summary="Experienced developer"
    )
    
    mock_story = CandidateStory(
        headline="Senior Developer with 5+ years experience",
        summary="Strong Python and React skills with proven track record",
        timeline=[
            {"year": "2020-2023", "title": "Senior Developer", "company": "Tech Corp", "achievement": "Built scalable API"}
        ],
        skills=["Python", "React", "AWS"],
        fit_score=85,
        highlights=["5 years experience", "Strong technical skills", "Team leadership"]
    )
    
    with patch('server.parse_cv_with_ai', new=AsyncMock(return_value=mock_parsed_resume)), \
         patch('server.generate_candidate_story', new=AsyncMock(return_value=mock_story)):
        yield


class TestRedactionLogic:
    """Unit tests for redaction utilities"""
    
    def test_redact_email(self):
        """Test email redaction"""
        text = "Contact me at john.doe@example.com for more info"
        redacted = redact_text(text)
        assert "john.doe@example.com" not in redacted
        assert "[EMAIL REDACTED]" in redacted
    
    def test_redact_phone(self):
        """Test phone number redaction"""
        text = "Call me at 555-123-4567 or (555) 123-4567"
        redacted = redact_text(text)
        assert "555-123-4567" not in redacted
        assert "[PHONE REDACTED]" in redacted
    
    def test_redact_linkedin(self):
        """Test LinkedIn URL redaction"""
        text = "Profile: https://www.linkedin.com/in/johndoe"
        redacted = redact_text(text)
        assert "linkedin.com/in/johndoe" not in redacted
        assert "[LINKEDIN REDACTED]" in redacted
    
    def test_redact_generic_urls(self):
        """Test generic URL redaction"""
        text = "Website: https://johndoe.com and http://portfolio.com"
        redacted = redact_text(text)
        assert "johndoe.com" not in redacted
        assert "[URL REDACTED]" in redacted
    
    def test_redact_multiple_items(self):
        """Test redacting multiple types of information"""
        text = "Contact John at john@example.com or 555-1234. LinkedIn: linkedin.com/in/john"
        redacted = redact_text(text)
        assert "john@example.com" not in redacted
        assert "555-1234" not in redacted
        assert "linkedin.com" not in redacted
        assert "[EMAIL REDACTED]" in redacted
        assert "[PHONE REDACTED]" in redacted


class TestCandidateManualCreation:
    """Tests for POST /api/candidates (manual creation)"""
    
    @pytest.mark.asyncio
    async def test_create_candidate_recruiter_success(self, client, recruiter_token, sample_job, mock_ai_functions):
        """Test recruiter can create candidate manually"""
        candidate_data = {
            "job_id": sample_job["job_id"],
            "name": "Jane Smith",
            "current_role": "Developer",
            "skills": ["Python", "Django"],
            "experience": [{"company": "StartupX", "role": "Dev", "duration": "2021-2023"}],
            "education": [{"degree": "BS CS", "institution": "Stanford", "year": "2020"}],
            "summary": "Great candidate"
        }
        
        response = await client.post(
            "/api/candidates",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json=candidate_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Jane Smith"
        assert data["job_id"] == sample_job["job_id"]
        assert data["status"] == "NEW"
        assert "candidate_id" in data
        assert data["ai_story"] is not None
    
    @pytest.mark.asyncio
    async def test_create_candidate_admin_success(self, client, admin_token, sample_job, mock_ai_functions):
        """Test admin can create candidate"""
        candidate_data = {
            "job_id": sample_job["job_id"],
            "name": "Bob Johnson",
            "skills": ["Java"],
            "experience": [],
            "education": []
        }
        
        response = await client.post(
            "/api/candidates",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=candidate_data
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_create_candidate_client_user_forbidden(self, client, client_user_token, sample_job):
        """Test client user cannot create candidate"""
        candidate_data = {
            "job_id": sample_job["job_id"],
            "name": "Test Candidate",
            "skills": []
        }
        
        response = await client.post(
            "/api/candidates",
            headers={"Authorization": f"Bearer {client_user_token}"},
            json=candidate_data
        )
        
        assert response.status_code == 403
        assert "Only admin/recruiter" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_candidate_invalid_job(self, client, recruiter_token, mock_ai_functions):
        """Test creating candidate for non-existent job"""
        candidate_data = {
            "job_id": "nonexistent_job",
            "name": "Test",
            "skills": []
        }
        
        response = await client.post(
            "/api/candidates",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json=candidate_data
        )
        
        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]


class TestCandidateUpload:
    """Tests for POST /api/candidates/upload (CV upload)"""
    
    @pytest.mark.asyncio
    async def test_upload_cv_recruiter_success(self, client, recruiter_token, sample_job, mock_ai_functions):
        """Test recruiter can upload CV"""
        # Create mock file
        file_content = b"Mock CV content for testing"
        files = {"file": ("resume.pdf", io.BytesIO(file_content), "application/pdf")}
        data = {"job_id": sample_job["job_id"]}
        
        response = await client.post(
            "/api/candidates/upload",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            data=data,
            files=files
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "John Doe"  # From mock
        assert result["cv_file_url"] is not None
        assert result["ai_story"] is not None
    
    @pytest.mark.asyncio
    async def test_upload_cv_admin_success(self, client, admin_token, sample_job, mock_ai_functions):
        """Test admin can upload CV"""
        file_content = b"Resume content"
        files = {"file": ("cv.docx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        data = {"job_id": sample_job["job_id"]}
        
        response = await client.post(
            "/api/candidates/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data=data,
            files=files
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_upload_cv_client_user_forbidden(self, client, client_user_token, sample_job):
        """Test client user cannot upload CV"""
        file_content = b"CV content"
        files = {"file": ("resume.pdf", io.BytesIO(file_content), "application/pdf")}
        data = {"job_id": sample_job["job_id"]}
        
        response = await client.post(
            "/api/candidates/upload",
            headers={"Authorization": f"Bearer {client_user_token}"},
            data=data,
            files=files
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_upload_cv_invalid_job(self, client, recruiter_token, mock_ai_functions):
        """Test upload with invalid job ID"""
        file_content = b"CV"
        files = {"file": ("resume.pdf", io.BytesIO(file_content), "application/pdf")}
        data = {"job_id": "invalid_job"}
        
        response = await client.post(
            "/api/candidates/upload",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            data=data,
            files=files
        )
        
        assert response.status_code == 404


class TestCandidateList:
    """Tests for GET /api/jobs/{job_id}/candidates"""
    
    @pytest.mark.asyncio
    async def test_list_candidates_empty(self, client, recruiter_token, sample_job):
        """Test listing candidates when none exist"""
        response = await client.get(
            f"/api/jobs/{sample_job['job_id']}/candidates",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        
        assert response.status_code == 200
        assert response.json() == []
    
    @pytest.mark.asyncio
    async def test_list_candidates_with_data(self, client, recruiter_token, sample_job, clean_db, mock_ai_functions):
        """Test listing candidates"""
        # Create candidate
        await clean_db.candidates.insert_one({
            "candidate_id": "cand_001",
            "job_id": sample_job["job_id"],
            "name": "Test Candidate",
            "skills": ["Python"],
            "experience": [],
            "education": [],
            "status": "NEW",
            "ai_story": {
                "headline": "Test",
                "summary": "Test",
                "timeline": [],
                "skills": [],
                "fit_score": 80,
                "highlights": []
            },
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@test.com"
        })
        
        response = await client.get(
            f"/api/jobs/{sample_job['job_id']}/candidates",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Candidate"
    
    @pytest.mark.asyncio
    async def test_list_candidates_client_user_own_job(self, client, client_user_token, sample_job):
        """Test client user can list candidates for their own job"""
        response = await client.get(
            f"/api/jobs/{sample_job['job_id']}/candidates",
            headers={"Authorization": f"Bearer {client_user_token}"}
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_list_candidates_client_user_other_job(self, client, second_client_user_token, sample_job):
        """Test client user cannot list candidates for other client's job"""
        response = await client.get(
            f"/api/jobs/{sample_job['job_id']}/candidates",
            headers={"Authorization": f"Bearer {second_client_user_token}"}
        )
        
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_list_candidates_invalid_job(self, client, recruiter_token):
        """Test listing candidates for non-existent job"""
        response = await client.get(
            "/api/jobs/nonexistent_job/candidates",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        
        assert response.status_code == 404


class TestCandidateDetail:
    """Tests for GET /api/candidates/{candidate_id}"""
    
    @pytest.mark.asyncio
    async def test_get_candidate_success(self, client, recruiter_token, sample_job, clean_db):
        """Test getting candidate details"""
        await clean_db.candidates.insert_one({
            "candidate_id": "cand_detail",
            "job_id": sample_job["job_id"],
            "name": "Detail Candidate",
            "current_role": "Engineer",
            "skills": ["Python"],
            "experience": [],
            "education": [],
            "status": "NEW",
            "ai_story": {
                "headline": "Great candidate",
                "summary": "Excellent fit",
                "timeline": [],
                "skills": ["Python"],
                "fit_score": 90,
                "highlights": ["5 years exp"]
            },
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@test.com"
        })
        
        response = await client.get(
            "/api/candidates/cand_detail",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["candidate_id"] == "cand_detail"
        assert data["name"] == "Detail Candidate"
        assert data["ai_story"]["fit_score"] == 90
    
    @pytest.mark.asyncio
    async def test_get_candidate_not_found(self, client, recruiter_token):
        """Test getting non-existent candidate"""
        response = await client.get(
            "/api/candidates/nonexistent",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_candidate_cross_tenant_forbidden(self, client, second_client_user_token, sample_job, clean_db):
        """Test client user cannot view other tenant's candidate"""
        await clean_db.candidates.insert_one({
            "candidate_id": "cand_cross",
            "job_id": sample_job["job_id"],
            "name": "Cross Tenant",
            "skills": [],
            "experience": [],
            "education": [],
            "status": "NEW",
            "ai_story": {},
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@test.com"
        })
        
        response = await client.get(
            "/api/candidates/cand_cross",
            headers={"Authorization": f"Bearer {second_client_user_token}"}
        )
        
        assert response.status_code == 403


class TestCandidateCVViewer:
    """Tests for GET /api/candidates/{candidate_id}/cv"""
    
    @pytest.mark.asyncio
    async def test_get_cv_redacted_client_user(self, client, client_user_token, sample_job, clean_db):
        """Test client user gets redacted CV"""
        cv_text = "Contact john@example.com or call 555-1234"
        redacted_cv = redact_text(cv_text)
        
        await clean_db.candidates.insert_one({
            "candidate_id": "cand_cv",
            "job_id": sample_job["job_id"],
            "name": "CV Candidate",
            "skills": [],
            "experience": [],
            "education": [],
            "cv_text_original": cv_text,
            "cv_text_redacted": redacted_cv,
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@test.com"
        })
        
        response = await client.get(
            "/api/candidates/cand_cv/cv?redacted=true",
            headers={"Authorization": f"Bearer {client_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_redacted"] is True
        assert "john@example.com" not in data["cv_text"]
        assert "[EMAIL REDACTED]" in data["cv_text"]
    
    @pytest.mark.asyncio
    async def test_get_cv_original_recruiter(self, client, recruiter_token, sample_job, clean_db):
        """Test recruiter gets original CV"""
        cv_text = "Contact john@example.com"
        
        await clean_db.candidates.insert_one({
            "candidate_id": "cand_cv_orig",
            "job_id": sample_job["job_id"],
            "name": "Original CV",
            "skills": [],
            "experience": [],
            "education": [],
            "cv_text_original": cv_text,
            "cv_text_redacted": redact_text(cv_text),
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@test.com"
        })
        
        response = await client.get(
            "/api/candidates/cand_cv_orig/cv?redacted=false",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_redacted"] is False
        assert "john@example.com" in data["cv_text"]
    
    @pytest.mark.asyncio
    async def test_get_cv_client_always_redacted(self, client, client_user_token, sample_job, clean_db):
        """Test client user always gets redacted even if requesting original"""
        cv_text = "Email: john@example.com"
        
        await clean_db.candidates.insert_one({
            "candidate_id": "cand_force_redact",
            "job_id": sample_job["job_id"],
            "name": "Force Redact",
            "skills": [],
            "experience": [],
            "education": [],
            "cv_text_original": cv_text,
            "cv_text_redacted": redact_text(cv_text),
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@test.com"
        })
        
        # Client requests original but should get redacted
        response = await client.get(
            "/api/candidates/cand_force_redact/cv?redacted=false",
            headers={"Authorization": f"Bearer {client_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_redacted"] is True  # Forced to true
        assert "john@example.com" not in data["cv_text"]


class TestCandidateUpdate:
    """Tests for PUT /api/candidates/{candidate_id}"""
    
    @pytest.mark.asyncio
    async def test_update_candidate_recruiter(self, client, recruiter_token, sample_job, clean_db):
        """Test recruiter can update all fields"""
        await clean_db.candidates.insert_one({
            "candidate_id": "cand_update",
            "job_id": sample_job["job_id"],
            "name": "Original Name",
            "skills": ["Python"],
            "experience": [],
            "education": [],
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@test.com"
        })
        
        update_data = {
            "name": "Updated Name",
            "skills": ["Python", "Java"],
            "status": "PIPELINE"
        }
        
        response = await client.put(
            "/api/candidates/cand_update",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert "Java" in data["skills"]
        assert data["status"] == "PIPELINE"
    
    @pytest.mark.asyncio
    async def test_update_candidate_client_status_only(self, client, client_user_token, sample_job, clean_db):
        """Test client user can only update status"""
        await clean_db.candidates.insert_one({
            "candidate_id": "cand_status",
            "job_id": sample_job["job_id"],
            "name": "Status Test",
            "skills": ["Python"],
            "experience": [],
            "education": [],
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@test.com"
        })
        
        # Client can update status
        response = await client.put(
            "/api/candidates/cand_status",
            headers={"Authorization": f"Bearer {client_user_token}"},
            json={"status": "APPROVED"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "APPROVED"
    
    @pytest.mark.asyncio
    async def test_update_candidate_client_other_fields_forbidden(self, client, client_user_token, sample_job, clean_db):
        """Test client user cannot update non-status fields"""
        await clean_db.candidates.insert_one({
            "candidate_id": "cand_forbidden",
            "job_id": sample_job["job_id"],
            "name": "Forbidden Test",
            "skills": [],
            "experience": [],
            "education": [],
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@test.com"
        })
        
        response = await client.put(
            "/api/candidates/cand_forbidden",
            headers={"Authorization": f"Bearer {client_user_token}"},
            json={"name": "Hacked Name"}
        )
        
        assert response.status_code == 403
        assert "can only update status" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_update_candidate_cross_tenant_forbidden(self, client, second_client_user_token, sample_job, clean_db):
        """Test cross-tenant update blocked"""
        await clean_db.candidates.insert_one({
            "candidate_id": "cand_cross_update",
            "job_id": sample_job["job_id"],
            "name": "Cross Update",
            "skills": [],
            "experience": [],
            "education": [],
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@test.com"
        })
        
        response = await client.put(
            "/api/candidates/cand_cross_update",
            headers={"Authorization": f"Bearer {second_client_user_token}"},
            json={"status": "APPROVED"}
        )
        
        assert response.status_code == 403


class TestStoryRegeneration:
    """Tests for POST /api/candidates/{id}/regenerate-story"""
    
    @pytest.mark.asyncio
    async def test_regenerate_story_recruiter_success(self, client, recruiter_token, sample_job, clean_db, mock_ai_functions):
        """Test recruiter can regenerate story"""
        await clean_db.candidates.insert_one({
            "candidate_id": "cand_regen",
            "job_id": sample_job["job_id"],
            "name": "Regen Test",
            "skills": ["Python"],
            "experience": [],
            "education": [],
            "status": "NEW",
            "ai_story": {
                "headline": "Old headline",
                "summary": "Old",
                "timeline": [],
                "skills": [],
                "fit_score": 50,
                "highlights": []
            },
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@test.com"
        })
        
        response = await client.post(
            "/api/candidates/cand_regen/regenerate-story",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should have new story from mock
        assert data["ai_story"]["fit_score"] == 85  # From mock
    
    @pytest.mark.asyncio
    async def test_regenerate_story_admin_success(self, client, admin_token, sample_job, clean_db, mock_ai_functions):
        """Test admin can regenerate story"""
        await clean_db.candidates.insert_one({
            "candidate_id": "cand_regen_admin",
            "job_id": sample_job["job_id"],
            "name": "Admin Regen",
            "skills": [],
            "experience": [],
            "education": [],
            "status": "NEW",
            "ai_story": {},
            "created_at": "2025-01-01T00:00:00",
            "created_by": "admin@test.com"
        })
        
        response = await client.post(
            "/api/candidates/cand_regen_admin/regenerate-story",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_regenerate_story_client_forbidden(self, client, client_user_token, sample_job, clean_db):
        """Test client user cannot regenerate story"""
        await clean_db.candidates.insert_one({
            "candidate_id": "cand_client_regen",
            "job_id": sample_job["job_id"],
            "name": "Client Regen",
            "skills": [],
            "experience": [],
            "education": [],
            "status": "NEW",
            "ai_story": {},
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@test.com"
        })
        
        response = await client.post(
            "/api/candidates/cand_client_regen/regenerate-story",
            headers={"Authorization": f"Bearer {client_user_token}"}
        )
        
        assert response.status_code == 403
        assert "Only admin/recruiter" in response.json()["detail"]


class TestTenantIsolation:
    """Tests for tenant isolation in candidate management"""
    
    @pytest.mark.asyncio
    async def test_candidates_filtered_by_tenant(self, client, clean_db):
        """Test candidates are properly filtered by tenant"""
        # Create two clients with jobs
        await clean_db.clients.insert_one({
            "client_id": "iso_client_A",
            "company_name": "Client A",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        await clean_db.clients.insert_one({
            "client_id": "iso_client_B",
            "company_name": "Client B",
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
        })
        
        # Create jobs
        await clean_db.jobs.insert_one({
            "job_id": "job_A",
            "client_id": "iso_client_A",
            "title": "Job A",
            "location": "NYC",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 1, "max_years": 3},
            "work_model": "Remote",
            "required_skills": [],
            "description": "Test",
            "status": "Active",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "admin@test.com"
        })
        await clean_db.jobs.insert_one({
            "job_id": "job_B",
            "client_id": "iso_client_B",
            "title": "Job B",
            "location": "LA",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 1, "max_years": 3},
            "work_model": "Remote",
            "required_skills": [],
            "description": "Test",
            "status": "Active",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "admin@test.com"
        })
        
        # Create candidates
        await clean_db.candidates.insert_one({
            "candidate_id": "cand_A",
            "job_id": "job_A",
            "name": "Candidate A",
            "skills": [],
            "experience": [],
            "education": [],
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@test.com"
        })
        await clean_db.candidates.insert_one({
            "candidate_id": "cand_B",
            "job_id": "job_B",
            "name": "Candidate B",
            "skills": [],
            "experience": [],
            "education": [],
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@test.com"
        })
        
        # Create user for client A
        await clean_db.users.insert_one({
            "email": "userA@test.com",
            "name": "User A",
            "role": "client_user",
            "client_id": "iso_client_A",
            "password_hash": hash_password("pass"),
            "created_at": "2025-01-01T00:00:00"
        })
        
        # Login and list candidates
        login_response = await client.post("/api/auth/login", json={
            "email": "userA@test.com",
            "password": "pass"
        })
        token = login_response.json()["access_token"]
        
        # Should only see job_A candidates
        response = await client.get(
            "/api/jobs/job_A/candidates",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        candidates = response.json()
        assert all(c["job_id"] == "job_A" for c in candidates)
        
        # Try to access job_B (should fail)
        response_b = await client.get(
            "/api/jobs/job_B/candidates",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response_b.status_code == 403
