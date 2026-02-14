from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from flask.testing import FlaskClient

from sleep_manager import create_app
from sleep_manager.core import ConfigurationError
from sleep_manager.state_machine import SleeperState

pytestmark = pytest.mark.unit


@pytest.fixture
def app(make_config) -> Flask:
    """Create a test Flask application."""
    make_config("waker")
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create a test client."""
    return app.test_client()


class TestWakerEndpoints:
    """Test waker endpoints."""

    def test_config_endpoint_without_api_key(self, client: FlaskClient) -> None:
        """Test config endpoint without API key returns 401."""
        response = client.get("/waker/config")
        assert response.status_code == 401

    def test_config_endpoint_with_api_key(self, client: FlaskClient) -> None:
        """Test config endpoint with valid API key."""
        response = client.get("/waker/config", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
        data = response.get_json()
        assert "name" in data
        assert "wol_exec" in data

    def test_wake_endpoint_without_api_key(self, client: FlaskClient) -> None:
        """Test wake endpoint without API key returns 401."""
        response = client.get("/waker/wake")
        assert response.status_code == 401

    @patch("sleep_manager.waker.subprocess.run")
    def test_wake_endpoint_success(self, mock_run: MagicMock, client: FlaskClient) -> None:
        """Test wake endpoint with valid API key transitions state machine to WAKING."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.args = ["/usr/sbin/etherwake", "00:11:22:33:44:55"]
        mock_run.return_value = mock_result

        response = client.get("/waker/wake", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["op"] == "wake"
        assert data["sleeper"]["mac_address"] == "00:11:22:33:44:55"
        # State machine should be WAKING after wake
        assert data["state"] == "WAKING"

    @patch("sleep_manager.waker.subprocess.run")
    def test_wake_calls_state_machine_wake_requested(
        self, mock_run: MagicMock, app: Flask, client: FlaskClient
    ) -> None:
        """Test wake() calls wake_requested() on state machine."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.args = []
        mock_run.return_value = mock_result

        sm = app.extensions["state_machine"]
        assert sm.get_state() == SleeperState.OFF

        client.get("/waker/wake", headers={"X-API-Key": "test-api-key"})
        assert sm.get_state() == SleeperState.WAKING

    @patch("sleep_manager.waker.subprocess.run")
    def test_wake_endpoint_failure(self, mock_run: MagicMock, client: FlaskClient) -> None:
        """Test wake endpoint when etherwake fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Permission denied"
        mock_run.return_value = mock_result

        response = client.get("/waker/wake", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
        assert data["error"]["type"] == "SystemCommandError"

    @patch("sleep_manager.waker.sleeper_request")
    def test_suspend_endpoint_success(self, mock_sleeper_request: MagicMock, client: FlaskClient) -> None:
        """Test suspend endpoint with valid API key."""
        mock_sleeper_request.return_value = {
            "op": "suspend",
            "sleeper_response": {"status_code": 200, "json": {"op": "suspend"}},
        }

        response = client.get("/waker/suspend", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["op"] == "suspend"

    def test_status_returns_state_machine_state(self, app: Flask, client: FlaskClient) -> None:
        """Test status endpoint returns state machine state, not proxied sleeper response."""
        response = client.get("/waker/status", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["op"] == "status"
        assert "state" in data
        assert "homekit" in data
        # Initial state is OFF
        assert data["state"] == "OFF"
        assert data["homekit"] == "off"

    def test_status_on_state(self, app: Flask, client: FlaskClient) -> None:
        """Test status returns on/homekit=on when state machine is ON."""
        sm = app.extensions["state_machine"]
        sm.heartbeat_received()  # OFF -> ON

        response = client.get("/waker/status", headers={"X-API-Key": "test-api-key"})
        data = response.get_json()
        assert data["state"] == "ON"
        assert data["homekit"] == "on"

    def test_status_failed_state(self, app: Flask, client: FlaskClient) -> None:
        """Test status returns failed/homekit=failed when state machine is FAILED."""
        sm = app.extensions["state_machine"]
        # Force FAILED state by manipulating internal state directly
        from sleep_manager.state_machine import SleeperState
        with sm._lock:
            sm.state = SleeperState.FAILED

        response = client.get("/waker/status", headers={"X-API-Key": "test-api-key"})
        data = response.get_json()
        assert data["state"] == "FAILED"
        assert data["homekit"] == "failed"

    def test_heartbeat_endpoint_without_api_key(self, client: FlaskClient) -> None:
        """Test heartbeat endpoint without API key returns 401."""
        response = client.post("/waker/heartbeat")
        assert response.status_code == 401

    def test_heartbeat_endpoint_transitions_state(self, app: Flask, client: FlaskClient) -> None:
        """Test POST /waker/heartbeat transitions state machine and returns state."""
        sm = app.extensions["state_machine"]
        assert sm.get_state() == SleeperState.OFF

        response = client.post("/waker/heartbeat", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["op"] == "heartbeat"
        assert data["state"] == "ON"
        assert sm.get_state() == SleeperState.ON

    def test_heartbeat_endpoint_waking_to_on(self, app: Flask, client: FlaskClient) -> None:
        """Test heartbeat received while WAKING transitions to ON."""
        sm = app.extensions["state_machine"]
        sm.wake_requested()  # OFF -> WAKING
        assert sm.get_state() == SleeperState.WAKING

        response = client.post("/waker/heartbeat", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["state"] == "ON"


class TestWakerConfiguration:
    """Test waker configuration handling."""

    def test_missing_configuration(self) -> None:
        """Test handling of missing configuration."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.config["COMMON"] = {"api_key": "test-api-key"}
        # Missing waker configuration

        with app.app_context():
            from sleep_manager.waker import waker_url

            with pytest.raises(ConfigurationError):
                waker_url()

    def test_waker_url_generation(self) -> None:
        """Test waker URL generation."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.config["COMMON"] = {"domain": "test.local", "port": 5000}
        app.config["WAKER"] = {"name": "test-waker"}

        with app.app_context():
            from sleep_manager.waker import waker_url

            url = waker_url()
            assert url == "http://test-waker.test.local:5000/waker"


class TestSleeperRequest:
    """Test sleeper request functionality."""

    @patch("sleep_manager.waker.requests.get")
    def test_sleeper_request_success(self, mock_get: MagicMock, app: Flask) -> None:
        """Test successful sleeper request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"op": "status", "status": "running"}
        mock_response.text = '{"op": "status", "status": "running"}'
        mock_response.url = "http://test-sleeper.test.local:5000/sleeper/status"
        mock_get.return_value = mock_response

        with app.app_context():
            from sleep_manager.waker import sleeper_request

            result = sleeper_request("status")
            assert result["op"] == "status"
            assert result["sleeper_response"]["status_code"] == 200

    @patch("sleep_manager.waker.requests.get")
    def test_sleeper_request_timeout(self, mock_get: MagicMock, app: Flask) -> None:
        """Test sleeper request timeout."""
        from requests.exceptions import Timeout

        mock_get.side_effect = Timeout("Request timed out")

        with app.app_context():
            from sleep_manager.waker import sleeper_request

            result = sleeper_request("status")
            assert result["op"] == "status"
            assert result["sleeper_status"] == "down"
            assert result["error"] == "Sleeper machine is not reachable"
            assert "Request to sleeper timed out" in result["details"]

    @patch("sleep_manager.waker.requests.get")
    def test_sleeper_request_connection_error(self, mock_get: MagicMock, app: Flask) -> None:
        """Test sleeper request connection error."""
        from requests.exceptions import ConnectionError

        mock_get.side_effect = ConnectionError("Connection failed")

        with app.app_context():
            from sleep_manager.waker import sleeper_request

            result = sleeper_request("status")
            assert result["op"] == "status"
            assert result["sleeper_status"] == "down"
            assert result["error"] == "Sleeper machine is not reachable"
            assert "Connection refused" in result["details"]

    @patch("sleep_manager.waker.requests.get")
    def test_sleeper_request_http_error(self, mock_get: MagicMock, app: Flask) -> None:
        """Test sleeper request with HTTP error response."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.ok = False
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        with app.app_context():
            from sleep_manager.waker import sleeper_request

            result = sleeper_request("status")
            assert result["op"] == "status"
            assert result["sleeper_status"] == "error"
            assert result["error"] == "Sleeper responded with error code 500"
            assert result["details"] == "Internal Server Error"

    @patch("sleep_manager.waker.requests.get")
    def test_sleeper_request_timeout_status_code(self, mock_get: MagicMock, app: Flask) -> None:
        """Test sleeper request with 408 timeout status code."""
        mock_response = MagicMock()
        mock_response.status_code = 408
        mock_response.ok = False
        mock_get.return_value = mock_response

        with app.app_context():
            from sleep_manager.waker import sleeper_request

            result = sleeper_request("status")
            assert result["op"] == "status"
            assert result["sleeper_status"] == "down"
            assert result["error"] == "Sleeper machine is not reachable"
            assert result["details"] == "Request to sleeper timed out"

    @patch("sleep_manager.waker.requests.get")
    def test_sleeper_request_general_request_exception(self, mock_get: MagicMock, app: Flask) -> None:
        """Test sleeper request with general request exception."""
        from requests.exceptions import RequestException

        mock_get.side_effect = RequestException("Network error")

        with app.app_context():
            from sleep_manager.waker import sleeper_request

            result = sleeper_request("status")
            assert result["op"] == "status"
            assert result["sleeper_status"] == "down"
            assert result["error"] == "Sleeper machine is not reachable"
            assert "Network error" in result["details"]
