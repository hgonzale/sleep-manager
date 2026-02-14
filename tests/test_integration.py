from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from flask.testing import FlaskClient

from sleep_manager import create_app

pytestmark = pytest.mark.integration


@pytest.fixture
def sleeper_app(make_config) -> Flask:
    """Create a test Flask application configured as sleeper."""
    make_config("sleeper")
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def waker_app(make_config) -> Flask:
    """Create a test Flask application configured as waker."""
    make_config("waker")
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def sleeper_client(sleeper_app: Flask) -> FlaskClient:
    """Create a test client for sleeper role."""
    return sleeper_app.test_client()


@pytest.fixture
def waker_client(waker_app: Flask) -> FlaskClient:
    """Create a test client for waker role."""
    return waker_app.test_client()


class TestIntegration:
    """Integration tests for the full application."""

    def test_health_endpoint(self, sleeper_client: FlaskClient) -> None:
        """Test the health endpoint."""
        response = sleeper_client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert "status" in data
        assert "config" in data
        assert "commands" in data

    def test_welcome_endpoint(self, sleeper_client: FlaskClient) -> None:
        """Test the welcome endpoint."""
        response = sleeper_client.get("/")
        assert response.status_code == 200
        assert "Welcome to sleep manager!" in response.get_data(as_text=True)

    def test_waker_status_uses_state_machine(
        self,
        waker_app: Flask,
        waker_client: FlaskClient,
    ) -> None:
        """Test waker status endpoint returns state machine state (not proxied sleeper response)."""
        # Initial state is OFF
        response = waker_client.get("/waker/status", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["op"] == "status"
        assert data["state"] == "OFF"
        assert data["homekit"] == "off"

        # Simulate a heartbeat arriving → ON
        sm = waker_app.extensions["state_machine"]
        sm.heartbeat_received()

        response = waker_client.get("/waker/status", headers={"X-API-Key": "test-api-key"})
        data = response.get_json()
        assert data["state"] == "ON"
        assert data["homekit"] == "on"

    def test_error_handling(self, sleeper_client: FlaskClient) -> None:
        """Test error handling for invalid endpoints."""
        response = sleeper_client.get("/invalid-endpoint")
        assert response.status_code == 404

    def test_api_key_validation_sleeper(self, sleeper_client: FlaskClient) -> None:
        """Test API key validation across sleeper endpoints."""
        endpoints = ["/sleeper/config", "/sleeper/status", "/sleeper/suspend"]

        for endpoint in endpoints:
            response = sleeper_client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require API key"

    def test_api_key_validation_waker(self, waker_client: FlaskClient) -> None:
        """Test API key validation across waker endpoints."""
        endpoints = ["/waker/config", "/waker/wake", "/waker/status", "/waker/suspend"]

        for endpoint in endpoints:
            response = waker_client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require API key"

    @patch("sleep_manager.sleeper.subprocess.run")
    def test_sleeper_status_flow(self, mock_run: MagicMock, sleeper_client: FlaskClient) -> None:
        """Test complete sleeper status flow."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "running"
        mock_result.stderr = ""
        mock_result.args = ["/usr/bin/systemctl", "is-system-running"]
        mock_run.return_value = mock_result

        response = sleeper_client.get("/sleeper/status", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["op"] == "status"
        assert data["status"] == "running"
        assert data["subprocess"]["returncode"] == 0

    @patch("sleep_manager.waker.subprocess.run")
    def test_waker_wake_flow(self, mock_run: MagicMock, waker_client: FlaskClient) -> None:
        """Test complete waker wake flow."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.args = ["/usr/sbin/etherwake", "00:11:22:33:44:55"]
        mock_run.return_value = mock_result

        response = waker_client.get("/waker/wake", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["op"] == "wake"
        assert data["sleeper"]["mac_address"] == "00:11:22:33:44:55"
        assert data["subprocess"]["returncode"] == 0


class TestConfiguration:
    """Test configuration handling."""

    def test_missing_api_key(self, make_config) -> None:
        """Test application with missing API key."""
        make_config("sleeper")
        app = create_app()
        app.config["TESTING"] = True
        # Remove api_key if present
        common = app.config.get("COMMON")
        if isinstance(common, dict) and "api_key" in common:
            del common["api_key"]
        client = app.test_client()
        # Call a protected endpoint
        response = client.get("/sleeper/config", headers={"X-API-Key": "test-api-key"})
        # Should return 500 (or 401, depending on your error handling)
        assert response.status_code in (401, 500)

    def test_complete_configuration(self, make_config) -> None:
        """Test application with complete configuration."""
        make_config("waker")
        app = create_app()
        app.config["TESTING"] = True

        # Should not raise any exceptions
        with app.app_context():
            from sleep_manager.sleeper import sleeper_url
            from sleep_manager.waker import waker_url

            sleeper_url()
            waker_url()
