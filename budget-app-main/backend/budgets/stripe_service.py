import stripe
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from .models import PaymentIntegration, PaymentTransaction, SavingsGoal, Account, Transaction
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Konfiguracja Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Sprawdź czy klucz jest ustawiony
if not stripe.api_key or stripe.api_key.startswith('sk_test_your_') or stripe.api_key.startswith('sk_test_TUTAJ'):
    logger.warning("Stripe secret key not properly configured! Please set STRIPE_SECRET_KEY in settings.py")


def validate_stripe_key():
    """Waliduje klucz Stripe przed użyciem"""
    if not stripe.api_key:
        raise Exception("Stripe secret key is not configured. Please set STRIPE_SECRET_KEY in environment variables.")
    
    if len(stripe.api_key) < 20:
        raise Exception("Stripe secret key appears to be invalid (too short). Please check your STRIPE_SECRET_KEY.")
    
    # Sprawdź czy to nie jest placeholder
    if stripe.api_key.startswith('sk_test_your_') or stripe.api_key.startswith('sk_test_TUTAJ'):
        raise Exception("Stripe secret key is not configured. Please set a valid STRIPE_SECRET_KEY in environment variables.")
    
    # Loguj informacje o kluczu (bez pełnego klucza dla bezpieczeństwa)
    key_preview = f"{stripe.api_key[:7]}...{stripe.api_key[-4:]}" if len(stripe.api_key) > 11 else "N/A"
    logger.info(f"Using Stripe API key: {key_preview} (length: {len(stripe.api_key)})")
    
    return True


def test_stripe_connection():
    """Testuje połączenie z Stripe API"""
    try:
        validate_stripe_key()
        # Ustaw klucz bezpośrednio przed wywołaniem (dla pewności)
        stripe.api_key = settings.STRIPE_SECRET_KEY
        # Próba pobrania listy klientów (limit 1) - to sprawdzi czy klucz działa
        stripe.Customer.list(limit=1)
        logger.info("Stripe API connection test: SUCCESS")
        return True
    except stripe.AuthenticationError as e:
        logger.error(f"Stripe API connection test: FAILED - Authentication error: {e}")
        raise Exception(
            f"Klucz API Stripe jest nieprawidłowy lub wygasł. "
            f"Błąd: {str(e)}. "
            f"Sprawdź w Stripe Dashboard czy klucz jest aktywny i wygeneruj nowy jeśli potrzeba."
        )
    except Exception as e:
        logger.error(f"Stripe API connection test: FAILED - {type(e).__name__}: {e}")
        raise


class StripeService:
    """Serwis do obsługi płatności Stripe"""
    
    @staticmethod
    def create_customer(user: User, email: str = None) -> str:
        """Tworzy klienta w Stripe"""
        try:
            # Waliduj klucz przed użyciem
            validate_stripe_key()
            
            # Ustaw klucz bezpośrednio przed wywołaniem (dla pewności)
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            customer = stripe.Customer.create(
                email=email or user.email,
                name=f"{user.first_name} {user.last_name}".strip() or user.username,
                metadata={
                    'user_id': str(user.id),
                    'username': user.username
                }
            )
            
            # Zapisz integrację w bazie danych
            payment_integration, created = PaymentIntegration.objects.get_or_create(
                user=user,
                provider='stripe',
                defaults={
                    'provider_customer_id': customer.id,
                    'is_active': True
                }
            )
            
            if not created:
                payment_integration.provider_customer_id = customer.id
                payment_integration.is_active = True
                payment_integration.save()
            
            return customer.id
            
        except stripe.AuthenticationError as e:
            # Błąd autentykacji - wygasły lub nieprawidłowy klucz
            logger.error(f"Stripe authentication error: {e}")
            raise Exception(
                "Klucz API Stripe jest nieprawidłowy lub wygasł. "
                "Skontaktuj się z administratorem lub zaktualizuj STRIPE_SECRET_KEY w ustawieniach."
            )
        except stripe.APIConnectionError as e:
            # Błąd połączenia z Stripe
            logger.error(f"Stripe API connection error: {e}")
            raise Exception("Nie można połączyć się z Stripe. Sprawdź połączenie internetowe.")
        except stripe.StripeError as e:
            # Inne błędy Stripe
            error_type = type(e).__name__
            error_message = str(e)
            logger.error(f"Stripe error creating customer ({error_type}): {error_message}")
            raise Exception(f"Błąd Stripe: {error_message}")
        except Exception as e:
            # Inne błędy
            error_type = type(e).__name__
            error_message = str(e)
            logger.error(f"Error creating customer ({error_type}): {error_message}")
            logger.error(f"Stripe API key length: {len(stripe.api_key) if stripe.api_key else 0}")
            logger.error(f"Stripe API key starts with: {stripe.api_key[:10] if stripe.api_key and len(stripe.api_key) > 10 else 'N/A'}")
            raise Exception(f"Błąd tworzenia klienta Stripe: {error_message}")
    
    @staticmethod
    def create_payment_intent(amount: Decimal, currency: str = 'pln', 
                            customer_id: str = None, metadata: dict = None) -> dict:
        """Tworzy Payment Intent w Stripe"""
        try:
            # Waliduj klucz przed użyciem
            validate_stripe_key()
            
            # Konwertuj na grosze (Stripe wymaga kwot w najmniejszej jednostce waluty)
            amount_cents = int(amount * 100)
            
            intent_data = {
                'amount': amount_cents,
                'currency': currency,
                'automatic_payment_methods': {
                    'enabled': True,
                },
                'metadata': metadata or {}
            }
            
            if customer_id:
                intent_data['customer'] = customer_id
            
            # Ustaw klucz bezpośrednio przed wywołaniem (dla pewności)
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            payment_intent = stripe.PaymentIntent.create(**intent_data)
            
            return {
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'amount': amount,
                'currency': currency
            }
            
        except stripe.AuthenticationError as e:
            logger.error(f"Stripe authentication error creating payment intent: {e}")
            raise Exception(
                "Klucz API Stripe jest nieprawidłowy lub wygasł. "
                "Skontaktuj się z administratorem lub zaktualizuj STRIPE_SECRET_KEY w ustawieniach."
            )
        except stripe.StripeError as e:
            error_type = type(e).__name__
            logger.error(f"Stripe error creating payment intent ({error_type}): {e}")
            raise Exception(f"Błąd Stripe: {str(e)}")
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Error creating payment intent ({error_type}): {e}")
            raise Exception(f"Błąd tworzenia płatności: {str(e)}")
    
    @staticmethod
    def confirm_payment_intent(payment_intent_id: str) -> dict:
        """Potwierdza Payment Intent"""
        try:
            # Ustaw klucz bezpośrednio przed wywołaniem
            stripe.api_key = settings.STRIPE_SECRET_KEY
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if payment_intent.status == 'succeeded':
                return {
                    'status': 'succeeded',
                    'payment_intent': payment_intent
                }
            elif payment_intent.status == 'requires_action':
                return {
                    'status': 'requires_action',
                    'client_secret': payment_intent.client_secret
                }
            else:
                return {
                    'status': payment_intent.status,
                    'payment_intent': payment_intent
                }
                
        except Exception as e:
            # Stripe 7.x używa ogólnych wyjątków
            error_type = type(e).__name__
            logger.error(f"Stripe error confirming payment intent ({error_type}): {e}")
            raise Exception(f"Błąd potwierdzania płatności: {str(e)}")
    
    @staticmethod
    def create_payment_for_savings_goal(user: User, savings_goal: SavingsGoal, 
                                      amount: Decimal) -> dict:
        """Tworzy płatność dla celu oszczędnościowego"""
        try:
            # Pobierz lub utwórz klienta Stripe
            try:
                payment_integration = PaymentIntegration.objects.get(
                    user=user, provider='stripe', is_active=True
                )
                customer_id = payment_integration.provider_customer_id
            except PaymentIntegration.DoesNotExist:
                customer_id = StripeService.create_customer(user)
            
            # Utwórz Payment Intent
            metadata = {
                'savings_goal_id': str(savings_goal.id),
                'user_id': str(user.id),
                'type': 'savings_goal_payment'
            }
            
            payment_data = StripeService.create_payment_intent(
                amount=amount,
                currency='pln',
                customer_id=customer_id,
                metadata=metadata
            )
            
            # Zapisz transakcję płatności w bazie danych
            payment_transaction = PaymentTransaction.objects.create(
                user=user,
                payment_integration=PaymentIntegration.objects.get(
                    user=user, provider='stripe'
                ),
                savings_goal=savings_goal,
                amount=amount,
                currency='PLN',
                status='pending',
                provider_payment_intent_id=payment_data['payment_intent_id'],
                description=f"Płatność na cel: {savings_goal.name}"
            )
            
            return {
                'client_secret': payment_data['client_secret'],
                'payment_intent_id': payment_data['payment_intent_id'],
                'payment_transaction_id': str(payment_transaction.id),
                'amount': amount,
                'currency': 'PLN'
            }
            
        except Exception as e:
            logger.error(f"Error creating payment for savings goal: {e}")
            raise Exception(f"Błąd tworzenia płatności: {str(e)}")
    
    @staticmethod
    def handle_webhook(payload: str, signature: str) -> dict:
        """Obsługuje webhook od Stripe"""
        try:
            # Ustaw klucz bezpośrednio przed wywołaniem
            stripe.api_key = settings.STRIPE_SECRET_KEY
            event = stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
            
            event_type = event['type']
            
            if event_type == 'checkout.session.completed':
                return StripeService.handle_checkout_session_completed(event['data']['object'])
            elif event_type == 'payment_intent.succeeded':
                return StripeService._handle_payment_succeeded(event['data']['object'])
            elif event_type == 'payment_intent.payment_failed':
                return StripeService._handle_payment_failed(event['data']['object'])
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return {'status': 'ignored'}
                
        except Exception as e:
            # Stripe 7.x - sprawdź czy to błąd weryfikacji podpisu
            error_type = type(e).__name__
            if 'SignatureVerification' in error_type or 'signature' in str(e).lower():
                logger.error(f"Stripe webhook signature verification failed ({error_type}): {e}")
                raise Exception("Nieprawidłowy podpis webhook")
            logger.error(f"Error handling webhook ({error_type}): {e}")
            raise Exception(f"Błąd obsługi webhook: {str(e)}")
    
    @staticmethod
    def _handle_payment_succeeded(payment_intent: dict) -> dict:
        """Obsługuje udaną płatność"""
        try:
            payment_intent_id = payment_intent['id']
            metadata = payment_intent.get('metadata', {})
            
            # Znajdź transakcję płatności
            try:
                payment_transaction = PaymentTransaction.objects.get(
                    provider_payment_intent_id=payment_intent_id
                )
            except PaymentTransaction.DoesNotExist:
                logger.error(f"Payment transaction not found for intent: {payment_intent_id}")
                return {'status': 'error', 'message': 'Transaction not found'}
            
            # Idempotency: jeśli już przetworzona, zakończ
            if payment_transaction.status == 'completed':
                logger.info(f"Payment already completed for transaction: {payment_transaction.id}")
                return {'status': 'already_processed', 'transaction_id': str(payment_transaction.id)}

            # Aktualizuj status
            payment_transaction.status = 'completed'
            payment_transaction.provider_charge_id = payment_intent.get('latest_charge')
            payment_transaction.save()
            
            # Jeśli to płatność na cel oszczędnościowy
            if payment_transaction.savings_goal:
                savings_goal = payment_transaction.savings_goal
                
                # Dodaj kwotę do celu
                savings_goal.current_amount += payment_transaction.amount
                
                # Sprawdź czy cel został osiągnięty
                if savings_goal.current_amount >= savings_goal.target_amount:
                    savings_goal.is_completed = True
                
                savings_goal.save()
                
                # Utwórz transakcję przychodu
                Transaction.objects.create(
                    user=payment_transaction.user,
                    account=savings_goal.account,
                    amount=payment_transaction.amount,
                    transaction_type='income',
                    description=f"Płatność online na cel: {savings_goal.name}",
                    date=timezone.now()
                )
            
            logger.info(f"Payment succeeded for transaction: {payment_transaction.id}")
            return {'status': 'success', 'transaction_id': str(payment_transaction.id)}
            
        except Exception as e:
            logger.error(f"Error handling payment success: {e}")
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def _handle_payment_failed(payment_intent: dict) -> dict:
        """Obsługuje nieudaną płatność"""
        try:
            payment_intent_id = payment_intent['id']
            
            # Znajdź transakcję płatności
            try:
                payment_transaction = PaymentTransaction.objects.get(
                    provider_payment_intent_id=payment_intent_id
                )
            except PaymentTransaction.DoesNotExist:
                logger.error(f"Payment transaction not found for intent: {payment_intent_id}")
                return {'status': 'error', 'message': 'Transaction not found'}
            
            # Aktualizuj status
            payment_transaction.status = 'failed'
            payment_transaction.save()
            
            logger.info(f"Payment failed for transaction: {payment_transaction.id}")
            return {'status': 'failed', 'transaction_id': str(payment_transaction.id)}
            
        except Exception as e:
            logger.error(f"Error handling payment failure: {e}")
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def create_checkout_session(user: User, savings_goal: SavingsGoal, 
                                amount: Decimal, success_url: str, cancel_url: str) -> str:
        """Tworzy Stripe Checkout Session dla celu oszczędnościowego"""
        try:
            # Waliduj klucz przed użyciem
            validate_stripe_key()
            
            # Pobierz lub utwórz klienta Stripe
            try:
                payment_integration = PaymentIntegration.objects.get(
                    user=user, provider='stripe', is_active=True
                )
                customer_id = payment_integration.provider_customer_id
            except PaymentIntegration.DoesNotExist:
                customer_id = StripeService.create_customer(user)
            
            # Konwertuj na grosze
            amount_cents = int(amount * 100)
            
            # Najpierw utwórz transakcję płatności w bazie danych (status pending)
            payment_integration = PaymentIntegration.objects.get(
                user=user, provider='stripe'
            )
            payment_transaction = PaymentTransaction.objects.create(
                user=user,
                payment_integration=payment_integration,
                savings_goal=savings_goal,
                amount=amount,
                currency='PLN',
                status='pending',
                description=f"Płatność na cel: {savings_goal.name}",
            )
            
            # Ustaw klucz bezpośrednio przed wywołaniem (dla pewności)
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Utwórz Checkout Session z metadata zawierającym payment_transaction_id
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'pln',
                        'product_data': {
                            'name': f'Wpłata na cel: {savings_goal.name}',
                            'description': savings_goal.description or f'Wpłata {amount} PLN na cel oszczędnościowy',
                        },
                        'unit_amount': amount_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'savings_goal_id': str(savings_goal.id),
                    'user_id': str(user.id),
                    'type': 'savings_goal_payment',
                    'amount': str(amount),
                    'payment_transaction_id': str(payment_transaction.id),
                },
                allow_promotion_codes=True,
            )
            
            # Zaktualizuj transakcję z session_id w opisie (opcjonalnie)
            payment_transaction.description = f"Płatność na cel: {savings_goal.name} (Session: {checkout_session.id})"
            if checkout_session.payment_intent:
                payment_transaction.provider_payment_intent_id = checkout_session.payment_intent
            payment_transaction.save()
            
            logger.info(f"Checkout session created: {checkout_session.id} for goal: {savings_goal.id}")
            return checkout_session.url
            
        except stripe.AuthenticationError as e:
            # Błąd autentykacji - wygasły lub nieprawidłowy klucz
            logger.error(f"Stripe authentication error creating checkout session: {e}")
            raise Exception(
                "Klucz API Stripe jest nieprawidłowy lub wygasł. "
                "Skontaktuj się z administratorem lub zaktualizuj STRIPE_SECRET_KEY w ustawieniach."
            )
        except stripe.APIConnectionError as e:
            # Błąd połączenia z Stripe
            logger.error(f"Stripe API connection error: {e}")
            raise Exception("Nie można połączyć się z Stripe. Sprawdź połączenie internetowe.")
        except stripe.StripeError as e:
            # Inne błędy Stripe
            error_type = type(e).__name__
            error_message = str(e)
            logger.error(f"Stripe error creating checkout session ({error_type}): {error_message}")
            raise Exception(f"Błąd Stripe: {error_message}")
        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            raise Exception(f"Błąd tworzenia sesji płatności: {str(e)}")
    
    @staticmethod
    def handle_checkout_session_completed(session: dict) -> dict:
        """Obsługuje zakończoną sesję Checkout"""
        try:
            session_id = session['id']
            metadata = session.get('metadata', {})
            payment_intent_id = session.get('payment_intent')
            
            if not payment_intent_id:
                logger.error(f"No payment_intent in checkout session: {session_id}")
                return {'status': 'error', 'message': 'No payment intent'}
            
            # Znajdź transakcję płatności po payment_transaction_id z metadata
            try:
                payment_transaction_id = metadata.get('payment_transaction_id')
                
                if payment_transaction_id:
                    payment_transaction = PaymentTransaction.objects.filter(
                        id=payment_transaction_id
                    ).first()
                
                # Fallback - znajdź po payment_intent
                if not payment_transaction and payment_intent_id:
                    payment_transaction = PaymentTransaction.objects.filter(
                        provider_payment_intent_id=payment_intent_id
                    ).first()
                
                # Fallback - znajdź najnowszą pending transakcję dla tego celu
                if not payment_transaction and metadata.get('savings_goal_id'):
                    savings_goal_id = metadata.get('savings_goal_id')
                    payment_transaction = PaymentTransaction.objects.filter(
                        savings_goal_id=savings_goal_id,
                        status='pending',
                        amount=Decimal(metadata.get('amount', '0'))
                    ).order_by('-created_at').first()
                
                if not payment_transaction:
                    logger.error(f"Payment transaction not found for session: {session_id}")
                    return {'status': 'error', 'message': 'Transaction not found'}
                    
            except Exception as e:
                logger.error(f"Error finding payment transaction: {e}")
                return {'status': 'error', 'message': str(e)}
            
            # Idempotency: jeśli już przetworzona, zakończ
            if payment_transaction.status == 'completed':
                logger.info(f"Checkout session already processed: {session_id} for transaction: {payment_transaction.id}")
                return {'status': 'already_processed', 'transaction_id': str(payment_transaction.id)}

            # Aktualizuj status
            payment_transaction.status = 'completed'
            payment_transaction.provider_payment_intent_id = payment_intent_id
            payment_transaction.provider_charge_id = session.get('payment_intent')
            payment_transaction.save()
            
            # Jeśli to płatność na cel oszczędnościowy
            if payment_transaction.savings_goal:
                savings_goal = payment_transaction.savings_goal
                
                # Dodaj kwotę do celu
                savings_goal.current_amount += payment_transaction.amount
                
                # Sprawdź czy cel został osiągnięty
                if savings_goal.current_amount >= savings_goal.target_amount:
                    savings_goal.is_completed = True
                
                savings_goal.save()
                
                # Utwórz transakcję przychodu
                Transaction.objects.create(
                    user=payment_transaction.user,
                    account=savings_goal.account,
                    amount=payment_transaction.amount,
                    transaction_type='income',
                    description=f"Płatność online na cel: {savings_goal.name}",
                    date=timezone.now()
                )
            
            logger.info(f"Checkout session completed: {session_id} for transaction: {payment_transaction.id}")
            return {'status': 'success', 'transaction_id': str(payment_transaction.id)}
            
        except Exception as e:
            logger.error(f"Error handling checkout completion: {e}")
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def confirm_checkout_session(session_id: str) -> dict:
        """Pobiera sesję Checkout z Stripe i przetwarza ją jak webhook.

        Używane jako fallback, gdy webhook nie jest skonfigurowany.
        """
        try:
            if not session_id:
                return {'status': 'error', 'message': 'Brak session_id'}

            # Ustaw klucz bezpośrednio przed wywołaniem
            stripe.api_key = settings.STRIPE_SECRET_KEY
            # Retrieve session from Stripe
            session = stripe.checkout.Session.retrieve(session_id)
            if not session:
                return {'status': 'error', 'message': 'Sesja nie znaleziona'}

            # Reuse the same business logic as webhook path
            return StripeService.handle_checkout_session_completed(session)
        except Exception as e:
            logger.error(f"Error confirming checkout session {session_id}: {e}")
            return {'status': 'error', 'message': str(e)}