from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch

from .models import Category, Account, Transaction, Budget, SavingsGoal, EmailVerificationToken


class UserRegistrationAndVerificationFlowTest(APITestCase):
    """Test integracyjny dla pełnego przepływu rejestracji i weryfikacji"""
    
    def test_complete_registration_verification_login_flow(self):
        """Test pełnego przepływu: rejestracja -> weryfikacja -> logowanie"""
        # 1. Rejestracja
        register_url = reverse('register')
        register_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'testpass123'
        }
        
        with patch('budgets.email_service.EmailService.send_verification_email', return_value=True):
            response = self.client.post(register_url, register_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        
        # Sprawdź czy użytkownik został utworzony jako nieaktywny
        user = User.objects.get(username='newuser')
        self.assertFalse(user.is_active)
        
        # Sprawdź czy token został utworzony
        token = EmailVerificationToken.objects.get(user=user)
        self.assertIsNotNone(token)
        self.assertFalse(token.is_used)
        
        # 2. Weryfikacja emaila
        verify_url = reverse('verify-email')
        verify_data = {'token': token.token}
        response = self.client.post(verify_url, verify_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Sprawdź czy użytkownik został aktywowany
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        
        # Sprawdź czy token został oznaczony jako użyty
        token.refresh_from_db()
        self.assertTrue(token.is_used)
        
        # 3. Logowanie
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'newuser',
            'password': 'testpass123'
        }
        response = self.client.post(login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)


class TransactionAndBudgetIntegrationTest(APITestCase):
    """Test integracyjny dla transakcji i budżetów"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=True
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        self.category = Category.objects.create(
            user=self.user,
            name='Food',
            category_type='expense'
        )
        
        self.account = Account.objects.create(
            user=self.user,
            name='Main Account',
            account_type='bank',
            balance=Decimal('1000.00')
        )
    
    def test_create_budget_and_transaction_flow(self):
        """Test tworzenia budżetu i transakcji wpływających na niego"""
        # 1. Utwórz budżet
        budget_url = reverse('budget-list')
        budget_data = {
            'name': 'Food Budget',
            'category': str(self.category.id),
            'amount': '500.00',
            'period': 'monthly',
            'start_date': timezone.now().date().isoformat(),
            'end_date': (timezone.now() + timedelta(days=30)).date().isoformat()
        }
        
        response = self.client.post(budget_url, budget_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        budget_id = response.data['id']
        
        # 2. Utwórz transakcję wydatku
        transaction_url = reverse('transaction-list')
        transaction_data = {
            'account': str(self.account.id),
            'category': str(self.category.id),
            'amount': '200.00',
            'transaction_type': 'expense',
            'description': 'Grocery shopping',
            'date': timezone.now().isoformat()
        }
        
        response = self.client.post(transaction_url, transaction_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 3. Sprawdź aktualizację budżetu
        budget_detail_url = reverse('budget-detail', kwargs={'pk': budget_id})
        response = self.client.get(budget_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['spent_amount']), Decimal('200.00'))
        self.assertEqual(Decimal(response.data['remaining_amount']), Decimal('300.00'))
        self.assertEqual(response.data['usage_percentage'], 40.0)
        
        # 4. Dodaj kolejną transakcję
        transaction_data['amount'] = '250.00'
        response = self.client.post(transaction_url, transaction_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 5. Sprawdź aktualizację budżetu po drugiej transakcji
        response = self.client.get(budget_detail_url)
        self.assertEqual(Decimal(response.data['spent_amount']), Decimal('450.00'))
        self.assertEqual(Decimal(response.data['remaining_amount']), Decimal('50.00'))
        self.assertEqual(response.data['usage_percentage'], 90.0)
    
    def test_account_balance_updates_with_transactions(self):
        """Test aktualizacji salda konta przy transakcjach"""
        initial_balance = self.account.balance
        
        # 1. Dodaj przychód
        transaction_url = reverse('transaction-list')
        income_data = {
            'account': str(self.account.id),
            'category': str(self.category.id),
            'amount': '1000.00',
            'transaction_type': 'income',
            'description': 'Salary',
            'date': timezone.now().isoformat()
        }
        
        response = self.client.post(transaction_url, income_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Sprawdź saldo
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance + Decimal('1000.00'))
        
        # 2. Dodaj wydatek
        expense_data = {
            'account': str(self.account.id),
            'category': str(self.category.id),
            'amount': '300.00',
            'transaction_type': 'expense',
            'description': 'Shopping',
            'date': timezone.now().isoformat()
        }
        
        response = self.client.post(transaction_url, expense_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Sprawdź saldo
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance + Decimal('1000.00') - Decimal('300.00'))


class DashboardIntegrationTest(APITestCase):
    """Test integracyjny dla dashboardu"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=True
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        self.category = Category.objects.create(
            user=self.user,
            name='Food',
            category_type='expense'
        )
        
        self.account = Account.objects.create(
            user=self.user,
            name='Main Account',
            account_type='bank',
            balance=Decimal('1000.00')
        )
    
    def test_dashboard_shows_correct_statistics(self):
        """Test czy dashboard pokazuje poprawne statystyki"""
        # Utwórz dane testowe
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category,
            amount=Decimal('100.00'),
            transaction_type='expense',
            description='Test expense',
            date=timezone.now()
        )
        
        Budget.objects.create(
            user=self.user,
            name='Test Budget',
            category=self.category,
            amount=Decimal('500.00'),
            period='monthly',
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=30)).date()
        )
        
        SavingsGoal.objects.create(
            user=self.user,
            name='Test Goal',
            target_amount=Decimal('1000.00'),
            current_amount=Decimal('500.00'),
            target_date=(timezone.now() + timedelta(days=90)).date(),
            account=self.account
        )
        
        # Pobierz dashboard
        dashboard_url = reverse('dashboard')
        response = self.client.get(dashboard_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Sprawdź statystyki
        stats = response.data['stats']
        self.assertGreaterEqual(stats['total_accounts'], 1)
        self.assertGreaterEqual(stats['active_budgets'], 1)
        self.assertGreaterEqual(stats['active_savings_goals'], 1)
        
        # Sprawdź czy są ostatnie transakcje
        self.assertIn('recent_transactions', response.data)
        self.assertGreaterEqual(len(response.data['recent_transactions']), 1)
        
        # Sprawdź czy są aktywne budżety
        self.assertIn('active_budgets', response.data)
        self.assertGreaterEqual(len(response.data['active_budgets']), 1)
        
        # Sprawdź czy są cele oszczędnościowe
        self.assertIn('savings_goals', response.data)
        self.assertGreaterEqual(len(response.data['savings_goals']), 1)

