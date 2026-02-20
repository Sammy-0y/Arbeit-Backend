import pytest
import pytest_asyncio
import asyncio
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

# Load environment
ROOT_DIR = Path(__file__).parent.parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

pytest_plugins = ('pytest_asyncio',)

@pytest_asyncio.fixture
async def mongo_client():
    """Create MongoDB client for tests"""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    yield client
    client.close()

@pytest_asyncio.fixture
async def test_db(mongo_client):
    """Get test database"""
    db_name = "test_arbeit_phase1"
    db = mongo_client[db_name]
    yield db
    # Cleanup after tests
    await mongo_client.drop_database(db_name)

@pytest_asyncio.fixture
async def clean_db(test_db):
    """Clean database before each test"""
    # Drop all collections
    collections = await test_db.list_collection_names()
    for collection in collections:
        await test_db[collection].drop()
    yield test_db

@pytest.fixture
def test_client_data():
    """Test client data"""
    return {
        "client_id": "test_client_001",
        "company_name": "Test Corp",
        "status": "active",
        "created_at": "2025-01-01T00:00:00"
    }

@pytest_asyncio.fixture
async def seed_test_client(clean_db, test_client_data):
    """Seed a test client"""
    await clean_db.clients.insert_one(test_client_data)
    yield clean_db

@pytest.fixture
def sample_users():
    """Sample user data for testing"""
    return [
        {
            "email": "test_admin@test.com",
            "password": "admin_pass123",
            "name": "Test Admin",
            "role": "admin",
            "client_id": None
        },
        {
            "email": "test_recruiter@test.com",
            "password": "recruiter_pass123",
            "name": "Test Recruiter",
            "role": "recruiter",
            "client_id": None
        },
        {
            "email": "test_client@test.com",
            "password": "client_pass123",
            "name": "Test Client User",
            "role": "client_user",
            "client_id": "test_client_001"
        }
    ]