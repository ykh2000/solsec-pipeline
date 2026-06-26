import pytest
from fastapi.testclient import TestClient
from backend.main import app
import os

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

def test_analyze_invalid_file_type():
    # Send a text file instead of .sol
    files = {"file": ("test.txt", "some content", "text/plain")}
    response = client.post("/analyze", files=files)
    assert response.status_code == 400
    assert "Only .sol files are supported" in response.json()["detail"]

def test_analyze_success():
    # Path to sample
    sample_path = "tests/sample_vulnerable.sol"
    if not os.path.exists(sample_path):
        pytest.skip("Sample vulnerable file not found")
        
    with open(sample_path, "rb") as f:
        files = {"file": ("sample_vulnerable.sol", f, "application/octet-stream")}
        response = client.post("/analyze", files=files)
        
    assert response.status_code == 200
    data = response.json()
    assert "findings" in data
    assert data["target_file"].endswith("sample_vulnerable.sol")
