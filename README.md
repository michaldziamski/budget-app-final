[README-budget-app-final-EN.md](https://github.com/user-attachments/files/31486557/README-budget-app-final-EN.md)
# Budget App

A full-stack personal budgeting application — a Django REST API paired with a React frontend. It lets users track transactions, accounts, savings goals, and budgets, and includes notifications and Stripe payment integration.

## About the project

Budget App is a full-stack engineering project where the backend (Django + DRF) handles business logic and data, while the frontend (React) provides the user-facing dashboard. It covers the full user lifecycle — from registration with email verification, through Google login, to day-to-day finance management and payments.

## Features

**Account \& authentication**

* Registration with email verification
* Google OAuth login
* JWT (access + refresh tokens)
* Password reset and change, profile editing

**Finance management**

* Accounts (`Account`) — multiple financial accounts per user
* Transactions (`Transaction`) — income and expenses linked to categories and accounts
* Categories (`Category`) — custom expense categorization
* Budgets (`Budget`) — spending limits with alerts on overspend
* Savings goals (`SavingsGoal`) — with the ability to contribute via Stripe

**Analytics \& reports**

* Dashboard with a financial summary
* Transaction and category-expense summaries
* Monthly reports (`monthly-report/<year>/<month>`)

**Notifications**

* Automatic budget alerts (limit exceeded) sent by email
* In-app notification system with read/unread state

**Payments**

* Stripe integration: checkout sessions, webhooks, payment transaction history
* Contributions to savings goals processed as real payments

## Tech stack

**Backend**

* Django 5 + Django REST Framework
* SimpleJWT — token-based authorization
* PostgreSQL (in production) via `dj-database-url` and `psycopg`
* Stripe SDK — payments
* SendGrid — email delivery (account verification, alerts, password reset)
* Google Auth — Google login
* Gunicorn — production server

**Frontend**

* React 19 + React Router
* React Hook Form + Yup — forms and validation
* Axios — API communication
* Tailwind CSS — styling
* Recharts — dashboard charts
* Stripe.js / React Stripe.js — client-side payments
* React Hot Toast — UI notifications

**Deployment**

* `render.yaml` — Render deployment configuration
* Firebase Hosting — frontend hosting configuration (`firebase.json`)

## Project structure

```
budget-app-main/
├── backend/
│   ├── core/            # Django project settings, main routing
│   ├── budgets/         # main app: models, views, serializers
│   │   ├── models.py           # Category, Account, Transaction, SavingsGoal,
│   │   │                        # Budget, Notification, PaymentIntegration...
│   │   ├── views.py            # API endpoint logic
│   │   ├── serializers.py
│   │   ├── alert\_service.py    # budget checks and alert delivery
│   │   ├── email\_service.py    # email delivery via SendGrid
│   │   ├── stripe\_service.py   # payment integration
│   │   ├── google\_auth\_service.py
│   │   └── test\_\*.py           # model, view, serializer, and integration tests
│   ├── manage.py
│   └── requirements.txt
└── frontend/
    └── src/
        ├── pages/        # Dashboard, Transactions, Budgets, SavingsGoals,
        │                  # Accounts, Categories, Notifications, Settings,
        │                  # Login/Register/ForgotPassword/ResetPassword/VerifyEmail
        ├── components/    # StripePaymentModal, Layout, ProtectedRoute
        ├── contexts/      # AuthContext, ThemeContext
        └── services/      # API client (Axios)
```

## Selected API endpoints

Main routes are defined under `budgets` and wired up in `core/urls.py`:

|Category|Example endpoints|
|-|-|
|Auth|`auth/register/`, `auth/token/`, `auth/google-login/`, `auth/verify-email/`|
|Accounts \& transactions|`accounts/`, `transactions/`, `categories/`|
|Budgets \& goals|`budgets/`, `savings-goals/`|
|Analytics|`analytics/summary/`, `analytics/category-expenses/`, `analytics/monthly-report/<year>/<month>/`, `dashboard/`|
|Notifications|`notifications/`, `notifications/<id>/read/`|
|Payments|`payments/savings-goals/<id>/checkout/`, `payments/stripe/webhook/`, `payments/transactions/`|
|Alerts|`alerts/run/`, `alerts/status/`|

## Running locally

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt

# set up environment variables (e.g. in a .env file):
# DATABASE\_URL, STRIPE\_SECRET\_KEY, STRIPE\_PUBLISHABLE\_KEY,
# STRIPE\_WEBHOOK\_SECRET, SENDGRID\_API\_KEY,
# GOOGLE\_OAUTH2\_CLIENT\_ID, GOOGLE\_OAUTH2\_CLIENT\_SECRET

python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm start
```

The frontend runs on `http://localhost:3000` by default and talks to the backend API.

### Backend tests

```bash
cd backend
python manage.py test
```

The project includes tests for models, views, and serializers, plus integration tests (e.g. for email verification and Google login).

## Environment variables

The app relies on a few external services that need to be configured via environment variables:

* **Stripe** — `STRIPE\_SECRET\_KEY`, `STRIPE\_PUBLISHABLE\_KEY`, `STRIPE\_WEBHOOK\_SECRET`
* **SendGrid** — `SENDGRID\_API\_KEY` (verification and alert emails)
* **Google OAuth** — `GOOGLE\_OAUTH2\_CLIENT\_ID`, `GOOGLE\_OAUTH2\_CLIENT\_SECRET`
* **Database** — `DATABASE\_URL` (PostgreSQL in production)

## Possible next steps

* PDF/CSV report export
* Shared household budgets across multiple users
* A mobile app built on the same API
* Broader frontend test coverage (currently concentrated on the backend)

\---

An engineering project combining Django REST Framework with a React frontend.

