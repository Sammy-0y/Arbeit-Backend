#!/usr/bin/env python3
"""
Comprehensive Regression Testing for Job CRUD and CV Viewer
Testing the specific fixes mentioned in the review request:
1. Job CRUD Operations (especially job updates)
2. CV File Upload and Viewing (especially CV viewer)
3. Multi-tenant isolation
4. Regression tests
"""

import requests
import json
import io
import os
from pathlib import Path
import time

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://hirematch-52.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class JobCVRegressionTester:
    def __init__(self):
        self.tokens = {}
        self.test_data = {}
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def log_result(self, test_name, success, message=""):
        """Log test result"""
        self.results['total_tests'] += 1
        if success:
            self.results['passed'] += 1
            print(f"✅ {test_name}")
        else:
            self.results['failed'] += 1
            self.results['errors'].append(f"{test_name}: {message}")
            print(f"❌ {test_name}: {message}")
    
    def setup_test_users(self):
        """Setup and authenticate test users"""
        print("\n🔧 Setting up test users...")
        
        # Test credentials from review request
        users = [
            {"email": "recruiter@arbeit.com", "password": "recruiter123", "role": "recruiter"},
            {"email": "client@acme.com", "password": "client123", "role": "client_user"}
        ]
        
        for user in users:
            try:
                response = requests.post(f"{API_BASE}/auth/login", json={
                    "email": user["email"],
                    "password": user["password"]
                })
                
                if response.status_code == 200:
                    token = response.json()["access_token"]
                    self.tokens[user["role"]] = token
                    print(f"✅ Authenticated {user['role']}: {user['email']}")
                else:
                    print(f"❌ Failed to authenticate {user['role']}: {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ Error authenticating {user['role']}: {str(e)}")
                return False
        
        return True
    
    # ============ JOB CRUD TESTS ============
    
    def test_job_create_recruiter(self):
        """Test recruiter creates a new job with all fields populated"""
        try:
            job_data = {
                "title": "Senior Full Stack Developer",
                "location": "San Francisco, CA",
                "employment_type": "Full-time",
                "experience_range": {"min_years": 5, "max_years": 10},
                "salary_range": {"min_amount": 140000, "max_amount": 200000, "currency": "USD"},
                "work_model": "Hybrid",
                "required_skills": ["React", "Node.js", "TypeScript", "AWS", "PostgreSQL"],
                "description": "We are looking for a senior full stack developer to join our growing team. You will be responsible for building scalable web applications using modern technologies.",
                "status": "Active",
                "client_id": "client_001"  # Assuming this exists
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.post(f"{API_BASE}/jobs", headers=headers, json=job_data)
            
            if response.status_code == 200:
                result = response.json()
                self.test_data['job_id'] = result['job_id']
                
                # Verify all fields are saved correctly
                success = (
                    result['title'] == job_data['title'] and
                    result['location'] == job_data['location'] and
                    result['employment_type'] == job_data['employment_type'] and
                    result['experience_range']['min_years'] == 5 and
                    result['experience_range']['max_years'] == 10 and
                    result['salary_range']['min_amount'] == 140000 and
                    result['work_model'] == job_data['work_model'] and
                    len(result['required_skills']) == 5 and
                    result['description'] == job_data['description'] and
                    result['status'] == "Active" and
                    'job_id' in result
                )
                self.log_result("Job Create - Recruiter", success, 
                              "Missing or incorrect job fields in response")
            else:
                self.log_result("Job Create - Recruiter", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Job Create - Recruiter", False, str(e))
    
    def test_job_update_recruiter(self):
        """Test recruiter updates an existing job (PRIMARY TEST - was broken)"""
        if 'job_id' not in self.test_data:
            self.log_result("Job Update - Recruiter", False, "No job ID available")
            return
            
        try:
            update_data = {
                "title": "Senior Full Stack Developer - Updated",
                "description": "Updated job description with new requirements and responsibilities. We now require experience with microservices architecture."
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.put(f"{API_BASE}/jobs/{self.test_data['job_id']}", 
                                  headers=headers, json=update_data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify updates persist in database
                success = (
                    result['title'] == "Senior Full Stack Developer - Updated" and
                    "Updated job description" in result['description'] and
                    "microservices architecture" in result['description']
                )
                self.log_result("Job Update - Recruiter", success,
                              "Updated fields not reflected in response")
            else:
                self.log_result("Job Update - Recruiter", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Job Update - Recruiter", False, str(e))
    
    def test_job_update_client(self):
        """Test client updates their own job"""
        if 'job_id' not in self.test_data:
            self.log_result("Job Update - Client", False, "No job ID available")
            return
            
        try:
            update_data = {
                "description": "Client updated description: We are expanding our team and looking for passionate developers who want to make an impact."
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
            response = requests.put(f"{API_BASE}/jobs/{self.test_data['job_id']}", 
                                  headers=headers, json=update_data)
            
            if response.status_code == 200:
                result = response.json()
                success = "Client updated description" in result['description']
                self.log_result("Job Update - Client", success,
                              "Client update not reflected in response")
            else:
                self.log_result("Job Update - Client", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Job Update - Client", False, str(e))
    
    def test_job_view_recruiter(self):
        """Test recruiter can view job details"""
        if 'job_id' not in self.test_data:
            self.log_result("Job View - Recruiter", False, "No job ID available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(f"{API_BASE}/jobs/{self.test_data['job_id']}", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                success = (
                    'job_id' in result and
                    'title' in result and
                    'description' in result and
                    'required_skills' in result and
                    'experience_range' in result and
                    'salary_range' in result
                )
                self.log_result("Job View - Recruiter", success,
                              "Missing required job fields")
            else:
                self.log_result("Job View - Recruiter", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Job View - Recruiter", False, str(e))
    
    def test_job_view_client(self):
        """Test client can view job details"""
        if 'job_id' not in self.test_data:
            self.log_result("Job View - Client", False, "No job ID available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
            response = requests.get(f"{API_BASE}/jobs/{self.test_data['job_id']}", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                success = (
                    'job_id' in result and
                    'title' in result and
                    'description' in result
                )
                self.log_result("Job View - Client", success,
                              "Missing required job fields")
            else:
                self.log_result("Job View - Client", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Job View - Client", False, str(e))
    
    def test_multi_tenant_isolation_jobs(self):
        """Test Client A cannot view or update Client B's jobs"""
        try:
            # First create a job for a different client using recruiter token
            headers_recruiter = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            job_data = {
                "title": "Multi-Tenant Test Job",
                "location": "Seattle, WA",
                "employment_type": "Full-time",
                "experience_range": {"min_years": 3, "max_years": 7},
                "work_model": "Remote",
                "required_skills": ["Java", "Spring Boot"],
                "description": "Test job for multi-tenant isolation testing",
                "client_id": "client_48d287d9"  # Different client
            }
            
            create_response = requests.post(f"{API_BASE}/jobs", headers=headers_recruiter, json=job_data)
            
            if create_response.status_code == 200:
                other_job = create_response.json()
                other_job_id = other_job['job_id']
                
                # Now try to access this job with client@acme.com (client_001)
                headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
                response = requests.get(f"{API_BASE}/jobs/{other_job_id}", headers=headers)
                
                # Should get 403 or 404 (depending on implementation)
                success = response.status_code in [403, 404]
                self.log_result("Multi-tenant Isolation - Jobs", success,
                              f"Expected 403/404, got {response.status_code}")
            else:
                self.log_result("Multi-tenant Isolation - Jobs", False,
                              f"Failed to create test job: {create_response.status_code}")
                          
        except Exception as e:
            self.log_result("Multi-tenant Isolation - Jobs", False, str(e))
    
    def test_recruiter_view_all_jobs(self):
        """Test recruiters can view all jobs"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(f"{API_BASE}/jobs", headers=headers)
            
            if response.status_code == 200:
                jobs = response.json()
                success = isinstance(jobs, list)
                self.log_result("Recruiter View All Jobs", success,
                              "Jobs list not returned")
            else:
                self.log_result("Recruiter View All Jobs", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Recruiter View All Jobs", False, str(e))
    
    # ============ CV UPLOAD AND VIEWING TESTS ============
    
    def test_cv_upload_and_storage(self):
        """Test CV upload saves file and creates database entry"""
        if 'job_id' not in self.test_data:
            self.log_result("CV Upload and Storage", False, "No job ID available")
            return
            
        try:
            # Create realistic PDF content
            cv_content = """
John Smith
Senior Software Engineer

Email: john.smith@email.com
Phone: (555) 123-4567
LinkedIn: https://linkedin.com/in/johnsmith

PROFESSIONAL EXPERIENCE

TechCorp Inc - Senior Software Engineer (2020-2024)
• Led development of microservices architecture serving 1M+ users
• Reduced API response time by 40% through optimization
• Mentored 3 junior developers and conducted code reviews

StartupXYZ - Full Stack Developer (2018-2020)
• Built React/Node.js applications from scratch
• Implemented CI/CD pipelines using Docker and AWS
• Collaborated with product team on feature specifications

TECHNICAL SKILLS
Languages: JavaScript, Python, TypeScript, Java
Frameworks: React, Node.js, Express, Django
Cloud: AWS (EC2, S3, Lambda), Docker, Kubernetes
Databases: PostgreSQL, MongoDB, Redis

EDUCATION
Bachelor of Science in Computer Science
University of California, Berkeley (2018)
            """.strip()
            
            files = {
                'file': ('john_smith_resume.pdf', io.BytesIO(cv_content.encode()), 'application/pdf')
            }
            data = {'job_id': self.test_data['job_id']}
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            
            response = requests.post(f"{API_BASE}/candidates/upload", headers=headers, data=data, files=files)
            
            if response.status_code == 200:
                result = response.json()
                self.test_data['candidate_id'] = result['candidate_id']
                
                # Verify file is saved and cv_file_url starts with /api/uploads/
                success = (
                    'candidate_id' in result and
                    result.get('cv_file_url') is not None and
                    result['cv_file_url'].startswith('/api/uploads/') and
                    result['status'] == "NEW"
                )
                self.log_result("CV Upload and Storage", success,
                              "Missing CV URL or incorrect URL format")
            else:
                self.log_result("CV Upload and Storage", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("CV Upload and Storage", False, str(e))
    
    def test_cv_file_accessibility(self):
        """Test CV file is accessible via GET request"""
        if 'candidate_id' not in self.test_data:
            self.log_result("CV File Accessibility", False, "No candidate ID available")
            return
            
        try:
            # First get the candidate to get the CV URL
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(f"{API_BASE}/candidates/{self.test_data['candidate_id']}", headers=headers)
            
            if response.status_code == 200:
                candidate = response.json()
                cv_url = candidate.get('cv_file_url')
                
                if cv_url:
                    # Test direct file access
                    file_response = requests.get(f"{BACKEND_URL}{cv_url}")
                    
                    success = (
                        file_response.status_code == 200 and
                        file_response.headers.get('content-type') == 'application/pdf'
                    )
                    self.log_result("CV File Accessibility", success,
                                  f"File not accessible or wrong MIME type. Status: {file_response.status_code}, Content-Type: {file_response.headers.get('content-type')}")
                else:
                    self.log_result("CV File Accessibility", False, "No CV URL found")
            else:
                self.log_result("CV File Accessibility", False,
                              f"Failed to get candidate: {response.status_code}")
                              
        except Exception as e:
            self.log_result("CV File Accessibility", False, str(e))
    
    def test_cv_viewer_iframe_functionality(self):
        """Test CV viewer iframe loads correctly (PRIMARY TEST - was broken)"""
        if 'candidate_id' not in self.test_data:
            self.log_result("CV Viewer Iframe", False, "No candidate ID available")
            return
            
        try:
            # Get candidate details to verify CV viewer setup
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(f"{API_BASE}/candidates/{self.test_data['candidate_id']}", headers=headers)
            
            if response.status_code == 200:
                candidate = response.json()
                cv_url = candidate.get('cv_file_url')
                
                if cv_url:
                    # Verify iframe src would point to correct URL
                    expected_iframe_src = f"/api/uploads/{self.test_data['candidate_id']}.pdf"
                    
                    # Test the actual file endpoint
                    file_response = requests.get(f"{BACKEND_URL}{cv_url}")
                    
                    success = (
                        file_response.status_code == 200 and
                        cv_url.endswith('.pdf') and
                        cv_url.startswith('/api/uploads/')
                    )
                    self.log_result("CV Viewer Iframe", success,
                                  f"CV URL format incorrect or file not accessible")
                else:
                    self.log_result("CV Viewer Iframe", False, "No CV URL found")
            else:
                self.log_result("CV Viewer Iframe", False,
                              f"Failed to get candidate: {response.status_code}")
                              
        except Exception as e:
            self.log_result("CV Viewer Iframe", False, str(e))
    
    def test_cv_viewer_full_access_recruiter(self):
        """Test recruiter gets full CV access"""
        if 'candidate_id' not in self.test_data:
            self.log_result("CV Viewer Full Access - Recruiter", False, "No candidate ID available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/cv?redacted=false", 
                                  headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                cv_text = result.get('cv_text', '')
                
                # Verify unredacted content (should contain email and phone)
                success = (
                    result.get('is_redacted') is False and
                    'john.smith@email.com' in cv_text and
                    '(555) 123-4567' in cv_text and
                    'linkedin.com/in/johnsmith' in cv_text
                )
                self.log_result("CV Viewer Full Access - Recruiter", success,
                              "CV not unredacted or missing contact information")
            else:
                self.log_result("CV Viewer Full Access - Recruiter", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("CV Viewer Full Access - Recruiter", False, str(e))
    
    def test_cv_viewer_redacted_access_client(self):
        """Test client gets redacted CV view only"""
        if 'candidate_id' not in self.test_data:
            self.log_result("CV Viewer Redacted Access - Client", False, "No candidate ID available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
            response = requests.get(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/cv", 
                                  headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                cv_text = result.get('cv_text', '')
                
                # Verify redacted content (should NOT contain email and phone)
                success = (
                    result.get('is_redacted') is True and
                    '[EMAIL REDACTED]' in cv_text and
                    '[PHONE REDACTED]' in cv_text and
                    '[LINKEDIN REDACTED]' in cv_text and
                    'john.smith@email.com' not in cv_text
                )
                self.log_result("CV Viewer Redacted Access - Client", success,
                              "CV not properly redacted or contains PII")
            else:
                self.log_result("CV Viewer Redacted Access - Client", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("CV Viewer Redacted Access - Client", False, str(e))
    
    def test_cv_viewer_toggle_functionality(self):
        """Test toggle between Full and Redacted views for recruiter"""
        if 'candidate_id' not in self.test_data:
            self.log_result("CV Viewer Toggle", False, "No candidate ID available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            
            # Test full view
            full_response = requests.get(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/cv?redacted=false", 
                                       headers=headers)
            
            # Test redacted view
            redacted_response = requests.get(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/cv?redacted=true", 
                                           headers=headers)
            
            if full_response.status_code == 200 and redacted_response.status_code == 200:
                full_result = full_response.json()
                redacted_result = redacted_response.json()
                
                full_text = full_result.get('cv_text', '')
                redacted_text = redacted_result.get('cv_text', '')
                
                success = (
                    full_result.get('is_redacted') is False and
                    redacted_result.get('is_redacted') is True and
                    'john.smith@email.com' in full_text and
                    '[EMAIL REDACTED]' in redacted_text
                )
                self.log_result("CV Viewer Toggle", success,
                              "Toggle between full and redacted views not working")
            else:
                self.log_result("CV Viewer Toggle", False,
                              f"API calls failed: Full={full_response.status_code}, Redacted={redacted_response.status_code}")
                              
        except Exception as e:
            self.log_result("CV Viewer Toggle", False, str(e))
    
    # ============ REGRESSION TESTS ============
    
    def test_candidate_creation_still_works(self):
        """Regression test: Verify candidate creation still works"""
        if 'job_id' not in self.test_data:
            self.log_result("Regression - Candidate Creation", False, "No job ID available")
            return
            
        try:
            candidate_data = {
                "job_id": self.test_data['job_id'],
                "name": "Alice Johnson",
                "current_role": "Frontend Developer",
                "email": "alice.johnson@email.com",
                "phone": "555-987-6543",
                "skills": ["React", "TypeScript", "CSS", "JavaScript"],
                "experience": [
                    {
                        "company": "WebDev Co",
                        "role": "Frontend Developer",
                        "duration": "2022-2024",
                        "achievements": ["Built responsive web applications", "Improved page load speed by 30%"]
                    }
                ],
                "education": [
                    {
                        "degree": "BS Computer Science",
                        "institution": "Tech University",
                        "year": "2022"
                    }
                ],
                "summary": "Passionate frontend developer with expertise in modern web technologies"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.post(f"{API_BASE}/candidates", headers=headers, json=candidate_data)
            
            success = response.status_code == 200
            if success:
                result = response.json()
                success = 'candidate_id' in result and result['name'] == "Alice Johnson"
            
            self.log_result("Regression - Candidate Creation", success,
                          f"Status {response.status_code}: {response.text}" if not success else "")
                          
        except Exception as e:
            self.log_result("Regression - Candidate Creation", False, str(e))
    
    def test_ai_story_generation_not_affected(self):
        """Regression test: Verify AI story generation is not affected"""
        if 'candidate_id' not in self.test_data:
            self.log_result("Regression - AI Story Generation", False, "No candidate ID available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(f"{API_BASE}/candidates/{self.test_data['candidate_id']}", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                ai_story = result.get('ai_story')
                
                success = (
                    ai_story is not None and
                    'headline' in ai_story and
                    'summary' in ai_story and
                    'fit_score' in ai_story
                )
                self.log_result("Regression - AI Story Generation", success,
                              "AI story missing or incomplete")
            else:
                self.log_result("Regression - AI Story Generation", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Regression - AI Story Generation", False, str(e))
    
    def test_job_listing_and_filtering_works(self):
        """Regression test: Verify job listing and filtering works"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            
            # Test basic listing
            response = requests.get(f"{API_BASE}/jobs", headers=headers)
            
            if response.status_code == 200:
                jobs = response.json()
                
                # Test filtering by status
                active_response = requests.get(f"{API_BASE}/jobs?status=Active", headers=headers)
                
                success = (
                    isinstance(jobs, list) and
                    active_response.status_code == 200 and
                    isinstance(active_response.json(), list)
                )
                self.log_result("Regression - Job Listing and Filtering", success,
                              "Job listing or filtering not working")
            else:
                self.log_result("Regression - Job Listing and Filtering", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Regression - Job Listing and Filtering", False, str(e))
    
    def test_candidate_listing_for_jobs_works(self):
        """Regression test: Verify candidate listing for jobs works"""
        if 'job_id' not in self.test_data:
            self.log_result("Regression - Candidate Listing", False, "No job ID available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(f"{API_BASE}/jobs/{self.test_data['job_id']}/candidates", headers=headers)
            
            if response.status_code == 200:
                candidates = response.json()
                success = isinstance(candidates, list)
                self.log_result("Regression - Candidate Listing", success,
                              "Candidate listing not working")
            else:
                self.log_result("Regression - Candidate Listing", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Regression - Candidate Listing", False, str(e))
    
    def run_all_tests(self):
        """Run all Job CRUD and CV viewer regression tests"""
        print("🚀 Starting Job CRUD and CV Viewer Regression Tests")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print("="*80)
        
        # Setup
        if not self.setup_test_users():
            print("❌ Failed to setup test users. Aborting tests.")
            return False
        
        print("\n📋 Running Job CRUD Tests...")
        print("-" * 50)
        
        # Job CRUD Tests
        self.test_job_create_recruiter()
        self.test_job_update_recruiter()  # PRIMARY TEST - was broken
        self.test_job_update_client()
        self.test_job_view_recruiter()
        self.test_job_view_client()
        self.test_multi_tenant_isolation_jobs()
        self.test_recruiter_view_all_jobs()
        
        print("\n📋 Running CV Upload and Viewer Tests...")
        print("-" * 50)
        
        # CV Upload and Viewer Tests
        self.test_cv_upload_and_storage()
        self.test_cv_file_accessibility()
        self.test_cv_viewer_iframe_functionality()  # PRIMARY TEST - was broken
        self.test_cv_viewer_full_access_recruiter()
        self.test_cv_viewer_redacted_access_client()
        self.test_cv_viewer_toggle_functionality()
        
        print("\n📋 Running Regression Tests...")
        print("-" * 50)
        
        # Regression Tests
        self.test_candidate_creation_still_works()
        self.test_ai_story_generation_not_affected()
        self.test_job_listing_and_filtering_works()
        self.test_candidate_listing_for_jobs_works()
        
        # Print results
        print("\n" + "="*80)
        print("📊 JOB CRUD & CV VIEWER REGRESSION TEST RESULTS")
        print("="*80)
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        
        if self.results['failed'] > 0:
            print(f"\n🔍 FAILED TESTS:")
            for error in self.results['errors']:
                print(f"   • {error}")
        
        success_rate = (self.results['passed'] / self.results['total_tests']) * 100 if self.results['total_tests'] > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            confidence = "HIGH"
        elif success_rate >= 70:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
            
        print(f"🎯 Confidence Rating: {confidence}")
        
        # Summary of key fixes tested
        print(f"\n🔧 KEY FIXES TESTED:")
        print(f"   • Job Update Functionality (was broken, now fixed)")
        print(f"   • CV Viewer Iframe Loading (was broken, now fixed)")
        print(f"   • Multi-tenant Isolation")
        print(f"   • Regression Coverage")
        
        print("="*80)
        
        return self.results['failed'] == 0


if __name__ == "__main__":
    tester = JobCVRegressionTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)