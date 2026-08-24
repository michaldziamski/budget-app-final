import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft } from 'lucide-react';
import { authAPI } from '../services/api';
import toast from 'react-hot-toast';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email) {
      toast.error('Podaj adres email');
      return;
    }

    setIsLoading(true);
    try {
      await authAPI.forgotPassword({ email });
      setEmailSent(true);
      toast.success('Email został wysłany!');
    } catch (error) {
      const errorMessage = error.response?.data?.email?.[0] ||
                          error.response?.data?.error ||
                          error.response?.data?.detail ||
                          'Błąd podczas wysyłania emaila';
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900">
            <Mail className="h-6 w-6 text-primary-600 dark:text-primary-300" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-white">
            Reset hasła
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
            Wprowadź swój adres email, a wyślemy Ci link do resetu hasła
          </p>
        </div>

        {emailSent ? (
          <div className="card p-6">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-success-100 dark:bg-success-900">
                <Mail className="h-6 w-6 text-success-600 dark:text-success-300" />
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
                Email został wysłany!
              </h3>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                Jeśli konto z adresem <strong>{email}</strong> istnieje, wysłaliśmy link do resetu hasła. 
                Sprawdź swoją skrzynkę pocztową.
              </p>
              <p className="mt-4 text-xs text-gray-500 dark:text-gray-400">
                ⏰ Link jest ważny przez 1 godzinę.
              </p>
              <div className="mt-6">
                <Link
                  to="/login"
                  className="text-sm text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300 inline-flex items-center"
                >
                  <ArrowLeft className="h-4 w-4 mr-1" />
                  Powrót do logowania
                </Link>
              </div>
            </div>
          </div>
        ) : (
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="email" className="label">
                Adres email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-field pl-10"
                  placeholder="twoj@email.com"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Wysyłanie...
                  </div>
                ) : (
                  'Wyślij link resetu hasła'
                )}
              </button>
            </div>

            <div className="text-center">
              <Link
                to="/login"
                className="text-sm text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300 inline-flex items-center"
              >
                <ArrowLeft className="h-4 w-4 mr-1" />
                Powrót do logowania
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default ForgotPassword;

