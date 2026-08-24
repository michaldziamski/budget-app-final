import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Lock, Eye, EyeOff, CheckCircle, XCircle } from 'lucide-react';
import { authAPI } from '../services/api';
import toast from 'react-hot-toast';

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');
  
  const [formData, setFormData] = useState({
    new_password: '',
    confirm_password: '',
  });
  const [showPasswords, setShowPasswords] = useState({
    new: false,
    confirm: false,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!token) {
      setError('Brak tokenu resetu hasła. Sprawdź link z emaila.');
    }
  }, [token]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!token) {
      setError('Brak tokenu resetu hasła');
      return;
    }

    if (!formData.new_password || !formData.confirm_password) {
      setError('Wszystkie pola są wymagane');
      return;
    }

    if (formData.new_password.length < 6) {
      setError('Hasło musi mieć co najmniej 6 znaków');
      return;
    }

    if (formData.new_password !== formData.confirm_password) {
      setError('Hasła nie są zgodne');
      return;
    }

    setIsLoading(true);
    try {
      await authAPI.resetPassword({
        token,
        new_password: formData.new_password,
      });
      setIsSuccess(true);
      toast.success('Hasło zostało pomyślnie zresetowane!');
      
      // Przekieruj do logowania po 3 sekundach
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (error) {
      const errorMessage = error.response?.data?.token?.[0] ||
                          error.response?.data?.new_password?.[0] ||
                          error.response?.data?.error ||
                          error.response?.data?.detail ||
                          'Błąd podczas resetowania hasła';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-success-100 dark:bg-success-900">
              <CheckCircle className="h-10 w-10 text-success-600 dark:text-success-300" />
            </div>
            <h2 className="mt-6 text-3xl font-extrabold text-gray-900 dark:text-white">
              Hasło zostało zresetowane!
            </h2>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              Twoje hasło zostało pomyślnie zmienione. Za chwilę zostaniesz przekierowany do strony logowania.
            </p>
            <div className="mt-6">
              <Link
                to="/login"
                className="btn-primary"
              >
                Przejdź do logowania
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-danger-100 dark:bg-danger-900">
              <XCircle className="h-10 w-10 text-danger-600 dark:text-danger-300" />
            </div>
            <h2 className="mt-6 text-3xl font-extrabold text-gray-900 dark:text-white">
              Błąd
            </h2>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              {error}
            </p>
            <div className="mt-6">
              <Link
                to="/forgot-password"
                className="btn-primary"
              >
                Poproś o nowy link
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900">
            <Lock className="h-6 w-6 text-primary-600 dark:text-primary-300" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-white">
            Ustaw nowe hasło
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
            Wprowadź nowe hasło dla swojego konta
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md bg-danger-50 dark:bg-danger-900/30 p-4">
              <div className="text-sm text-danger-700 dark:text-danger-300">{error}</div>
            </div>
          )}

          <div>
            <label htmlFor="new_password" className="label">
              Nowe hasło
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="new_password"
                name="new_password"
                type={showPasswords.new ? 'text' : 'password'}
                autoComplete="new-password"
                required
                value={formData.new_password}
                onChange={handleChange}
                className="input-field pl-10 pr-10"
                placeholder="Wprowadź nowe hasło (min. 6 znaków)"
                minLength={6}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPasswords((prev) => ({ ...prev, new: !prev.new }))}
              >
                {showPasswords.new ? (
                  <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                ) : (
                  <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                )}
              </button>
            </div>
          </div>

          <div>
            <label htmlFor="confirm_password" className="label">
              Potwierdź nowe hasło
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="confirm_password"
                name="confirm_password"
                type={showPasswords.confirm ? 'text' : 'password'}
                autoComplete="new-password"
                required
                value={formData.confirm_password}
                onChange={handleChange}
                className="input-field pl-10 pr-10"
                placeholder="Potwierdź nowe hasło"
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPasswords((prev) => ({ ...prev, confirm: !prev.confirm }))}
              >
                {showPasswords.confirm ? (
                  <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                ) : (
                  <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                )}
              </button>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading || !token}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Resetowanie...
                </div>
              ) : (
                'Zresetuj hasło'
              )}
            </button>
          </div>

          <div className="text-center">
            <Link
              to="/login"
              className="text-sm text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
            >
              Powrót do logowania
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ResetPassword;

