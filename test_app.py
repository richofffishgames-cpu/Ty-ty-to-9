import unittest
from unittest.mock import MagicMock, patch
import json
import os

# Mock GCP environment variables before importing app
os.environ['PROJECT_ID'] = 'test-project'
os.environ['ARTIFACT_BUCKET'] = 'test-bucket'

from app import app

class ReconAgentTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_health_check(self):
        response = self.app.get('/health')
        data = json.loads(response.get_data(as_text=True))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['config']['project_id'], 'test-project')

    @patch('app.get_gcp_clients')
    @patch('nmap.PortScanner')
    def test_scan_target_success(self, mock_nmap, mock_gcp):
        # Setup mocks
        mock_publisher = MagicMock()
        mock_db = MagicMock()
        mock_storage = MagicMock()
        mock_bucket = MagicMock()
        mock_gcp.return_value = (mock_publisher, mock_db, mock_storage, mock_bucket)

        # Mock nmap
        mock_nm_instance = mock_nmap.return_value
        mock_nm_instance.all_hosts.return_value = ['127.0.0.1']

        # Mock the host dictionary object
        mock_host_info = MagicMock()
        mock_host_info.state.return_value = 'up'
        mock_host_info.all_protocols.return_value = ['tcp']
        mock_host_info.__getitem__.side_effect = lambda key: {
            80: {'state': 'open', 'name': 'http', 'version': '1.0', 'product': 'nginx', 'extrainfo': '', 'conf': '10'}
        } if key == 'tcp' else None

        mock_nm_instance.__getitem__.return_value = mock_host_info
        mock_nm_instance.xml_output.return_value = '<xml>test</xml>'

        # Request
        payload = {
            "target": "127.0.0.1",
            "scan_type": "basic"
        }
        response = self.app.post('/', data=json.dumps(payload), content_type='application/json')
        data = json.loads(response.get_data(as_text=True))

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'completed')
        self.assertEqual(data['hypotheses_generated'], 1)

        # Verify bug fix: xml_output was called
        mock_nm_instance.xml_output.assert_called_once()

        # Verify storage interaction
        mock_bucket.blob.assert_called_once()
        mock_bucket.blob.return_value.upload_from_string.assert_called_with('<xml>test</xml>')

        # Verify DB interaction
        mock_db.collection.assert_called()

        # Verify Pub/Sub interaction
        mock_publisher.publish.assert_called_once()

    def test_scan_target_missing_target(self):
        payload = {"scan_type": "basic"}
        response = self.app.post('/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Target is required', response.get_data(as_text=True))

    def test_scan_target_misconfigured(self):
        with patch.dict(os.environ, {'PROJECT_ID': ''}):
            import app as app_module
            old_val = app_module.PROJECT_ID
            app_module.PROJECT_ID = None

            payload = {"target": "127.0.0.1"}
            response = self.app.post('/', data=json.dumps(payload), content_type='application/json')
            self.assertEqual(response.status_code, 500)
            self.assertIn('Service misconfigured', response.get_data(as_text=True))

            # Reset for other tests
            app_module.PROJECT_ID = old_val

if __name__ == '__main__':
    unittest.main()
