# tests/test_app.py

# -- basic test for Flask app --

def test_submit():
    """Test the /submit endpoint of the Flask app."""
    from app import app
    client = app.test_client()

    # Test the /submit endpoint with a sample payload
    response = client.post(
        "/submit",
        json={"text": "Sample text", 
              "creator_id": "12345"})
    assert response.status_code == 200
    data = response.get_json()
    print(data)
    assert "content_id" in data
    assert data["attribution"] == "uncertain"
    assert data["confidence"] == 0.5
    assert data["label"] == "We're not sure who wrote this."

def test_rate_limiter():
    """Test rate limiting by making multiple requests to the /submit endpoint."""
    from app import app
    client = app.test_client()

    # Test the rate limiter by making 11 requests in quick succession
    for i in range(10):
        response = client.post(
            "/submit",
            json={"text": "Sample text", 
                  "creator_id": "12345"})
        assert response.status_code == 200

    # The 11th request should be rate limited
    response = client.post(
        "/submit",
        json={"text": "Sample text", 
              "creator_id": "12345"})
    assert response.status_code == 429  # Too Many Requests