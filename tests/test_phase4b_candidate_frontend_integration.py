#!/usr/bin/env python3
"""
Phase 4b: Candidate Management - Comprehensive Automated Testing
Tests backend APIs, role-based access, and integration scenarios for candidate management.
"""

import pytest
import pytest_asyncio
import sys
import asyncio
import json
import io
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from server import app, hash_password, redact_text, ParsedResume, CandidateStory
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

# Test configuration
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = "test_phase4b_candidate_db"

@pytest_asyncio.fixture(scope="session")
async def test_db():
    """Create test database connection"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    yield db
    # Cleanup after all tests
    await client.drop_database(DB_NAME)
    client.close()

@pytest_asyncio.fixture
async def clean_db(test_db):
    """Clean database before each test"""
    collections = ['users', 'clients', 'jobs', 'candidates']
    for collection in collections:
        await test_db[collection].delete_many({})
    yield test_db

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
async def seed_test_data(clean_db):
    """Seed basic test data (clients, users, jobs)"""
    # Create test client
    await clean_db.clients.insert_one({
        "client_id": "client_001",
        "company_name": "Acme Corporation",
        "status": "active",
        "created_at": "2025-01-01T00:00:00",
        "created_by": "admin@arbeit.com"
    })
    
    # Create users with exact credentials from review request
    users = [
        {
            "email": "admin@arbeit.com",
            "name": "Admin User",
            "role": "admin",
            "client_id": None,
            "password_hash": hash_password("admin123"),
            "created_at": "2025-01-01T00:00:00"
        },
        {
            "email": "recruiter@arbeit.com", 
            "name": "Sarah Recruiter",
            "role": "recruiter",
            "client_id": None,
            "password_hash": hash_password("recruiter123"),
            "created_at": "2025-01-01T00:00:00"
        },
        {
            "email": "client@acme.com",
            "name": "John Client",
            "role": "client_user",
            "client_id": "client_001",
            "password_hash": hash_password("client123"),
            "created_at": "2025-01-01T00:00:00"
        }
    ]
    
    for user in users:
        await clean_db.users.insert_one(user)
    
    # Create test job
    await clean_db.jobs.insert_one({
        "job_id": "job_001",
        "client_id": "client_001",
        "title": "Senior Software Engineer",
        "location": "San Francisco, CA",
        "employment_type": "Full-time",
        "experience_range": {"min_years": 3, "max_years": 8},
        "salary_range": {"min_amount": 120000, "max_amount": 180000, "currency": "USD"},
        "work_model": "Hybrid",
        "required_skills": ["Python", "React", "AWS", "Docker"],
        "description": "We are looking for a senior software engineer to join our growing team...",
        "status": "Active",
        "created_at": "2025-01-01T00:00:00",
        "created_by": "admin@arbeit.com"
    })
    
    yield clean_db

@pytest_asyncio.fixture
async def admin_token(client, seed_test_data):
    """Get admin authentication token"""
    response = await client.post("/api/auth/login", json={
        "email": "admin@arbeit.com",
        "password": "admin123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest_asyncio.fixture
async def recruiter_token(client, seed_test_data):
    """Get recruiter authentication token"""
    response = await client.post("/api/auth/login", json={
        "email": "recruiter@arbeit.com",
        "password": "recruiter123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest_asyncio.fixture
async def client_user_token(client, seed_test_data):
    """Get client user authentication token"""
    response = await client.post("/api/auth/login", json={
        "email": "client@acme.com",
        "password": "client123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest_asyncio.fixture
async def mock_ai_functions():
    """Mock AI parsing and story generation for consistent testing"""
    mock_parsed_resume = ParsedResume(
        name="Sarah Johnson",
        current_role="Senior Software Engineer",
        email="sarah.johnson@email.com",
        phone="415-555-0123",
        linkedin="https://linkedin.com/in/sarahjohnson",
        skills=["Python", "React", "AWS", "Docker", "Kubernetes"],
        experience=[
            {
                "company": "TechCorp Inc",
                "role": "Senior Software Engineer", 
                "duration": "2021-2024",
                "achievements": ["Led team of 5 developers", "Reduced deployment time by 60%", "Built microservices architecture"]
            },
            {
                "company": "StartupXYZ",
                "role": "Full Stack Developer",
                "duration": "2019-2021", 
                "achievements": ["Developed React frontend", "Built Python APIs", "Implemented CI/CD pipeline"]
            }
        ],
        education=[
            {
                "degree": "BS Computer Science",
                "institution": "Stanford University",
                "year": "2019"
            }
        ],
        summary="Experienced software engineer with 5+ years building scalable web applications using Python, React, and cloud technologies."
    )
    
    mock_story = CandidateStory(
        headline="Senior Software Engineer with 5+ years of full-stack experience and proven leadership skills",
        summary="Sarah is an exceptional senior engineer who combines deep technical expertise in Python and React with strong leadership experience. Her track record of reducing deployment times and leading development teams makes her an ideal fit for senior engineering roles.",
        timeline=[
            {
                "year": "2021-2024",
                "title": "Senior Software Engineer",
                "company": "TechCorp Inc",
                "achievement": "Led team of 5 developers and reduced deployment time by 60%"
            },
            {
                "year": "2019-2021", 
                "title": "Full Stack Developer",
                "company": "StartupXYZ",
                "achievement": "Built complete React frontend and Python API backend"
            }
        ],
        skills=["Python", "React", "AWS", "Docker", "Kubernetes", "Team Leadership"],
        fit_score=92,
        highlights=[
            "5+ years of experience with Python and React - perfect match for required skills",
            "Proven leadership experience managing development teams",
            "Strong DevOps background with AWS, Docker, and CI/CD",
            "Stanford CS degree with excellent technical foundation"
        ]
    )
    
    with patch('server.parse_cv_with_ai', new=AsyncMock(return_value=mock_parsed_resume)), \
         patch('server.generate_candidate_story', new=AsyncMock(return_value=mock_story)):
        yield


class TestCandidateListPage:
    """Test Candidate List Page functionality"""
    
    @pytest.mark.asyncio
    async def test_empty_candidate_list(self, client, recruiter_token, seed_test_data):
        """Test candidate list shows empty state when no candidates exist"""
        response = await client.get(
            "/api/jobs/job_001/candidates",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        
        assert response.status_code == 200
        candidates = response.json()
        assert candidates == []
        print("✓ Empty candidate list returns correctly")
    
    @pytest.mark.asyncio
    async def test_candidate_list_with_data(self, client, recruiter_token, seed_test_data):
        """Test candidate list displays with correct fields and status filtering"""
        # Create test candidates with different statuses
        candidates_data = [
            {
                "candidate_id": "cand_001",
                "job_id": "job_001",
                "name": "Alice Smith",
                "current_role": "Software Engineer",
                "skills": ["Python", "React"],
                "experience": [{"company": "TechCorp", "role": "Engineer", "duration": "2020-2023"}],
                "education": [{"degree": "BS CS", "institution": "MIT", "year": "2020"}],
                "status": "NEW",
                "ai_story": {
                    "headline": "Experienced Engineer",
                    "summary": "Great fit",
                    "timeline": [],
                    "skills": ["Python", "React"],
                    "fit_score": 85,
                    "highlights": ["5 years experience"]
                },
                "created_at": "2025-01-01T00:00:00",
                "created_by": "recruiter@arbeit.com"
            },
            {
                "candidate_id": "cand_002", 
                "job_id": "job_001",
                "name": "Bob Johnson",
                "current_role": "Senior Developer",
                "skills": ["Python", "AWS"],
                "experience": [],
                "education": [],
                "status": "PIPELINE",
                "ai_story": {
                    "headline": "Senior Developer",
                    "summary": "Strong candidate",
                    "timeline": [],
                    "skills": ["Python", "AWS"],
                    "fit_score": 90,
                    "highlights": ["AWS expertise"]
                },
                "created_at": "2025-01-01T00:00:00",
                "created_by": "recruiter@arbeit.com"
            }
        ]
        
        for candidate in candidates_data:
            await seed_test_data.candidates.insert_one(candidate)
        
        response = await client.get(
            "/api/jobs/job_001/candidates",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        
        assert response.status_code == 200
        candidates = response.json()
        assert len(candidates) == 2
        
        # Verify candidate fields are present
        for candidate in candidates:
            assert "candidate_id" in candidate
            assert "name" in candidate
            assert "current_role" in candidate
            assert "skills" in candidate
            assert "ai_story" in candidate
            assert "status" in candidate
            assert candidate["ai_story"]["fit_score"] > 0
        
        print("✓ Candidate list displays with correct fields and AI match scores")
    
    @pytest.mark.asyncio
    async def test_candidate_access_by_role(self, client, admin_token, recruiter_token, client_user_token, seed_test_data):
        """Test role-based access to candidate list"""
        # Admin can access
        response = await client.get(
            "/api/jobs/job_001/candidates",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        # Recruiter can access
        response = await client.get(
            "/api/jobs/job_001/candidates", 
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        assert response.status_code == 200
        
        # Client user can access their own job
        response = await client.get(
            "/api/jobs/job_001/candidates",
            headers={"Authorization": f"Bearer {client_user_token}"}
        )
        assert response.status_code == 200
        
        print("✓ All roles can view candidate list for authorized jobs")


class TestAddCandidateFlow:
    """Test Add Candidate workflows (manual and CV upload)"""
    
    @pytest.mark.asyncio
    async def test_manual_candidate_creation_recruiter(self, client, recruiter_token, seed_test_data, mock_ai_functions):
        """Test manual candidate creation by recruiter"""
        candidate_data = {
            "job_id": "job_001",
            "name": "Emma Wilson",
            "current_role": "Full Stack Developer",
            "email": "emma.wilson@email.com",
            "phone": "555-0199",
            "skills": ["Python", "React", "PostgreSQL"],
            "experience": [
                {
                    "company": "InnovateTech",
                    "role": "Full Stack Developer",
                    "duration": "2022-2024",
                    "achievements": ["Built e-commerce platform", "Improved performance by 40%"]
                }
            ],
            "education": [
                {
                    "degree": "MS Computer Science", 
                    "institution": "UC Berkeley",
                    "year": "2022"
                }
            ],
            "summary": "Passionate full-stack developer with expertise in modern web technologies"
        }
        
        response = await client.post(
            "/api/candidates",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json=candidate_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify candidate creation
        assert result["name"] == "Emma Wilson"
        assert result["job_id"] == "job_001"
        assert result["status"] == "NEW"
        assert "candidate_id" in result
        assert result["ai_story"] is not None
        assert result["ai_story"]["fit_score"] == 92  # From mock
        
        print("✓ Manual candidate creation by recruiter successful with AI story generation")
    
    @pytest.mark.asyncio
    async def test_manual_candidate_creation_admin(self, client, admin_token, seed_test_data, mock_ai_functions):
        """Test manual candidate creation by admin"""
        candidate_data = {
            "job_id": "job_001",
            "name": "David Chen",
            "skills": ["Python", "Django", "React"]
        }
        
        response = await client.post(
            "/api/candidates",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=candidate_data
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "David Chen"
        
        print("✓ Manual candidate creation by admin successful")
    
    @pytest.mark.asyncio
    async def test_manual_candidate_creation_client_forbidden(self, client, client_user_token, seed_test_data):
        """Test client user cannot create candidates manually"""
        candidate_data = {
            "job_id": "job_001",
            "name": "Test Candidate",
            "skills": ["Python"]
        }
        
        response = await client.post(
            "/api/candidates",
            headers={"Authorization": f"Bearer {client_user_token}"},
            json=candidate_data
        )
        
        assert response.status_code == 403
        assert "Only admin/recruiter can create candidates" in response.json()["detail"]
        
        print("✓ Client user correctly forbidden from creating candidates")
    
    @pytest.mark.asyncio
    async def test_cv_upload_workflow_recruiter(self, client, recruiter_token, seed_test_data, mock_ai_functions):
        """Test CV upload workflow by recruiter"""
        # Create mock CV file
        cv_content = b"""
        Sarah Johnson
        Senior Software Engineer
        
        Email: sarah.johnson@email.com
        Phone: 415-555-0123
        LinkedIn: https://linkedin.com/in/sarahjohnson
        
        EXPERIENCE:
        TechCorp Inc - Senior Software Engineer (2021-2024)
        - Led team of 5 developers
        - Reduced deployment time by 60%
        - Built microservices architecture
        
        SKILLS: Python, React, AWS, Docker, Kubernetes
        
        EDUCATION:
        Stanford University - BS Computer Science (2019)
        """
        
        files = {"file": ("sarah_johnson_resume.pdf", io.BytesIO(cv_content), "application/pdf")}
        data = {"job_id": "job_001"}
        
        response = await client.post(
            "/api/candidates/upload",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            data=data,
            files=files
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify AI parsing worked
        assert result["name"] == "Sarah Johnson"  # From mock
        assert result["current_role"] == "Senior Software Engineer"
        assert "Python" in result["skills"]
        assert "React" in result["skills"]
        assert result["cv_file_url"] is not None
        assert result["ai_story"] is not None
        assert result["ai_story"]["fit_score"] == 92
        
        print("✓ CV upload workflow successful with AI parsing and story generation")
    
    @pytest.mark.asyncio
    async def test_cv_upload_client_forbidden(self, client, client_user_token, seed_test_data):
        """Test client user cannot upload CVs"""
        cv_content = b"Test CV content"
        files = {"file": ("test.pdf", io.BytesIO(cv_content), "application/pdf")}
        data = {"job_id": "job_001"}
        
        response = await client.post(
            "/api/candidates/upload",
            headers={"Authorization": f"Bearer {client_user_token}"},
            data=data,
            files=files
        )
        
        assert response.status_code == 403
        assert "Only admin/recruiter can upload candidates" in response.json()["detail"]
        
        print("✓ Client user correctly forbidden from uploading CVs")
    
    @pytest.mark.asyncio
    async def test_candidate_creation_validation(self, client, recruiter_token, seed_test_data, mock_ai_functions):
        """Test form validation for candidate creation"""
        # Test missing required name field
        invalid_data = {
            "job_id": "job_001",
            "skills": ["Python"]
            # Missing required "name" field
        }
        
        response = await client.post(
            "/api/candidates",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json=invalid_data
        )
        
        assert response.status_code == 422  # Validation error
        
        # Test invalid job_id
        invalid_job_data = {
            "job_id": "nonexistent_job",
            "name": "Test Candidate",
            "skills": ["Python"]
        }
        
        response = await client.post(
            "/api/candidates",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json=invalid_job_data
        )
        
        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]
        
        print("✓ Form validation working correctly")


class TestCandidateDetailPage:
    """Test Candidate Detail Page functionality"""
    
    @pytest.mark.asyncio
    async def test_candidate_detail_loading(self, client, recruiter_token, seed_test_data):
        """Test loading candidate details with all sections"""
        # Create test candidate
        candidate_data = {
            "candidate_id": "cand_detail_001",
            "job_id": "job_001",
            "name": "Michael Rodriguez",
            "current_role": "Senior Backend Engineer",
            "email": "michael.rodriguez@email.com",
            "phone": "555-0156",
            "linkedin": "https://linkedin.com/in/michaelrodriguez",
            "skills": ["Python", "Django", "PostgreSQL", "Redis"],
            "experience": [
                {
                    "company": "DataFlow Systems",
                    "role": "Senior Backend Engineer",
                    "duration": "2020-2024",
                    "achievements": ["Designed scalable API architecture", "Optimized database queries"]
                }
            ],
            "education": [
                {
                    "degree": "MS Software Engineering",
                    "institution": "Carnegie Mellon",
                    "year": "2020"
                }
            ],
            "summary": "Backend specialist with expertise in high-performance systems",
            "cv_file_url": "/uploads/cvs/cand_detail_001.pdf",
            "cv_text_original": "Michael Rodriguez\nSenior Backend Engineer\nEmail: michael.rodriguez@email.com\nPhone: 555-0156",
            "cv_text_redacted": "Michael Rodriguez\nSenior Backend Engineer\nEmail: [EMAIL REDACTED]\nPhone: [PHONE REDACTED]",
            "ai_story": {
                "headline": "Senior Backend Engineer with 4+ years of scalable systems experience",
                "summary": "Michael brings deep expertise in Python and database optimization",
                "timeline": [
                    {
                        "year": "2020-2024",
                        "title": "Senior Backend Engineer", 
                        "company": "DataFlow Systems",
                        "achievement": "Designed scalable API architecture serving 1M+ requests/day"
                    }
                ],
                "skills": ["Python", "Django", "PostgreSQL", "Redis"],
                "fit_score": 88,
                "highlights": ["4+ years backend experience", "Database optimization expert", "Scalable architecture design"]
            },
            "status": "PIPELINE",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@arbeit.com"
        }
        
        await seed_test_data.candidates.insert_one(candidate_data)
        
        response = await client.get(
            "/api/candidates/cand_detail_001",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify all sections are present
        assert result["candidate_id"] == "cand_detail_001"
        assert result["name"] == "Michael Rodriguez"
        assert result["current_role"] == "Senior Backend Engineer"
        assert result["ai_story"]["fit_score"] == 88
        assert result["ai_story"]["headline"] is not None
        assert len(result["skills"]) > 0
        assert len(result["experience"]) > 0
        assert result["cv_file_url"] is not None
        
        print("✓ Candidate detail page loads with all sections (header, AI story, resume, CV viewer)")
    
    @pytest.mark.asyncio
    async def test_ai_story_regeneration_recruiter(self, client, recruiter_token, seed_test_data, mock_ai_functions):
        """Test AI story regeneration by recruiter"""
        # Create candidate with existing story
        await seed_test_data.candidates.insert_one({
            "candidate_id": "cand_regen_001",
            "job_id": "job_001",
            "name": "Lisa Park",
            "skills": ["Python", "React"],
            "experience": [],
            "education": [],
            "ai_story": {
                "headline": "Old headline",
                "summary": "Old summary",
                "timeline": [],
                "skills": [],
                "fit_score": 50,
                "highlights": []
            },
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@arbeit.com"
        })
        
        response = await client.post(
            "/api/candidates/cand_regen_001/regenerate-story",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify story was regenerated (using mock data)
        assert result["ai_story"]["fit_score"] == 92  # From mock
        assert result["ai_story"]["headline"] != "Old headline"
        
        print("✓ AI story regeneration by recruiter successful")
    
    @pytest.mark.asyncio
    async def test_ai_story_regeneration_client_forbidden(self, client, client_user_token, seed_test_data):
        """Test client user cannot regenerate AI story"""
        await seed_test_data.candidates.insert_one({
            "candidate_id": "cand_client_regen",
            "job_id": "job_001",
            "name": "Test Candidate",
            "skills": [],
            "experience": [],
            "education": [],
            "ai_story": {},
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@arbeit.com"
        })
        
        response = await client.post(
            "/api/candidates/cand_client_regen/regenerate-story",
            headers={"Authorization": f"Bearer {client_user_token}"}
        )
        
        assert response.status_code == 403
        assert "Only admin/recruiter can regenerate stories" in response.json()["detail"]
        
        print("✓ Client user correctly forbidden from regenerating AI stories")


class TestCandidateResumeEditing:
    """Test Candidate Resume Editing functionality"""
    
    @pytest.mark.asyncio
    async def test_resume_edit_recruiter(self, client, recruiter_token, seed_test_data):
        """Test recruiter can edit resume fields"""
        # Create candidate
        await seed_test_data.candidates.insert_one({
            "candidate_id": "cand_edit_001",
            "job_id": "job_001",
            "name": "Original Name",
            "current_role": "Original Role",
            "skills": ["Python"],
            "experience": [{"company": "OldCorp", "role": "Dev", "duration": "2020-2022"}],
            "education": [],
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@arbeit.com"
        })
        
        update_data = {
            "name": "Updated Name",
            "current_role": "Senior Software Engineer",
            "skills": ["Python", "React", "AWS"],
            "experience": [
                {
                    "company": "NewCorp",
                    "role": "Senior Engineer", 
                    "duration": "2022-2024",
                    "achievements": ["Led migration project"]
                }
            ]
        }
        
        response = await client.put(
            "/api/candidates/cand_edit_001",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json=update_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["name"] == "Updated Name"
        assert result["current_role"] == "Senior Software Engineer"
        assert "AWS" in result["skills"]
        assert result["experience"][0]["company"] == "NewCorp"
        
        print("✓ Recruiter can edit all resume fields")
    
    @pytest.mark.asyncio
    async def test_resume_edit_client_readonly(self, client, client_user_token, seed_test_data):
        """Test client user cannot edit resume fields (read-only)"""
        await seed_test_data.candidates.insert_one({
            "candidate_id": "cand_readonly_001",
            "job_id": "job_001",
            "name": "Readonly Test",
            "skills": ["Python"],
            "experience": [],
            "education": [],
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@arbeit.com"
        })
        
        # Try to update name (should fail)
        response = await client.put(
            "/api/candidates/cand_readonly_001",
            headers={"Authorization": f"Bearer {client_user_token}"},
            json={"name": "Hacked Name"}
        )
        
        assert response.status_code == 403
        assert "can only update status" in response.json()["detail"]
        
        print("✓ Client user correctly restricted from editing resume fields")


class TestCandidateCVViewer:
    """Test Candidate CV Viewer functionality"""
    
    @pytest.mark.asyncio
    async def test_cv_viewer_full_access_recruiter(self, client, recruiter_token, seed_test_data):
        """Test recruiter gets full CV access"""
        cv_original = """
        John Smith
        Software Engineer
        
        Contact Information:
        Email: john.smith@email.com
        Phone: 555-123-4567
        LinkedIn: https://linkedin.com/in/johnsmith
        
        Experience and achievements...
        """
        
        await seed_test_data.candidates.insert_one({
            "candidate_id": "cand_cv_001",
            "job_id": "job_001",
            "name": "John Smith",
            "skills": [],
            "experience": [],
            "education": [],
            "cv_text_original": cv_original,
            "cv_text_redacted": redact_text(cv_original),
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@arbeit.com"
        })
        
        response = await client.get(
            "/api/candidates/cand_cv_001/cv?redacted=false",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["is_redacted"] is False
        assert "john.smith@email.com" in result["cv_text"]
        assert "555-123-4567" in result["cv_text"]
        assert "linkedin.com/in/johnsmith" in result["cv_text"]
        
        print("✓ Recruiter gets full CV access with contact information")
    
    @pytest.mark.asyncio
    async def test_cv_viewer_redacted_client(self, client, client_user_token, seed_test_data):
        """Test client user gets redacted CV"""
        cv_original = """
        Jane Doe
        Senior Developer
        
        Email: jane.doe@email.com
        Phone: 555-987-6543
        LinkedIn: https://linkedin.com/in/janedoe
        Personal website: https://janedoe.dev
        
        Technical skills and experience...
        """
        
        await seed_test_data.candidates.insert_one({
            "candidate_id": "cand_redacted_001",
            "job_id": "job_001", 
            "name": "Jane Doe",
            "skills": [],
            "experience": [],
            "education": [],
            "cv_text_original": cv_original,
            "cv_text_redacted": redact_text(cv_original),
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@arbeit.com"
        })
        
        response = await client.get(
            "/api/candidates/cand_redacted_001/cv?redacted=true",
            headers={"Authorization": f"Bearer {client_user_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["is_redacted"] is True
        assert "jane.doe@email.com" not in result["cv_text"]
        assert "555-987-6543" not in result["cv_text"]
        assert "linkedin.com/in/janedoe" not in result["cv_text"]
        assert "[EMAIL REDACTED]" in result["cv_text"]
        assert "[PHONE REDACTED]" in result["cv_text"]
        assert "[LINKEDIN REDACTED]" in result["cv_text"]
        
        print("✓ Client user gets properly redacted CV with PII masked")
    
    @pytest.mark.asyncio
    async def test_cv_client_always_redacted(self, client, client_user_token, seed_test_data):
        """Test client user always gets redacted CV even when requesting original"""
        cv_text = "Contact: test@email.com or call 555-1234"
        
        await seed_test_data.candidates.insert_one({
            "candidate_id": "cand_force_redact",
            "job_id": "job_001",
            "name": "Force Redact Test",
            "skills": [],
            "experience": [],
            "education": [],
            "cv_text_original": cv_text,
            "cv_text_redacted": redact_text(cv_text),
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@arbeit.com"
        })
        
        # Client requests original but should get redacted
        response = await client.get(
            "/api/candidates/cand_force_redact/cv?redacted=false",
            headers={"Authorization": f"Bearer {client_user_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["is_redacted"] is True  # Forced to redacted
        assert "test@email.com" not in result["cv_text"]
        assert "[EMAIL REDACTED]" in result["cv_text"]
        
        print("✓ Client user always gets redacted CV regardless of request parameter")


class TestStatusUpdates:
    """Test Candidate Status Update functionality"""
    
    @pytest.mark.asyncio
    async def test_status_update_flow(self, client, recruiter_token, seed_test_data):
        """Test complete status update flow: NEW → PIPELINE → APPROVED → REJECTED"""
        # Create candidate
        await seed_test_data.candidates.insert_one({
            "candidate_id": "cand_status_001",
            "job_id": "job_001",
            "name": "Status Test Candidate",
            "skills": ["Python"],
            "experience": [],
            "education": [],
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@arbeit.com"
        })
        
        # NEW → PIPELINE
        response = await client.put(
            "/api/candidates/cand_status_001",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json={"status": "PIPELINE"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "PIPELINE"
        
        # PIPELINE → APPROVED
        response = await client.put(
            "/api/candidates/cand_status_001",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json={"status": "APPROVED"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "APPROVED"
        
        # APPROVED → REJECTED (edge case)
        response = await client.put(
            "/api/candidates/cand_status_001",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json={"status": "REJECTED"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "REJECTED"
        
        print("✓ Complete status update flow working correctly")
    
    @pytest.mark.asyncio
    async def test_status_update_client_user(self, client, client_user_token, seed_test_data):
        """Test client user can update candidate status"""
        await seed_test_data.candidates.insert_one({
            "candidate_id": "cand_client_status",
            "job_id": "job_001",
            "name": "Client Status Test",
            "skills": [],
            "experience": [],
            "education": [],
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@arbeit.com"
        })
        
        response = await client.put(
            "/api/candidates/cand_client_status",
            headers={"Authorization": f"Bearer {client_user_token}"},
            json={"status": "APPROVED"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "APPROVED"
        
        print("✓ Client user can update candidate status")


class TestMultiTenantIsolation:
    """Test Multi-Tenant and Tenant Isolation"""
    
    @pytest.mark.asyncio
    async def test_tenant_isolation_setup(self, client, clean_db):
        """Set up multi-tenant test scenario"""
        # Create second client
        await clean_db.clients.insert_one({
            "client_id": "client_002",
            "company_name": "Beta Corp",
            "status": "active",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "admin@arbeit.com"
        })
        
        # Create second client user
        await clean_db.users.insert_one({
            "email": "client2@beta.com",
            "name": "Beta Client User",
            "role": "client_user",
            "client_id": "client_002",
            "password_hash": hash_password("client123"),
            "created_at": "2025-01-01T00:00:00"
        })
        
        # Create job for second client
        await clean_db.jobs.insert_one({
            "job_id": "job_002",
            "client_id": "client_002",
            "title": "Data Scientist",
            "location": "New York, NY",
            "employment_type": "Full-time",
            "experience_range": {"min_years": 2, "max_years": 6},
            "work_model": "Remote",
            "required_skills": ["Python", "Machine Learning"],
            "description": "Data science role",
            "status": "Active",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "admin@arbeit.com"
        })
        
        # Create candidates for both clients
        await clean_db.candidates.insert_one({
            "candidate_id": "cand_client1",
            "job_id": "job_001",  # Client 1 job
            "name": "Client 1 Candidate",
            "skills": ["Python"],
            "experience": [],
            "education": [],
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@arbeit.com"
        })
        
        await clean_db.candidates.insert_one({
            "candidate_id": "cand_client2",
            "job_id": "job_002",  # Client 2 job
            "name": "Client 2 Candidate",
            "skills": ["Python"],
            "experience": [],
            "education": [],
            "status": "NEW",
            "created_at": "2025-01-01T00:00:00",
            "created_by": "recruiter@arbeit.com"
        })
        
        yield clean_db
    
    @pytest.mark.asyncio
    async def test_client_user_isolation(self, client, test_tenant_isolation_setup):
        """Test client user can only see their own candidates"""
        # Login as client 1 user
        response = await client.post("/api/auth/login", json={
            "email": "client@acme.com",
            "password": "client123"
        })
        client1_token = response.json()["access_token"]
        
        # Login as client 2 user
        response = await client.post("/api/auth/login", json={
            "email": "client2@beta.com",
            "password": "client123"
        })
        client2_token = response.json()["access_token"]
        
        # Client 1 can access their job candidates
        response = await client.get(
            "/api/jobs/job_001/candidates",
            headers={"Authorization": f"Bearer {client1_token}"}
        )
        assert response.status_code == 200
        candidates = response.json()
        assert all(c["name"] == "Client 1 Candidate" for c in candidates)
        
        # Client 1 cannot access client 2's job candidates
        response = await client.get(
            "/api/jobs/job_002/candidates",
            headers={"Authorization": f"Bearer {client1_token}"}
        )
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
        
        # Client 2 can access their job candidates
        response = await client.get(
            "/api/jobs/job_002/candidates",
            headers={"Authorization": f"Bearer {client2_token}"}
        )
        assert response.status_code == 200
        
        # Client 2 cannot access client 1's candidates
        response = await client.get(
            "/api/candidates/cand_client1",
            headers={"Authorization": f"Bearer {client2_token}"}
        )
        assert response.status_code == 403
        
        print("✓ Tenant isolation working correctly - clients can only access their own data")
    
    @pytest.mark.asyncio
    async def test_admin_recruiter_cross_tenant_access(self, client, test_tenant_isolation_setup):
        """Test admin/recruiter can see candidates across all clients"""
        # Login as admin
        response = await client.post("/api/auth/login", json={
            "email": "admin@arbeit.com",
            "password": "admin123"
        })
        admin_token = response.json()["access_token"]
        
        # Admin can access both client jobs
        response = await client.get(
            "/api/jobs/job_001/candidates",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        response = await client.get(
            "/api/jobs/job_002/candidates",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        # Admin can access candidates from both clients
        response = await client.get(
            "/api/candidates/cand_client1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        response = await client.get(
            "/api/candidates/cand_client2",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        print("✓ Admin/recruiter can access candidates across all clients")


class TestIntegrationScenarios:
    """Test Integration Scenarios"""
    
    @pytest.mark.asyncio
    async def test_full_candidate_lifecycle(self, client, recruiter_token, client_user_token, seed_test_data, mock_ai_functions):
        """Test complete flow: Create job → Add candidate → View candidate → Update status"""
        
        # 1. Create candidate (already have job from seed_test_data)
        candidate_data = {
            "job_id": "job_001",
            "name": "Integration Test Candidate",
            "current_role": "Software Engineer",
            "skills": ["Python", "React", "AWS"],
            "experience": [
                {
                    "company": "TechStart",
                    "role": "Software Engineer",
                    "duration": "2021-2024",
                    "achievements": ["Built scalable APIs", "Led frontend migration"]
                }
            ],
            "education": [
                {
                    "degree": "BS Computer Science",
                    "institution": "MIT",
                    "year": "2021"
                }
            ],
            "summary": "Full-stack engineer with startup experience"
        }
        
        # Create candidate
        response = await client.post(
            "/api/candidates",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json=candidate_data
        )
        assert response.status_code == 200
        candidate = response.json()
        candidate_id = candidate["candidate_id"]
        
        # 2. View candidate details
        response = await client.get(
            f"/api/candidates/{candidate_id}",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        assert response.status_code == 200
        details = response.json()
        assert details["name"] == "Integration Test Candidate"
        assert details["ai_story"]["fit_score"] == 92  # From mock
        
        # 3. Client user views candidate (should work)
        response = await client.get(
            f"/api/candidates/{candidate_id}",
            headers={"Authorization": f"Bearer {client_user_token}"}
        )
        assert response.status_code == 200
        
        # 4. Update status progression
        statuses = ["PIPELINE", "APPROVED"]
        for status in statuses:
            response = await client.put(
                f"/api/candidates/{candidate_id}",
                headers={"Authorization": f"Bearer {client_user_token}"},
                json={"status": status}
            )
            assert response.status_code == 200
            assert response.json()["status"] == status
        
        # 5. View updated candidate
        response = await client.get(
            f"/api/candidates/{candidate_id}",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        assert response.status_code == 200
        final_candidate = response.json()
        assert final_candidate["status"] == "APPROVED"
        
        print("✓ Complete candidate lifecycle integration test successful")
    
    @pytest.mark.asyncio
    async def test_ai_integration_flow(self, client, recruiter_token, seed_test_data, mock_ai_functions):
        """Test AI integration: Candidate creation triggers AI story generation"""
        
        # Test manual creation triggers AI story
        candidate_data = {
            "job_id": "job_001",
            "name": "AI Test Candidate",
            "skills": ["Python", "Machine Learning"],
            "experience": [
                {
                    "company": "AI Corp",
                    "role": "ML Engineer",
                    "duration": "2022-2024",
                    "achievements": ["Built recommendation system"]
                }
            ]
        }
        
        response = await client.post(
            "/api/candidates",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json=candidate_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify AI story was generated
        assert result["ai_story"] is not None
        assert result["ai_story"]["fit_score"] == 92
        assert result["ai_story"]["headline"] is not None
        assert len(result["ai_story"]["highlights"]) > 0
        
        # Test story regeneration
        candidate_id = result["candidate_id"]
        response = await client.post(
            f"/api/candidates/{candidate_id}/regenerate-story",
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )
        
        assert response.status_code == 200
        regenerated = response.json()
        assert regenerated["ai_story"]["fit_score"] == 92  # From mock
        
        print("✓ AI integration working - story generation and regeneration successful")


# Fixture for tenant isolation tests
@pytest_asyncio.fixture
async def test_tenant_isolation_setup(clean_db):
    """Setup for tenant isolation tests"""
    # Create clients
    await clean_db.clients.insert_one({
        "client_id": "client_001",
        "company_name": "Acme Corporation",
        "status": "active",
        "created_at": "2025-01-01T00:00:00"
    })
    
    await clean_db.clients.insert_one({
        "client_id": "client_002",
        "company_name": "Beta Corp",
        "status": "active",
        "created_at": "2025-01-01T00:00:00"
    })
    
    # Create users
    users = [
        {
            "email": "admin@arbeit.com",
            "name": "Admin User",
            "role": "admin",
            "client_id": None,
            "password_hash": hash_password("admin123"),
            "created_at": "2025-01-01T00:00:00"
        },
        {
            "email": "client@acme.com",
            "name": "Acme Client",
            "role": "client_user",
            "client_id": "client_001",
            "password_hash": hash_password("client123"),
            "created_at": "2025-01-01T00:00:00"
        },
        {
            "email": "client2@beta.com",
            "name": "Beta Client",
            "role": "client_user",
            "client_id": "client_002",
            "password_hash": hash_password("client123"),
            "created_at": "2025-01-01T00:00:00"
        }
    ]
    
    for user in users:
        await clean_db.users.insert_one(user)
    
    # Create jobs
    await clean_db.jobs.insert_one({
        "job_id": "job_001",
        "client_id": "client_001",
        "title": "Software Engineer",
        "location": "SF",
        "employment_type": "Full-time",
        "experience_range": {"min_years": 2, "max_years": 5},
        "work_model": "Hybrid",
        "required_skills": ["Python"],
        "description": "Job 1",
        "status": "Active",
        "created_at": "2025-01-01T00:00:00",
        "created_by": "admin@arbeit.com"
    })
    
    await clean_db.jobs.insert_one({
        "job_id": "job_002",
        "client_id": "client_002",
        "title": "Data Scientist",
        "location": "NYC",
        "employment_type": "Full-time",
        "experience_range": {"min_years": 3, "max_years": 7},
        "work_model": "Remote",
        "required_skills": ["Python", "ML"],
        "description": "Job 2",
        "status": "Active",
        "created_at": "2025-01-01T00:00:00",
        "created_by": "admin@arbeit.com"
    })
    
    # Create candidates
    await clean_db.candidates.insert_one({
        "candidate_id": "cand_client1",
        "job_id": "job_001",
        "name": "Client 1 Candidate",
        "skills": ["Python"],
        "experience": [],
        "education": [],
        "status": "NEW",
        "created_at": "2025-01-01T00:00:00",
        "created_by": "recruiter@arbeit.com"
    })
    
    await clean_db.candidates.insert_one({
        "candidate_id": "cand_client2",
        "job_id": "job_002",
        "name": "Client 2 Candidate",
        "skills": ["Python"],
        "experience": [],
        "education": [],
        "status": "NEW",
        "created_at": "2025-01-01T00:00:00",
        "created_by": "recruiter@arbeit.com"
    })
    
    yield clean_db


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])