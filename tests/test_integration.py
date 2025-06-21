import pytest
import subprocess
from unittest.mock import patch, MagicMock
from sleep_manager import create_app


@pytest.fixture
def app():
    """Create a test Flask application."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['API_KEY'] = 'test-api-key'
    app.config['DOMAIN'] = 'test.local'
    app.config['PORT'] = 5000
    app.config['DEFAULT_REQUEST_TIMEOUT'] = 3
    app.config['SLEEPER'] = {
        'name': 'test-sleeper',
        'mac_address': '00:11:22:33:44:55',
        'systemctl_command': '/usr/bin/systemctl',
        'suspend_verb': 'suspend',
        'status_verb': 'is-system-running'
    }
    app.config['WAKER'] = {
        'name': 'test-waker',
        'wol_exec': '/usr/sbin/etherwake'
    }
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


class TestIntegration:
    """Integration tests for the full application."""

    def test_health_endpoint(self, client):
        """Test the health endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert 'config' in data
        assert 'commands' in data

    def test_welcome_endpoint(self, client):
        """Test the welcome endpoint."""
        response = client.get('/')
        assert response.status_code == 200
        assert 'Welcome to sleep manager!' in response.get_data(as_text=True)

    @patch('sleep_manager.waker.requests.get')
    @patch('sleep_manager.sleeper.subprocess.run')
    def test_waker_to_sleeper_communication(self, mock_sleeper_run, mock_waker_get, client):
        """Test waker communicating with sleeper."""
        # Mock sleeper response
        mock_sleeper_response = MagicMock()
        mock_sleeper_response.status_code = 200
        mock_sleeper_response.ok = True
        mock_sleeper_response.json.return_value = {
            'op': 'status',
            'status': 'running',
            'subprocess': {
                'returncode': 0,
                'stdout': 'running'
            }
        }
        mock_sleeper_response.text = '{"op": "status", "status": "running"}'
        mock_sleeper_response.url = 'http://test-sleeper.test.local:5000/sleeper/status'
        mock_waker_get.return_value = mock_sleeper_response

        # Test waker status endpoint
        response = client.get('/waker/status', headers={'X-API-Key': 'test-api-key'})
        assert response.status_code == 200
        data = response.get_json()
        assert data['op'] == 'status'
        assert data['sleeper_response']['status_code'] == 200

    def test_error_handling(self, client):
        """Test error handling for invalid endpoints."""
        response = client.get('/invalid-endpoint')
        assert response.status_code == 404

    def test_api_key_validation(self, client):
        """Test API key validation across all endpoints."""
        endpoints = [
            '/sleeper/config',
            '/sleeper/status',
            '/sleeper/suspend',
            '/waker/config',
            '/waker/wake',
            '/waker/status',
            '/waker/suspend'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require API key"

    @patch('sleep_manager.sleeper.subprocess.run')
    def test_sleeper_status_flow(self, mock_run, client):
        """Test complete sleeper status flow."""
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
        assert data['subprocess']['returncode'] == 0

    @patch('sleep_manager.waker.subprocess.run')
    def test_waker_wake_flow(self, mock_run, client):
        """Test complete waker wake flow."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.args = ['/usr/sbin/etherwake', '00:11:22:33:44:55']
        mock_run.return_value = mock_result
        
        response = client.get('/waker/wake', headers={'X-API-Key': 'test-api-key'})
        assert response.status_code == 200
        data = response.get_json()
        assert data['op'] == 'wake'
        assert data['sleeper']['mac_address'] == '00:11:22:33:44:55'
        assert data['subprocess']['returncode'] == 0


class TestConfiguration:
    """Test configuration handling."""

    def test_missing_api_key(self):
        """Test application with missing API key."""
        app = create_app()
        app.config['TESTING'] = True
        # Remove API_KEY if present
        if 'API_KEY' in app.config:
            del app.config['API_KEY']
        client = app.test_client()
        # Call a protected endpoint
        response = client.get('/sleeper/config', headers={'X-API-Key': 'test-api-key'})
        # Should return 500 (or 401, depending on your error handling)
        assert response.status_code in (401, 500)

    def test_complete_configuration(self):
        """Test application with complete configuration."""
        app = create_app()
        app.config['TESTING'] = True
        app.config['API_KEY'] = 'test-key'
        app.config['DOMAIN'] = 'test.local'
        app.config['PORT'] = 5000
        app.config['DEFAULT_REQUEST_TIMEOUT'] = 3
        app.config['SLEEPER'] = {
            'name': 'test-sleeper',
            'mac_address': '00:11:22:33:44:55',
            'systemctl_command': '/usr/bin/systemctl',
            'suspend_verb': 'suspend',
            'status_verb': 'is-system-running'
        }
        app.config['WAKER'] = {
            'name': 'test-waker',
            'wol_exec': '/usr/sbin/etherwake'
        }
        
        # Should not raise any exceptions
        with app.app_context():
            from sleep_manager.sleeper import sleeper_url
            from sleep_manager.waker import waker_url
            sleeper_url()
            waker_url() 