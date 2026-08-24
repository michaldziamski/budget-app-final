from django.contrib import admin
from .models import (
    Category, Account, Transaction, SavingsGoal, 
    Budget, Notification, PaymentIntegration, PaymentTransaction,
    EmailVerificationToken, PasswordResetToken
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'category_type', 'is_active', 'created_at')
    list_filter = ('category_type', 'is_active', 'created_at')
    search_fields = ('name', 'user__username')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'account_type', 'balance', 'currency', 'is_active')
    list_filter = ('account_type', 'currency', 'is_active', 'created_at')
    search_fields = ('name', 'user__username')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('description', 'user', 'account', 'category', 'amount', 'transaction_type', 'date')
    list_filter = ('transaction_type', 'date', 'created_at')
    search_fields = ('description', 'user__username', 'account__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'date'


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'target_amount', 'current_amount', 'target_date', 'is_completed')
    list_filter = ('is_completed', 'is_active', 'target_date')
    search_fields = ('name', 'user__username')
    readonly_fields = ('id', 'created_at', 'updated_at', 'progress_percentage', 'days_remaining')


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'category', 'amount', 'period', 'start_date', 'end_date', 'is_active')
    list_filter = ('period', 'is_active', 'start_date')
    search_fields = ('name', 'user__username', 'category__name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'spent_amount', 'remaining_amount', 'usage_percentage')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'is_email_sent', 'created_at')
    list_filter = ('notification_type', 'is_read', 'is_email_sent', 'created_at')
    search_fields = ('title', 'user__username')
    readonly_fields = ('id', 'created_at')


@admin.register(PaymentIntegration)
class PaymentIntegrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'is_active', 'created_at')
    list_filter = ('provider', 'is_active', 'created_at')
    search_fields = ('user__username', 'provider_customer_id')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'currency', 'status', 'savings_goal', 'created_at')
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('user__username', 'savings_goal__name')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'is_used', 'is_expired', 'created_at', 'expires_at')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__username', 'user__email', 'token')
    readonly_fields = ('id', 'token', 'created_at', 'expires_at', 'is_expired')
    
    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Wygasł'


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'is_used', 'is_expired', 'is_valid', 'created_at', 'expires_at')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__username', 'user__email', 'token')
    readonly_fields = ('id', 'token', 'created_at', 'expires_at', 'is_expired', 'is_valid')
    
    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Wygasł'
    
    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Ważny'
