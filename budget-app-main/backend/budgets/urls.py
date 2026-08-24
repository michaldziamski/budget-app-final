from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    test_api, RegisterView, me, profile, change_password, forgot_password, reset_password,
    verify_email, resend_verification_email, google_login, CustomTokenObtainPairView,
    CategoryListCreateView, CategoryDetailView,
    AccountListCreateView, AccountDetailView,
    TransactionListCreateView, TransactionDetailView,
    SavingsGoalListCreateView, SavingsGoalDetailView,
    BudgetListCreateView, BudgetDetailView,
    NotificationListView, mark_notification_read,
    transaction_summary, category_expenses, monthly_report, dashboard,
    create_payment_for_savings_goal, create_checkout_session, payment_statistics,
    payment_transactions, payment_transaction_detail,
    stripe_webhook, stripe_config, stripe_test_connection, run_alerts, alert_status, stripe_checkout_confirm
)

# Router dla ViewSets (jeśli będziemy ich używać)
router = DefaultRouter()

urlpatterns = [
    # Test endpoint
    path('test/', test_api, name='test_api'),
    
    # Authentication
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/verify-email/', verify_email, name='verify-email'),
    path('auth/resend-verification/', resend_verification_email, name='resend-verification'),
    path('auth/google-login/', google_login, name='google-login'),
    path('auth/me/', me, name='me'),
    path('auth/profile/', profile, name='profile'),
    path('auth/change-password/', change_password, name='change-password'),
    path('auth/forgot-password/', forgot_password, name='forgot-password'),
    path('auth/reset-password/', reset_password, name='reset-password'),
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Categories
    path('categories/', CategoryListCreateView.as_view(), name='category-list'),
    path('categories/<uuid:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    
    # Accounts
    path('accounts/', AccountListCreateView.as_view(), name='account-list'),
    path('accounts/<uuid:pk>/', AccountDetailView.as_view(), name='account-detail'),
    
    # Transactions
    path('transactions/', TransactionListCreateView.as_view(), name='transaction-list'),
    path('transactions/<uuid:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),
    
    # Savings Goals
    path('savings-goals/', SavingsGoalListCreateView.as_view(), name='savings-goal-list'),
    path('savings-goals/<uuid:pk>/', SavingsGoalDetailView.as_view(), name='savings-goal-detail'),
    
    # Budgets
    path('budgets/', BudgetListCreateView.as_view(), name='budget-list'),
    path('budgets/<uuid:pk>/', BudgetDetailView.as_view(), name='budget-detail'),
    
    # Notifications
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<uuid:notification_id>/read/', mark_notification_read, name='notification-read'),
    
    # Analytics & Reports
    path('analytics/summary/', transaction_summary, name='transaction-summary'),
    path('analytics/category-expenses/', category_expenses, name='category-expenses'),
    path('analytics/monthly-report/<int:year>/<int:month>/', monthly_report, name='monthly-report'),
    
    # Dashboard
    path('dashboard/', dashboard, name='dashboard'),
    
    # Payments
    path('payments/savings-goals/<uuid:savings_goal_id>/create/', create_payment_for_savings_goal, name='create-payment-savings-goal'),
    path('payments/savings-goals/<uuid:savings_goal_id>/checkout/', create_checkout_session, name='create-checkout-session'),
    path('payments/savings-goals/<uuid:savings_goal_id>/statistics/', payment_statistics, name='payment-statistics'),
    path('payments/transactions/', payment_transactions, name='payment-transactions'),
    path('payments/transactions/<uuid:transaction_id>/', payment_transaction_detail, name='payment-transaction-detail'),
    path('payments/stripe/config/', stripe_config, name='stripe-config'),
    path('payments/stripe/test/', stripe_test_connection, name='stripe-test'),
    path('payments/stripe/webhook/', stripe_webhook, name='stripe-webhook'),
    path('payments/stripe/confirm/', stripe_checkout_confirm, name='stripe-checkout-confirm'),
    
    # Alerts & Notifications
    path('alerts/run/', run_alerts, name='run-alerts'),
    path('alerts/status/', alert_status, name='alert-status'),
    
    # Router URLs (dla przyszłych ViewSets)
    path('', include(router.urls)),
]
