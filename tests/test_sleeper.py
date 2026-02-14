import threading
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from flask.testing import FlaskClient

from sleep_manager import create_app
from sleep_manager.core import ConfigurationError

pytestmark = pytest.mark.unit


@pytest.fixture
def app(make_config) -> Flask:
    """Create a test Flask application."""
    make_config("sleeper")
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create a test client."""
    return app.test_client()


class TestSleeperEndpoints:
    """Test sleeper endpoints."""

    def test_config_endpoint_without_api_key(self, client: FlaskClient) -> None:
        """Test config endpoint without API key returns 401."""
        response = client.get("/sleeper/config")
        assert response.status_code == 401

    def test_config_endpoint_with_api_key(self, client: FlaskClient) -> None:
        """Test config endpoint with valid API key."""
        response = client.get("/sleeper/config", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
        data = response.get_json()
        assert "SLEEPER" in data

    def test_config_endpoint_sanitizes_bytes(self, app: Flask, client: FlaskClient) -> None:
        """Test config endpoint sanitizes bytes values."""
        app.config["CUSTOM_BYTES"] = b"hello"
        app.config["CUSTOM_LIST"] = [b"\xff", "ok"]
        response = client.get("/sleeper/config", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["CUSTOM_BYTES"] == "hello"
        assert data["CUSTOM_LIST"][0] == "b'\\xff'"
        assert data["CUSTOM_LIST"][1] == "ok"

    def test_suspend_endpoint_without_api_key(self, client: FlaskClient) -> None:
        """Test suspend endpoint without API key returns 401."""
        response = client.get("/sleeper/suspend")
        assert response.status_code == 401

    @patch("sleep_manager.sleeper.subprocess.Popen")
    def test_suspend_endpoint_success(self, mock_popen: MagicMock, client: FlaskClient) -> None:
        """Test suspend endpoint with valid API key."""
        mock_popen.return_value = MagicMock()

        response = client.get("/sleeper/suspend", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["op"] == "suspend"
        assert "subprocess" in data

    @patch("sleep_manager.sleeper.subprocess.run")
    def test_status_endpoint_success(self, mock_run: MagicMock, client: FlaskClient) -> None:
        """Test status endpoint with valid API key."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "running"
        mock_result.stderr = ""
        mock_result.args = ["/usr/bin/systemctl", "is-system-running"]
        mock_run.return_value = mock_result

        response = client.get("/sleeper/status", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["op"] == "status"
        assert data["status"] == "running"

    @patch("sleep_manager.sleeper.subprocess.run")
    def test_status_endpoint_failure(self, mock_run: MagicMock, client: FlaskClient) -> None:
        """Test status endpoint when systemctl fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Permission denied"
        mock_run.return_value = mock_result

        response = client.get("/sleeper/status", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
        assert data["error"]["type"] == "SystemCommandError"


class TestSleeperConfiguration:
    """Test sleeper configuration handling."""

    def test_missing_configuration(self) -> None:
        """Test handling of missing configuration."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.config["COMMON"] = {"api_key": "test-api-key"}
        # Missing sleeper configuration

        with app.app_context():
            from sleep_manager.sleeper import sleeper_url

            with pytest.raises(ConfigurationError):
                sleeper_url()

    def test_sleeper_url_generation(self) -> None:
        """Test sleeper URL generation."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.config["COMMON"] = {"domain": "test.local", "port": 5000}
        app.config["SLEEPER"] = {"name": "test-sleeper"}

        with app.app_context():
            from sleep_manager.sleeper import sleeper_url

            url = sleeper_url()
            assert url == "http://test-sleeper.test.local:5000/sleeper"


class TestHeartbeatSender:
    """Test the heartbeat sender daemon thread."""

    def test_heartbeat_sender_starts_on_sleeper_app_creation(self, make_config) -> None:
        """Test that heartbeat sender thread is started when sleeper app is created."""
        make_config("sleeper")
        app = create_app()
        app.config["TESTING"] = True
        threads_after = {t.name for t in threading.enumerate()}
        assert "heartbeat-sender" in threads_after

    @patch("sleep_manager.sleeper.requests.post")
    def test_heartbeat_sender_posts_to_waker(self, mock_post: MagicMock, make_config) -> None:
        """Test that the heartbeat sender thread POSTs to the waker heartbeat endpoint."""
        make_config("sleeper")

        posted_urls: list[str] = []
        event = threading.Event()

        def fake_post(url, **kwargs):
            posted_urls.append(url)
            event.set()
            resp = MagicMock()
            resp.json.return_value = {"op": "heartbeat", "state": "ON"}
            return resp

        mock_post.side_effect = fake_post

        # Patch time.sleep in sleeper to avoid real 60s wait
        with patch("sleep_manager.sleeper.time.sleep", return_value=None):
            from sleep_manager.sleeper import _start_heartbeat_sender
            flask_app = Flask(__name__)
            flask_app.config["TESTING"] = True
            flask_app.config["COMMON"] = {
                "heartbeat_interval": 60,
                "domain": "test.local",
                "port": 5000,
                "api_key": "test-api-key",
            }
            flask_app.config["WAKER"] = {"name": "test-waker"}
            flask_app.config["SLEEPER"] = {}

            _start_heartbeat_sender(flask_app)
            # Give the thread a moment to make the POST
            event.wait(timeout=2.0)

        assert any("heartbeat" in url for url in posted_urls), f"No heartbeat POST, got: {posted_urls}"
