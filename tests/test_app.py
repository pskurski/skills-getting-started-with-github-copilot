"""
Tests for the Mergington High School API application.

This test module uses pytest with the following structure:
- sys.path adjustment to add `src` directory for application imports
- A fixture that deep-copies and restores the activities database for each test
- Five comprehensive tests covering success and error conditions
"""

import sys
from pathlib import Path
import copy
import pytest
from fastapi.testclient import TestClient

# Add src directory to sys.path so we can import app without making src a package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def reset_activities():
    """
    Fixture that restores the activities dictionary to its original state
    before each test, preventing state bleed between tests.
    
    Uses deep copy to ensure nested modifications don't persist.
    """
    # Store the original activities state
    original_activities = copy.deepcopy(activities)
    
    yield  # Run the test
    
    # Restore the original state after the test
    activities.clear()
    activities.update(original_activities)


@pytest.fixture
def client():
    """Provide a TestClient for the FastAPI application."""
    return TestClient(app)


# ============================================================================
# Test 1: Root path redirects to /static/index.html
# ============================================================================
def test_root_redirect(client, reset_activities):
    """
    Arrange: Create a client and prepare for a GET request to root
    Act: Send GET request to /
    Assert: Verify response is a 307 redirect to /static/index.html
    """
    # Arrange
    expected_redirect_url = "/static/index.html"
    
    # Act
    response = client.get("/", follow_redirects=False)
    
    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_redirect_url


# ============================================================================
# Test 2: GET /activities returns all activities
# ============================================================================
def test_get_activities(client, reset_activities):
    """
    Arrange: Initialize the client with the reset activities fixture
    Act: Send GET request to /activities
    Assert: Verify response contains all activities with expected structure
    """
    # Arrange
    expected_activity_names = {
        "Chess Club", "Programming Class", "Gym Class",
        "Basketball Team", "Soccer Club", "Art Studio",
        "Drama Club", "Science Club", "Debate Team"
    }
    
    # Act
    response = client.get("/activities")
    data = response.json()
    
    # Assert
    assert response.status_code == 200
    assert set(data.keys()) == expected_activity_names
    # Verify the structure of an activity
    assert "description" in data["Chess Club"]
    assert "schedule" in data["Chess Club"]
    assert "max_participants" in data["Chess Club"]
    assert "participants" in data["Chess Club"]


# ============================================================================
# Test 3: POST signup with new email succeeds
# ============================================================================
def test_signup_success(client, reset_activities):
    """
    Arrange: Select an activity and a new email address
    Act: Send POST request to sign up with the new email
    Assert: Verify response contains success message and email is added to participants
    """
    # Arrange
    activity_name = "Chess Club"
    new_email = "new_student@mergington.edu"
    original_participant_count = len(activities[activity_name]["participants"])
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email}
    )
    data = response.json()
    
    # Assert
    assert response.status_code == 200
    assert data["message"] == f"Signed up {new_email} for {activity_name}"
    assert new_email in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == original_participant_count + 1


# ============================================================================
# Test 4: POST signup for unknown activity returns 404
# ============================================================================
def test_signup_unknown_activity(client, reset_activities):
    """
    Arrange: Create parameters for a non-existent activity
    Act: Send POST request to sign up for unknown activity
    Assert: Verify response is 404 with appropriate error message
    """
    # Arrange
    unknown_activity = "Nonexistent Club"
    email = "student@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{unknown_activity}/signup",
        params={"email": email}
    )
    data = response.json()
    
    # Assert
    assert response.status_code == 404
    assert data["detail"] == "Activity not found"


# ============================================================================
# Test 5: POST signup with already-signed-up email returns 400
# ============================================================================
def test_signup_already_signed_up(client, reset_activities):
    """
    Arrange: Select an activity and an email already in its participants list
    Act: Send POST request to sign up with the existing email
    Assert: Verify response is 400 with appropriate error message
    """
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"  # Already in Chess Club participants
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email}
    )
    data = response.json()
    
    # Assert
    assert response.status_code == 400
    assert data["detail"] == "Student already signed up"
