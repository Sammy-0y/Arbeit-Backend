# Phase 1 Automated Tests - Quick Reference

## Quick Start

```bash
# Run all tests
cd /app && python3 tests/test_runner.py

# Or use pytest directly
pytest tests/ -v
```

## Test Organization

```
tests/
├── conftest.py                   # Fixtures & test configuration
├── test_auth_utils.py           # Unit tests (11 tests)
│   ├── Password hashing (5)
│   └── JWT tokens (6)
├── test_auth_endpoints.py       # API integration tests (15 tests)
│   ├── Register endpoint (6)
│   ├── Login endpoint (5)
│   └── Auth me endpoint (4)
├── test_role_based_access.py    # RBAC & multi-tenant (9 tests)
│   ├── Role-based access (5)
│   └── Multi-tenant foundation (4)
└── test_runner.py               # Main test runner script
```

## Run Specific Tests

```bash
# Run single test file
pytest tests/test_auth_utils.py -v

# Run specific test class
pytest tests/test_auth_endpoints.py::TestAuthLogin -v

# Run specific test
pytest tests/test_auth_endpoints.py::TestAuthLogin::test_login_success_admin -v

# Run tests matching pattern
pytest tests/ -k "login" -v
```

## Debugging Tests

```bash
# Show print statements
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -x

# Show full error traceback
pytest tests/ -v --tb=long

# Run last failed tests only
pytest tests/ --lf
```

## Coverage

```bash
# Run with coverage report
pytest tests/ --cov=backend --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=backend --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Results

✅ **35/35 tests passing**

- Unit Tests: 11/11 ✅
- Integration Tests (Auth): 15/15 ✅
- Integration Tests (RBAC): 5/5 ✅  
- Integration Tests (Multi-tenant): 4/4 ✅

## What's Tested

### Authentication
- ✅ User registration (admin, recruiter, client_user)
- ✅ Login with JWT
- ✅ Token validation
- ✅ Password hashing
- ✅ Error handling (401, 403, 422)

### Authorization  
- ✅ Role-based access control
- ✅ Protected endpoints
- ✅ Token payload validation

### Multi-Tenant
- ✅ Client ID in tokens
- ✅ User-client association
- ✅ Foundation for data isolation

## Common Issues

### Issue: ModuleNotFoundError
```bash
# Solution: Install test dependencies
pip install -r requirements-test.txt
```

### Issue: MongoDB connection error
```bash
# Solution: Ensure MongoDB is running
sudo supervisorctl status mongodb
```

### Issue: Tests hang or timeout
```bash
# Solution: Check if backend is running
sudo supervisorctl status backend
# Restart if needed
sudo supervisorctl restart backend
```

## Test Data

Tests use isolated database: `test_arbeit_phase1`
- Automatically created
- Cleaned before each test
- Dropped after test suite completes

No impact on development database (`test_database`).

## Adding New Tests

1. Create test file: `test_<feature>.py`
2. Import fixtures from `conftest.py`
3. Use `@pytest.mark.asyncio` for async tests
4. Follow AAA pattern (Arrange-Act-Assert)
5. Add docstrings explaining what is tested

Example:
```python
import pytest

@pytest.mark.asyncio
async def test_new_feature(client, clean_db):
    \"\"\"Test description here\"\"\"
    # Arrange
    test_data = {...}
    
    # Act
    response = await client.post(\"/api/endpoint\", json=test_data)
    
    # Assert
    assert response.status_code == 200
    assert response.json()[\"key\"] == expected_value
```

## Future Tests (TODO)

- [ ] Data isolation tests (Phase 3+)
- [ ] Frontend UI tests
- [ ] Performance tests
- [ ] Security tests (rate limiting, injection)
- [ ] End-to-end user journeys

---

**Status**: All Phase 1 tests passing ✅
