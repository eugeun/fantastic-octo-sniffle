import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities dict before each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_root_redirect():
    # don't automatically follow redirects so we can verify the status code
    response = client.get("/", follow_redirects=False)
    # FastAPI's RedirectResponse uses 307 Temporary Redirect by default
    assert response.status_code in (307, 308)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_success():
    email = "newstudent@mergington.edu"
    activity = "Chess Club"
    response = client.post(
        f"/activities/{activity}/signup", params={"email": email}
    )
    assert response.status_code == 200
    assert email in activities[activity]["participants"]
    assert "Signed up" in response.json()["message"]


def test_signup_already_registered():
    activity = "Chess Club"
    email = activities[activity]["participants"][0]
    response = client.post(
        f"/activities/{activity}/signup", params={"email": email}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_activity_not_found():
    response = client.post(
        "/activities/Nonexistent/signup", params={"email": "test@example.com"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_success():
    activity = "Chess Club"
    email = activities[activity]["participants"][0]
    response = client.delete(
        f"/activities/{activity}/participants", params={"email": email}
    )
    assert response.status_code == 200
    assert email not in activities[activity]["participants"]
    assert "Removed" in response.json()["message"]


def test_remove_participant_not_registered():
    activity = "Chess Club"
    response = client.delete(
        f"/activities/{activity}/participants", params={"email": "not@here.edu"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Student not registered for this activity"


def test_remove_participant_activity_not_found():
    response = client.delete(
        "/activities/Nonexistent/participants", params={"email": "test@example.com"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
