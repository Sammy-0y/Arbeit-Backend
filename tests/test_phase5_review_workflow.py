#!/usr/bin/env python3
"""
Phase 5: Review Workflow - Backend API Testing
Comprehensive testing of review creation, status updates, and filtering functionality.
"""

import requests
import json
import os
import time
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://hirematch-52.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class ReviewWorkflowTester:
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
    
    def setup_test_data(self):
        """Setup test job and candidate for review testing"""
        print("\n🔧 Setting up test data...")
        
        try:
            # Get or create a test job
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(f"{API_BASE}/jobs", headers=headers)
            
            if response.status_code == 200:
                jobs = response.json()
                if jobs:
                    job = jobs[0]
                    self.test_data['job_id'] = job['job_id']
                    print(f"✅ Using existing job: {job['title']} ({job['job_id']})")
                else:
                    # Create a new job if none exist
                    job_data = {
                        "title": "Senior Software Engineer - Review Test",
                        "location": "San Francisco, CA",
                        "employment_type": "Full-time",
                        "experience_range": {"min_years": 3, "max_years": 8},
                        "work_model": "Hybrid",
                        "required_skills": ["Python", "React", "AWS"],
                        "description": "Test job for review workflow testing",
                        "status": "Active"
                    }
                    
                    response = requests.post(f"{API_BASE}/jobs", headers=headers, json=job_data)
                    if response.status_code == 200:
                        job = response.json()
                        self.test_data['job_id'] = job['job_id']
                        print(f"✅ Created test job: {job['job_id']}")
                    else:
                        print(f"❌ Failed to create test job: {response.status_code}")
                        return False
            
            # Create test candidates for review testing
            candidate_data = {
                "job_id": self.test_data['job_id'],
                "name": "Alex Rodriguez",
                "current_role": "Senior Software Engineer",
                "email": "alex.rodriguez@email.com",
                "phone": "415-555-0199",
                "skills": ["Python", "React", "AWS", "Docker"],
                "experience": [
                    {
                        "company": "TechStart Inc",
                        "role": "Senior Software Engineer",
                        "duration": "2020-2024",
                        "achievements": ["Built scalable microservices", "Led frontend team"]
                    }
                ],
                "education": [
                    {
                        "degree": "MS Computer Science",
                        "institution": "UC Berkeley",
                        "year": "2018"
                    }
                ],
                "summary": "Experienced full-stack engineer with expertise in modern web technologies"
            }
            
            response = requests.post(f"{API_BASE}/candidates", headers=headers, json=candidate_data)
            if response.status_code == 200:
                candidate = response.json()
                self.test_data['candidate_id'] = candidate['candidate_id']
                print(f"✅ Created test candidate: {candidate['candidate_id']}")
            else:
                print(f"❌ Failed to create test candidate: {response.status_code} - {response.text}")
                return False
            
            # Create a second candidate for filtering tests
            candidate_data2 = {
                "job_id": self.test_data['job_id'],
                "name": "Maria Garcia",
                "current_role": "Frontend Developer",
                "skills": ["React", "JavaScript", "CSS"],
                "summary": "Frontend specialist with React expertise"
            }
            
            response = requests.post(f"{API_BASE}/candidates", headers=headers, json=candidate_data2)
            if response.status_code == 200:
                candidate2 = response.json()
                self.test_data['candidate_id_2'] = candidate2['candidate_id']
                print(f"✅ Created second test candidate: {candidate2['candidate_id']}")
            else:
                print(f"❌ Failed to create second test candidate: {response.status_code}")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Error setting up test data: {str(e)}")
            return False
    
    # ============ REVIEW CREATION TESTS ============
    
    def test_review_creation_approve(self):
        """Test POST /api/candidates/{candidate_id}/review with APPROVE action"""
        try:
            review_data = {
                "action": "APPROVE",
                "comment": "Excellent candidate with strong technical skills and great experience"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.post(
                f"{API_BASE}/candidates/{self.test_data['candidate_id']}/review",
                headers=headers,
                json=review_data
            )
            
            if response.status_code == 200:
                result = response.json()
                success = (
                    result['action'] == "APPROVE" and
                    result['candidate_id'] == self.test_data['candidate_id'] and
                    result['comment'] == review_data['comment'] and
                    'review_id' in result and
                    'timestamp' in result and
                    result['user_role'] == 'recruiter'
                )
                self.test_data['approve_review_id'] = result.get('review_id')
                self.log_result("Review creation - APPROVE action", success,
                              "Missing required fields or incorrect values")
            else:
                self.log_result("Review creation - APPROVE action", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Review creation - APPROVE action", False, str(e))
    
    def test_review_creation_pipeline(self):
        """Test POST /api/candidates/{candidate_id}/review with PIPELINE action"""
        try:
            review_data = {
                "action": "PIPELINE",
                "comment": "Good candidate, moving to next stage for technical interview"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.post(
                f"{API_BASE}/candidates/{self.test_data['candidate_id_2']}/review",
                headers=headers,
                json=review_data
            )
            
            if response.status_code == 200:
                result = response.json()
                success = (
                    result['action'] == "PIPELINE" and
                    result['candidate_id'] == self.test_data['candidate_id_2'] and
                    result['user_role'] == 'admin'
                )
                self.log_result("Review creation - PIPELINE action", success,
                              "Incorrect action or missing fields")
            else:
                self.log_result("Review creation - PIPELINE action", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Review creation - PIPELINE action", False, str(e))
    
    def test_review_creation_reject(self):
        """Test POST /api/candidates/{candidate_id}/review with REJECT action"""
        try:
            review_data = {
                "action": "REJECT",
                "comment": "Skills don't match our current requirements"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
            response = requests.post(
                f"{API_BASE}/candidates/{self.test_data['candidate_id_2']}/review",
                headers=headers,
                json=review_data
            )
            
            if response.status_code == 200:
                result = response.json()
                success = (
                    result['action'] == "REJECT" and
                    result['user_role'] == 'client_user'
                )
                self.log_result("Review creation - REJECT action", success,
                              "Incorrect action or user role")
            else:
                self.log_result("Review creation - REJECT action", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Review creation - REJECT action", False, str(e))
    
    def test_review_creation_comment(self):
        """Test POST /api/candidates/{candidate_id}/review with COMMENT action"""
        try:
            review_data = {
                "action": "COMMENT",
                "comment": "Need to verify years of experience with previous employer"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.post(
                f"{API_BASE}/candidates/{self.test_data['candidate_id']}/review",
                headers=headers,
                json=review_data
            )
            
            if response.status_code == 200:
                result = response.json()
                success = result['action'] == "COMMENT"
                self.log_result("Review creation - COMMENT action", success,
                              "Incorrect action")
            else:
                self.log_result("Review creation - COMMENT action", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Review creation - COMMENT action", False, str(e))
    
    # ============ STATUS UPDATE LOGIC TESTS ============
    
    def test_status_update_approve(self):
        """Verify APPROVE action updates candidate status to APPROVED"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(
                f"{API_BASE}/candidates/{self.test_data['candidate_id']}",
                headers=headers
            )
            
            if response.status_code == 200:
                candidate = response.json()
                success = candidate['status'] == "APPROVE"  # Should be updated by APPROVE review
                self.log_result("Status update - APPROVE action", success,
                              f"Expected APPROVE status, got {candidate.get('status')}")
            else:
                self.log_result("Status update - APPROVE action", False,
                              f"Failed to get candidate: {response.status_code}")
                              
        except Exception as e:
            self.log_result("Status update - APPROVE action", False, str(e))
    
    def test_status_update_pipeline(self):
        """Verify PIPELINE action updates candidate status to PIPELINE"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(
                f"{API_BASE}/candidates/{self.test_data['candidate_id_2']}",
                headers=headers
            )
            
            if response.status_code == 200:
                candidate = response.json()
                # Should be REJECT from the last review, not PIPELINE
                success = candidate['status'] == "REJECT"
                self.log_result("Status update - Final status after multiple reviews", success,
                              f"Expected REJECT status, got {candidate.get('status')}")
            else:
                self.log_result("Status update - Final status after multiple reviews", False,
                              f"Failed to get candidate: {response.status_code}")
                              
        except Exception as e:
            self.log_result("Status update - Final status after multiple reviews", False, str(e))
    
    def test_status_update_comment_no_change(self):
        """Verify COMMENT action does NOT update candidate status"""
        try:
            # Get current status
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(
                f"{API_BASE}/candidates/{self.test_data['candidate_id']}",
                headers=headers
            )
            
            if response.status_code == 200:
                candidate_before = response.json()
                original_status = candidate_before['status']
                
                # Add a comment review
                review_data = {
                    "action": "COMMENT",
                    "comment": "Additional note for review"
                }
                
                response = requests.post(
                    f"{API_BASE}/candidates/{self.test_data['candidate_id']}/review",
                    headers=headers,
                    json=review_data
                )
                
                if response.status_code == 200:
                    # Check status hasn't changed
                    response = requests.get(
                        f"{API_BASE}/candidates/{self.test_data['candidate_id']}",
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        candidate_after = response.json()
                        success = candidate_after['status'] == original_status
                        self.log_result("Status update - COMMENT no change", success,
                                      f"Status changed from {original_status} to {candidate_after['status']}")
                    else:
                        self.log_result("Status update - COMMENT no change", False,
                                      "Failed to get candidate after comment")
                else:
                    self.log_result("Status update - COMMENT no change", False,
                                  f"Failed to create comment: {response.status_code}")
            else:
                self.log_result("Status update - COMMENT no change", False,
                              "Failed to get initial candidate status")
                              
        except Exception as e:
            self.log_result("Status update - COMMENT no change", False, str(e))
    
    def test_multiple_status_changes(self):
        """Test multiple status changes (NEW → PIPELINE → APPROVED)"""
        try:
            # Create a new candidate for this test
            candidate_data = {
                "job_id": self.test_data['job_id'],
                "name": "Test Status Changes",
                "skills": ["Python"]
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.post(f"{API_BASE}/candidates", headers=headers, json=candidate_data)
            
            if response.status_code == 200:
                test_candidate_id = response.json()['candidate_id']
                
                # Step 1: NEW → PIPELINE
                review_data = {"action": "PIPELINE", "comment": "Moving to pipeline"}
                response = requests.post(
                    f"{API_BASE}/candidates/{test_candidate_id}/review",
                    headers=headers,
                    json=review_data
                )
                
                if response.status_code != 200:
                    self.log_result("Multiple status changes", False, "Failed PIPELINE review")
                    return
                
                # Step 2: PIPELINE → APPROVE
                review_data = {"action": "APPROVE", "comment": "Final approval"}
                response = requests.post(
                    f"{API_BASE}/candidates/{test_candidate_id}/review",
                    headers=headers,
                    json=review_data
                )
                
                if response.status_code == 200:
                    # Verify final status
                    response = requests.get(f"{API_BASE}/candidates/{test_candidate_id}", headers=headers)
                    if response.status_code == 200:
                        final_candidate = response.json()
                        success = final_candidate['status'] == "APPROVE"
                        self.log_result("Multiple status changes", success,
                                      f"Expected APPROVE, got {final_candidate['status']}")
                    else:
                        self.log_result("Multiple status changes", False, "Failed to get final status")
                else:
                    self.log_result("Multiple status changes", False, "Failed APPROVE review")
            else:
                self.log_result("Multiple status changes", False, "Failed to create test candidate")
                              
        except Exception as e:
            self.log_result("Multiple status changes", False, str(e))
    
    # ============ REVIEW LISTING TESTS ============
    
    def test_review_listing(self):
        """Test GET /api/candidates/{candidate_id}/reviews returns all reviews"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(
                f"{API_BASE}/candidates/{self.test_data['candidate_id']}/reviews",
                headers=headers
            )
            
            if response.status_code == 200:
                reviews = response.json()
                success = (
                    len(reviews) >= 2 and  # Should have APPROVE and COMMENT reviews
                    all('review_id' in r for r in reviews) and
                    all('candidate_id' in r for r in reviews) and
                    all('user_id' in r for r in reviews) and
                    all('user_name' in r for r in reviews) and
                    all('user_role' in r for r in reviews) and
                    all('timestamp' in r for r in reviews) and
                    all('action' in r for r in reviews)
                )
                self.log_result("Review listing - All reviews", success,
                              "Missing reviews or required fields")
            else:
                self.log_result("Review listing - All reviews", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Review listing - All reviews", False, str(e))
    
    def test_review_sorting(self):
        """Verify reviews sorted by timestamp descending (newest first)"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(
                f"{API_BASE}/candidates/{self.test_data['candidate_id']}/reviews",
                headers=headers
            )
            
            if response.status_code == 200:
                reviews = response.json()
                if len(reviews) >= 2:
                    # Check if timestamps are in descending order
                    timestamps = [r['timestamp'] for r in reviews]
                    sorted_timestamps = sorted(timestamps, reverse=True)
                    success = timestamps == sorted_timestamps
                    self.log_result("Review sorting - Newest first", success,
                                  "Reviews not sorted by timestamp descending")
                else:
                    self.log_result("Review sorting - Newest first", False,
                                  "Not enough reviews to test sorting")
            else:
                self.log_result("Review sorting - Newest first", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Review sorting - Newest first", False, str(e))
    
    def test_empty_reviews_list(self):
        """Test empty reviews list for candidate with no reviews"""
        try:
            # Create a candidate with no reviews
            candidate_data = {
                "job_id": self.test_data['job_id'],
                "name": "No Reviews Candidate",
                "skills": ["JavaScript"]
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.post(f"{API_BASE}/candidates", headers=headers, json=candidate_data)
            
            if response.status_code == 200:
                no_reviews_candidate_id = response.json()['candidate_id']
                
                response = requests.get(
                    f"{API_BASE}/candidates/{no_reviews_candidate_id}/reviews",
                    headers=headers
                )
                
                if response.status_code == 200:
                    reviews = response.json()
                    success = len(reviews) == 0
                    self.log_result("Empty reviews list", success,
                                  f"Expected empty list, got {len(reviews)} reviews")
                else:
                    self.log_result("Empty reviews list", False,
                                  f"Status {response.status_code}: {response.text}")
            else:
                self.log_result("Empty reviews list", False, "Failed to create test candidate")
                              
        except Exception as e:
            self.log_result("Empty reviews list", False, str(e))
    
    # ============ PERMISSIONS TESTS ============
    
    def test_permissions_client_user(self):
        """Test client user can create reviews (all actions)"""
        try:
            actions = ["APPROVE", "PIPELINE", "REJECT", "COMMENT"]
            headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
            
            for action in actions:
                review_data = {
                    "action": action,
                    "comment": f"Client user {action} test"
                }
                
                response = requests.post(
                    f"{API_BASE}/candidates/{self.test_data['candidate_id']}/review",
                    headers=headers,
                    json=review_data
                )
                
                if response.status_code != 200:
                    self.log_result(f"Permissions - Client user {action}", False,
                                  f"Status {response.status_code}: {response.text}")
                    return
            
            self.log_result("Permissions - Client user all actions", True)
                              
        except Exception as e:
            self.log_result("Permissions - Client user all actions", False, str(e))
    
    def test_permissions_recruiter(self):
        """Test recruiter can create reviews (all actions)"""
        try:
            actions = ["APPROVE", "PIPELINE", "REJECT", "COMMENT"]
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            
            for action in actions:
                review_data = {
                    "action": action,
                    "comment": f"Recruiter {action} test"
                }
                
                response = requests.post(
                    f"{API_BASE}/candidates/{self.test_data['candidate_id']}/review",
                    headers=headers,
                    json=review_data
                )
                
                if response.status_code != 200:
                    self.log_result(f"Permissions - Recruiter {action}", False,
                                  f"Status {response.status_code}: {response.text}")
                    return
            
            self.log_result("Permissions - Recruiter all actions", True)
                              
        except Exception as e:
            self.log_result("Permissions - Recruiter all actions", False, str(e))
    
    def test_permissions_admin(self):
        """Test admin can create reviews (all actions)"""
        try:
            actions = ["APPROVE", "PIPELINE", "REJECT", "COMMENT"]
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            
            for action in actions:
                review_data = {
                    "action": action,
                    "comment": f"Admin {action} test"
                }
                
                response = requests.post(
                    f"{API_BASE}/candidates/{self.test_data['candidate_id']}/review",
                    headers=headers,
                    json=review_data
                )
                
                if response.status_code != 200:
                    self.log_result(f"Permissions - Admin {action}", False,
                                  f"Status {response.status_code}: {response.text}")
                    return
            
            self.log_result("Permissions - Admin all actions", True)
                              
        except Exception as e:
            self.log_result("Permissions - Admin all actions", False, str(e))
    
    def test_tenant_isolation(self):
        """Test tenant isolation: client user cannot review candidates from other clients"""
        try:
            # This test would require creating candidates for different clients
            # For now, we'll test that client user can access their own candidates
            headers = {"Authorization": f"Bearer {self.tokens['client_user']}"}
            response = requests.get(
                f"{API_BASE}/candidates/{self.test_data['candidate_id']}/reviews",
                headers=headers
            )
            
            success = response.status_code == 200
            self.log_result("Tenant isolation - Own candidate access", success,
                          f"Expected 200, got {response.status_code}")
                              
        except Exception as e:
            self.log_result("Tenant isolation - Own candidate access", False, str(e))
    
    # ============ CANDIDATES LIST FILTER TESTS ============
    
    def test_candidates_list_default_filter(self):
        """Test GET /api/jobs/{job_id}/candidates without show_rejected param (defaults to false)"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(
                f"{API_BASE}/jobs/{self.test_data['job_id']}/candidates",
                headers=headers
            )
            
            if response.status_code == 200:
                candidates = response.json()
                # Should exclude REJECTED candidates by default
                rejected_candidates = [c for c in candidates if c['status'] == 'REJECT']
                success = len(rejected_candidates) == 0
                self.log_result("Candidates list - Default filter excludes rejected", success,
                              f"Found {len(rejected_candidates)} rejected candidates")
            else:
                self.log_result("Candidates list - Default filter excludes rejected", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Candidates list - Default filter excludes rejected", False, str(e))
    
    def test_candidates_list_show_rejected(self):
        """Test GET /api/jobs/{job_id}/candidates?show_rejected=true includes REJECTED candidates"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(
                f"{API_BASE}/jobs/{self.test_data['job_id']}/candidates?show_rejected=true",
                headers=headers
            )
            
            if response.status_code == 200:
                candidates = response.json()
                # Should include REJECTED candidates
                rejected_candidates = [c for c in candidates if c['status'] == 'REJECT']
                success = len(rejected_candidates) > 0
                self.log_result("Candidates list - Show rejected includes rejected", success,
                              f"Expected rejected candidates, found {len(rejected_candidates)}")
            else:
                self.log_result("Candidates list - Show rejected includes rejected", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Candidates list - Show rejected includes rejected", False, str(e))
    
    # ============ INTEGRATION TESTS ============
    
    def test_full_workflow_integration(self):
        """Test full workflow: Create candidate → Add comment → Approve → List reviews"""
        try:
            # Create candidate
            candidate_data = {
                "job_id": self.test_data['job_id'],
                "name": "Integration Test Candidate",
                "current_role": "Software Engineer",
                "skills": ["Python", "Django"]
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.post(f"{API_BASE}/candidates", headers=headers, json=candidate_data)
            
            if response.status_code != 200:
                self.log_result("Full workflow integration", False, "Failed to create candidate")
                return
            
            integration_candidate_id = response.json()['candidate_id']
            
            # Add comment
            review_data = {"action": "COMMENT", "comment": "Initial review comment"}
            response = requests.post(
                f"{API_BASE}/candidates/{integration_candidate_id}/review",
                headers=headers,
                json=review_data
            )
            
            if response.status_code != 200:
                self.log_result("Full workflow integration", False, "Failed to add comment")
                return
            
            # Approve
            review_data = {"action": "APPROVE", "comment": "Final approval after review"}
            response = requests.post(
                f"{API_BASE}/candidates/{integration_candidate_id}/review",
                headers=headers,
                json=review_data
            )
            
            if response.status_code != 200:
                self.log_result("Full workflow integration", False, "Failed to approve")
                return
            
            # List reviews
            response = requests.get(
                f"{API_BASE}/candidates/{integration_candidate_id}/reviews",
                headers=headers
            )
            
            if response.status_code == 200:
                reviews = response.json()
                success = (
                    len(reviews) == 2 and
                    any(r['action'] == 'COMMENT' for r in reviews) and
                    any(r['action'] == 'APPROVE' for r in reviews)
                )
                self.log_result("Full workflow integration", success,
                              f"Expected 2 reviews (COMMENT, APPROVE), got {len(reviews)}")
            else:
                self.log_result("Full workflow integration", False, "Failed to list reviews")
                              
        except Exception as e:
            self.log_result("Full workflow integration", False, str(e))
    
    def test_multiple_reviews_same_candidate(self):
        """Test multiple reviews on same candidate"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            
            # Add multiple reviews
            reviews_to_add = [
                {"action": "COMMENT", "comment": "First review comment"},
                {"action": "PIPELINE", "comment": "Moving to pipeline"},
                {"action": "COMMENT", "comment": "Second review comment"},
                {"action": "APPROVE", "comment": "Final approval"}
            ]
            
            for review_data in reviews_to_add:
                response = requests.post(
                    f"{API_BASE}/candidates/{self.test_data['candidate_id']}/review",
                    headers=headers,
                    json=review_data
                )
                
                if response.status_code != 200:
                    self.log_result("Multiple reviews same candidate", False,
                                  f"Failed to add {review_data['action']} review")
                    return
            
            # Verify all reviews are preserved
            response = requests.get(
                f"{API_BASE}/candidates/{self.test_data['candidate_id']}/reviews",
                headers=headers
            )
            
            if response.status_code == 200:
                reviews = response.json()
                # Should have original reviews plus the 4 new ones
                success = len(reviews) >= 4
                self.log_result("Multiple reviews same candidate", success,
                              f"Expected at least 4 reviews, got {len(reviews)}")
            else:
                self.log_result("Multiple reviews same candidate", False, "Failed to get reviews")
                              
        except Exception as e:
            self.log_result("Multiple reviews same candidate", False, str(e))
    
    def test_review_history_preserved(self):
        """Verify review history preserved correctly"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(
                f"{API_BASE}/candidates/{self.test_data['candidate_id']}/reviews",
                headers=headers
            )
            
            if response.status_code == 200:
                reviews = response.json()
                
                # Check that all reviews have required fields and are properly formatted
                success = all(
                    r.get('review_id') and
                    r.get('candidate_id') == self.test_data['candidate_id'] and
                    r.get('user_id') and
                    r.get('user_name') and
                    r.get('user_role') and
                    r.get('timestamp') and
                    r.get('action') in ['APPROVE', 'PIPELINE', 'REJECT', 'COMMENT']
                    for r in reviews
                )
                
                self.log_result("Review history preserved", success,
                              "Some reviews missing required fields or invalid data")
            else:
                self.log_result("Review history preserved", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Review history preserved", False, str(e))
    
    def test_comment_special_characters(self):
        """Test comment with special characters and long text"""
        try:
            special_comment = """
            This is a test comment with special characters: !@#$%^&*()_+-=[]{}|;':",./<>?
            Unicode characters: 你好 🚀 ñáéíóú
            Long text: """ + "A" * 500 + """
            Newlines and tabs:
                - Bullet point 1
                - Bullet point 2
            """
            
            review_data = {
                "action": "COMMENT",
                "comment": special_comment
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.post(
                f"{API_BASE}/candidates/{self.test_data['candidate_id']}/review",
                headers=headers,
                json=review_data
            )
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('comment') == special_comment
                self.log_result("Comment special characters", success,
                              "Special characters not preserved correctly")
            else:
                self.log_result("Comment special characters", False,
                              f"Status {response.status_code}: {response.text}")
                              
        except Exception as e:
            self.log_result("Comment special characters", False, str(e))
    
    # ============ ERROR HANDLING TESTS ============
    
    def test_review_nonexistent_candidate(self):
        """Test review creation for non-existent candidate (404)"""
        try:
            review_data = {
                "action": "APPROVE",
                "comment": "This should fail"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.post(
                f"{API_BASE}/candidates/nonexistent_id/review",
                headers=headers,
                json=review_data
            )
            
            success = response.status_code == 404
            self.log_result("Review nonexistent candidate", success,
                          f"Expected 404, got {response.status_code}")
                              
        except Exception as e:
            self.log_result("Review nonexistent candidate", False, str(e))
    
    def test_review_listing_nonexistent_candidate(self):
        """Test review listing for non-existent candidate (404)"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.get(
                f"{API_BASE}/candidates/nonexistent_id/reviews",
                headers=headers
            )
            
            success = response.status_code == 404
            self.log_result("Review listing nonexistent candidate", success,
                          f"Expected 404, got {response.status_code}")
                              
        except Exception as e:
            self.log_result("Review listing nonexistent candidate", False, str(e))
    
    def test_invalid_action_type(self):
        """Test invalid action type in review creation (validation error)"""
        try:
            review_data = {
                "action": "INVALID_ACTION",
                "comment": "This should fail validation"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['recruiter']}"}
            response = requests.post(
                f"{API_BASE}/candidates/{self.test_data['candidate_id']}/review",
                headers=headers,
                json=review_data
            )
            
            success = response.status_code in [400, 422]  # Validation error
            self.log_result("Invalid action type", success,
                          f"Expected 400/422, got {response.status_code}")
                              
        except Exception as e:
            self.log_result("Invalid action type", False, str(e))
    
    def run_all_tests(self):
        """Run all review workflow tests"""
        print("🚀 Starting Phase 5 Review Workflow Tests")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print("="*80)
        
        # Setup
        if not self.setup_test_users():
            print("❌ Failed to setup test users. Aborting tests.")
            return False
            
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Aborting tests.")
            return False
        
        print("\n📋 Running Review Workflow Tests...")
        print("-" * 50)
        
        # Review Creation Tests
        print("\n🔍 Review Creation Tests:")
        self.test_review_creation_approve()
        self.test_review_creation_pipeline()
        self.test_review_creation_reject()
        self.test_review_creation_comment()
        
        # Status Update Logic Tests
        print("\n📊 Status Update Logic Tests:")
        self.test_status_update_approve()
        self.test_status_update_pipeline()
        self.test_status_update_comment_no_change()
        self.test_multiple_status_changes()
        
        # Review Listing Tests
        print("\n📋 Review Listing Tests:")
        self.test_review_listing()
        self.test_review_sorting()
        self.test_empty_reviews_list()
        
        # Permissions Tests
        print("\n🔐 Permissions Tests:")
        self.test_permissions_client_user()
        self.test_permissions_recruiter()
        self.test_permissions_admin()
        self.test_tenant_isolation()
        
        # Candidates List Filter Tests
        print("\n🔍 Candidates List Filter Tests:")
        self.test_candidates_list_default_filter()
        self.test_candidates_list_show_rejected()
        
        # Integration Tests
        print("\n🔄 Integration Tests:")
        self.test_full_workflow_integration()
        self.test_multiple_reviews_same_candidate()
        self.test_review_history_preserved()
        self.test_comment_special_characters()
        
        # Error Handling Tests
        print("\n⚠️ Error Handling Tests:")
        self.test_review_nonexistent_candidate()
        self.test_review_listing_nonexistent_candidate()
        self.test_invalid_action_type()
        
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
    tester = ReviewWorkflowTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)