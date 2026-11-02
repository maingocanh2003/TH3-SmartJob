from django.test import RequestFactory, TestCase
from django.core import signing
from django.core.management import call_command
from rest_framework.test import APIClient
from unittest.mock import patch

from .authentication import SmartJobTokenAuthentication
from .models import Users


class AuthenticationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_candidate_can_register_and_login_with_frontend_fields(self):
        registration = self.client.post('/api/auth/register/', {
            'email': 'candidate-login-test@example.com',
            'password': 'TestPass123!',
            'user_type': 'candidate',
            'full_name': 'Test Candidate',
        }, format='json')

        self.assertEqual(registration.status_code, 201)
        response = self.client.post('/api/auth/login/', {
            'email': 'CANDIDATE-LOGIN-TEST@example.com',
            'password': 'TestPass123!',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user_type'], 'candidate')
        self.assertEqual(response.data['email'], 'candidate-login-test@example.com')
        self.assertEqual(response.data['full_name'], 'Test Candidate')
        self.assertIn('candidate_id', response.data)
        self.assertTrue(response.data['token'])

    def test_company_login_includes_company_profile_fields(self):
        self.client.post('/api/auth/register/', {
            'email': 'company-login-test@example.com',
            'password': 'TestPass123!',
            'user_type': 'company',
            'company_name': 'Test Company',
        }, format='json')

        response = self.client.post('/api/auth/login/', {
            'email': 'company-login-test@example.com',
            'password': 'TestPass123!',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user_type'], 'company')
        self.assertEqual(response.data['company_name'], 'Test Company')
        self.assertIn('company_id', response.data)

    def test_public_registration_cannot_create_admin_accounts(self):
        response = self.client.post('/api/auth/register/', {
            'email': 'admin-login-test@example.com',
            'password': 'TestPass123!',
            'user_type': 'admin',
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Users.objects.filter(email='admin-login-test@example.com').exists())

    @patch(
        'api.management.commands.create_smartjob_admin.getpass',
        side_effect=['SecureAdminPass!42', 'SecureAdminPass!42'],
    )
    def test_created_admin_can_login(self, _mock_getpass):
        call_command('create_smartjob_admin', email='admin-login-test@example.com', verbosity=0)

        response = self.client.post('/api/auth/login/', {
            'email': 'admin-login-test@example.com',
            'password': 'SecureAdminPass!42',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user_type'], 'admin')
        self.assertTrue(response.data['token'])

    def test_issued_login_token_authenticates_user(self):
        user = Users.objects.create(
            email='token-login-test@example.com',
            password_hash='unused',
            user_type='candidate',
            is_active=True,
        )
        token = signing.dumps(user.user_id, salt=SmartJobTokenAuthentication.salt)

        request = RequestFactory().get(
            '/api/skills/',
            HTTP_AUTHORIZATION=f'Token {token}',
        )
        authenticated_user, _ = SmartJobTokenAuthentication().authenticate(request)

        self.assertEqual(authenticated_user.user_id, user.user_id)
