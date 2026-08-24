import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { authAPI } from '../services/api';
import toast from 'react-hot-toast';

// Stan początkowy
const initialState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// Typy akcji
const AUTH_ACTIONS = {
  LOGIN_START: 'LOGIN_START',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAILURE: 'LOGIN_FAILURE',
  LOGOUT: 'LOGOUT',
  REGISTER_START: 'REGISTER_START',
  REGISTER_SUCCESS: 'REGISTER_SUCCESS',
  REGISTER_FAILURE: 'REGISTER_FAILURE',
  LOAD_USER_START: 'LOAD_USER_START',
  LOAD_USER_SUCCESS: 'LOAD_USER_SUCCESS',
  LOAD_USER_FAILURE: 'LOAD_USER_FAILURE',
  CLEAR_ERROR: 'CLEAR_ERROR',
};

// Reducer
const authReducer = (state, action) => {
  switch (action.type) {
    case AUTH_ACTIONS.LOGIN_START:
    case AUTH_ACTIONS.REGISTER_START:
    case AUTH_ACTIONS.LOAD_USER_START:
      return {
        ...state,
        isLoading: true,
        error: null,
      };

    case AUTH_ACTIONS.LOGIN_SUCCESS:
    case AUTH_ACTIONS.REGISTER_SUCCESS:
      return {
        ...state,
        user: action.payload.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };

    case AUTH_ACTIONS.LOAD_USER_SUCCESS:
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };

    case AUTH_ACTIONS.LOGIN_FAILURE:
    case AUTH_ACTIONS.REGISTER_FAILURE:
    case AUTH_ACTIONS.LOAD_USER_FAILURE:
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      };

    case AUTH_ACTIONS.LOGOUT:
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };

    case AUTH_ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null,
      };

    default:
      return state;
  }
};

// Kontekst
const AuthContext = createContext();

// Provider
export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Sprawdź czy użytkownik jest zalogowany przy starcie aplikacji
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      loadUser();
    } else {
      // Wyczyść stan jeśli nie ma tokena
      dispatch({ type: AUTH_ACTIONS.LOAD_USER_FAILURE });
    }
  }, []);

  // Załaduj dane użytkownika
  const loadUser = async () => {
    try {
      dispatch({ type: AUTH_ACTIONS.LOAD_USER_START });
      const response = await authAPI.getProfile();
      dispatch({
        type: AUTH_ACTIONS.LOAD_USER_SUCCESS,
        payload: response.data,
      });
    } catch (error) {
      console.error('Error loading user:', error);
      // Jeśli błąd 401 - token jest nieprawidłowy, wyczyść go
      if (error.response?.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
      dispatch({
        type: AUTH_ACTIONS.LOAD_USER_FAILURE,
        payload: error.response?.data?.detail || 'Błąd ładowania użytkownika',
      });
    }
  };

  // Logowanie przez Google
  const loginWithGoogle = async (googleToken) => {
    try {
      dispatch({ type: AUTH_ACTIONS.LOGIN_START });
      
      // Wyczyść stare tokeny przed logowaniem
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      
      const response = await authAPI.googleLogin(googleToken);
      
      const { access, refresh, user: userData } = response.data;
      
      // Zapisz tokeny w localStorage
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      
      // Ustaw dane użytkownika
      dispatch({
        type: AUTH_ACTIONS.LOGIN_SUCCESS,
        payload: { user: userData }
      });
      
      toast.success('Pomyślnie zalogowano przez Google!');
    } catch (error) {
      console.error('Google login error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
      });
      
      // Wyczyść tokeny w przypadku błędu
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      
      let errorMessage = 'Błąd logowania przez Google';
      if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      dispatch({
        type: AUTH_ACTIONS.LOGIN_FAILURE,
        payload: errorMessage,
      });
      toast.error(errorMessage);
      throw error;
    }
  };

  // Logowanie
  const login = async (credentials) => {
    try {
      dispatch({ type: AUTH_ACTIONS.LOGIN_START });
      
      // Wyczyść stare tokeny przed logowaniem
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      
      const response = await authAPI.login(credentials);
      
      const { access, refresh } = response.data;
      
      // Zapisz tokeny w localStorage
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      
      // Załaduj dane użytkownika
      await loadUser();
      
      toast.success('Pomyślnie zalogowano!');
    } catch (error) {
      console.error('Login error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        url: error.config?.url,
      });
      
      // Wyczyść tokeny w przypadku błędu
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      
      let errorMessage = 'Błąd logowania';
      
      // Obsługa błędów 500 - pokaż szczegóły jeśli są dostępne
      if (error.response?.status === 500) {
        if (error.response.data?.error) {
          errorMessage = `Błąd serwera: ${error.response.data.error}`;
        } else if (error.response.data?.detail) {
          errorMessage = `Błąd serwera: ${error.response.data.detail}`;
        } else if (typeof error.response.data === 'string') {
          errorMessage = `Błąd serwera: ${error.response.data}`;
        } else {
          errorMessage = 'Błąd serwera (500). Sprawdź konsolę przeglądarki (F12) dla szczegółów lub skontaktuj się z administratorem.';
        }
      } else if (error.response?.data) {
        // Sprawdź różne formaty błędów
        if (error.response.data.error) {
          // Błąd z CustomTokenObtainPairSerializer (obiekt z 'error')
          if (typeof error.response.data.error === 'string') {
            errorMessage = error.response.data.error;
          } else if (error.response.data.error.error) {
            errorMessage = error.response.data.error.error;
          } else {
            errorMessage = JSON.stringify(error.response.data.error);
          }
        } else if (error.response.data.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response.data.non_field_errors) {
          errorMessage = Array.isArray(error.response.data.non_field_errors)
            ? error.response.data.non_field_errors.join(', ')
            : error.response.data.non_field_errors;
        } else if (typeof error.response.data === 'string') {
          errorMessage = error.response.data;
        }
      } else if (error.message) {
        if (error.message.includes('Network Error') || error.code === 'ERR_NETWORK') {
          errorMessage = 'Nie można połączyć się z serwerem. Sprawdź połączenie internetowe.';
        } else {
          errorMessage = error.message;
        }
      }
      
      dispatch({
        type: AUTH_ACTIONS.LOGIN_FAILURE,
        payload: errorMessage,
      });
      toast.error(errorMessage);
      throw error;
    }
  };

  // Rejestracja
  const register = async (userData) => {
    try {
      dispatch({ type: AUTH_ACTIONS.REGISTER_START });
      await authAPI.register(userData);
      
      // Po rejestracji automatycznie zaloguj użytkownika
      await login({
        username: userData.username,
        password: userData.password,
      });
      
      toast.success('Konto zostało utworzone!');
    } catch (error) {
      console.error('Registration error details:', error);
      console.error('Error response:', error.response);
      console.error('Error response data:', error.response?.data);
      
      // Obsługa różnych formatów błędów z backendu
      let errorMessage = 'Błąd rejestracji';
      
      // Obsługa błędów 500 - pokaż szczegóły jeśli są dostępne
      if (error.response?.status === 500) {
        if (error.response.data?.error) {
          errorMessage = `Błąd serwera: ${error.response.data.error}`;
        } else if (error.response.data?.detail) {
          errorMessage = `Błąd serwera: ${error.response.data.detail}`;
        } else if (typeof error.response.data === 'string') {
          errorMessage = `Błąd serwera: ${error.response.data}`;
        } else {
          errorMessage = 'Błąd serwera (500). Sprawdź konsolę przeglądarki (F12) dla szczegółów lub skontaktuj się z administratorem.';
        }
      } else if (error.response?.data) {
        // Jeśli backend zwrócił szczegóły błędu
        if (error.response.data.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response.data.non_field_errors) {
          // Błędy ogólne
          errorMessage = Array.isArray(error.response.data.non_field_errors)
            ? error.response.data.non_field_errors.join(', ')
            : error.response.data.non_field_errors;
        } else if (error.response.data.username) {
          // Błąd z polem username
          errorMessage = Array.isArray(error.response.data.username)
            ? `Nazwa użytkownika: ${error.response.data.username.join(', ')}`
            : `Nazwa użytkownika: ${error.response.data.username}`;
        } else if (error.response.data.email) {
          // Błąd z polem email
          errorMessage = Array.isArray(error.response.data.email)
            ? `Email: ${error.response.data.email.join(', ')}`
            : `Email: ${error.response.data.email}`;
        } else if (error.response.data.password) {
          // Błąd z polem password
          errorMessage = Array.isArray(error.response.data.password)
            ? `Hasło: ${error.response.data.password.join(', ')}`
            : `Hasło: ${error.response.data.password}`;
        } else if (typeof error.response.data === 'object') {
          // Inne błędy walidacji - pokaż pierwszy błąd
          const firstErrorKey = Object.keys(error.response.data)[0];
          const firstError = error.response.data[firstErrorKey];
          errorMessage = Array.isArray(firstError)
            ? `${firstErrorKey}: ${firstError.join(', ')}`
            : `${firstErrorKey}: ${firstError}`;
        } else if (typeof error.response.data === 'string') {
          errorMessage = error.response.data;
        }
      } else if (error.message) {
        // Błąd sieciowy (np. brak połączenia)
        if (error.message.includes('Network Error') || error.code === 'ERR_NETWORK') {
          errorMessage = 'Nie można połączyć się z serwerem. Sprawdź połączenie internetowe lub URL API.';
        } else {
          errorMessage = error.message;
        }
      }
      
      dispatch({
        type: AUTH_ACTIONS.REGISTER_FAILURE,
        payload: errorMessage,
      });
      toast.error(errorMessage);
      throw error;
    }
  };

  // Funkcja do czyszczenia danych Google z localStorage, sessionStorage i cookies
  const clearGoogleData = () => {
    // 1. Wyczyść localStorage
    const localStorageKeysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      // Usuń wszystkie klucze związane z Google
      if (key && (key.startsWith('g_') || key.startsWith('gid_') || key.includes('google'))) {
        localStorageKeysToRemove.push(key);
      }
    }
    localStorageKeysToRemove.forEach(key => localStorage.removeItem(key));
    
    // 2. Wyczyść sessionStorage
    const sessionStorageKeysToRemove = [];
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key && (key.startsWith('g_') || key.startsWith('gid_') || key.includes('google'))) {
        sessionStorageKeysToRemove.push(key);
      }
    }
    sessionStorageKeysToRemove.forEach(key => sessionStorage.removeItem(key));
    
    // 3. Wyczyść cookies Google (g_state, g_csrf_token, itp.)
    const cookiesToRemove = ['g_state', 'g_csrf_token'];
    cookiesToRemove.forEach(cookieName => {
      // Usuń cookie dla aktualnej domeny
      document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
      // Usuń cookie dla domeny z kropką (np. .google.com)
      document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=${window.location.hostname};`;
      // Usuń cookie dla domeny głównej
      const domainParts = window.location.hostname.split('.');
      if (domainParts.length > 1) {
        const rootDomain = '.' + domainParts.slice(-2).join('.');
        document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=${rootDomain};`;
      }
    });
    
    // 4. Wywołaj metodę Google do czyszczenia sesji (jeśli dostępna)
    if (window.google && window.google.accounts && window.google.accounts.id) {
      try {
        // Wyłącz automatyczny wybór konta - zapobiega pokazywaniu kont między urządzeniami
        window.google.accounts.id.disableAutoSelect();
      } catch (error) {
        console.log('Google accounts cleanup:', error);
      }
    }
  };

  // Wylogowanie
  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    // Wyczyść dane Google Identity Services
    clearGoogleData();
    dispatch({ type: AUTH_ACTIONS.LOGOUT });
    toast.success('Wylogowano pomyślnie');
  };

  // Wyczyść błędy
  const clearError = () => {
    dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR });
  };

  // Aktualizuj profil
  const updateProfile = async (data) => {
    try {
      const response = await authAPI.updateProfile(data);
      dispatch({
        type: AUTH_ACTIONS.LOAD_USER_SUCCESS,
        payload: response.data,
      });
      toast.success('Profil został zaktualizowany!');
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Błąd aktualizacji profilu';
      toast.error(errorMessage);
      throw error;
    }
  };

  const value = {
    ...state,
    login,
    loginWithGoogle,
    register,
    logout,
    clearError,
    updateProfile,
    loadUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook do używania kontekstu
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
