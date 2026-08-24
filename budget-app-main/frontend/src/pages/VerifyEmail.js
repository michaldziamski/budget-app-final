import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CheckCircle, XCircle, Loader } from 'lucide-react';
import api from '../services/api';

const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('loading'); // loading, success, error
  const [message, setMessage] = useState('');
  const token = searchParams.get('token');

  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setStatus('error');
        setMessage('Brak tokenu weryfikacyjnego w linku.');
        return;
      }

      try {
        const response = await api.post('/auth/verify-email/', { token });
        setStatus('success');
        setMessage(response.data.message || 'Email został pomyślnie zweryfikowany!');
        
        // Przekieruj do logowania po 3 sekundach
        setTimeout(() => {
          navigate('/login', { 
            state: { 
              message: 'Email zweryfikowany! Możesz się teraz zalogować.' 
            } 
          });
        }, 3000);
      } catch (error) {
        setStatus('error');
        if (error.response?.data?.error) {
          setMessage(error.response.data.error);
        } else if (error.response?.data?.detail) {
          setMessage(error.response.data.detail);
        } else {
          setMessage('Wystąpił błąd podczas weryfikacji emaila. Spróbuj ponownie.');
        }
        console.error('Verification error:', error);
      }
    };

    verifyEmail();
  }, [token, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
          {status === 'loading' && (
            <>
              <Loader className="h-16 w-16 text-primary-600 dark:text-primary-400 mx-auto animate-spin mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Weryfikacja emaila...
              </h2>
              <p className="text-gray-600 dark:text-gray-300">
                Proszę czekać, trwa weryfikacja Twojego adresu email.
              </p>
            </>
          )}

          {status === 'success' && (
            <>
              <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Email zweryfikowany!
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                {message}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Przekierowywanie do strony logowania...
              </p>
            </>
          )}

          {status === 'error' && (
            <>
              <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Błąd weryfikacji
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                {message}
              </p>
              <div className="space-y-2">
                <button
                  onClick={() => navigate('/login')}
                  className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  Przejdź do logowania
                </button>
                <button
                  onClick={() => navigate('/register')}
                  className="w-full bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  Zarejestruj się ponownie
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default VerifyEmail;

