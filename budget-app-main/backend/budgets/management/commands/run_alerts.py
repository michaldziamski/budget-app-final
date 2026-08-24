from django.core.management.base import BaseCommand
from budgets.alert_service import AlertService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Uruchamia wszystkie sprawdzenia alertów i powiadomień'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['all', 'budget', 'goals', 'payments', 'weekly'],
            default='all',
            help='Typ sprawdzeń do uruchomienia'
        )

    def handle(self, *args, **options):
        alert_type = options['type']
        
        self.stdout.write(
            self.style.SUCCESS(f'Uruchamianie sprawdzeń alertów: {alert_type}')
        )
        
        try:
            if alert_type == 'all':
                results = AlertService.run_all_checks()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Sprawdzenia zakończone. '
                        f'Alerty budżetowe: {results.get("budget_alerts", 0)}, '
                        f'Przypomnienia celów: {results.get("goal_reminders", 0)}, '
                        f'Przypomnienia płatności: {results.get("payment_reminders", 0)}, '
                        f'Razem: {results.get("total", 0)}'
                    )
                )
                
            elif alert_type == 'budget':
                count = AlertService.check_budget_alerts()
                self.stdout.write(
                    self.style.SUCCESS(f'Wysłano {count} alertów budżetowych')
                )
                
            elif alert_type == 'goals':
                count = AlertService.check_savings_goals_reminders()
                self.stdout.write(
                    self.style.SUCCESS(f'Wysłano {count} przypomnień o celach')
                )
                
            elif alert_type == 'payments':
                count = AlertService.check_payment_reminders()
                self.stdout.write(
                    self.style.SUCCESS(f'Wysłano {count} przypomnień o płatnościach')
                )
                
            elif alert_type == 'weekly':
                count = AlertService.create_weekly_summary()
                self.stdout.write(
                    self.style.SUCCESS(f'Utworzono {count} cotygodniowych podsumowań')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Błąd podczas uruchamiania alertów: {str(e)}')
            )
            logger.error(f'Error running alerts command: {e}')


