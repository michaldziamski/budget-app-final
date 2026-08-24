from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase
from rest_framework import status

# Mock Google auth libraries if not available
try:
    from .google_auth_service import GoogleAuthService
except ImportError:
    # If google-auth is not installed, skip these tests
    import unittest
    GoogleAuthService = None


class GoogleAuthServiceTest(TestCase):
    def setUp(self):
        if GoogleAuthService is None:
            self.skipTest("Google auth libraries not installed")
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=True
        )
    
    @patch('budgets.google_auth_service.id_token.verify_oauth2_token')
    @patch('budgets.google_auth_service.settings.GOOGLE_OAUTH2_CLIENT_ID', 'test-client-id')
    def test_verify_google_token_success(self, mock_verify):
        """Test pomyślnej weryfikacji tokena Google"""
        mock_verify.return_value = {
            'email': 'test@example.com',
            'given_name': 'Test',
            'family_name': 'User',
            'picture': 'https://example.com/pic.jpg',
            'sub': 'google-id-123',
            'aud': 'test-client-id'
        }
        
        result = GoogleAuthService.verify_google_token('fake-token')
        
        self.assertEqual(result['email'], 'test@example.com')
        self.assertEqual(result['first_name'], 'Test')
        self.assertEqual(result['last_name'], 'User')
        self.assertEqual(result['google_id'], 'google-id-123')
        mock_verify.assert_called_once()
    
    @patch('budgets.google_auth_service.id_token.verify_oauth2_token')
    @patch('budgets.google_auth_service.settings.GOOGLE_OAUTH2_CLIENT_ID', 'test-client-id')
    def test_verify_google_token_wrong_audience(self, mock_verify):
        """Test weryfikacji tokena z nieprawidłowym aud"""
        mock_verify.return_value = {
            'email': 'test@example.com',
            'aud': 'wrong-client-id'
        }
        
        with self.assertRaises(Exception) as context:
            GoogleAuthService.verify_google_token('fake-token')
        
        self.assertIn('Token nie jest dla tej aplikacji', str(context.exception))
    
    @patch('budgets.google_auth_service.id_token.verify_oauth2_token')
    def test_verify_google_token_invalid(self, mock_verify):
        """Test weryfikacji nieprawidłowego tokena"""
        mock_verify.side_effect = ValueError('Invalid token')
        
        with self.assertRaises(Exception) as context:
            GoogleAuthService.verify_google_token('invalid-token')
        
        self.assertIn('Nieprawidłowy token Google', str(context.exception))
    
    @patch('budgets.google_auth_service.GoogleAuthService.verify_google_token')
    def test_login_with_google_success(self, mock_verify):
        """Test pomyślnego logowania przez Google"""
        mock_verify.return_value = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'google_id': 'google-id-123'
        }
        
        result = GoogleAuthService.login_with_google('fake-token')
        
        self.assertIn('access', result)
        self.assertIn('refresh', result)
        self.assertIn('user', result)
        self.assertEqual(result['user']['email'], 'test@example.com')
        self.assertEqual(result['user']['username'], 'testuser')
    
    @patch('budgets.google_auth_service.GoogleAuthService.verify_google_token')
    def test_login_with_google_nonexistent_user(self, mock_verify):
        """Test logowania przez Google dla nieistniejącego użytkownika"""
        mock_verify.return_value = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'google_id': 'google-id-456'
        }
        
        with self.assertRaises(Exception) as context:
            GoogleAuthService.login_with_google('fake-token')
        
        self.assertIn('Konto z tym adresem email nie istnieje', str(context.exception))
    
    @patch('budgets.google_auth_service.GoogleAuthService.verify_google_token')
    def test_login_with_google_inactive_user(self, mock_verify):
        """Test logowania przez Google dla nieaktywnego użytkownika"""
        inactive_user = User.objects.create_user(
            username='inactiveuser',
            email='inactive@example.com',
            password='testpass123',
            is_active=False
        )
        
        mock_verify.return_value = {
            'email': 'inactive@example.com',
            'first_name': 'Inactive',
            'last_name': 'User',
            'google_id': 'google-id-789'
        }
        
        with self.assertRaises(Exception) as context:
            GoogleAuthService.login_with_google('fake-token')
        
        self.assertIn('Konto nie jest aktywne', str(context.exception))
    
    @patch('budgets.google_auth_service.GoogleAuthService.verify_google_token')
    def test_login_with_google_no_email(self, mock_verify):
        """Test logowania przez Google bez emaila w tokenie"""
        mock_verify.return_value = {
            'first_name': 'Test',
            'last_name': 'User',
            'google_id': 'google-id-123'
        }
        
        with self.assertRaises(Exception) as context:
            GoogleAuthService.login_with_google('fake-token')
        
        self.assertIn('Email nie został znaleziony', str(context.exception))


class GoogleLoginAPITest(APITestCase):
    def setUp(self):
        if GoogleAuthService is None:
            self.skipTest("Google auth libraries not installed")
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=True
        )
        self.google_login_url = reverse('google-login')
    
    @patch('budgets.google_auth_service.GoogleAuthService.login_with_google')
    def test_google_login_success(self, mock_login):
        """Test pomyślnego logowania przez Google API"""
        mock_login.return_value = {
            'access': 'access-token',
            'refresh': 'refresh-token',
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'first_name': '',
                'last_name': ''
            }
        }
        
        data = {'token': 'google-id-token'}
        response = self.client.post(self.google_login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        mock_login.assert_called_once_with('google-id-token')
    
    @patch('budgets.google_auth_service.GoogleAuthService.login_with_google')
    def test_google_login_missing_token(self, mock_login):
        """Test logowania przez Google bez tokena"""
        response = self.client.post(self.google_login_url, {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        mock_login.assert_not_called()
    
    @patch('budgets.google_auth_service.GoogleAuthService.login_with_google')
    def test_google_login_invalid_token(self, mock_login):
        """Test logowania przez Google z nieprawidłowym tokenem"""
        mock_login.side_effect = Exception('Nieprawidłowy token Google')
        
        data = {'token': 'invalid-token'}
        response = self.client.post(self.google_login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        mock_login.assert_called_once_with('invalid-token')
    
    @patch('budgets.google_auth_service.GoogleAuthService.login_with_google')
    def test_google_login_nonexistent_user(self, mock_login):
        """Test logowania przez Google dla nieistniejącego użytkownika"""
        mock_login.side_effect = Exception('Konto z tym adresem email nie istnieje. Zarejestruj się najpierw przez formularz rejestracji.')
        
        data = {'token': 'google-id-token'}
        response = self.client.post(self.google_login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('nie istnieje', response.data['error'].lower())

