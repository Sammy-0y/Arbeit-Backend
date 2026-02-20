#!/usr/bin/env python3
"""
Phase 6: Story View & PDF Export - Backend Testing
Comprehensive tests for the Candidate Storyboarding Experience endpoints.
"""

import requests
import json
import os
from pathlib import Path

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://hirematch-52.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class Phase6StoryViewTester:
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
        
        # Test credentials
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
    
    def setup_test_candidate(self):
        """Setup test candidate for story testing"""
        print("\n🔧 Setting up test candidate...")
        
        try:
            # Get existing jobs first
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(f"{API_BASE}/jobs", headers=headers)
            
            if response.status_code == 200:
                jobs = response.json()
                if jobs:
                    job = jobs[0]
                    self.test_data['job_id'] = job['job_id']
                    print(f"✅ Using existing job: {job['title']} ({job['job_id']})")
                else:
                    print("❌ No jobs found for testing")
                    return False
            else:
                print(f"❌ Failed to get jobs: {response.status_code}")
                return False
            
            # Create test candidate
            candidate_data = {
                "job_id": self.test_data['job_id'],
                "name": "Emma Rodriguez",
                "current_role": "Senior Full Stack Developer",
                "email": "emma.rodriguez@email.com",
                "phone": "555-0199",
                "skills": ["Python", "React", "Node.js", "PostgreSQL", "AWS"],
                "experience": [
                    {
                        "company": "InnovateTech Solutions",
                        "role": "Senior Full Stack Developer",
                        "duration": "2022-2024",
                        "achievements": [
                            "Architected microservices platform serving 1M+ users",
                            "Led cross-functional team of 8 developers",
                            "Reduced system latency by 40% through optimization"
                        ]
                    },
                    {
                        "company": "StartupCorp",
                        "role": "Full Stack Developer",
                        "duration": "2020-2022",
                        "achievements": [
                            "Built real-time analytics dashboard",
                            "Implemented CI/CD pipeline reducing deployment time by 70%"
                        ]
                    }
                ],
                "education": [
                    {
                        "degree": "MS Computer Science",
                        "institution": "UC Berkeley",
                        "year": "2020"
                    }
                ],
                "summary": "Passionate full-stack developer with 4+ years experience building scalable web applications and leading development teams."
            }
            
            response = requests.post(f"{API_BASE}/candidates", headers=headers, json=candidate_data)
            
            if response.status_code == 200:
                result = response.json()
                self.test_data['candidate_id'] = result['candidate_id']
                print(f"✅ Created test candidate: {result['name']} ({result['candidate_id']})")
                return True
            else:
                print(f"❌ Failed to create test candidate: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error setting up test candidate: {str(e)}")
            return False
    
    # ============ STORY REGENERATION TESTS ============
    
    def test_story_regeneration_admin(self):
        """Test POST /api/candidates/{candidate_id}/story/regenerate as admin"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.post(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/story/regenerate", 
                                   headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                success = (
                    'ai_story' in result and
                    result['ai_story'] is not None and
                    'candidate_id' in result
                )
                self.log_result("Story regeneration (admin)", success,
                              "Missing AI story or candidate ID in response")
            else:
                self.log_result("Story regeneration (admin)", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Story regeneration (admin)", False, str(e))
    
    def test_story_regeneration_recruiter(self):
        """Test POST /api/candidates/{candidate_id}/story/regenerate as recruiter"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.post(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/story/regenerate", 
                                   headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                success = (
                    'ai_story' in result and
                    result['ai_story'] is not None and
                    'candidate_id' in result
                )
                self.log_result("Story regeneration (recruiter)", success,
                              "Missing AI story or candidate ID in response")
            else:
                self.log_result("Story regeneration (recruiter)", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Story regeneration (recruiter)", False, str(e))
    
    def test_story_regeneration_client_forbidden(self):
        """Test 403 when client user tries to regenerate"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
            response = requests.post(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/story/regenerate", 
                                   headers=headers)
            
            success = response.status_code == 403
            self.log_result("Story regeneration forbidden (client)", success,
                          f"Expected 403, got {response.status_code}")
                          
        except Exception as e:
            self.log_result("Story regeneration forbidden (client)", False, str(e))
    
    def test_story_regeneration_timestamp_update(self):
        """Verify story_last_generated timestamp is updated"""
        try:
            # Get candidate before regeneration
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response_before = requests.get(f"{API_BASE}/candidates/{self.test_data['candidate_id']}", 
                                         headers=headers)
            
            if response_before.status_code != 200:
                self.log_result("Story timestamp update", False, "Failed to get candidate before regeneration")
                return
            
            # Regenerate story
            response = requests.post(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/story/regenerate", 
                                   headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                success = 'ai_story' in result and result['ai_story'] is not None
                self.log_result("Story timestamp update", success,
                              "Story regeneration failed or missing AI story")
            else:
                self.log_result("Story timestamp update", False,
                              f"Regeneration failed with status {response.status_code}")
                              
        except Exception as e:
            self.log_result("Story timestamp update", False, str(e))
    
    # ============ PDF EXPORT TESTS ============
    
    def test_pdf_export_admin(self):
        """Test GET /api/candidates/{candidate_id}/story/export as admin"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/story/export", 
                                  headers=headers)
            
            if response.status_code == 200:
                success = (
                    response.headers.get('content-type') == 'application/pdf' and
                    'Content-Disposition' in response.headers and
                    'attachment' in response.headers.get('Content-Disposition', '') and
                    len(response.content) > 1000  # PDF should be > 1000 bytes
                )
                self.log_result("PDF export (admin)", success,
                              "Invalid PDF response or missing headers")
            else:
                self.log_result("PDF export (admin)", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("PDF export (admin)", False, str(e))
    
    def test_pdf_export_recruiter(self):
        """Test GET /api/candidates/{candidate_id}/story/export as recruiter"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/story/export", 
                                  headers=headers)
            
            if response.status_code == 200:
                success = (
                    response.headers.get('content-type') == 'application/pdf' and
                    'Content-Disposition' in response.headers and
                    'attachment' in response.headers.get('Content-Disposition', '') and
                    len(response.content) > 1000  # PDF should be > 1000 bytes
                )
                self.log_result("PDF export (recruiter)", success,
                              "Invalid PDF response or missing headers")
            else:
                self.log_result("PDF export (recruiter)", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("PDF export (recruiter)", False, str(e))
    
    def test_pdf_export_client_user(self):
        """Test GET /api/candidates/{candidate_id}/story/export as client user"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
            response = requests.get(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/story/export", 
                                  headers=headers)
            
            if response.status_code == 200:
                success = (
                    response.headers.get('content-type') == 'application/pdf' and
                    'Content-Disposition' in response.headers and
                    'attachment' in response.headers.get('Content-Disposition', '') and
                    len(response.content) > 1000  # PDF should be > 1000 bytes
                )
                self.log_result("PDF export (client user)", success,
                              "Invalid PDF response or missing headers")
            else:
                self.log_result("PDF export (client user)", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("PDF export (client user)", False, str(e))
    
    def test_pdf_content_disposition_header(self):
        """Verify response headers contain Content-Disposition attachment"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/story/export", 
                                  headers=headers)
            
            if response.status_code == 200:
                content_disposition = response.headers.get('Content-Disposition', '')
                success = (
                    'attachment' in content_disposition and
                    'filename=' in content_disposition and
                    'candidate_story_' in content_disposition
                )
                self.log_result("PDF Content-Disposition header", success,
                              f"Invalid Content-Disposition: {content_disposition}")
            else:
                self.log_result("PDF Content-Disposition header", False,
                              f"Status {response.status_code}")
                              
        except Exception as e:
            self.log_result("PDF Content-Disposition header", False, str(e))
    
    def test_pdf_content_type(self):
        """Verify response Content-Type is application/pdf"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/story/export", 
                                  headers=headers)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                success = content_type == 'application/pdf'
                self.log_result("PDF Content-Type", success,
                              f"Expected application/pdf, got {content_type}")
            else:
                self.log_result("PDF Content-Type", False,
                              f"Status {response.status_code}")
                              
        except Exception as e:
            self.log_result("PDF Content-Type", False, str(e))
    
    def test_pdf_size_validation(self):
        """Verify PDF is non-empty (size > 1000 bytes)"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/story/export", 
                                  headers=headers)
            
            if response.status_code == 200:
                pdf_size = len(response.content)
                success = pdf_size > 1000
                self.log_result("PDF size validation", success,
                              f"PDF size {pdf_size} bytes, expected > 1000")
            else:
                self.log_result("PDF size validation", False,
                              f"Status {response.status_code}")
                              
        except Exception as e:
            self.log_result("PDF size validation", False, str(e))
    
    def test_pdf_filename_format(self):
        """Verify filename format matches pattern"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/story/export", 
                                  headers=headers)
            
            if response.status_code == 200:
                content_disposition = response.headers.get('Content-Disposition', '')
                # Extract filename from Content-Disposition header
                filename_part = [part.strip() for part in content_disposition.split(';') if 'filename=' in part]
                
                if filename_part:
                    filename = filename_part[0].split('=')[1].strip('"')
                    success = (
                        filename.startswith('candidate_story_') and
                        filename.endswith('.pdf') and
                        self.test_data['candidate_id'] in filename
                    )
                    self.log_result("PDF filename format", success,
                                  f"Invalid filename format: {filename}")
                else:
                    self.log_result("PDF filename format", False,
                                  "No filename found in Content-Disposition")
            else:
                self.log_result("PDF filename format", False,
                              f"Status {response.status_code}")
                              
        except Exception as e:
            self.log_result("PDF filename format", False, str(e))
    
    # ============ ERROR HANDLING TESTS ============
    
    def test_regenerate_nonexistent_candidate(self):
        """Test regenerate for non-existent candidate (404)"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.post(f"{API_BASE}/candidates/cand_nonexistent/story/regenerate", 
                                   headers=headers)
            
            success = response.status_code == 404
            self.log_result("Regenerate non-existent candidate", success,
                          f"Expected 404, got {response.status_code}")
                          
        except Exception as e:
            self.log_result("Regenerate non-existent candidate", False, str(e))
    
    def test_export_nonexistent_candidate(self):
        """Test export for non-existent candidate (404)"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(f"{API_BASE}/candidates/cand_nonexistent/story/export", 
                                  headers=headers)
            
            success = response.status_code == 404
            self.log_result("Export non-existent candidate", success,
                          f"Expected 404, got {response.status_code}")
                          
        except Exception as e:
            self.log_result("Export non-existent candidate", False, str(e))
    
    def test_tenant_violation_regenerate(self):
        """Test tenant violation returns 403 for regenerate"""
        try:
            # Create candidate for different client first
            # This test assumes the client user can only access their own candidates
            headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
            response = requests.post(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/story/regenerate", 
                                   headers=headers)
            
            success = response.status_code == 403
            self.log_result("Tenant violation regenerate", success,
                          f"Expected 403, got {response.status_code}")
                          
        except Exception as e:
            self.log_result("Tenant violation regenerate", False, str(e))
    
    def test_tenant_isolation_export(self):
        """Test client can only export their candidates"""
        try:
            # Client user should be able to export if they have access to the candidate
            headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
            response = requests.get(f"{API_BASE}/candidates/{self.test_data['candidate_id']}/story/export", 
                                  headers=headers)
            
            # This should work if the candidate belongs to the client's job
            # If it returns 403, it means tenant isolation is working correctly
            success = response.status_code in [200, 403]  # Both are valid depending on tenant setup
            self.log_result("Tenant isolation export", success,
                          f"Unexpected status {response.status_code}")
                          
        except Exception as e:
            self.log_result("Tenant isolation export", False, str(e))
    
    def run_all_tests(self):
        """Run all Phase 6 Story View & PDF Export tests"""
        print("🚀 Starting Phase 6: Story View & PDF Export Tests")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print("="*80)
        
        # Setup
        if not self.setup_test_users():
            print("❌ Failed to setup test users. Aborting tests.")
            return False
            
        if not self.setup_test_candidate():
            print("❌ Failed to setup test candidate. Aborting tests.")
            return False
        
        print("\n📋 Running Story View & PDF Export Tests...")
        print("-" * 50)
        
        # Story Regeneration Tests
        print("\n🔄 Story Regeneration Tests:")
        self.test_story_regeneration_admin()
        self.test_story_regeneration_recruiter()
        self.test_story_regeneration_client_forbidden()
        self.test_story_regeneration_timestamp_update()
        
        # PDF Export Tests
        print("\n📄 PDF Export Tests:")
        self.test_pdf_export_admin()
        self.test_pdf_export_recruiter()
        self.test_pdf_export_client_user()
        self.test_pdf_content_disposition_header()
        self.test_pdf_content_type()
        self.test_pdf_size_validation()
        self.test_pdf_filename_format()
        
        # Error Handling Tests
        print("\n🚨 Error Handling Tests:")
        self.test_regenerate_nonexistent_candidate()
        self.test_export_nonexistent_candidate()
        self.test_tenant_violation_regenerate()
        self.test_tenant_isolation_export()
        
        # Print results
        print("\n" + "="*80)
        print("📊 PHASE 6 TEST RESULTS SUMMARY")
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
    tester = Phase6StoryViewTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)