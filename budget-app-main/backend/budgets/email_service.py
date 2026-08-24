import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from .models import Notification, Budget, SavingsGoal, EmailVerificationToken, PasswordResetToken
from decimal import Decimal
import sendgrid
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)


class EmailService:
    """Serwis do obsługi wysyłania emaili"""
    
    @staticmethod
    def send_budget_alert_email(user: User, budget: Budget, spent_percentage: float):
        """Wysyła email o przekroczeniu budżetu"""
        try:
            subject = f"🚨 Alert budżetowy: {budget.name}"
            
            # Szablon HTML
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #e74c3c;">🚨 Alert Budżetowy</h2>
                    
                    <p>Witaj {user.first_name or user.username},</p>
                    
                    <p>Twoj budżet <strong>"{budget.name}"</strong> został przekroczony!</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #495057;">Szczegóły budżetu:</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li><strong>Kategoria:</strong> {budget.category.name}</li>
                            <li><strong>Planowana kwota:</strong> {budget.amount} PLN</li>
                            <li><strong>Wydano:</strong> {budget.spent_amount} PLN</li>
                            <li><strong>Pozostało:</strong> {budget.remaining_amount} PLN</li>
                            <li><strong>Wykorzystanie:</strong> {spent_percentage:.1f}%</li>
                        </ul>
                    </div>
                    
                    <p style="color: #e74c3c; font-weight: bold;">
                        ⚠️ Twoje wydatki przekroczyły zaplanowany budżet o {abs(budget.remaining_amount)} PLN!
                    </p>
                    
                    <p>Zaloguj się do aplikacji, aby przeanalizować swoje wydatki i dostosować budżet.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{settings.FRONTEND_URL}/dashboard" 
                           style="background-color: #007bff; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Przejdź do Dashboard
                        </a>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        To jest automatyczny email z aplikacji budżetowej. 
                        Jeśli nie chcesz otrzymywać takich powiadomień, możesz je wyłączyć w ustawieniach.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Wersja tekstowa
            text_message = f"""
            Alert Budżetowy
            
            Witaj {user.first_name or user.username},
            
            Twój budżet "{budget.name}" został przekroczony!
            
            Szczegóły:
            - Kategoria: {budget.category.name}
            - Planowana kwota: {budget.amount} PLN
            - Wydano: {budget.spent_amount} PLN
            - Pozostało: {budget.remaining_amount} PLN
            - Wykorzystanie: {spent_percentage:.1f}%
            
            ⚠️ Twoje wydatki przekroczyły zaplanowany budżet o {abs(budget.remaining_amount)} PLN!
            
            Zaloguj się do aplikacji: {settings.FRONTEND_URL}/dashboard
            """
            
            # Wyślij email
            EmailService._send_email(
                subject=subject,
                html_message=html_message,
                text_message=text_message,
                recipient_list=[user.email]
            )
            
            # Oznacz powiadomienie jako wysłane
            notification = Notification.objects.create(
                user=user,
                notification_type='budget_alert',
                title=subject,
                message=f"Budżet '{budget.name}' przekroczony o {abs(budget.remaining_amount)} PLN",
                is_email_sent=True
            )
            
            logger.info(f"Budget alert email sent to {user.email} for budget {budget.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending budget alert email: {e}")
            return False
    
    @staticmethod
    def send_savings_goal_reminder_email(user: User, savings_goal: SavingsGoal):
        """Wysyła email z przypomnieniem o celu oszczędnościowym"""
        try:
            subject = f"🎯 Przypomnienie o celu: {savings_goal.name}"
            
            progress_percentage = savings_goal.progress_percentage
            days_remaining = savings_goal.days_remaining
            
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #28a745;">🎯 Przypomnienie o Celu Oszczędnościowym</h2>
                    
                    <p>Witaj {user.first_name or user.username},</p>
                    
                    <p>Przypominamy o Twoim celu oszczędnościowym <strong>"{savings_goal.name}"</strong></p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #495057;">Postęp celu:</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li><strong>Cel:</strong> {savings_goal.name}</li>
                            <li><strong>Kwota docelowa:</strong> {savings_goal.target_amount} PLN</li>
                            <li><strong>Zebrano:</strong> {savings_goal.current_amount} PLN</li>
                            <li><strong>Pozostało:</strong> {savings_goal.target_amount - savings_goal.current_amount} PLN</li>
                            <li><strong>Postęp:</strong> {progress_percentage:.1f}%</li>
                            <li><strong>Data docelowa:</strong> {savings_goal.target_date}</li>
                            <li><strong>Dni pozostałe:</strong> {days_remaining}</li>
                        </ul>
                    </div>
                    
                    <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 0; color: #28a745; font-weight: bold;">
                            💡 Wskazówka: Aby osiągnąć cel na czas, powinieneś oszczędzać 
                            {(savings_goal.target_amount - savings_goal.current_amount) / max(days_remaining, 1):.2f} PLN dziennie.
                        </p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{settings.FRONTEND_URL}/savings-goals" 
                           style="background-color: #28a745; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Zobacz Cele Oszczędnościowe
                        </a>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        To jest automatyczny email z aplikacji budżetowej.
                    </p>
                </div>
            </body>
            </html>
            """
            
            text_message = f"""
            Przypomnienie o Celu Oszczędnościowym
            
            Witaj {user.first_name or user.username},
            
            Przypominamy o Twoim celu oszczędnościowym "{savings_goal.name}"
            
            Postęp celu:
            - Cel: {savings_goal.name}
            - Kwota docelowa: {savings_goal.target_amount} PLN
            - Zebrano: {savings_goal.current_amount} PLN
            - Pozostało: {savings_goal.target_amount - savings_goal.current_amount} PLN
            - Postęp: {progress_percentage:.1f}%
            - Data docelowa: {savings_goal.target_date}
            - Dni pozostałe: {days_remaining}
            
            💡 Wskazówka: Aby osiągnąć cel na czas, powinieneś oszczędzać 
            {(savings_goal.target_amount - savings_goal.current_amount) / max(days_remaining, 1):.2f} PLN dziennie.
            
            Zobacz cele: {settings.FRONTEND_URL}/savings-goals
            """
            
            EmailService._send_email(
                subject=subject,
                html_message=html_message,
                text_message=text_message,
                recipient_list=[user.email]
            )
            
            # Utwórz powiadomienie
            Notification.objects.create(
                user=user,
                notification_type='goal_reminder',
                title=subject,
                message=f"Przypomnienie o celu '{savings_goal.name}' - {progress_percentage:.1f}% ukończone",
                is_email_sent=True
            )
            
            logger.info(f"Savings goal reminder email sent to {user.email} for goal {savings_goal.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending savings goal reminder email: {e}")
            return False
    
    @staticmethod
    def send_payment_reminder_email(user: User, transaction_description: str, amount: Decimal, due_date):
        """Wysyła email z przypomnieniem o zbliżającej się płatności"""
        try:
            subject = f"💳 Przypomnienie o płatności: {transaction_description}"
            
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #ffc107;">💳 Przypomnienie o Płatności</h2>
                    
                    <p>Witaj {user.first_name or user.username},</p>
                    
                    <p>Przypominamy o zbliżającej się płatności:</p>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                        <h3 style="margin-top: 0; color: #856404;">Szczegóły płatności:</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li><strong>Opis:</strong> {transaction_description}</li>
                            <li><strong>Kwota:</strong> {amount} PLN</li>
                            <li><strong>Termin:</strong> {due_date}</li>
                        </ul>
                    </div>
                    
                    <p style="color: #856404; font-weight: bold;">
                        ⏰ Nie zapomnij o tej płatności!
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{settings.FRONTEND_URL}/transactions" 
                           style="background-color: #ffc107; color: #212529; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Zobacz Transakcje
                        </a>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        To jest automatyczny email z aplikacji budżetowej.
                    </p>
                </div>
            </body>
            </html>
            """
            
            text_message = f"""
            Przypomnienie o Płatności
            
            Witaj {user.first_name or user.username},
            
            Przypominamy o zbliżającej się płatności:
            
            Szczegóły:
            - Opis: {transaction_description}
            - Kwota: {amount} PLN
            - Termin: {due_date}
            
            ⏰ Nie zapomnij o tej płatności!
            
            Zobacz transakcje: {settings.FRONTEND_URL}/transactions
            """
            
            EmailService._send_email(
                subject=subject,
                html_message=html_message,
                text_message=text_message,
                recipient_list=[user.email]
            )
            
            # Utwórz powiadomienie
            Notification.objects.create(
                user=user,
                notification_type='payment_reminder',
                title=subject,
                message=f"Przypomnienie o płatności: {transaction_description} - {amount} PLN",
                is_email_sent=True
            )
            
            logger.info(f"Payment reminder email sent to {user.email} for {transaction_description}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending payment reminder email: {e}")
            return False
    
    @staticmethod
    def _send_email(subject: str, html_message: str, text_message: str, recipient_list: list):
        """Wysyła email używając SendGrid lub Django SMTP"""
        try:
            # Sprawdź czy SendGrid API Key jest skonfigurowany i nie jest pusty
            sendgrid_key = getattr(settings, 'SENDGRID_API_KEY', None)
            if sendgrid_key and sendgrid_key.strip() and not sendgrid_key.startswith('your_'):
                # Użyj SendGrid API
                EmailService._send_with_sendgrid(subject, html_message, text_message, recipient_list)
            else:
                # Fallback do Django SMTP (wymaga EMAIL_HOST_PASSWORD = SENDGRID_API_KEY)
                send_mail(
                    subject=subject,
                    message=text_message,
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipient_list,
                    fail_silently=False,
                )
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise
    
    @staticmethod
    def _send_with_sendgrid(subject: str, html_message: str, text_message: str, recipient_list: list):
        """Wysyła email używając SendGrid API"""
        try:
            sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
            
            for recipient in recipient_list:
                message = Mail(
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to_emails=recipient,
                    subject=subject,
                    html_content=html_message,
                    plain_text_content=text_message
                )
                
                response = sg.send(message)
                logger.info(f"SendGrid email sent to {recipient}, status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            raise
    
    @staticmethod
    def send_verification_email(user: User, verification_token: EmailVerificationToken):
        """Wysyła email weryfikacyjny do użytkownika"""
        try:
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token.token}"
            
            subject = "✅ Zweryfikuj swój adres email"
            
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #28a745;">✅ Weryfikacja adresu email</h2>
                    
                    <p>Witaj {user.first_name or user.username},</p>
                    
                    <p>Dziękujemy za rejestrację w aplikacji budżetowej!</p>
                    
                    <p>Aby aktywować swoje konto, kliknij w poniższy link weryfikacyjny:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}" 
                           style="background-color: #28a745; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Zweryfikuj adres email
                        </a>
                    </div>
                    
                    <p style="font-size: 12px; color: #666;">
                        Lub skopiuj i wklej ten link do przeglądarki:<br>
                        <a href="{verification_url}" style="color: #007bff; word-break: break-all;">{verification_url}</a>
                    </p>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                        <p style="margin: 0; color: #856404;">
                            ⏰ <strong>Ważne:</strong> Link jest ważny przez 24 godziny. 
                            Jeśli link wygasł, możesz poprosić o nowy w aplikacji.
                        </p>
                    </div>
                    
                    <p>Jeśli nie rejestrowałeś się w naszej aplikacji, możesz zignorować ten email.</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        To jest automatyczny email z aplikacji budżetowej.
                    </p>
                </div>
            </body>
            </html>
            """
            
            text_message = f"""
            Weryfikacja adresu email
            
            Witaj {user.first_name or user.username},
            
            Dziękujemy za rejestrację w aplikacji budżetowej!
            
            Aby aktywować swoje konto, kliknij w poniższy link:
            {verification_url}
            
            ⏰ Ważne: Link jest ważny przez 24 godziny.
            
            Jeśli nie rejestrowałeś się w naszej aplikacji, możesz zignorować ten email.
            """
            
            EmailService._send_email(
                subject=subject,
                html_message=html_message,
                text_message=text_message,
                recipient_list=[user.email]
            )
            
            logger.info(f"Verification email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending verification email: {e}")
            return False
    
    @staticmethod
    def send_password_reset_email(user: User, reset_token: PasswordResetToken):
        """Wysyła email z linkiem do resetu hasła"""
        try:
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token.token}"
            
            subject = "🔐 Reset hasła"
            
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #dc3545;">🔐 Reset hasła</h2>
                    
                    <p>Witaj {user.first_name or user.username},</p>
                    
                    <p>Otrzymaliśmy żądanie zresetowania hasła do Twojego konta.</p>
                    
                    <p>Aby zresetować hasło, kliknij w poniższy link:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" 
                           style="background-color: #dc3545; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Zresetuj hasło
                        </a>
                    </div>
                    
                    <p style="font-size: 12px; color: #666;">
                        Lub skopiuj i wklej ten link do przeglądarki:<br>
                        <a href="{reset_url}" style="color: #007bff; word-break: break-all;">{reset_url}</a>
                    </p>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                        <p style="margin: 0; color: #856404;">
                            ⏰ <strong>Ważne:</strong> Link jest ważny przez 1 godzinę. 
                            Jeśli link wygasł, możesz poprosić o nowy.
                        </p>
                    </div>
                    
                    <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #dc3545;">
                        <p style="margin: 0; color: #721c24;">
                            ⚠️ <strong>Bezpieczeństwo:</strong> Jeśli nie prosiłeś o reset hasła, zignoruj ten email. 
                            Twoje hasło pozostanie niezmienione.
                        </p>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        To jest automatyczny email z aplikacji budżetowej.
                    </p>
                </div>
            </body>
            </html>
            """
            
            text_message = f"""
            Reset hasła
            
            Witaj {user.first_name or user.username},
            
            Otrzymaliśmy żądanie zresetowania hasła do Twojego konta.
            
            Aby zresetować hasło, kliknij w poniższy link:
            {reset_url}
            
            Ważne: Link jest ważny przez 1 godzinę.
            
            Jeśli nie prosiłeś o reset hasła, zignoruj ten email.
            
            To jest automatyczny email z aplikacji budżetowej.
            """
            
            EmailService._send_email(
                subject=subject,
                html_message=html_message,
                text_message=text_message,
                recipient_list=[user.email]
            )
            
            logger.info(f"Password reset email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
            return False


