from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import (
    Category, Account, Transaction, SavingsGoal, 
    Budget, Notification, PaymentIntegration, PaymentTransaction,
    EmailVerificationToken
)
from decimal import Decimal


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom serializer dla JWT, który sprawdza czy użytkownik jest aktywny"""
    
    def validate(self, attrs):
        from django.contrib.auth import authenticate
        from django.contrib.auth import get_user_model
        from rest_framework_simplejwt.exceptions import AuthenticationFailed
        
        username = attrs.get('username')
        password = attrs.get('password')
        
        if not username or not password:
            raise serializers.ValidationError('Username i password są wymagane.')
        
        # Najpierw sprawdź czy użytkownik istnieje i czy jest aktywny
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
            
            # Sprawdź czy użytkownik jest aktywny
            if not user.is_active:
                raise serializers.ValidationError({
                    'error': 'Konto nie jest aktywne. Sprawdź email w celu weryfikacji adresu.',
                    'code': 'account_inactive',
                    'email': user.email
                })
            
            # Sprawdź hasło ręcznie (zamiast używać authenticate(), które sprawdza is_active)
            if not user.check_password(password):
                raise serializers.ValidationError('Nieprawidłowe dane logowania.')
            
        except User.DoesNotExist:
            # Jeśli użytkownik nie istnieje, nie ujawniaj tego (bezpieczeństwo)
            raise serializers.ValidationError('Nieprawidłowe dane logowania.')
        
        # Teraz użyj standardowej metody do generowania tokenów
        refresh = self.get_token(user)
        
        data = {}
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        
        return data


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    email = serializers.EmailField(required=True)  # Email jest wymagany dla weryfikacji

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def validate_username(self, value):
        """Sprawdź czy username już istnieje"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Użytkownik o tej nazwie już istnieje.")
        return value

    def validate_email(self, value):
        """Sprawdź czy email już istnieje i jest poprawny"""
        if not value:
            raise serializers.ValidationError("Email jest wymagany.")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Użytkownik o tym adresie email już istnieje.")
        return value

    def create(self, validated_data):
        try:
            # Utwórz użytkownika jako nieaktywnego (do czasu weryfikacji emaila)
            user = User(
                username=validated_data['username'], 
                email=validated_data.get('email', ''),
                is_active=False  # Użytkownik nieaktywny do czasu weryfikacji
            )
            user.set_password(validated_data['password'])
            user.save()
            return user
        except Exception as e:
            # Obsługa błędów bazy danych (np. IntegrityError)
            raise serializers.ValidationError(f"Błąd podczas tworzenia użytkownika: {str(e)}")


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined')
        read_only_fields = ('id', 'date_joined')


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer do zmiany hasła użytkownika"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=6)
    
    def validate_old_password(self, value):
        """Sprawdź czy stare hasło jest poprawne"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Stare hasło jest nieprawidłowe.")
        return value
    
    def validate_new_password(self, value):
        """Sprawdź czy nowe hasło jest różne od starego"""
        old_password = self.initial_data.get('old_password')
        if old_password and value == old_password:
            raise serializers.ValidationError("Nowe hasło musi być różne od starego hasła.")
        return value
    
    def save(self):
        """Zapisz nowe hasło"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer do żądania resetu hasła"""
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Sprawdź czy użytkownik z tym emailem istnieje"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=value)
            if not user.is_active:
                raise serializers.ValidationError("Konto nie jest aktywne. Najpierw zweryfikuj adres email.")
        except User.DoesNotExist:
            # Dla bezpieczeństwa nie ujawniamy czy użytkownik istnieje
            pass
        return value


class PasswordResetSerializer(serializers.Serializer):
    """Serializer do resetu hasła na podstawie tokena"""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=6)
    
    def validate_token(self, value):
        """Sprawdź czy token jest ważny"""
        from .models import PasswordResetToken
        try:
            reset_token = PasswordResetToken.objects.get(token=value)
            if reset_token.is_used:
                raise serializers.ValidationError("Ten token został już użyty.")
            if reset_token.is_expired():
                raise serializers.ValidationError("Token wygasł. Poproś o nowy link resetu hasła.")
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Nieprawidłowy token resetu hasła.")
        return value
    
    def save(self):
        """Zresetuj hasło użytkownika"""
        from .models import PasswordResetToken
        token = self.validated_data['token']
        new_password = self.validated_data['new_password']
        
        reset_token = PasswordResetToken.objects.get(token=token)
        user = reset_token.user
        
        # Ustaw nowe hasło
        user.set_password(new_password)
        user.save()
        
        # Oznacz token jako użyty
        reset_token.is_used = True
        reset_token.save()
        
        return user


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def validate(self, data):
        # Sprawdź czy użytkownik nie ma już kategorii o tej samej nazwie i typie
        user = self.context['request'].user
        if Category.objects.filter(
            user=user, 
            name=data['name'], 
            category_type=data['category_type']
        ).exists():
            raise serializers.ValidationError(
                f"Kategoria '{data['name']}' typu '{data['category_type']}' już istnieje."
            )
        return data


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def validate_balance(self, value):
        if value < 0:
            raise serializers.ValidationError("Saldo nie może być ujemne.")
        return value


class TransactionSerializer(serializers.ModelSerializer):
    # Pola do zapisu (akceptują ID) - queryset będzie ustawiony w __init__
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.none(), write_only=False)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.none(), required=False, allow_null=True, write_only=False)
    transfer_to_account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.none(), required=False, allow_null=True, write_only=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ustaw queryset dla kont i kategorii użytkownika
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            # Filtruj tylko konta i kategorie użytkownika
            self.fields['account'].queryset = Account.objects.filter(user=user, is_active=True)
            self.fields['category'].queryset = Category.objects.filter(user=user, is_active=True)
            self.fields['transfer_to_account'].queryset = Account.objects.filter(user=user, is_active=True)
    
    # Pola pomocnicze do odczytu (pełne obiekty)
    account_detail = AccountSerializer(source='account', read_only=True)
    category_detail = CategorySerializer(source='category', read_only=True)
    transfer_to_account_detail = AccountSerializer(source='transfer_to_account', read_only=True)
    
    # Dodatkowe pola pomocnicze
    account_name = serializers.CharField(source='account.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    transfer_to_account_name = serializers.CharField(source='transfer_to_account.name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'account', 'category', 'transfer_to_account',
            'account_detail', 'category_detail', 'transfer_to_account_detail',
            'amount', 'transaction_type', 'description', 'date',
            'tags', 'location', 'receipt_image',
            'account_name', 'category_name', 'transfer_to_account_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def validate(self, data):
        # Pobierz użytkownika z kontekstu (ustawiany w view)
        user = self.context.get('request').user if self.context.get('request') else None
        
        # Walidacja konta - musi należeć do użytkownika
        account = data.get('account')
        if account and user:
            if account.user != user:
                raise serializers.ValidationError({
                    'account': 'Konto nie należy do Ciebie.'
                })
        
        # Walidacja kategorii - musi należeć do użytkownika (jeśli podano)
        category = data.get('category')
        if category and user:
            if category.user != user:
                raise serializers.ValidationError({
                    'category': 'Kategoria nie należy do Ciebie.'
                })
        
        # Walidacja transferu
        if data.get('transaction_type') == 'transfer':
            transfer_to_account = data.get('transfer_to_account')
            if not transfer_to_account:
                raise serializers.ValidationError({
                    'transfer_to_account': 'Transfer wymaga określenia konta docelowego.'
                })
            if account == transfer_to_account:
                raise serializers.ValidationError({
                    'transfer_to_account': 'Nie można transferować na to samo konto.'
                })
            # Sprawdź czy konto docelowe należy do użytkownika
            if transfer_to_account and user:
                if transfer_to_account.user != user:
                    raise serializers.ValidationError({
                        'transfer_to_account': 'Konto docelowe nie należy do Ciebie.'
                    })
        
        # Walidacja kwoty
        if data.get('amount') and data['amount'] <= 0:
            raise serializers.ValidationError({
                'amount': 'Kwota musi być większa od 0.'
            })
        
        return data
    
    def to_representation(self, instance):
        """Zwraca pełne obiekty przy odczycie zamiast ID"""
        representation = super().to_representation(instance)
        # Zamień ID na pełne obiekty przy odczycie (jeśli istnieją)
        if 'account_detail' in representation:
            representation['account'] = representation['account_detail'] if representation['account_detail'] else None
        if 'category_detail' in representation:
            representation['category'] = representation['category_detail'] if representation['category_detail'] else None
        if 'transfer_to_account_detail' in representation:
            representation['transfer_to_account'] = representation['transfer_to_account_detail'] if representation['transfer_to_account_detail'] else None
        # Usuń pomocnicze pola _detail (nie są potrzebne w odpowiedzi)
        representation.pop('account_detail', None)
        representation.pop('category_detail', None)
        representation.pop('transfer_to_account_detail', None)
        return representation


class SavingsGoalSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = SavingsGoal
        fields = '__all__'
        read_only_fields = ('id', 'user', 'created_at', 'updated_at', 'progress_percentage', 'days_remaining')
    
    def validate_target_date(self, value):
        from django.utils import timezone
        if value <= timezone.now().date():
            raise serializers.ValidationError("Data docelowa musi być w przyszłości.")
        return value


class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    spent_amount = serializers.ReadOnlyField()
    remaining_amount = serializers.ReadOnlyField()
    usage_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Budget
        fields = '__all__'
        read_only_fields = ('id', 'user', 'created_at', 'updated_at', 'spent_amount', 'remaining_amount', 'usage_percentage')
    
    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("Data rozpoczęcia musi być wcześniejsza niż data zakończenia.")
        return data


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class PaymentIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentIntegration
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class PaymentTransactionSerializer(serializers.ModelSerializer):
    savings_goal_name = serializers.CharField(source='savings_goal.name', read_only=True)
    
    class Meta:
        model = PaymentTransaction
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


# Serializers dla raportów i analityki
class TransactionSummarySerializer(serializers.Serializer):
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    transaction_count = serializers.IntegerField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()


class CategoryExpenseSerializer(serializers.Serializer):
    category_name = serializers.CharField()
    category_id = serializers.UUIDField()
    category_color = serializers.CharField(required=False, allow_null=True)
    category_icon = serializers.CharField(required=False, allow_null=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    transaction_count = serializers.IntegerField()
    percentage = serializers.FloatField()


class MonthlyReportSerializer(serializers.Serializer):
    month = serializers.CharField()
    year = serializers.IntegerField()
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    category_breakdown = CategoryExpenseSerializer(many=True)
