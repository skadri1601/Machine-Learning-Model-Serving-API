import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_register_user():
    """Test user registration."""
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
    )
    assert response.status_code == 201
    assert response.json()["username"] == "testuser"


def test_login():
    """Test user login."""
    # Register user first
    client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
    )

    # Login
    response = client.post(
        "/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_duplicate_username():
    """Test duplicate username registration."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }

    # First registration
    response1 = client.post("/auth/register", json=user_data)
    assert response1.status_code == 201

    # Second registration with same username
    user_data["email"] = "different@example.com"
    response2 = client.post("/auth/register", json=user_data)
    assert response2.status_code == 400
    assert "already registered" in response2.json()["detail"].lower()


def test_invalid_login():
    """Test login with invalid credentials."""
    response = client.post(
        "/auth/login",
        data={
            "username": "nonexistent",
            "password": "wrongpass"
        }
    )
    assert response.status_code == 401


def test_list_models_unauthorized():
    """Test listing models without authentication."""
    response = client.get("/models")
    assert response.status_code == 401


def test_list_models_authorized():
    """Test listing models with authentication."""
    # Register and login
    client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]

    # List models
    response = client.get(
        "/models",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "models" in response.json()
    assert "total" in response.json()


def test_get_metrics():
    """Test metrics endpoint."""
    # Register and login
    client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]

    # Get metrics
    response = client.get(
        "/metrics",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_predictions" in data
    assert "total_active_models" in data
    assert "average_latency_seconds" in data
