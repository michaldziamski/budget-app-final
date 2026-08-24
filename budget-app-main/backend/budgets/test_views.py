from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
import json

from .models import Category, Account, Transaction, SavingsGoal, Budget, Notification


class AuthenticationAPITest(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.token_url = reverse('token_obtain_pair')
        self.me_url = reverse('me')
    
    def test_user_registration(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'testuser')
        
        # Sprawdź czy użytkownik został utworzony
        self.assertTrue(User.objects.filter(username='testuser').exists())
    
    def test_user_login(self):
        # Utwórz użytkownika
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.token_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_authenticated_request(self):
        # Utwórz użytkownika i uzyskaj token
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Użyj tokenu w nagłówku
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
    
    def test_unauthenticated_request(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CategoryAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Uzyskaj token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        self.categories_url = reverse('category-list')
    
    def test_create_category(self):
        data = {
            'name': 'Żywność',
            'category_type': 'expense',
            'color': '#e74c3c',
            'description': 'Kategoria na żywność'
        }
        
        response = self.client.post(self.categories_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Żywność')
        self.assertEqual(response.data['user'], self.user.id)
    
    def test_list_categories(self):
        # Utwórz kategorię
        Category.objects.create(
            user=self.user,
            name='Transport',
            category_type='expense'
        )
        
        response = self.client.get(self.categories_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Widok nie używa paginacji, więc response.data to lista
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Transport')
    
    def test_update_category(self):
        category = Category.objects.create(
            user=self.user,
            name='Transport',
            category_type='expense'
        )
        
        data = {
            'name': 'Transport Publiczny',
            'category_type': 'expense',
            'color': '#3498db'
        }
        
        url = reverse('category-detail', kwargs={'pk': category.id})
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Transport Publiczny')
    
    def test_delete_category(self):
        category = Category.objects.create(
            user=self.user,
            name='Transport',
            category_type='expense'
        )
        
        url = reverse('category-detail', kwargs={'pk': category.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Sprawdź czy kategoria została oznaczona jako nieaktywna
        category.refresh_from_db()
        self.assertFalse(category.is_active)


class AccountAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        self.accounts_url = reverse('account-list')
    
    def test_create_account(self):
        data = {
            'name': 'Konto główne',
            'account_type': 'bank',
            'balance': '1000.00',
            'currency': 'PLN',
            'description': 'Główne konto bankowe'
        }
        
        response = self.client.post(self.accounts_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Konto główne')
        self.assertEqual(response.data['balance'], '1000.00')
    
    def test_list_accounts(self):
        Account.objects.create(
            user=self.user,
            name='Konto oszczędnościowe',
            account_type='savings',
            balance=Decimal('5000.00')
        )
        
        response = self.client.get(self.accounts_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Widok nie używa paginacji, więc response.data to lista
        self.assertEqual(len(response.data), 1)


class TransactionAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        self.account = Account.objects.create(
            user=self.user,
            name='Konto główne',
            account_type='bank',
            balance=Decimal('1000.00')
        )
        
        self.category = Category.objects.create(
            user=self.user,
            name='Żywność',
            category_type='expense'
        )
        
        self.transactions_url = reverse('transaction-list')
    
    def test_create_income_transaction(self):
        initial_balance = self.account.balance
        
        data = {
            'account': str(self.account.id),
            'category': str(self.category.id),
            'amount': '500.00',
            'transaction_type': 'income',
            'description': 'Wypłata',
            'date': '2024-01-15T10:00:00Z'
        }
        
        response = self.client.post(self.transactions_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Sprawdź czy saldo zostało zaktualizowane
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance + Decimal('500.00'))
    
    def test_create_expense_transaction(self):
        initial_balance = self.account.balance
        
        data = {
            'account': str(self.account.id),
            'category': str(self.category.id),
            'amount': '100.00',
            'transaction_type': 'expense',
            'description': 'Zakupy w supermarkecie',
            'date': '2024-01-15T10:00:00Z'
        }
        
        response = self.client.post(self.transactions_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Sprawdź czy saldo zostało zaktualizowane
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance - Decimal('100.00'))
    
    def test_list_transactions_with_filters(self):
        # Utwórz transakcję
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category,
            amount=Decimal('100.00'),
            transaction_type='expense',
            description='Test transaction',
            date='2024-01-15T10:00:00Z'
        )
        
        # Test filtrowania po typie
        response = self.client.get(self.transactions_url, {'type': 'expense'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Widok nie używa paginacji, więc response.data to lista
        self.assertEqual(len(response.data), 1)
        
        # Test filtrowania po koncie
        response = self.client.get(self.transactions_url, {'account': str(self.account.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class SavingsGoalAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        self.account = Account.objects.create(
            user=self.user,
            name='Konto oszczędnościowe',
            account_type='savings',
            balance=Decimal('0.00')
        )
        
        self.goals_url = reverse('savings-goal-list')
    
    def test_create_savings_goal(self):
        data = {
            'name': 'Wakacje 2024',
            'target_amount': '5000.00',
            'current_amount': '1000.00',
            # Data docelowa musi być w przyszłości względem dnia dzisiejszego
            'target_date': '2099-12-31',
            'account': str(self.account.id),
            'description': 'Oszczędności na wakacje'
        }
        
        response = self.client.post(self.goals_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Wakacje 2024')
        self.assertEqual(response.data['target_amount'], '5000.00')
    
    def test_savings_goal_progress_calculation(self):
        goal = SavingsGoal.objects.create(
            user=self.user,
            name='Test Goal',
            target_amount=Decimal('1000.00'),
            current_amount=Decimal('250.00'),
            target_date='2024-12-31',
            account=self.account
        )
        
        url = reverse('savings-goal-detail', kwargs={'pk': goal.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['progress_percentage'], 25.0)


class BudgetAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        self.category = Category.objects.create(
            user=self.user,
            name='Żywność',
            category_type='expense'
        )
        
        self.budgets_url = reverse('budget-list')
    
    def test_create_budget(self):
        data = {
            'name': 'Budżet Żywność',
            'category': str(self.category.id),
            'amount': '600.00',
            'period': 'monthly',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        }
        
        response = self.client.post(self.budgets_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Budżet Żywność')
        self.assertEqual(response.data['amount'], '600.00')


class DashboardAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        self.dashboard_url = reverse('dashboard')
    
    def test_dashboard_data(self):
        # Utwórz dane testowe
        account = Account.objects.create(
            user=self.user,
            name='Test Account',
            account_type='bank',
            balance=Decimal('1000.00')
        )
        
        category = Category.objects.create(
            user=self.user,
            name='Test Category',
            category_type='expense'
        )
        
        Transaction.objects.create(
            user=self.user,
            account=account,
            category=category,
            amount=Decimal('100.00'),
            transaction_type='expense',
            description='Test transaction',
            date='2024-01-15T10:00:00Z'
        )
        
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Sprawdź strukturę odpowiedzi
        self.assertIn('stats', response.data)
        self.assertIn('recent_transactions', response.data)
        self.assertIn('active_budgets', response.data)
        self.assertIn('savings_goals', response.data)
        
        # Sprawdź statystyki
        stats = response.data['stats']
        self.assertIn('total_accounts', stats)
        self.assertIn('total_categories', stats)
        self.assertIn('total_balance', stats)


class AnalyticsAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        self.account = Account.objects.create(
            user=self.user,
            name='Test Account',
            account_type='bank',
            balance=Decimal('0.00')
        )
        
        self.category = Category.objects.create(
            user=self.user,
            name='Test Category',
            category_type='expense'
        )
    
    def test_transaction_summary(self):
        # Utwórz transakcje
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            amount=Decimal('1000.00'),
            transaction_type='income',
            description='Income',
            date='2024-01-15T10:00:00Z'
        )
        
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category,
            amount=Decimal('300.00'),
            transaction_type='expense',
            description='Expense',
            date='2024-01-15T10:00:00Z'
        )
        
        url = reverse('transaction-summary')
        # Podajemy jawnie zakres dat, aby objąć utworzone transakcje
        response = self.client.get(url, {
            'date_from': '2024-01-01',
            'date_to': '2024-01-31',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(response.data['total_income'], '1000.00')
        self.assertEqual(response.data['total_expenses'], '300.00')
        self.assertEqual(response.data['net_income'], '700.00')
        self.assertEqual(response.data['transaction_count'], 2)
    
    def test_category_expenses(self):
        # Utwórz transakcje wydatków
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category,
            amount=Decimal('100.00'),
            transaction_type='expense',
            description='Expense 1',
            date='2024-01-15T10:00:00Z'
        )
        
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category,
            amount=Decimal('200.00'),
            transaction_type='expense',
            description='Expense 2',
            date='2024-01-16T10:00:00Z'
        )
        
        url = reverse('category-expenses')
        # Podajemy jawnie zakres dat, aby objąć utworzone transakcje
        response = self.client.get(url, {
            'date_from': '2024-01-01',
            'date_to': '2024-01-31',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['category_name'], 'Test Category')
        self.assertEqual(response.data[0]['total_amount'], '300.00')
        self.assertEqual(response.data[0]['transaction_count'], 2)
        self.assertEqual(response.data[0]['percentage'], 100.0)


