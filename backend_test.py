#!/usr/bin/env python3
"""
Phase 4b: Candidate Management - Backend API Testing
Direct API testing using requests to test all candidate management endpoints.
"""

import requests
import json
import io
import os
from pathlib import Path

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://hirematch-52.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class CandidateManagementTester:
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
            {"email": "admin@arbeit.com", "password": "admin123", "role": "admin"},
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
    
    def get_test_job(self):
        """Get or create a test job for candidate testing"""
        print("\n🔧 Setting up test job...")
        
        try:
            # Try to get existing jobs first
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(f"{API_BASE}/jobs", headers=headers)
            
            if response.status_code == 200:
                jobs = response.json()
                if jobs:
                    job = jobs[0]
                    self.test_data['job_id'] = job['job_id']
                    print(f"✅ Using existing job: {job['title']} ({job['job_id']})")
                    return True
            
            # Create a new job if none exist
            job_data = {
                "title": "Senior Software Engineer - Test",
                "location": "San Francisco, CA",
                "employment_type": "Full-time",
                "experience_range": {"min_years": 3, "max_years": 8},
                "salary_range": {"min_amount": 120000, "max_amount": 180000, "currency": "USD"},
                "work_model": "Hybrid",
                "required_skills": ["Python", "React", "AWS", "Docker"],
                "description": "Test job for candidate management testing",
                "status": "Active",
                "client_id": "client_001"  # Assuming this exists from seed data
            }
            
            response = requests.post(f"{API_BASE}/jobs", headers=headers, json=job_data)
            
            if response.status_code == 200:
                job = response.json()
                self.test_data['job_id'] = job['job_id']
                print(f"✅ Created test job: {job['job_id']}")
                return True
            else:
                print(f"❌ Failed to create test job: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error setting up test job: {str(e)}")
            return False
    
    def test_candidate_list_empty(self):
        """Test empty candidate list"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(f"{API_BASE}/jobs/{self.test_data['job_id']}/candidates", headers=headers)
            
            success = response.status_code == 200 and response.json() == []
            self.log_result("Empty candidate list", success, 
                          f"Expected 200 and empty list, got {response.status_code}")
        except Exception as e:
            self.log_result("Empty candidate list", False, str(e))
    
    def test_manual_candidate_creation_recruiter(self):
        """Test manual candidate creation by recruiter"""
        try:
            candidate_data = {
                "job_id": self.test_data['job_id'],
                "name": "Sarah Johnson",
                "current_role": "Senior Software Engineer",
                "email": "sarah.johnson@email.com",
                "phone": "415-555-0123",
                "skills": ["Python", "React", "AWS", "Docker"],
                "experience": [
                    {
                        "company": "TechCorp Inc",
                        "role": "Senior Software Engineer",
                        "duration": "2021-2024",
                        "achievements": ["Led team of 5 developers", "Reduced deployment time by 60%"]
                    }
                ],
                "education": [
                    {
                        "degree": "BS Computer Science",
                        "institution": "Stanford University",
                        "year": "2019"
                    }
                ],
                "summary": "Experienced software engineer with 5+ years building scalable web applications"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.post(f"{API_BASE}/candidates", headers=headers, json=candidate_data)
            
            if response.status_code == 200:
                result = response.json()
                self.test_data['candidate_id'] = result['candidate_id']
                
                # Verify required fields (AI story may fail due to API key issues)
                success = (
                    result['name'] == "Sarah Johnson" and
                    result['job_id'] == self.test_data['job_id'] and
                    result['status'] == "NEW" and
                    'candidate_id' in result
                )
                self.log_result("Manual candidate creation (recruiter)", success,
                              "Missing required fields")
            elif response.status_code == 500:
                # Check if it's an AI-related error
                error_text = response.text.lower()
                if "llm" in error_text or "api key" in error_text or "openai" in error_text:
                    self.log_result("Manual candidate creation (recruiter)", False,
                                  "AI integration error - LLM API key invalid")
                else:
                    self.log_result("Manual candidate creation (recruiter)", False,
                                  f"Status {response.status_code}: {response.text}")
            else:
                self.log_result("Manual candidate creation (recruiter)", False,
                              f"Status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Manual candidate creation (recruiter)", False, str(e))
    
    def test_manual_candidate_creation_client_forbidden(self):
        """Test client user cannot create candidates manually"""
        try:
            candidate_data = {
                "job_id": self.test_data['job_id'],
                "name": "Test Candidate",
                "skills": ["Python"]
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
            response = requests.post(f"{API_BASE}/candidates", headers=headers, json=candidate_data)
            
            success = response.status_code == 403
            self.log_result("Manual candidate creation forbidden (client)", success,
                          f"Expected 403, got {response.status_code}")
                          
        except Exception as e:
            self.log_result("Manual candidate creation forbidden (client)", False, str(e))
    
    def test_cv_upload_workflow_recruiter(self):
        """Test CV upload workflow by recruiter"""
        try:
            # Create mock CV file content
            cv_content = """
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
            """.strip()
            
            files = {
                'file': ('sarah_johnson_resume.pdf', io.BytesIO(cv_content.encode()), 'application/pdf')
            }
            data = {'job_id': self.test_data['job_id']}
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            
            response = requests.post(f"{API_BASE}/candidates/upload", headers=headers, data=data, files=files)
            
            if response.status_code == 200:
                result = response.json()
                self.test_data['uploaded_candidate_id'] = result['candidate_id']
                
                success = (
                    'candidate_id' in result and
                    result.get('cv_file_url') is not None and
                    result.get('ai_story') is not None and
                    result['status'] == "NEW"
                )
                self.log_result("CV upload workflow (recruiter)", success,
                              "Missing CV URL, AI story, or incorrect status")
            else:
                self.log_result("CV upload workflow (recruiter)", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("CV upload workflow (recruiter)", False, str(e))
    
    def test_cv_upload_client_forbidden(self):
        """Test client user cannot upload CVs"""
        try:
            cv_content = b"Test CV content"
            files = {'file': ('test.pdf', io.BytesIO(cv_content), 'application/pdf')}
            data = {'job_id': self.test_data['job_id']}
            headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
            
            response = requests.post(f"{API_BASE}/candidates/upload", headers=headers, data=data, files=files)
            
            success = response.status_code == 403
            self.log_result("CV upload forbidden (client)", success,
                          f"Expected 403, got {response.status_code}")
                          
        except Exception as e:
            self.log_result("CV upload forbidden (client)", False, str(e))
    
    def test_candidate_detail_loading(self):
        """Test loading candidate details"""
        if 'candidate_id' not in self.test_data:
            self.log_result("Candidate detail loading", False, "No candidate ID available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(f"{API_BASE}/candidates/{self.test_data['candidate_id']}", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                success = (
                    result['candidate_id'] == self.test_data['candidate_id'] and
                    'name' in result and
                    'ai_story' in result and
                    'skills' in result and
                    'experience' in result
                )
                self.log_result("Candidate detail loading", success,
                              "Missing required candidate fields")
            else:
                self.log_result("Candidate detail loading", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Candidate detail loading", False, str(e))
    
    def test_ai_story_regeneration_recruiter(self):
        """Test AI story regeneration by recruiter"""
        if 'candidate_id' not in self.test_data:
            self.log_result("AI story regeneration (recruiter)", False, "No candidate ID available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.post(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/regenerate-story", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('ai_story') is not None
                self.log_result("AI story regeneration (recruiter)", success,
                              "AI story not present in response")
            else:
                self.log_result("AI story regeneration (recruiter)", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("AI story regeneration (recruiter)", False, str(e))
    
    def test_ai_story_regeneration_client_forbidden(self):
        """Test client user cannot regenerate AI story"""
        if 'candidate_id' not in self.test_data:
            self.log_result("AI story regeneration forbidden (client)", False, "No candidate ID available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
            response = requests.post(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/regenerate-story", headers=headers)
            
            success = response.status_code == 403
            self.log_result("AI story regeneration forbidden (client)", success,
                          f"Expected 403, got {response.status_code}")
                          
        except Exception as e:
            self.log_result("AI story regeneration forbidden (client)", False, str(e))
    
    def test_resume_editing_recruiter(self):
        """Test recruiter can edit resume fields"""
        if 'candidate_id' not in self.test_data:
            self.log_result("Resume editing (recruiter)", False, "No candidate ID available")
            return
            
        try:
            update_data = {
                "name": "Sarah Johnson Updated",
                "current_role": "Principal Software Engineer",
                "skills": ["Python", "React", "AWS", "Docker", "Kubernetes"]
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.put(f"{API_BASE}/candidates/{self.test_data['candidate_id']}", 
                                  headers=headers, json=update_data)
            
            if response.status_code == 200:
                result = response.json()
                success = (
                    result['name'] == "Sarah Johnson Updated" and
                    result['current_role'] == "Principal Software Engineer" and
                    "Kubernetes" in result['skills']
                )
                self.log_result("Resume editing (recruiter)", success,
                              "Updated fields not reflected in response")
            else:
                self.log_result("Resume editing (recruiter)", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Resume editing (recruiter)", False, str(e))
    
    def test_resume_editing_client_readonly(self):
        """Test client user cannot edit resume fields"""
        if 'candidate_id' not in self.test_data:
            self.log_result("Resume editing forbidden (client)", False, "No candidate ID available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
            response = requests.put(f"{API_BASE}/candidates/{self.test_data['candidate_id']}", 
                                  headers=headers, json={"name": "Hacked Name"})
            
            success = response.status_code == 403
            self.log_result("Resume editing forbidden (client)", success,
                          f"Expected 403, got {response.status_code}")
                          
        except Exception as e:
            self.log_result("Resume editing forbidden (client)", False, str(e))
    
    def test_cv_viewer_full_access_recruiter(self):
        """Test recruiter gets full CV access"""
        if 'uploaded_candidate_id' not in self.test_data:
            self.log_result("CV viewer full access (recruiter)", False, "No uploaded candidate ID available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(f"{API_BASE}/candidates/{self.test_data['uploaded_candidate_id']}/cv?redacted=false", 
                                  headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                success = (
                    result.get('is_redacted') is False and
                    'cv_text' in result
                )
                self.log_result("CV viewer full access (recruiter)", success,
                              "CV not unredacted or missing CV text")
            else:
                self.log_result("CV viewer full access (recruiter)", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("CV viewer full access (recruiter)", False, str(e))
    
    def test_cv_viewer_redacted_client(self):
        """Test client user gets redacted CV"""
        if 'uploaded_candidate_id' not in self.test_data:
            self.log_result("CV viewer redacted (client)", False, "No uploaded candidate ID available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
            response = requests.get(f"{API_BASE}/candidates/{self.test_data['uploaded_candidate_id']}/cv?redacted=true", 
                                  headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                success = (
                    result.get('is_redacted') is True and
                    'cv_text' in result
                )
                self.log_result("CV viewer redacted (client)", success,
                              "CV not redacted or missing CV text")
            else:
                self.log_result("CV viewer redacted (client)", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("CV viewer redacted (client)", False, str(e))
    
    def test_status_updates(self):
        """Test candidate status updates"""
        if 'candidate_id' not in self.test_data:
            self.log_result("Status updates", False, "No candidate ID available")
            return
            
        try:
            statuses = ["PIPELINE", "APPROVED", "REJECTED"]
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            
            for status in statuses:
                response = requests.put(f"{API_BASE}/candidates/{self.test_data['candidate_id']}", 
                                      headers=headers, json={"status": status})
                
                if response.status_code != 200 or response.json().get('status') != status:
                    self.log_result("Status updates", False,
                                  f"Failed to update status to {status}")
                    return
            
            self.log_result("Status updates", True)
                              
        except Exception as e:
            self.log_result("Status updates", False, str(e))
    
    def test_status_update_client_user(self):
        """Test client user can update candidate status"""
        if 'candidate_id' not in self.test_data:
            self.log_result("Status update (client user)", False, "No candidate ID available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
            response = requests.put(f"{API_BASE}/candidates/{self.test_data['candidate_id']}", 
                                  headers=headers, json={"status": "APPROVED"})
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('status') == "APPROVED"
                self.log_result("Status update (client user)", success,
                              "Status not updated correctly")
            else:
                self.log_result("Status update (client user)", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Status update (client user)", False, str(e))
    
    def test_candidate_list_with_data(self):
        """Test candidate list shows created candidates"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(f"{API_BASE}/jobs/{self.test_data['job_id']}/candidates", headers=headers)
            
            if response.status_code == 200:
                candidates = response.json()
                success = len(candidates) > 0
                
                if success and candidates:
                    # Verify candidate fields
                    candidate = candidates[0]
                    success = (
                        'candidate_id' in candidate and
                        'name' in candidate and
                        'skills' in candidate and
                        'status' in candidate
                    )
                
                self.log_result("Candidate list with data", success,
                              "No candidates found or missing required fields")
            else:
                self.log_result("Candidate list with data", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Candidate list with data", False, str(e))
    
    def test_tenant_isolation(self):
        """Test basic tenant isolation"""
        try:
            # Client user should be able to access their job's candidates
            headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
            response = requests.get(f"{API_BASE}/jobs/{self.test_data['job_id']}/candidates", headers=headers)
            
            success = response.status_code == 200
            self.log_result("Tenant isolation (own job access)", success,
                          f"Expected 200, got {response.status_code}")
                          
        except Exception as e:
            self.log_result("Tenant isolation (own job access)", False, str(e))
    
    def run_all_tests(self):
        """Run all candidate management tests"""
        print("🚀 Starting Phase 4b Candidate Management Tests")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print("="*80)
        
        # Setup
        if not self.setup_test_users():
            print("❌ Failed to setup test users. Aborting tests.")
            return False
            
        if not self.get_test_job():
            print("❌ Failed to setup test job. Aborting tests.")
            return False
        
        print("\n📋 Running Candidate Management Tests...")
        print("-" * 50)
        
        # Run all tests
        self.test_candidate_list_empty()
        self.test_manual_candidate_creation_recruiter()
        self.test_manual_candidate_creation_client_forbidden()
        self.test_cv_upload_workflow_recruiter()
        self.test_cv_upload_client_forbidden()
        self.test_candidate_detail_loading()
        self.test_ai_story_regeneration_recruiter()
        self.test_ai_story_regeneration_client_forbidden()
        self.test_resume_editing_recruiter()
        self.test_resume_editing_client_readonly()
        self.test_cv_viewer_full_access_recruiter()
        self.test_cv_viewer_redacted_client()
        self.test_status_updates()
        self.test_status_update_client_user()
        self.test_candidate_list_with_data()
        self.test_tenant_isolation()
        
        # Print results
        print("\n" + "="*80)
        print("📊 TEST RESULTS SUMMARY")
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
        
        if success_rate >= 80:
            confidence = "HIGH"
        elif success_rate >= 60:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
            
        print(f"🎯 Confidence Rating: {confidence}")
        print("="*80)
        
        return self.results['failed'] == 0


if __name__ == "__main__":
    tester = CandidateManagementTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)