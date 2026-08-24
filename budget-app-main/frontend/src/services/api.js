import axios from 'axios';

// Konfiguracja API
// Automatycznie wykrywa czy jesteśmy w produkcji czy development
const getApiUrl = () => {
  // Sprawdź najpierw czy jesteśmy na produkcji (Firebase)
  const isProduction = window.location.hostname === 'budget-app-adbaf.web.app' || 
                        window.location.hostname === 'budget-app-adbaf.firebaseapp.com';
  
  // Jeśli jesteśmy na produkcji, zawsze używaj URL produkcyjny
  if (isProduction) {
    return 'https://budget-app-5xsv.onrender.com/api';
  }
  
  // Jeśli jest ustawiony REACT_APP_API_URL i nie wskazuje na localhost, użyj go
  if (process.env.REACT_APP_API_URL && 
      !process.env.REACT_APP_API_URL.includes('localhost') && 
      !process.env.REACT_APP_API_URL.includes('127.0.0.1')) {
    return process.env.REACT_APP_API_URL;
  }
  
  // Dla developmentu lokalnego
  return 'http://localhost:8000/api';
};

const API_BASE_URL = getApiUrl();

// Debug: wyświetl URL API w konsoli
console.log('🔗 API URL:', API_BASE_URL);
console.log('🔗 REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
console.log('🔗 NODE_ENV:', process.env.NODE_ENV);

// Utworzenie instancji axios
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor do dodawania tokenu JWT
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor do obsługi błędów i odświeżania tokenu
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Jeśli błąd 401 (Unauthorized) - spróbuj odświeżyć token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          // Ponów oryginalne żądanie z nowym tokenem
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        } else {
          // Brak refresh tokena - wyczyść wszystko i przekieruj do logowania
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
        }
      } catch (refreshError) {
        // Token odświeżania wygasł lub jest nieprawidłowy - wyczyść wszystko
        console.error('Token refresh failed:', refreshError);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }

    // Loguj inne błędy dla debugowania
    if (error.response) {
      const statusCode = error.response.status;
      const errorData = error.response.data;
      
      console.error('API Error:', {
        status: statusCode,
        statusText: error.response.statusText,
        data: errorData,
        url: error.config?.url,
        method: error.config?.method,
      });
      
      // Dla błędów 500, dodaj więcej informacji diagnostycznych
      if (statusCode === 500) {
        console.error('🔴 Błąd 500 - Internal Server Error');
        console.error('📋 Szczegóły błędu:', errorData);
        console.error('🌐 URL:', error.config?.url);
        console.error('📝 Metoda:', error.config?.method);
        console.error('💡 Sprawdź logi backendu dla więcej informacji');
        
        // Jeśli backend zwrócił szczegóły błędu, dodaj je do obiektu błędu
        if (errorData && typeof errorData === 'object') {
          error.serverErrorDetails = errorData;
        }
      }
    } else if (error.request) {
      console.error('Network Error:', {
        message: error.message,
        url: error.config?.url,
        baseURL: API_BASE_URL,
      });
    }

    return Promise.reject(error);
  }
);

// API endpoints
export const authAPI = {
  // Rejestracja
  register: (userData) => api.post('/auth/register/', userData),
  
  // Logowanie
  login: (credentials) => api.post('/auth/token/', credentials),
  
  // Odświeżanie tokenu
  refreshToken: (refreshToken) => api.post('/auth/token/refresh/', { refresh: refreshToken }),
  
  // Weryfikacja emaila
  verifyEmail: (token) => api.post('/auth/verify-email/', { token }),
  resendVerificationEmail: (emailOrUsername) => api.post('/auth/resend-verification/', emailOrUsername),
  
  // Logowanie przez Google
  googleLogin: (token) => api.post('/auth/google-login/', { token }),
  
  // Profil użytkownika
  getProfile: () => api.get('/auth/me/'),
  updateProfile: (data) => api.put('/auth/profile/', data),
  changePassword: (data) => api.post('/auth/change-password/', data),
  
  // Reset hasła
  forgotPassword: (data) => api.post('/auth/forgot-password/', data),
  resetPassword: (data) => api.post('/auth/reset-password/', data),
};

export const dashboardAPI = {
  getDashboard: () => api.get('/dashboard/'),
};

export const categoriesAPI = {
  getCategories: (params = {}) => api.get('/categories/', { params }),
  getCategory: (id) => api.get(`/categories/${id}/`),
  createCategory: (data) => api.post('/categories/', data),
  updateCategory: (id, data) => api.put(`/categories/${id}/`, data),
  deleteCategory: (id) => api.delete(`/categories/${id}/`),
};

export const accountsAPI = {
  getAccounts: (params = {}) => api.get('/accounts/', { params }),
  getAccount: (id) => api.get(`/accounts/${id}/`),
  createAccount: (data) => api.post('/accounts/', data),
  updateAccount: (id, data) => api.put(`/accounts/${id}/`, data),
  deleteAccount: (id) => api.delete(`/accounts/${id}/`),
};

export const transactionsAPI = {
  getTransactions: (params = {}) => api.get('/transactions/', { params }),
  getTransaction: (id) => api.get(`/transactions/${id}/`),
  createTransaction: (data) => api.post('/transactions/', data),
  updateTransaction: (id, data) => api.put(`/transactions/${id}/`, data),
  deleteTransaction: (id) => api.delete(`/transactions/${id}/`),
};

export const savingsGoalsAPI = {
  getSavingsGoals: (params = {}) => api.get('/savings-goals/', { params }),
  getSavingsGoal: (id) => api.get(`/savings-goals/${id}/`),
  createSavingsGoal: (data) => api.post('/savings-goals/', data),
  updateSavingsGoal: (id, data) => api.put(`/savings-goals/${id}/`, data),
  deleteSavingsGoal: (id) => api.delete(`/savings-goals/${id}/`),
};

export const budgetsAPI = {
  getBudgets: (params = {}) => api.get('/budgets/', { params }),
  getBudget: (id) => api.get(`/budgets/${id}/`),
  createBudget: (data) => api.post('/budgets/', data),
  updateBudget: (id, data) => api.put(`/budgets/${id}/`, data),
  deleteBudget: (id) => api.delete(`/budgets/${id}/`),
};

export const notificationsAPI = {
  getNotifications: (params = {}) => api.get('/notifications/', { params }),
  markAsRead: (id) => api.put(`/notifications/${id}/read/`),
};

export const analyticsAPI = {
  getTransactionSummary: (params = {}) => api.get('/analytics/summary/', { params }),
  getCategoryExpenses: (params = {}) => api.get('/analytics/category-expenses/', { params }),
  getMonthlyReport: (year, month) => api.get(`/analytics/monthly-report/${year}/${month}/`),
};

export const paymentsAPI = {
  getStripeConfig: () => api.get('/payments/stripe/config/'),
  createPaymentForSavingsGoal: (savingsGoalId, amount) => 
    api.post(`/payments/savings-goals/${savingsGoalId}/create/`, { amount }),
  createCheckoutSession: (savingsGoalId, amount) =>
    api.post(`/payments/savings-goals/${savingsGoalId}/checkout/`, { amount }),
  confirmCheckoutSession: (sessionId) =>
    api.post('/payments/stripe/confirm/', { session_id: sessionId }),
  getPaymentStatistics: (savingsGoalId) =>
    api.get(`/payments/savings-goals/${savingsGoalId}/statistics/`),
  getPaymentTransactions: () => api.get('/payments/transactions/'),
  getPaymentTransaction: (id) => api.get(`/payments/transactions/${id}/`),
};

export const alertsAPI = {
  runAlerts: (type = 'all') => api.post('/alerts/run/', { type }),
  getAlertStatus: () => api.get('/alerts/status/'),
};

export default api;


