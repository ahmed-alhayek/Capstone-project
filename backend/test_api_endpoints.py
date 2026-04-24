import unittest
import json
from app import app

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_health_endpoint(self):
        """Test the health check endpoint returns 200 OK"""
        response = self.app.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data.get('status'), 'ok')

    def test_mock_chat_without_auth(self):
        """Test the chat endpoint requires authentication"""
        response = self.app.post('/api/chat', json={"message": "Hello!"})
        self.assertEqual(response.status_code, 401)
        
        data = json.loads(response.data)
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()
