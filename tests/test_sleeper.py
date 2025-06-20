import pytest
import subprocess
from unittest.mock import patch, MagicMock
from flask import Flask
from sleep_manager import create_app, ConfigurationError, SystemCommandError


@pytest.fixture
def app():
    """Create a test Flask application."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['API_KEY'] = 'test-api-key'
    app.config['SLEEPER'] = {
        'name': 'test-sleeper',
        'mac_address': '00:11:22:33:44:55',
        'systemctl_command': '/usr/bin/systemctl',
        'suspend_verb': 'suspend',
        'status_verb': 'is-system-running'
    }
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


class TestSleeperEndpoints:
    """Test sleeper endpoints."""

    def test_config_endpoint_without_api_key(self, client):
        """Test config endpoint without API key returns 401."""
        response = client.get('/sleeper/config')
        assert response.status_code == 401

    def test_config_endpoint_with_api_key(self, client):
        """Test config endpoint with valid API key."""
        response = client.get('/sleeper/config', headers={'X-API-Key': 'test-api-key'})
        assert response.status_code == 200
        data = response.get_json()
        assert 'SLEEPER' in data

    def test_suspend_endpoint_without_api_key(self, client):
        """Test suspend endpoint without API key returns 401."""
        response = client.get('/sleeper/suspend')
        assert response.status_code == 401

    @patch('sleep_manager.sleeper.subprocess.Popen')
    def test_suspend_endpoint_success(self, mock_popen, client):
        """Test suspend endpoint with valid API key."""
        mock_popen.return_value = MagicMock()
        
        response = client.get('/sleeper/suspend', headers={'X-API-Key': 'test-api-key'})
        assert response.status_code == 200
        data = response.get_json()
        assert data['op'] == 'suspend'
        assert 'subprocess' in data

    @patch('sleep_manager.sleeper.subprocess.run')
    def test_status_endpoint_success(self, mock_run, client):
        """Test status endpoint with valid API key."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "running"
        mock_result.stderr = ""
        mock_result.args = ['/usr/bin/systemctl', 'is-system-running']
        mock_run.return_value = mock_result
        
        response = client.get('/sleeper/status', headers={'X-API-Key': 'test-api-key'})
        assert response.status_code == 200
        data = response.get_json()
        assert data['op'] == 'status'
        assert data['status'] == 'running'

    @patch('sleep_manager.sleeper.subprocess.run')
    def test_status_endpoint_failure(self, mock_run, client):
        """Test status endpoint when systemctl fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Permission denied"
        mock_run.return_value = mock_result
        
        response = client.get('/sleeper/status', headers={'X-API-Key': 'test-api-key'})
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert data['error']['type'] == 'SystemCommandError'


class TestSleeperConfiguration:
    """Test sleeper configuration handling."""

    def test_missing_configuration(self):
        """Test handling of missing configuration."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['API_KEY'] = 'test-api-key'
        # Missing SLEEPER configuration
        
        with app.app_context():
            from sleep_manager.sleeper import sleeper_url
            with pytest.raises(ConfigurationError):
                sleeper_url()

    def test_sleeper_url_generation(self):
        """Test sleeper URL generation."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['DOMAIN'] = 'test.local'
        app.config['PORT'] = 5000
        app.config['SLEEPER'] = {'name': 'test-sleeper'}
        
        with app.app_context():
            from sleep_manager.sleeper import sleeper_url
            url = sleeper_url()
            assert url == 'http://test-sleeper.test.local:5000/sleeper' 