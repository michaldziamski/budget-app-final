import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Eye, EyeOff, Mail, Lock } from 'lucide-react';
import toast from 'react-hot-toast';

const Login = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const { login, loginWithGoogle, error, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  // Wyświetl komunikat po weryfikacji emaila
  useEffect(() => {
    if (location.state?.message) {
      toast.success(location.state.message);
      // Wyczyść state, żeby komunikat nie pokazywał się ponownie
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location, navigate]);

  const handleGoogleSignIn = useCallback(async (response) => {
    setIsGoogleLoading(true);
    try {
      await loginWithGoogle(response.credential);
      navigate('/');
    } catch (error) {
      console.error('Google login error:', error);
    } finally {
      setIsGoogleLoading(false);
    }
  }, [loginWithGoogle, navigate]);

  // Inicjalizacja Google Sign-In
  useEffect(() => {
    const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID || '';
    
    // Debug: wyświetl Client ID w konsoli
    console.log('🔑 Google Client ID:', clientId ? `${clientId.substring(0, 20)}...` : 'BRAK');
    console.log('🌐 Current URL:', window.location.origin);
    
    // Sprawdź czy Client ID jest ustawiony
    if (!clientId) {
      console.warn('⚠️ REACT_APP_GOOGLE_CLIENT_ID nie jest ustawiony. Logowanie przez Google nie będzie działać.');
      console.warn('💡 Dodaj REACT_APP_GOOGLE_CLIENT_ID do pliku .env w folderze frontend/');
      return;
    }

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

    // Wyczyść dane Google przed inicjalizacją - zapobiega pokazywaniu kont innych użytkowników
    clearGoogleData();

    const initializeGoogleSignIn = () => {
      if (window.google && window.google.accounts) {
        try {
          // Wyłącz automatyczny wybór konta przed inicjalizacją - zapobiega pokazywaniu kont między urządzeniami
          if (window.google.accounts.id) {
            try {
              window.google.accounts.id.disableAutoSelect();
            } catch (error) {
              console.log('disableAutoSelect error:', error);
            }
          }
          
          console.log('✅ Inicjalizacja Google Sign-In...');
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: handleGoogleSignIn,
            // Wyłącz automatyczny wybór konta - zapobiega pokazywaniu kont między urządzeniami
            auto_select: false,
            cancel_on_tap_outside: true,
            prompt_parent_id: 'google-signin-button',
            ux_mode: 'popup',
            // Wymuś wybór konta za każdym razem - zapobiega pokazywaniu cache'owanego konta
            prompt: 'select_account',
            // Wyłącz ITP (Intelligent Tracking Prevention) - zapobiega synchronizacji między urządzeniami
            itp_support: false,
            // Wyłącz FedCM - zapobiega synchronizacji kont między urządzeniami
            use_fedcm_for_prompt: false,
          });

          const buttonElement = document.getElementById('google-signin-button');
          if (buttonElement) {
            window.google.accounts.id.renderButton(buttonElement, {
              theme: 'outline',
              size: 'large',
              width: '100%',
              text: 'signin_with',
              locale: 'pl',
            });
            console.log('✅ Przycisk Google został wyrenderowany');
          } else {
            console.error('❌ Nie znaleziono elementu #google-signin-button');
          }
        } catch (error) {
          console.error('❌ Błąd inicjalizacji Google Sign-In:', error);
        }
      } else {
        console.warn('⚠️ window.google.accounts nie jest dostępne');
      }
    };

    // Poczekaj aż Google Identity Services się załaduje
    if (window.google && window.google.accounts) {
      initializeGoogleSignIn();
    } else {
      const checkGoogle = setInterval(() => {
        if (window.google && window.google.accounts) {
          clearInterval(checkGoogle);
          initializeGoogleSignIn();
        }
      }, 100);

      // Cleanup po 10 sekundach
      setTimeout(() => clearInterval(checkGoogle), 10000);
    }
  }, [handleGoogleSignIn]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    // Wyczyść błąd przy zmianie danych
    if (error) clearError();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await login(formData);
      navigate('/');
    } catch (error) {
      console.error('Login error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900">
            <Lock className="h-6 w-6 text-primary-600 dark:text-primary-300" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-white">
            Zaloguj się do swojego konta
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
            Lub{' '}
            <Link
              to="/register"
              className="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
            >
              utwórz nowe konto
            </Link>
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md bg-danger-50 dark:bg-danger-900/30 p-4">
              <div className="text-sm text-danger-700 dark:text-danger-300">{error}</div>
            </div>
          )}
          
          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="label">
                Nazwa użytkownika
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  value={formData.username}
                  onChange={handleChange}
                  className="input-field pl-10"
                  placeholder="Wprowadź nazwę użytkownika"
                />
              </div>
            </div>
            
            <div>
              <label htmlFor="password" className="label">
                Hasło
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className="input-field pl-10 pr-10"
                  placeholder="Wprowadź hasło"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  )}
                </button>
              </div>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading || isGoogleLoading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Logowanie...
                </div>
              ) : (
                'Zaloguj się'
              )}
            </button>
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gray-50 dark:bg-gray-900 text-gray-500 dark:text-gray-400">
                Lub
              </span>
            </div>
          </div>

          <div>
            <div id="google-signin-button" className="w-full"></div>
            {isGoogleLoading && (
              <div className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
                <div className="inline-flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600 mr-2"></div>
                  Logowanie przez Google...
                </div>
              </div>
            )}
          </div>

          <div className="text-center">
            <Link
              to="/forgot-password"
              className="text-sm text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
            >
              Zapomniałeś hasła?
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;







