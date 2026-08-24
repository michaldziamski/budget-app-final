from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailVerificationToken


class EmailVerificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=False  # Użytkownik nieaktywny przed weryfikacją
        )
    
    def test_create_verification_token(self):
        """Test tworzenia tokenu weryfikacyjnego"""
        token = EmailVerificationToken.create_for_user(self.user)
        
        self.assertIsNotNone(token)
        self.assertEqual(token.user, self.user)
        self.assertFalse(token.is_used)
        self.assertFalse(token.is_expired())
        self.assertIsNotNone(token.token)
        self.assertEqual(len(token.token), 36)  # UUID ma 36 znaków
    
    def test_token_expiration(self):
        """Test wygasania tokenu"""
        token = EmailVerificationToken.create_for_user(self.user)
        
        # Token powinien być ważny przez 24 godziny
        self.assertFalse(token.is_expired())
        
        # Symuluj wygasły token
        token.expires_at = timezone.now() - timedelta(hours=1)
        token.save()
        
        self.assertTrue(token.is_expired())
    
    def test_token_is_valid(self):
        """Test sprawdzania ważności tokenu"""
        token = EmailVerificationToken.create_for_user(self.user)
        
        # Nowy token powinien być ważny
        self.assertTrue(token.is_valid())
        
        # Użyty token nie powinien być ważny
        token.is_used = True
        token.save()
        self.assertFalse(token.is_valid())
        
        # Wygasły token nie powinien być ważny
        token2 = EmailVerificationToken.create_for_user(self.user)
        token2.expires_at = timezone.now() - timedelta(hours=1)
        token2.save()
        self.assertFalse(token2.is_valid())
    
    def test_replace_old_token(self):
        """Test zastępowania starego tokenu nowym"""
        token1 = EmailVerificationToken.create_for_user(self.user)
        token1_id = token1.id
        
        # Utwórz nowy token - stary powinien zostać usunięty
        token2 = EmailVerificationToken.create_for_user(self.user)
        
        # Sprawdź czy stary token został usunięty
        self.assertFalse(EmailVerificationToken.objects.filter(id=token1_id).exists())
        # Sprawdź czy istnieje tylko nowy token
        self.assertEqual(EmailVerificationToken.objects.filter(user=self.user).count(), 1)
        self.assertEqual(EmailVerificationToken.objects.filter(user=self.user).first().id, token2.id)


class EmailVerificationAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=False  # Użytkownik nieaktywny przed weryfikacją
        )
        self.verify_url = reverse('verify-email')
        self.resend_url = reverse('resend-verification')
    
    def test_verify_email_success(self):
        """Test pomyślnej weryfikacji emaila"""
        token = EmailVerificationToken.create_for_user(self.user)
        
        data = {'token': token.token}
        response = self.client.post(self.verify_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Sprawdź czy użytkownik został aktywowany
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        
        # Sprawdź czy token został oznaczony jako użyty
        token.refresh_from_db()
        self.assertTrue(token.is_used)
    
    def test_verify_email_invalid_token(self):
        """Test weryfikacji z nieprawidłowym tokenem"""
        data = {'token': 'invalid-token-12345'}
        response = self.client.post(self.verify_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Użytkownik powinien pozostać nieaktywny
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
    
    def test_verify_email_missing_token(self):
        """Test weryfikacji bez tokena"""
        response = self.client.post(self.verify_url, {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_verify_email_expired_token(self):
        """Test weryfikacji z wygasłym tokenem"""
        token = EmailVerificationToken.create_for_user(self.user)
        token.expires_at = timezone.now() - timedelta(hours=1)
        token.save()
        
        data = {'token': token.token}
        response = self.client.post(self.verify_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('wygasł', response.data['error'].lower())
        
        # Użytkownik powinien pozostać nieaktywny
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
    
    def test_verify_email_already_used_token(self):
        """Test weryfikacji z już użytym tokenem"""
        token = EmailVerificationToken.create_for_user(self.user)
        token.is_used = True
        token.save()
        
        data = {'token': token.token}
        response = self.client.post(self.verify_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('już użyty', response.data['error'].lower())
    
    def test_resend_verification_email(self):
        """Test ponownego wysłania emaila weryfikacyjnego"""
        # Utwórz użytkownika bez tokenu
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
            is_active=False
        )
        
        data = {'email': user2.email}
        response = self.client.post(self.resend_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Sprawdź czy token został utworzony
        self.assertTrue(EmailVerificationToken.objects.filter(user=user2).exists())
    
    def test_resend_verification_email_already_verified(self):
        """Test ponownego wysłania emaila dla już zweryfikowanego użytkownika"""
        self.user.is_active = True
        self.user.save()
        
        data = {'email': self.user.email}
        response = self.client.post(self.resend_url, data)
        
        # Zgodnie z implementacją zwraca 200 z komunikatem
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_resend_verification_email_nonexistent_user(self):
        """Test ponownego wysłania emaila dla nieistniejącego użytkownika"""
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(self.resend_url, data)
        
        # Zgodnie z implementacją zwraca 404 jeśli użytkownik nie istnieje
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CustomTokenObtainPairSerializerTest(APITestCase):
    def setUp(self):
        self.token_url = reverse('token_obtain_pair')
    
    def test_login_inactive_user(self):
        """Test logowania nieaktywnego użytkownika"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=False
        )
        
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.token_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Sprawdź czy błąd jest w odpowiedzi (może być jako dict lub lista)
        error_msg = str(response.data).lower()
        self.assertIn('aktywne', error_msg)
    
    def test_login_active_user(self):
        """Test logowania aktywnego użytkownika"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=True
        )
        
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.token_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_login_wrong_password(self):
        """Test logowania z nieprawidłowym hasłem"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=True
        )
        
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.token_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Sprawdź czy błąd jest w odpowiedzi (może być jako dict lub lista)
        error_msg = str(response.data).lower()
        self.assertIn('nieprawidłowe', error_msg)
    
    def test_login_nonexistent_user(self):
        """Test logowania nieistniejącego użytkownika"""
        data = {
            'username': 'nonexistent',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.token_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Sprawdź czy błąd jest w odpowiedzi (może być jako dict lub lista)
        error_msg = str(response.data).lower()
        self.assertIn('nieprawidłowe', error_msg)

