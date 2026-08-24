import logging
from django.utils import timezone
from django.db.models import Sum, Q
from datetime import datetime, timedelta
from decimal import Decimal
from .models import Budget, SavingsGoal, Transaction, Notification
from .email_service import EmailService

logger = logging.getLogger(__name__)


class AlertService:
    """Serwis do automatycznych alertów i sprawdzania budżetów"""
    
    @staticmethod
    def check_budget_alerts(user=None):
        """Sprawdza aktywne budżety i wysyła alerty o przekroczeniach
        
        Args:
            user: Jeśli podany, sprawdza tylko budżety tego użytkownika.
                  Jeśli None, sprawdza wszystkie budżety (dla management command).
        """
        try:
            if user:
                active_budgets = Budget.objects.filter(is_active=True, user=user)
            else:
                active_budgets = Budget.objects.filter(is_active=True)
            alerts_sent = 0
            
            for budget in active_budgets:
                # Sprawdź czy budżet został przekroczony
                if budget.usage_percentage >= 100:
                    # Sprawdź czy już wysłano alert w ostatnich 24 godzinach
                    recent_alert = Notification.objects.filter(
                        user=budget.user,
                        notification_type='budget_alert',
                        title__icontains=budget.name,
                        created_at__gte=timezone.now() - timedelta(hours=24)
                    ).exists()
                    
                    if not recent_alert:
                        # Wyślij alert email
                        if EmailService.send_budget_alert_email(
                            user=budget.user,
                            budget=budget,
                            spent_percentage=budget.usage_percentage
                        ):
                            alerts_sent += 1
                            logger.info(f"Budget alert sent for budget: {budget.name}")
                
                # Sprawdź czy budżet jest bliski przekroczenia (80%+)
                elif budget.usage_percentage >= 80:
                    # Sprawdź czy już wysłano ostrzeżenie w ostatnich 48 godzinach
                    recent_warning = Notification.objects.filter(
                        user=budget.user,
                        notification_type='budget_alert',
                        title__icontains=f"Ostrzeżenie: {budget.name}",
                        created_at__gte=timezone.now() - timedelta(hours=48)
                    ).exists()
                    
                    if not recent_warning:
                        # Wyślij ostrzeżenie
                        AlertService._send_budget_warning(budget)
                        alerts_sent += 1
            
            logger.info(f"Budget alerts check completed. {alerts_sent} alerts sent.")
            return alerts_sent
            
        except Exception as e:
            logger.error(f"Error checking budget alerts: {e}")
            return 0
    
    @staticmethod
    def check_savings_goals_reminders(user=None):
        """Sprawdza cele oszczędnościowe i wysyła przypomnienia
        
        Args:
            user: Jeśli podany, sprawdza tylko cele tego użytkownika.
                  Jeśli None, sprawdza wszystkie cele (dla management command).
        """
        try:
            if user:
                active_goals = SavingsGoal.objects.filter(is_active=True, is_completed=False, user=user)
            else:
                active_goals = SavingsGoal.objects.filter(is_active=True, is_completed=False)
            reminders_sent = 0
            
            for goal in active_goals:
                days_remaining = goal.days_remaining
                
                # Wyślij przypomnienie jeśli zostało 7 dni lub mniej
                if 0 < days_remaining <= 7:
                    # Sprawdź czy już wysłano przypomnienie w ostatnich 24 godzinach
                    recent_reminder = Notification.objects.filter(
                        user=goal.user,
                        notification_type='goal_reminder',
                        title__icontains=goal.name,
                        created_at__gte=timezone.now() - timedelta(hours=24)
                    ).exists()
                    
                    if not recent_reminder:
                        if EmailService.send_savings_goal_reminder_email(goal.user, goal):
                            reminders_sent += 1
                            logger.info(f"Savings goal reminder sent for goal: {goal.name}")
                
                # Wyślij przypomnienie jeśli cel jest bliski ukończenia (90%+)
                elif goal.progress_percentage >= 90:
                    # Sprawdź czy już wysłano gratulacje w ostatnich 48 godzinach
                    recent_congrats = Notification.objects.filter(
                        user=goal.user,
                        notification_type='goal_reminder',
                        title__icontains=f"Gratulacje: {goal.name}",
                        created_at__gte=timezone.now() - timedelta(hours=48)
                    ).exists()
                    
                    if not recent_congrats:
                        AlertService._send_goal_congratulations(goal)
                        reminders_sent += 1
            
            logger.info(f"Savings goals reminders check completed. {reminders_sent} reminders sent.")
            return reminders_sent
            
        except Exception as e:
            logger.error(f"Error checking savings goals reminders: {e}")
            return 0
    
    @staticmethod
    def check_payment_reminders(user=None):
        """Sprawdza zbliżające się płatności i wysyła przypomnienia
        
        Args:
            user: Jeśli podany, sprawdza tylko transakcje tego użytkownika.
                  Jeśli None, sprawdza wszystkie transakcje (dla management command).
        """
        try:
            # Znajdź transakcje z przyszłymi datami (prawdopodobnie zaplanowane płatności)
            tomorrow = timezone.now().date() + timedelta(days=1)
            day_after_tomorrow = timezone.now().date() + timedelta(days=2)
            
            filter_kwargs = {
                'date__date__gte': tomorrow,
                'date__date__lte': day_after_tomorrow,
                'transaction_type__in': ['expense', 'transfer']
            }
            if user:
                filter_kwargs['user'] = user
            
            upcoming_transactions = Transaction.objects.filter(**filter_kwargs).select_related('user')
            
            reminders_sent = 0
            
            for transaction in upcoming_transactions:
                # Sprawdź czy już wysłano przypomnienie
                recent_reminder = Notification.objects.filter(
                    user=transaction.user,
                    notification_type='payment_reminder',
                    title__icontains=transaction.description[:50],
                    created_at__gte=timezone.now() - timedelta(hours=24)
                ).exists()
                
                if not recent_reminder:
                    if EmailService.send_payment_reminder_email(
                        user=transaction.user,
                        transaction_description=transaction.description,
                        amount=transaction.amount,
                        due_date=transaction.date.date()
                    ):
                        reminders_sent += 1
                        logger.info(f"Payment reminder sent for transaction: {transaction.description}")
            
            logger.info(f"Payment reminders check completed. {reminders_sent} reminders sent.")
            return reminders_sent
            
        except Exception as e:
            logger.error(f"Error checking payment reminders: {e}")
            return 0
    
    @staticmethod
    def run_all_checks(user=None):
        """Uruchamia wszystkie sprawdzenia alertów
        
        Args:
            user: Jeśli podany, sprawdza tylko dane tego użytkownika.
                  Jeśli None, sprawdza wszystkich użytkowników (dla management command).
        """
        try:
            logger.info(f"Starting all alert checks{' for user ' + user.username if user else ''}...")
            
            budget_alerts = AlertService.check_budget_alerts(user=user)
            goal_reminders = AlertService.check_savings_goals_reminders(user=user)
            payment_reminders = AlertService.check_payment_reminders(user=user)
            
            total_alerts = budget_alerts + goal_reminders + payment_reminders
            
            logger.info(f"All alert checks completed. Total alerts sent: {total_alerts}")
            return {
                'budget_alerts': budget_alerts,
                'goal_reminders': goal_reminders,
                'payment_reminders': payment_reminders,
                'total': total_alerts
            }
            
        except Exception as e:
            logger.error(f"Error running alert checks: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def _send_budget_warning(budget: Budget):
        """Wysyła ostrzeżenie o zbliżającym się przekroczeniu budżetu"""
        try:
            subject = f"⚠️ Ostrzeżenie: {budget.name} - {budget.usage_percentage:.1f}% wykorzystane"
            
            notification = Notification.objects.create(
                user=budget.user,
                notification_type='budget_alert',
                title=subject,
                message=f"Budżet '{budget.name}' wykorzystany w {budget.usage_percentage:.1f}%. Pozostało {budget.remaining_amount} PLN.",
                is_email_sent=False  # Można dodać wysyłanie emaila jeśli potrzeba
            )
            
            logger.info(f"Budget warning notification created for budget: {budget.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending budget warning: {e}")
            return False
    
    @staticmethod
    def _send_goal_congratulations(goal: SavingsGoal):
        """Wysyła gratulacje za bliskie ukończenie celu"""
        try:
            subject = f"🎉 Gratulacje: {goal.name} - {goal.progress_percentage:.1f}% ukończone!"
            
            notification = Notification.objects.create(
                user=goal.user,
                notification_type='goal_reminder',
                title=subject,
                message=f"Cel '{goal.name}' jest ukończony w {goal.progress_percentage:.1f}%! Pozostało {goal.target_amount - goal.current_amount} PLN.",
                is_email_sent=False  # Można dodać wysyłanie emaila jeśli potrzeba
            )
            
            logger.info(f"Goal congratulations notification created for goal: {goal.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending goal congratulations: {e}")
            return False
    
    @staticmethod
    def create_weekly_summary():
        """Tworzy cotygodniowe podsumowanie dla użytkowników"""
        try:
            from django.contrib.auth.models import User
            
            # Znajdź użytkowników z aktywnymi kontami
            users_with_activity = User.objects.filter(
                Q(transactions__isnull=False) | 
                Q(budgets__isnull=False) | 
                Q(savings_goals__isnull=False)
            ).distinct()
            
            summaries_created = 0
            
            for user in users_with_activity:
                # Sprawdź czy już utworzono podsumowanie w tym tygodniu
                week_start = timezone.now().date() - timedelta(days=7)
                recent_summary = Notification.objects.filter(
                    user=user,
                    notification_type='system',
                    title__icontains='Podsumowanie tygodnia',
                    created_at__gte=week_start
                ).exists()
                
                if not recent_summary:
                    AlertService._create_user_weekly_summary(user)
                    summaries_created += 1
            
            logger.info(f"Weekly summaries created: {summaries_created}")
            return summaries_created
            
        except Exception as e:
            logger.error(f"Error creating weekly summaries: {e}")
            return 0
    
    @staticmethod
    def _create_user_weekly_summary(user):
        """Tworzy cotygodniowe podsumowanie dla konkretnego użytkownika"""
        try:
            from django.db.models import Sum
            
            # Okres ostatniego tygodnia
            week_ago = timezone.now() - timedelta(days=7)
            
            # Statystyki z ostatniego tygodnia
            weekly_transactions = Transaction.objects.filter(
                user=user,
                date__gte=week_ago
            )
            
            total_income = weekly_transactions.filter(
                transaction_type='income'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            total_expenses = weekly_transactions.filter(
                transaction_type='expense'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            net_income = total_income - total_expenses
            transaction_count = weekly_transactions.count()
            
            # Aktywne budżety
            active_budgets = Budget.objects.filter(user=user, is_active=True).count()
            
            # Aktywne cele oszczędnościowe
            active_goals = SavingsGoal.objects.filter(user=user, is_active=True, is_completed=False).count()
            
            subject = f"📊 Podsumowanie tygodnia - {user.first_name or user.username}"
            
            message = f"""
            Podsumowanie ostatniego tygodnia:
            
            💰 Finanse:
            - Przychody: {total_income} PLN
            - Wydatki: {total_expenses} PLN
            - Bilans: {net_income} PLN
            - Liczba transakcji: {transaction_count}
            
            📋 Aktywne elementy:
            - Budżety: {active_budgets}
            - Cele oszczędnościowe: {active_goals}
            
            {'🎉 Gratulacje za pozytywny bilans!' if net_income > 0 else '💡 Rozważ ograniczenie wydatków.'}
            """
            
            Notification.objects.create(
                user=user,
                notification_type='system',
                title=subject,
                message=message.strip(),
                is_email_sent=False
            )
            
            logger.info(f"Weekly summary created for user: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating weekly summary for user {user.username}: {e}")
            return False


