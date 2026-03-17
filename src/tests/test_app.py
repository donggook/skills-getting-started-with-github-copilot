import pytest
from fastapi.testclient import TestClient
from ..app import app

client = TestClient(app, follow_redirects=False)


def test_get_activities():
    """Test retrieving all activities"""
    response = client.get("/activities")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0

    # Check structure of first activity
    first_activity = next(iter(data.values()))
    assert "description" in first_activity
    assert "schedule" in first_activity
    assert "max_participants" in first_activity
    assert "participants" in first_activity
    assert isinstance(first_activity["participants"], list)


def test_root_redirect():
    """Test root endpoint redirects to static HTML"""
    response = client.get("/")
    assert response.status_code in [302, 303, 307, 308]  # Any redirect status
    assert response.headers["location"] == "/static/index.html"


def test_signup_success():
    """Test successful signup for an activity"""
    email = "test@example.com"
    activity = "Chess Club"

    # Get initial participants count
    response = client.get("/activities")
    initial_data = response.json()
    initial_count = len(initial_data[activity]["participants"])

    # Sign up
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert email in data["message"]

    # Verify participant was added
    response = client.get("/activities")
    updated_data = response.json()
    assert email in updated_data[activity]["participants"]
    assert len(updated_data[activity]["participants"]) == initial_count + 1


def test_signup_duplicate():
    """Test signing up for the same activity twice"""
    email = "duplicate@example.com"
    activity = "Programming Class"

    # First signup should succeed
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 200

    # Second signup should fail
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 400

    data = response.json()
    assert "detail" in data
    assert "already signed up" in data["detail"]


def test_signup_invalid_activity():
    """Test signing up for non-existent activity"""
    response = client.post("/activities/InvalidActivity/signup?email=test@example.com")
    assert response.status_code == 404

    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]


def test_unregister_success():
    """Test successful unregistration from an activity"""
    email = "unregister@example.com"
    activity = "Gym Class"

    # First sign up
    client.post(f"/activities/{activity}/signup?email={email}")

    # Get count before unregister
    response = client.get("/activities")
    data = response.json()
    initial_count = len(data[activity]["participants"])

    # Unregister
    response = client.delete(f"/activities/{activity}/participants?email={email}")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert email in data["message"]

    # Verify participant was removed
    response = client.get("/activities")
    updated_data = response.json()
    assert email not in updated_data[activity]["participants"]
    assert len(updated_data[activity]["participants"]) == initial_count - 1


def test_unregister_not_signed_up():
    """Test unregistering a student who is not signed up"""
    email = "notsigned@example.com"
    activity = "Basketball Team"

    response = client.delete(f"/activities/{activity}/participants?email={email}")
    assert response.status_code == 400

    data = response.json()
    assert "detail" in data
    assert "not signed up" in data["detail"]


def test_unregister_invalid_activity():
    """Test unregistering from non-existent activity"""
    response = client.delete("/activities/InvalidActivity/participants?email=test@example.com")
    assert response.status_code == 404

    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]