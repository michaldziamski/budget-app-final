from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import random

from budgets.models import Category, Account, Transaction, SavingsGoal, Budget, Notification


class Command(BaseCommand):
    help = 'Tworzy dane testowe dla aplikacji budżetowej'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Nazwa użytkownika dla którego tworzyć dane (domyślnie: testuser)',
            default='testuser'
        )

    def handle(self, *args, **options):
        username = options['user']
        
        # Utwórz użytkownika jeśli nie istnieje
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Utworzono użytkownika: {username}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Użytkownik {username} już istnieje')
            )

        # Usuń istniejące dane użytkownika
        Transaction.objects.filter(user=user).delete()
        SavingsGoal.objects.filter(user=user).delete()
        Budget.objects.filter(user=user).delete()
        Account.objects.filter(user=user).delete()
        Category.objects.filter(user=user).delete()
        Notification.objects.filter(user=user).delete()

        # Twórz kategorie
        categories_data = [
            # Wydatki
            {'name': 'Żywność', 'type': 'expense', 'color': '#e74c3c', 'icon': 'fas fa-utensils'},
            {'name': 'Transport', 'type': 'expense', 'color': '#3498db', 'icon': 'fas fa-car'},
            {'name': 'Rozrywka', 'type': 'expense', 'color': '#9b59b6', 'icon': 'fas fa-gamepad'},
            {'name': 'Ubrania', 'type': 'expense', 'color': '#f39c12', 'icon': 'fas fa-tshirt'},
            {'name': 'Zdrowie', 'type': 'expense', 'color': '#e67e22', 'icon': 'fas fa-heartbeat'},
            {'name': 'Rachunki', 'type': 'expense', 'color': '#34495e', 'icon': 'fas fa-file-invoice'},
            {'name': 'Edukacja', 'type': 'expense', 'color': '#1abc9c', 'icon': 'fas fa-graduation-cap'},
            {'name': 'Inne wydatki', 'type': 'expense', 'color': '#95a5a6', 'icon': 'fas fa-ellipsis-h'},
            
            # Przychody
            {'name': 'Wynagrodzenie', 'type': 'income', 'color': '#27ae60', 'icon': 'fas fa-money-bill-wave'},
            {'name': 'Freelance', 'type': 'income', 'color': '#2ecc71', 'icon': 'fas fa-laptop'},
            {'name': 'Inwestycje', 'type': 'income', 'color': '#16a085', 'icon': 'fas fa-chart-line'},
            {'name': 'Inne przychody', 'type': 'income', 'color': '#7f8c8d', 'icon': 'fas fa-gift'},
        ]

        categories = {}
        for cat_data in categories_data:
            category = Category.objects.create(
                user=user,
                name=cat_data['name'],
                category_type=cat_data['type'],
                color=cat_data['color'],
                icon=cat_data['icon'],
                description=f"Kategoria {cat_data['name'].lower()}"
            )
            categories[cat_data['name']] = category

        # Twórz konta
        accounts_data = [
            {'name': 'Konto główne', 'type': 'bank', 'balance': 5000.00},
            {'name': 'Konto oszczędnościowe', 'type': 'savings', 'balance': 15000.00},
            {'name': 'Gotówka', 'type': 'cash', 'balance': 500.00},
            {'name': 'Karta kredytowa', 'type': 'credit_card', 'balance': -2000.00},
        ]

        accounts = {}
        for acc_data in accounts_data:
            account = Account.objects.create(
                user=user,
                name=acc_data['name'],
                account_type=acc_data['type'],
                balance=Decimal(str(acc_data['balance'])),
                description=f"Konto {acc_data['name'].lower()}"
            )
            accounts[acc_data['name']] = account

        # Twórz transakcje z ostatnich 3 miesięcy
        today = timezone.now().date()
        start_date = today - timedelta(days=90)
        
        # Przychody
        income_transactions = [
            {'amount': 5000, 'category': 'Wynagrodzenie', 'account': 'Konto główne', 'description': 'Wynagrodzenie miesięczne'},
            {'amount': 5000, 'category': 'Wynagrodzenie', 'account': 'Konto główne', 'description': 'Wynagrodzenie miesięczne'},
            {'amount': 5000, 'category': 'Wynagrodzenie', 'account': 'Konto główne', 'description': 'Wynagrodzenie miesięczne'},
            {'amount': 1200, 'category': 'Freelance', 'account': 'Konto główne', 'description': 'Projekt web development'},
            {'amount': 800, 'category': 'Freelance', 'account': 'Konto główne', 'description': 'Konsultacje IT'},
            {'amount': 300, 'category': 'Inwestycje', 'account': 'Konto oszczędnościowe', 'description': 'Dywidenda z akcji'},
        ]

        # Wydatki
        expense_transactions = [
            # Żywność
            {'amount': 150, 'category': 'Żywność', 'account': 'Konto główne', 'description': 'Zakupy w supermarkecie'},
            {'amount': 80, 'category': 'Żywność', 'account': 'Konto główne', 'description': 'Restauracja'},
            {'amount': 200, 'category': 'Żywność', 'account': 'Konto główne', 'description': 'Zakupy tygodniowe'},
            {'amount': 120, 'category': 'Żywność', 'account': 'Konto główne', 'description': 'Zakupy w supermarkecie'},
            {'amount': 90, 'category': 'Żywność', 'account': 'Konto główne', 'description': 'Pizza na wynos'},
            
            # Transport
            {'amount': 200, 'category': 'Transport', 'account': 'Konto główne', 'description': 'Paliwo'},
            {'amount': 150, 'category': 'Transport', 'account': 'Konto główne', 'description': 'Paliwo'},
            {'amount': 80, 'category': 'Transport', 'account': 'Konto główne', 'description': 'Bilet miesięczny'},
            {'amount': 300, 'category': 'Transport', 'account': 'Konto główne', 'description': 'Naprawa samochodu'},
            
            # Rozrywka
            {'amount': 50, 'category': 'Rozrywka', 'account': 'Konto główne', 'description': 'Kino'},
            {'amount': 120, 'category': 'Rozrywka', 'account': 'Konto główne', 'description': 'Netflix'},
            {'amount': 200, 'category': 'Rozrywka', 'account': 'Konto główne', 'description': 'Koncert'},
            {'amount': 80, 'category': 'Rozrywka', 'account': 'Konto główne', 'description': 'Gra na Steam'},
            
            # Rachunki
            {'amount': 400, 'category': 'Rachunki', 'account': 'Konto główne', 'description': 'Czynsz'},
            {'amount': 150, 'category': 'Rachunki', 'account': 'Konto główne', 'description': 'Prąd'},
            {'amount': 80, 'category': 'Rachunki', 'account': 'Konto główne', 'description': 'Internet'},
            {'amount': 60, 'category': 'Rachunki', 'account': 'Konto główne', 'description': 'Telefon'},
            
            # Zdrowie
            {'amount': 200, 'category': 'Zdrowie', 'account': 'Konto główne', 'description': 'Wizyta u lekarza'},
            {'amount': 80, 'category': 'Zdrowie', 'account': 'Konto główne', 'description': 'Leki'},
            
            # Ubrania
            {'amount': 300, 'category': 'Ubrania', 'account': 'Konto główne', 'description': 'Zakupy odzieżowe'},
            {'amount': 150, 'category': 'Ubrania', 'account': 'Konto główne', 'description': 'Buty'},
        ]

        # Dodaj transakcje z losowymi datami
        all_transactions = income_transactions + expense_transactions
        
        for i, trans_data in enumerate(all_transactions):
            # Losowa data z ostatnich 3 miesięcy
            random_days = random.randint(0, 90)
            transaction_date = start_date + timedelta(days=random_days)
            transaction_datetime = timezone.make_aware(
                datetime.combine(transaction_date, datetime.min.time())
            )
            
            Transaction.objects.create(
                user=user,
                account=accounts[trans_data['account']],
                category=categories[trans_data['category']],
                amount=Decimal(str(trans_data['amount'])),
                transaction_type='income' if trans_data['category'] in ['Wynagrodzenie', 'Freelance', 'Inwestycje', 'Inne przychody'] else 'expense',
                description=trans_data['description'],
                date=transaction_datetime,
                tags=f"test,{trans_data['category'].lower()}"
            )

        # Twórz cele oszczędnościowe
        savings_goals_data = [
            {
                'name': 'Wakacje 2024',
                'target_amount': 5000,
                'current_amount': 2500,
                'target_date': today + timedelta(days=180),
                'account': 'Konto oszczędnościowe'
            },
            {
                'name': 'Nowy laptop',
                'target_amount': 3000,
                'current_amount': 1200,
                'target_date': today + timedelta(days=120),
                'account': 'Konto oszczędnościowe'
            },
            {
                'name': 'Fundusz awaryjny',
                'target_amount': 10000,
                'current_amount': 8000,
                'target_date': today + timedelta(days=365),
                'account': 'Konto oszczędnościowe'
            }
        ]

        for goal_data in savings_goals_data:
            SavingsGoal.objects.create(
                user=user,
                name=goal_data['name'],
                target_amount=Decimal(str(goal_data['target_amount'])),
                current_amount=Decimal(str(goal_data['current_amount'])),
                target_date=goal_data['target_date'],
                account=accounts[goal_data['account']],
                description=f"Cel oszczędnościowy: {goal_data['name']}"
            )

        # Twórz budżety
        current_month_start = today.replace(day=1)
        current_month_end = (current_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        budgets_data = [
            {'category': 'Żywność', 'amount': 600, 'period': 'monthly'},
            {'category': 'Transport', 'amount': 400, 'period': 'monthly'},
            {'category': 'Rozrywka', 'amount': 300, 'period': 'monthly'},
            {'category': 'Rachunki', 'amount': 800, 'period': 'monthly'},
            {'category': 'Zdrowie', 'amount': 200, 'period': 'monthly'},
        ]

        for budget_data in budgets_data:
            Budget.objects.create(
                user=user,
                name=f"Budżet {budget_data['category']}",
                category=categories[budget_data['category']],
                amount=Decimal(str(budget_data['amount'])),
                period=budget_data['period'],
                start_date=current_month_start,
                end_date=current_month_end
            )

        # Twórz powiadomienia
        notifications_data = [
            {
                'type': 'budget_alert',
                'title': 'Przekroczenie budżetu - Żywność',
                'message': 'Wykorzystałeś 85% budżetu na żywność w tym miesiącu.'
            },
            {
                'type': 'goal_reminder',
                'title': 'Przypomnienie o celu oszczędnościowym',
                'message': 'Pamiętaj o regularnym oszczędzaniu na wakacje 2024.'
            },
            {
                'type': 'system',
                'title': 'Witamy w aplikacji budżetowej!',
                'message': 'Dziękujemy za rejestrację. Twoje dane testowe zostały utworzone.'
            }
        ]

        for notif_data in notifications_data:
            Notification.objects.create(
                user=user,
                notification_type=notif_data['type'],
                title=notif_data['title'],
                message=notif_data['message']
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Pomyślnie utworzono dane testowe dla użytkownika {username}:\n'
                f'- {len(categories)} kategorii\n'
                f'- {len(accounts)} kont\n'
                f'- {len(all_transactions)} transakcji\n'
                f'- {len(savings_goals_data)} celów oszczędnościowych\n'
                f'- {len(budgets_data)} budżetów\n'
                f'- {len(notifications_data)} powiadomień'
            )
        )
