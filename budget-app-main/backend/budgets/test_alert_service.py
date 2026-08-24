from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from .models import Category, Account, Transaction, Budget, SavingsGoal, Notification
from .alert_service import AlertService


class AlertServiceTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123',
            is_active=True
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123',
            is_active=True
        )
        
        self.category = Category.objects.create(
            user=self.user1,
            name='Test Category',
            category_type='expense'
        )
        
        self.account = Account.objects.create(
            user=self.user1,
            name='Test Account',
            account_type='bank',
            balance=Decimal('1000.00')
        )
    
    @patch('budgets.alert_service.EmailService.send_budget_alert_email')
    def test_check_budget_alerts_user_specific(self, mock_send_email):
        """Test sprawdzania alertów budżetowych dla konkretnego użytkownika"""
        mock_send_email.return_value = True
        
        # Utwórz budżet przekroczony dla user1
        budget = Budget.objects.create(
            user=self.user1,
            name='Test Budget',
            category=self.category,
            amount=Decimal('100.00'),
            period='monthly',
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=30)).date()
        )
        
        # Dodaj transakcje przekraczające budżet
        Transaction.objects.create(
            user=self.user1,
            account=self.account,
            category=self.category,
            amount=Decimal('120.00'),
            transaction_type='expense',
            description='Test expense',
            date=timezone.now()
        )
        
        # Sprawdź alerty tylko dla user1
        AlertService.check_budget_alerts(user=self.user1)
        
        # Sprawdź czy email został wysłany
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        self.assertEqual(call_args[1]['user'], self.user1)
        self.assertEqual(call_args[1]['budget'], budget)
    
    @patch('budgets.alert_service.EmailService.send_budget_alert_email')
    def test_check_budget_alerts_all_users(self, mock_send_email):
        """Test sprawdzania alertów budżetowych dla wszystkich użytkowników"""
        mock_send_email.return_value = True
        
        # Utwórz budżety dla obu użytkowników
        budget1 = Budget.objects.create(
            user=self.user1,
            name='Budget 1',
            category=self.category,
            amount=Decimal('100.00'),
            period='monthly',
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=30)).date()
        )
        
        category2 = Category.objects.create(
            user=self.user2,
            name='Category 2',
            category_type='expense'
        )
        
        account2 = Account.objects.create(
            user=self.user2,
            name='Account 2',
            account_type='bank',
            balance=Decimal('1000.00')
        )
        
        budget2 = Budget.objects.create(
            user=self.user2,
            name='Budget 2',
            category=category2,
            amount=Decimal('100.00'),
            period='monthly',
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=30)).date()
        )
        
        # Dodaj transakcje przekraczające budżety
        Transaction.objects.create(
            user=self.user1,
            account=self.account,
            category=self.category,
            amount=Decimal('120.00'),
            transaction_type='expense',
            description='Test expense 1',
            date=timezone.now()
        )
        
        Transaction.objects.create(
            user=self.user2,
            account=account2,
            category=category2,
            amount=Decimal('120.00'),
            transaction_type='expense',
            description='Test expense 2',
            date=timezone.now()
        )
        
        # Sprawdź alerty dla wszystkich użytkowników
        AlertService.check_budget_alerts(user=None)
        
        # Sprawdź czy emaile zostały wysłane dla obu użytkowników
        self.assertEqual(mock_send_email.call_count, 2)
    
    @patch('budgets.alert_service.EmailService.send_budget_alert_email')
    def test_check_budget_alerts_no_recent_alert(self, mock_send_email):
        """Test że alert nie jest wysyłany jeśli był już wysłany w ostatnich 24h"""
        mock_send_email.return_value = True
        
        budget = Budget.objects.create(
            user=self.user1,
            name='Test Budget',
            category=self.category,
            amount=Decimal('100.00'),
            period='monthly',
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=30)).date()
        )
        
        # Utwórz istniejący alert z ostatnich 24h
        Notification.objects.create(
            user=self.user1,
            notification_type='budget_alert',
            title=f'Budżet {budget.name} przekroczony',
            message='Test',
            created_at=timezone.now() - timedelta(hours=12)
        )
        
        # Dodaj transakcje przekraczające budżet
        Transaction.objects.create(
            user=self.user1,
            account=self.account,
            category=self.category,
            amount=Decimal('120.00'),
            transaction_type='expense',
            description='Test expense',
            date=timezone.now()
        )
        
        AlertService.check_budget_alerts(user=self.user1)
        
        # Email nie powinien zostać wysłany
        mock_send_email.assert_not_called()
    
    @patch('budgets.alert_service.EmailService.send_savings_goal_reminder_email')
    def test_check_savings_goals_reminders(self, mock_send_email):
        """Test sprawdzania przypomnień o celach oszczędnościowych"""
        mock_send_email.return_value = True
        
        savings_goal = SavingsGoal.objects.create(
            user=self.user1,
            name='Test Goal',
            target_amount=Decimal('1000.00'),
            current_amount=Decimal('500.00'),
            target_date=(timezone.now() + timedelta(days=7)).date(),
            account=self.account
        )
        
        AlertService.check_savings_goals_reminders(user=self.user1)
        
        # Sprawdź czy email został wysłany
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        # Funkcja przyjmuje argumenty pozycyjne: (user, goal)
        self.assertEqual(call_args[0][0], self.user1)
        self.assertEqual(call_args[0][1], savings_goal)
    
    @patch('budgets.alert_service.EmailService.send_payment_reminder_email')
    def test_check_payment_reminders(self, mock_send_email):
        """Test sprawdzania przypomnień o płatnościach"""
        mock_send_email.return_value = True
        
        # Utwórz transakcję z datą w przyszłości (w ciągu 2 dni)
        transaction = Transaction.objects.create(
            user=self.user1,
            account=self.account,
            category=self.category,
            amount=Decimal('100.00'),
            transaction_type='expense',
            description='Test Payment',
            date=(timezone.now() + timedelta(days=2))
        )
        
        AlertService.check_payment_reminders(user=self.user1)
        
        # Sprawdź czy email został wysłany
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        # Funkcja w kodzie używa argumentów nazwanych, więc sprawdzamy kwargs
        kwargs = call_args.kwargs
        self.assertEqual(kwargs['user'], self.user1)
        self.assertIn('Test Payment', kwargs['transaction_description'])
        self.assertEqual(kwargs['amount'], transaction.amount)
        self.assertEqual(kwargs['due_date'], transaction.date.date())
    
    def test_run_all_checks_user_specific(self):
        """Test uruchomienia wszystkich sprawdzeń dla konkretnego użytkownika"""
        with patch.object(AlertService, 'check_budget_alerts') as mock_budget, \
             patch.object(AlertService, 'check_savings_goals_reminders') as mock_savings, \
             patch.object(AlertService, 'check_payment_reminders') as mock_payment:
            
            AlertService.run_all_checks(user=self.user1)
            
            mock_budget.assert_called_once_with(user=self.user1)
            mock_savings.assert_called_once_with(user=self.user1)
            mock_payment.assert_called_once_with(user=self.user1)
    
    def test_run_all_checks_all_users(self):
        """Test uruchomienia wszystkich sprawdzeń dla wszystkich użytkowników"""
        with patch.object(AlertService, 'check_budget_alerts') as mock_budget, \
             patch.object(AlertService, 'check_savings_goals_reminders') as mock_savings, \
             patch.object(AlertService, 'check_payment_reminders') as mock_payment:
            
            AlertService.run_all_checks(user=None)
            
            mock_budget.assert_called_once_with(user=None)
            mock_savings.assert_called_once_with(user=None)
            mock_payment.assert_called_once_with(user=None)

