from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

from .models import (
    Category, Account, Transaction, SavingsGoal, 
    Budget, Notification, PaymentIntegration, PaymentTransaction
)
from .serializers import (
    UserRegisterSerializer, UserProfileSerializer, CustomTokenObtainPairSerializer,
    CategorySerializer, AccountSerializer, TransactionSerializer,
    SavingsGoalSerializer, BudgetSerializer, NotificationSerializer,
    PaymentIntegrationSerializer, PaymentTransactionSerializer,
    TransactionSummarySerializer, CategoryExpenseSerializer, MonthlyReportSerializer
)
from .stripe_service import StripeService


@csrf_exempt
def test_api(request):
    return JsonResponse({"message": "Polaczenie dziala!"})


# ========== AUTHENTICATION VIEWS ==========

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom view dla JWT, który używa CustomTokenObtainPairSerializer"""
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from .models import EmailVerificationToken
        from .email_service import EmailService
        
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                
                # Utwórz token weryfikacyjny
                verification_token = EmailVerificationToken.create_for_user(user)
                
                # Wyślij email weryfikacyjny
                email_sent = EmailService.send_verification_email(user, verification_token)
                
                if email_sent:
                    return Response({
                        'id': user.id, 
                        'username': user.username,
                        'email': user.email,
                        'message': 'Konto zostało utworzone. Sprawdź email w celu weryfikacji adresu.'
                    }, status=status.HTTP_201_CREATED)
                else:
                    # Jeśli email nie został wysłany, zwróć błąd ale użytkownik został utworzony
                    logger.warning(f"User {user.username} ({user.email}) registered but verification email failed to send")
                    return Response({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'warning': 'Konto zostało utworzone, ale email weryfikacyjny nie został wysłany. Skontaktuj się z administratorem.'
                    }, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error during user registration: {e}", exc_info=True)
                return Response({
                    'error': f'Błąd podczas rejestracji: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Loguj błędy walidacji dla debugowania
            logger.warning(f"Registration validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    user = request.user
    return Response({'id': user.id, 'username': user.username, 'email': user.email})


@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def profile(request):
    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """Zmienia hasło użytkownika"""
    from .serializers import ChangePasswordSerializer
    
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        logger.info(f"Password changed for user: {request.user.username}")
        return Response({'message': 'Hasło zostało zmienione pomyślnie.'}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def forgot_password(request):
    """Wysyła email z linkiem do resetu hasła"""
    from .models import PasswordResetToken
    from .serializers import PasswordResetRequestSerializer
    from .email_service import EmailService
    
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email, is_active=True)
            
            # Utwórz token resetu hasła
            reset_token = PasswordResetToken.create_for_user(user)
            
            # Wyślij email
            email_sent = EmailService.send_password_reset_email(user, reset_token)
            
            if email_sent:
                # Dla bezpieczeństwa zawsze zwracamy ten sam komunikat
                return Response({
                    'message': 'Jeśli konto z tym adresem email istnieje, wysłaliśmy link do resetu hasła. Sprawdź swoją skrzynkę.'
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f"Failed to send password reset email to {email}")
                return Response({
                    'error': 'Nie udało się wysłać emaila. Spróbuj ponownie później.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except User.DoesNotExist:
            # Dla bezpieczeństwa nie ujawniamy czy użytkownik istnieje
            return Response({
                'message': 'Jeśli konto z tym adresem email istnieje, wysłaliśmy link do resetu hasła. Sprawdź swoją skrzynkę.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in forgot_password: {e}", exc_info=True)
            return Response({
                'error': 'Wystąpił błąd podczas przetwarzania żądania.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    """Resetuje hasło użytkownika na podstawie tokena"""
    from .serializers import PasswordResetSerializer
    
    serializer = PasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            logger.info(f"Password reset successful for user: {user.username}")
            return Response({
                'message': 'Hasło zostało pomyślnie zresetowane. Możesz się teraz zalogować.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error resetting password: {e}", exc_info=True)
            return Response({
                'error': 'Wystąpił błąd podczas resetowania hasła.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_email(request):
    """Weryfikuje adres email użytkownika na podstawie tokena"""
    from .models import EmailVerificationToken
    
    token = request.data.get('token')
    if not token:
        return Response(
            {'error': 'Token weryfikacyjny jest wymagany'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        verification_token = EmailVerificationToken.objects.get(token=token)
        
        # Sprawdź czy token jest ważny
        if verification_token.is_used:
            return Response(
                {'error': 'Ten token został już użyty'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if verification_token.is_expired():
            return Response(
                {'error': 'Token wygasł. Poproś o nowy email weryfikacyjny'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Aktywuj użytkownika
        user = verification_token.user
        user.is_active = True
        user.save()
        
        # Oznacz token jako użyty
        verification_token.is_used = True
        verification_token.save()
        
        return Response({
            'message': 'Email został pomyślnie zweryfikowany. Możesz się teraz zalogować.',
            'username': user.username
        }, status=status.HTTP_200_OK)
        
    except EmailVerificationToken.DoesNotExist:
        return Response(
            {'error': 'Nieprawidłowy token weryfikacyjny'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error verifying email: {e}")
        return Response(
            {'error': f'Błąd podczas weryfikacji: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def google_login(request):
    """Logowanie przez Google OAuth (tylko dla istniejących kont)"""
    from .google_auth_service import GoogleAuthService
    
    token = request.data.get('token')
    if not token:
        return Response(
            {'error': 'Token Google jest wymagany'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        result = GoogleAuthService.login_with_google(token)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Google login error: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def resend_verification_email(request):
    """Wysyła ponownie email weryfikacyjny"""
    from .models import EmailVerificationToken
    from .email_service import EmailService
    
    email = request.data.get('email')
    username = request.data.get('username')
    
    if not email and not username:
        return Response(
            {'error': 'Email lub username jest wymagany'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Znajdź użytkownika
        if email:
            user = User.objects.get(email=email)
        else:
            user = User.objects.get(username=username)
        
        # Sprawdź czy użytkownik nie jest już zweryfikowany
        if user.is_active:
            return Response(
                {'message': 'Ten adres email jest już zweryfikowany'}, 
                status=status.HTTP_200_OK
            )
        
        # Utwórz nowy token
        verification_token = EmailVerificationToken.create_for_user(user)
        
        # Wyślij email
        email_sent = EmailService.send_verification_email(user, verification_token)
        
        if email_sent:
            return Response({
                'message': 'Email weryfikacyjny został wysłany ponownie. Sprawdź swoją skrzynkę.'
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Nie udało się wysłać emaila weryfikacyjnego'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except User.DoesNotExist:
        return Response(
            {'error': 'Użytkownik nie został znaleziony'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error resending verification email: {e}")
        return Response(
            {'error': f'Błąd podczas wysyłania emaila: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ========== CATEGORY VIEWS ==========

class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user, is_active=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


# ========== ACCOUNT VIEWS ==========

class AccountListCreateView(generics.ListCreateAPIView):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'balance', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user, is_active=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


# ========== TRANSACTION VIEWS ==========

class TransactionListCreateView(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'tags']
    ordering_fields = ['date', 'amount', 'created_at']
    ordering = ['-date', '-created_at']

    def get_queryset(self):
        # Użyj select_related, żeby uniknąć problemów N+1 queries
        queryset = Transaction.objects.filter(user=self.request.user).select_related(
            'account', 'category', 'transfer_to_account'
        )
        
        # Filtry
        account_id = self.request.query_params.get('account')
        category_id = self.request.query_params.get('category')
        transaction_type = self.request.query_params.get('type')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).select_related(
            'account', 'category', 'transfer_to_account'
        )


# ========== SAVINGS GOAL VIEWS ==========

class SavingsGoalListCreateView(generics.ListCreateAPIView):
    serializer_class = SavingsGoalSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'target_date', 'created_at']
    ordering = ['target_date']

    def get_queryset(self):
        return SavingsGoal.objects.filter(user=self.request.user, is_active=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SavingsGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SavingsGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavingsGoal.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


# ========== BUDGET VIEWS ==========

class BudgetListCreateView(generics.ListCreateAPIView):
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'start_date', 'amount']
    ordering = ['-start_date']

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user, is_active=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BudgetDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


# ========== NOTIFICATION VIEWS ==========

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering = ['-created_at']

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({'status': 'success'})
    except Notification.DoesNotExist:
        return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)


# ========== ANALYTICS & REPORTS VIEWS ==========

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def transaction_summary(request):
    """Podsumowanie transakcji w danym okresie"""
    user = request.user
    
    # Parametry dat
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    
    if not date_from or not date_to:
        # Domyślnie ostatni miesiąc
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Zapytania
    transactions = Transaction.objects.filter(
        user=user,
        date__date__gte=start_date,
        date__date__lte=end_date
    )
    
    total_income = transactions.filter(transaction_type='income').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    total_expenses = transactions.filter(transaction_type='expense').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    net_income = total_income - total_expenses
    transaction_count = transactions.count()
    
    data = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_income': net_income,
        'transaction_count': transaction_count,
        'period_start': start_date,
        'period_end': end_date
    }
    
    serializer = TransactionSummarySerializer(data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def category_expenses(request):
    """Wydatki według kategorii"""
    user = request.user
    
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    
    if not date_from or not date_to:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Agregacja wydatków według kategorii
    category_expenses = Transaction.objects.filter(
        user=user,
        transaction_type='expense',
        date__date__gte=start_date,
        date__date__lte=end_date,
        category__isnull=False
    ).select_related('category').values(
        'category__name', 
        'category__id',
        'category__color',
        'category__icon'
    ).annotate(
        total_amount=Sum('amount'),
        transaction_count=Count('id')
    ).order_by('-total_amount')
    
    total_expenses = sum(item['total_amount'] for item in category_expenses)
    
    result = []
    for item in category_expenses:
        percentage = (item['total_amount'] / total_expenses * 100) if total_expenses > 0 else 0
        result.append({
            'category_name': item['category__name'],
            'category_id': item['category__id'],
            'category_color': item.get('category__color', '#3498db'),
            'category_icon': item.get('category__icon', None),
            'total_amount': item['total_amount'],
            'transaction_count': item['transaction_count'],
            'percentage': round(percentage, 2)
        })
    
    serializer = CategoryExpenseSerializer(result, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def monthly_report(request, year, month):
    """Raport miesięczny"""
    user = request.user
    
    # Okres miesięczny
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    # Transakcje w danym miesiącu
    transactions = Transaction.objects.filter(
        user=user,
        date__date__gte=start_date,
        date__date__lte=end_date
    )
    
    total_income = transactions.filter(transaction_type='income').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    total_expenses = transactions.filter(transaction_type='expense').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    net_income = total_income - total_expenses
    
    # Wydatki według kategorii
    category_breakdown = Transaction.objects.filter(
        user=user,
        transaction_type='expense',
        date__date__gte=start_date,
        date__date__lte=end_date,
        category__isnull=False
    ).values('category__name', 'category__id').annotate(
        total_amount=Sum('amount'),
        transaction_count=Count('id')
    ).order_by('-total_amount')
    
    category_data = []
    for item in category_breakdown:
        percentage = (item['total_amount'] / total_expenses * 100) if total_expenses > 0 else 0
        category_data.append({
            'category_name': item['category__name'],
            'category_id': item['category__id'],
            'total_amount': item['total_amount'],
            'transaction_count': item['transaction_count'],
            'percentage': round(percentage, 2)
        })
    
    data = {
        'month': start_date.strftime('%B'),
        'year': year,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_income': net_income,
        'category_breakdown': category_data
    }
    
    serializer = MonthlyReportSerializer(data)
    return Response(serializer.data)


# ========== DASHBOARD VIEW ==========

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard(request):
    """Dashboard z podstawowymi statystykami"""
    user = request.user
    
    # Podstawowe statystyki
    total_accounts = Account.objects.filter(user=user, is_active=True).count()
    total_categories = Category.objects.filter(user=user, is_active=True).count()
    active_budgets = Budget.objects.filter(user=user, is_active=True).count()
    active_savings_goals = SavingsGoal.objects.filter(user=user, is_active=True).count()
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()
    
    # Saldo wszystkich kont
    total_balance = Account.objects.filter(user=user, is_active=True).aggregate(
        total=Sum('balance')
    )['total'] or Decimal('0.00')
    
    # Ostatnie transakcje
    recent_transactions = Transaction.objects.filter(user=user).select_related(
        'account', 'category', 'transfer_to_account'
    ).order_by('-date')[:5]
    recent_transactions_data = TransactionSerializer(recent_transactions, many=True).data
    
    # Aktywne budżety z wykorzystaniem
    active_budgets_data = Budget.objects.filter(user=user, is_active=True)[:5]
    budgets_data = BudgetSerializer(active_budgets_data, many=True).data
    
    # Cele oszczędnościowe
    savings_goals_data = SavingsGoal.objects.filter(user=user, is_active=True)[:5]
    goals_data = SavingsGoalSerializer(savings_goals_data, many=True).data
    
    return Response({
        'stats': {
            'total_accounts': total_accounts,
            'total_categories': total_categories,
            'active_budgets': active_budgets,
            'active_savings_goals': active_savings_goals,
            'unread_notifications': unread_notifications,
            'total_balance': total_balance
        },
        'recent_transactions': recent_transactions_data,
        'active_budgets': budgets_data,
        'savings_goals': goals_data
    })


# ========== PAYMENT VIEWS ==========

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_payment_for_savings_goal(request, savings_goal_id):
    """Tworzy płatność Stripe dla celu oszczędnościowego (legacy - Payment Intent)"""
    try:
        # Sprawdź czy cel oszczędnościowy istnieje i należy do użytkownika
        savings_goal = SavingsGoal.objects.get(
            id=savings_goal_id, 
            user=request.user, 
            is_active=True
        )
        
        # Walidacja danych
        amount = request.data.get('amount')
        if not amount:
            return Response(
                {'error': 'Kwota jest wymagana'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                return Response(
                    {'error': 'Kwota musi być większa od 0'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Nieprawidłowa kwota'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Sprawdź czy cel nie jest już ukończony
        if savings_goal.is_completed:
            return Response(
                {'error': 'Cel oszczędnościowy został już ukończony'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Utwórz płatność
        payment_data = StripeService.create_payment_for_savings_goal(
            user=request.user,
            savings_goal=savings_goal,
            amount=amount
        )
        
        return Response(payment_data, status=status.HTTP_201_CREATED)
        
    except SavingsGoal.DoesNotExist:
        return Response(
            {'error': 'Cel oszczędnościowy nie został znaleziony'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_checkout_session(request, savings_goal_id):
    """Tworzy Stripe Checkout Session dla celu oszczędnościowego"""
    try:
        from django.conf import settings
        
        # Sprawdź czy cel oszczędnościowy istnieje i należy do użytkownika
        savings_goal = SavingsGoal.objects.get(
            id=savings_goal_id, 
            user=request.user, 
            is_active=True
        )
        
        # Walidacja danych
        amount = request.data.get('amount')
        if not amount:
            return Response(
                {'error': 'Kwota jest wymagana'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                return Response(
                    {'error': 'Kwota musi być większa od 0'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Nieprawidłowa kwota'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Sprawdź czy cel nie jest już ukończony
        if savings_goal.is_completed:
            return Response(
                {'error': 'Cel oszczędnościowy został już ukończony'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # URL do przekierowania po płatności
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://budget-app-adbaf.web.app')
        if not frontend_url:
            frontend_url = 'https://budget-app-adbaf.web.app'
        frontend_url = frontend_url.rstrip('/')
        success_url = f"{frontend_url}/savings-goals?payment=success&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{frontend_url}/savings-goals?payment=cancelled"
        
        # Utwórz Checkout Session
        checkout_url = StripeService.create_checkout_session(
            user=request.user,
            savings_goal=savings_goal,
            amount=amount,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        return Response({
            'checkout_url': checkout_url,
            'amount': amount,
            'currency': 'PLN'
        }, status=status.HTTP_201_CREATED)
        
    except SavingsGoal.DoesNotExist:
        return Response(
            {'error': 'Cel oszczędnościowy nie został znaleziony'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error creating checkout session for savings goal {savings_goal_id}: {e}", exc_info=True)
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def payment_statistics(request, savings_goal_id):
    """Zwraca statystyki wpłat dla celu oszczędnościowego"""
    try:
        from django.db.models import Sum, Count
        
        # Sprawdź czy cel oszczędnościowy należy do użytkownika
        savings_goal = SavingsGoal.objects.get(
            id=savings_goal_id,
            user=request.user
        )
        
        # Pobierz transakcje płatności dla tego celu
        payments = PaymentTransaction.objects.filter(
            savings_goal=savings_goal,
            user=request.user
        )
        
        # Statystyki
        total_amount = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        total_count = payments.count()
        completed_count = payments.filter(status='completed').count()
        completed_amount = payments.filter(status='completed').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return Response({
            'goal_id': str(savings_goal.id),
            'goal_name': savings_goal.name,
            'total_payments': total_count,
            'completed_payments': completed_count,
            'total_amount': total_amount,
            'completed_amount': completed_amount,
            'pending_amount': total_amount - completed_amount,
        })
        
    except SavingsGoal.DoesNotExist:
        return Response(
            {'error': 'Cel oszczędnościowy nie został znaleziony'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def payment_transactions(request):
    """Lista transakcji płatności użytkownika"""
    transactions = PaymentTransaction.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    serializer = PaymentTransactionSerializer(transactions, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def payment_transaction_detail(request, transaction_id):
    """Szczegóły transakcji płatności"""
    try:
        transaction = PaymentTransaction.objects.get(
            id=transaction_id, 
            user=request.user
        )
        serializer = PaymentTransactionSerializer(transaction)
        return Response(serializer.data)
    except PaymentTransaction.DoesNotExist:
        return Response(
            {'error': 'Transakcja nie została znaleziona'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # Stripe webhook
def stripe_webhook(request):
    """Webhook endpoint dla Stripe"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        result = StripeService.handle_webhook(payload, sig_header)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def stripe_config(request):
    """Zwraca konfigurację Stripe dla frontendu"""
    from django.conf import settings
    
    return Response({
        'publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'currency': 'PLN'
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def stripe_test_connection(request):
    """Testuje połączenie z Stripe API - sprawdza czy klucz jest poprawny"""
    try:
        from .stripe_service import test_stripe_connection, validate_stripe_key
        from django.conf import settings
        
        # Waliduj klucz
        validate_stripe_key()
        
        # Test połączenia
        test_stripe_connection()
        
        # Pokaż preview klucza (bez pełnego klucza)
        key_preview = f"{settings.STRIPE_SECRET_KEY[:7]}...{settings.STRIPE_SECRET_KEY[-4:]}" if settings.STRIPE_SECRET_KEY and len(settings.STRIPE_SECRET_KEY) > 11 else "N/A"
        
        return Response({
            'status': 'success',
            'message': 'Połączenie z Stripe działa poprawnie',
            'key_preview': key_preview,
            'key_length': len(settings.STRIPE_SECRET_KEY) if settings.STRIPE_SECRET_KEY else 0
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e),
            'key_preview': f"{settings.STRIPE_SECRET_KEY[:7]}...{settings.STRIPE_SECRET_KEY[-4:]}" if settings.STRIPE_SECRET_KEY and len(settings.STRIPE_SECRET_KEY) > 11 else "N/A",
            'key_length': len(settings.STRIPE_SECRET_KEY) if settings.STRIPE_SECRET_KEY else 0
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def stripe_checkout_confirm(request):
    """Potwierdza Stripe Checkout po powrocie z sukcesem (fallback bez webhooków)."""
    try:
        session_id = request.data.get('session_id') or request.query_params.get('session_id')
        if not session_id:
            return Response({'error': 'Brak session_id'}, status=status.HTTP_400_BAD_REQUEST)

        result = StripeService.confirm_checkout_session(session_id)
        http_status = status.HTTP_200_OK if result.get('status') in ('success', 'ignored') else status.HTTP_400_BAD_REQUEST
        return Response(result, status=http_status)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ========== ALERT MANAGEMENT VIEWS ==========

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def run_alerts(request):
    """Uruchamia sprawdzenia alertów dla zalogowanego użytkownika"""
    from .alert_service import AlertService
    
    alert_type = request.data.get('type', 'all')
    user = request.user  # Tylko dla zalogowanego użytkownika
    
    try:
        if alert_type == 'budget':
            count = AlertService.check_budget_alerts(user=user)
            return Response({
                'message': f'Sprawdzono alerty budżetowe. Wysłano {count} alertów.',
                'alerts_sent': count
            })
        elif alert_type == 'goals':
            count = AlertService.check_savings_goals_reminders(user=user)
            return Response({
                'message': f'Sprawdzono przypomnienia o celach. Wysłano {count} przypomnień.',
                'alerts_sent': count
            })
        elif alert_type == 'payments':
            count = AlertService.check_payment_reminders(user=user)
            return Response({
                'message': f'Sprawdzono przypomnienia o płatnościach. Wysłano {count} przypomnień.',
                'alerts_sent': count
            })
        elif alert_type == 'weekly':
            count = AlertService.create_weekly_summary()
            return Response({
                'message': f'Utworzono {count} cotygodniowych podsumowań.',
                'summaries_created': count
            })
        else:
            # Wszystkie sprawdzenia
            results = AlertService.run_all_checks(user=user)
            return Response({
                'message': 'Wszystkie sprawdzenia alertów zakończone.',
                'results': results,
                'alerts_sent': results.get('total', 0),
                'weekly_summaries': results.get('weekly_summaries', 0)
            })
            
    except Exception as e:
        return Response(
            {'error': f'Błąd podczas uruchamiania alertów: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def alert_status(request):
    """Zwraca status alertów dla użytkownika"""
    user = request.user
    
    # Nieprzeczytane powiadomienia
    unread_notifications = Notification.objects.filter(
        user=user, 
        is_read=False
    ).count()
    
    # Ostatnie alerty budżetowe
    recent_budget_alerts = Notification.objects.filter(
        user=user,
        notification_type='budget_alert',
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    # Ostatnie przypomnienia o celach
    recent_goal_reminders = Notification.objects.filter(
        user=user,
        notification_type='goal_reminder',
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    # Ostatnie przypomnienia o płatnościach
    recent_payment_reminders = Notification.objects.filter(
        user=user,
        notification_type='payment_reminder',
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    return Response({
        'unread_notifications': unread_notifications,
        'recent_alerts': {
            'budget_alerts': recent_budget_alerts,
            'goal_reminders': recent_goal_reminders,
            'payment_reminders': recent_payment_reminders,
            'total': recent_budget_alerts + recent_goal_reminders + recent_payment_reminders
        }
    })
