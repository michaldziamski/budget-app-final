from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import timedelta


class Category(models.Model):
    """Kategorie wydatków i przychodów"""
    CATEGORY_TYPES = [
        ('expense', 'Wydatek'),
        ('income', 'Przychód'),
        ('transfer', 'Transfer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    color = models.CharField(max_length=7, default='#3498db')  # Hex color
    icon = models.CharField(max_length=50, blank=True, null=True)  # FontAwesome icon class
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"
        unique_together = ['user', 'name', 'category_type']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class Account(models.Model):
    """Konta bankowe, portfele, gotówka"""
    ACCOUNT_TYPES = [
        ('bank', 'Konto bankowe'),
        ('cash', 'Gotówka'),
        ('credit_card', 'Karta kredytowa'),
        ('savings', 'Konto oszczędnościowe'),
        ('investment', 'Inwestycje'),
        ('other', 'Inne'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='PLN')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Konto"
        verbose_name_plural = "Konta"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()}) - {self.balance} {self.currency}"


class Transaction(models.Model):
    """Transakcje finansowe"""
    TRANSACTION_TYPES = [
        ('expense', 'Wydatek'),
        ('income', 'Przychód'),
        ('transfer', 'Transfer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    # Podstawowe informacje
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.TextField()
    date = models.DateTimeField()
    
    # Transfer między kontami
    transfer_to_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_received')
    
    # Dodatkowe informacje
    tags = models.CharField(max_length=200, blank=True, null=True)  # CSV tags
    location = models.CharField(max_length=200, blank=True, null=True)
    receipt_image = models.ImageField(upload_to='receipts/', blank=True, null=True)
    
    # Metadane
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Transakcja"
        verbose_name_plural = "Transakcje"
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['account', 'date']),
            models.Index(fields=['category', 'date']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()}: {self.amount} - {self.description[:50]}"
    
    def save(self, *args, **kwargs):
        # Automatyczne aktualizowanie salda konta
        super().save(*args, **kwargs)
        self.update_account_balance()
    
    def update_account_balance(self):
        """Aktualizuje saldo konta na podstawie transakcji"""
        if self.transaction_type == 'income':
            self.account.balance += self.amount
        elif self.transaction_type == 'expense':
            self.account.balance -= self.amount
        elif self.transaction_type == 'transfer' and self.transfer_to_account:
            self.account.balance -= self.amount
            self.transfer_to_account.balance += self.amount
            self.transfer_to_account.save()
        
        self.account.save()


class SavingsGoal(models.Model):
    """Cele oszczędnościowe"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='savings_goals')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    target_date = models.DateField()
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='savings_goals')
    is_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cel oszczędnościowy"
        verbose_name_plural = "Cele oszczędnościowe"
        ordering = ['target_date']
    
    def __str__(self):
        return f"{self.name} - {self.current_amount}/{self.target_amount}"
    
    @property
    def progress_percentage(self):
        """Procent ukończenia celu"""
        if self.target_amount > 0:
            return (self.current_amount / self.target_amount) * 100
        return 0
    
    @property
    def days_remaining(self):
        """Liczba dni do osiągnięcia celu"""
        from django.utils import timezone
        today = timezone.now().date()
        return (self.target_date - today).days


class Budget(models.Model):
    """Budżety miesięczne/roczne"""
    BUDGET_PERIODS = [
        ('monthly', 'Miesięczny'),
        ('yearly', 'Roczny'),
        ('weekly', 'Tygodniowy'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    period = models.CharField(max_length=10, choices=BUDGET_PERIODS)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Budżet"
        verbose_name_plural = "Budżety"
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} - {self.amount} ({self.get_period_display()})"
    
    @property
    def spent_amount(self):
        """Kwota wydana w danym okresie"""
        from django.db.models import Sum
        spent = self.category.transactions.filter(
            transaction_type='expense',
            date__gte=self.start_date,
            date__lte=self.end_date
        ).aggregate(total=Sum('amount'))['total']
        return spent or Decimal('0.00')
    
    @property
    def remaining_amount(self):
        """Pozostała kwota w budżecie"""
        return self.amount - self.spent_amount
    
    @property
    def usage_percentage(self):
        """Procent wykorzystania budżetu"""
        if self.amount > 0:
            return (self.spent_amount / self.amount) * 100
        return 0


class Notification(models.Model):
    """Powiadomienia systemowe"""
    NOTIFICATION_TYPES = [
        ('budget_alert', 'Alert budżetowy'),
        ('payment_reminder', 'Przypomnienie o płatności'),
        ('goal_reminder', 'Przypomnienie o celu'),
        ('system', 'Systemowe'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Powiadomienie"
        verbose_name_plural = "Powiadomienia"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"


class PaymentIntegration(models.Model):
    """Integracja z systemami płatności (Stripe)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_integrations')
    provider = models.CharField(max_length=50, default='stripe')  # stripe, paypal, etc.
    provider_customer_id = models.CharField(max_length=100)
    provider_payment_method_id = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Integracja płatności"
        verbose_name_plural = "Integracje płatności"
        unique_together = ['user', 'provider']
    
    def __str__(self):
        return f"{self.user.username} - {self.provider}"


class PaymentTransaction(models.Model):
    """Transakcje płatności online"""
    PAYMENT_STATUS = [
        ('pending', 'Oczekująca'),
        ('completed', 'Zakończona'),
        ('failed', 'Nieudana'),
        ('cancelled', 'Anulowana'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_transactions')
    payment_integration = models.ForeignKey(PaymentIntegration, on_delete=models.CASCADE, related_name='payment_transactions')
    savings_goal = models.ForeignKey(SavingsGoal, on_delete=models.CASCADE, related_name='payment_transactions', null=True, blank=True)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='PLN')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Provider specific data
    provider_payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    provider_charge_id = models.CharField(max_length=100, blank=True, null=True)
    
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Transakcja płatności"
        verbose_name_plural = "Transakcje płatności"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Płatność {self.amount} - {self.get_status_display()}"


class EmailVerificationToken(models.Model):
    """Tokeny weryfikacyjne dla adresów email"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification_token')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Token weryfikacyjny email"
        verbose_name_plural = "Tokeny weryfikacyjne email"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Token dla {self.user.email} - {self.token[:8]}..."
    
    def is_expired(self):
        """Sprawdza czy token wygasł"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Sprawdza czy token jest ważny (nie użyty i nie wygasły)"""
        return not self.is_used and not self.is_expired()
    
    @staticmethod
    def generate_token():
        """Generuje unikalny token weryfikacyjny"""
        return str(uuid.uuid4())
    
    @staticmethod
    def create_for_user(user):
        """Tworzy token weryfikacyjny dla użytkownika"""
        # Usuń stary token jeśli istnieje
        EmailVerificationToken.objects.filter(user=user).delete()
        
        # Utwórz nowy token
        token = EmailVerificationToken.generate_token()
        expires_at = timezone.now() + timedelta(hours=24)  # Token ważny 24 godziny
        
        return EmailVerificationToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )


class PasswordResetToken(models.Model):
    """Tokeny do resetu hasła"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Token resetu hasła"
        verbose_name_plural = "Tokeny resetu hasła"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_used']),
        ]
    
    def __str__(self):
        return f"Token resetu dla {self.user.email} - {self.token[:8]}..."
    
    def is_expired(self):
        """Sprawdza czy token wygasł"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Sprawdza czy token jest ważny (nie użyty i nie wygasły)"""
        return not self.is_used and not self.is_expired()
    
    @staticmethod
    def generate_token():
        """Generuje unikalny token resetu hasła"""
        return str(uuid.uuid4())
    
    @staticmethod
    def create_for_user(user):
        """Tworzy token resetu hasła dla użytkownika"""
        # Usuń stare nieużywane tokeny dla tego użytkownika
        PasswordResetToken.objects.filter(user=user, is_used=False).delete()
        
        # Utwórz nowy token
        token = PasswordResetToken.generate_token()
        expires_at = timezone.now() + timedelta(hours=1)  # Token ważny 1 godzinę
        
        return PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
