import os
import requests
import socket


def test_health_endpoint_available():
    url = os.environ.get('TEST_FLASK_URL', 'http://127.0.0.1:5050/health')
    try:
        resp = requests.get(url, timeout=5)
        assert resp.status_code == 200, f'health endpoint returned {resp.status_code}'
        data = resp.json()
        assert data.get('status') == 'ok'
    except requests.ConnectionError as e:
        # Connection failed — provide a helpful message for debugging
        raise AssertionError(f'Could not connect to Flask server at {url}: {e}')
