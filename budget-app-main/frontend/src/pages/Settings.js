import React, { useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { authAPI } from '../services/api';
import { Eye, EyeOff, Lock } from 'lucide-react';
import toast from 'react-hot-toast';

const Settings = () => {
  const { theme, toggle, setTheme } = useTheme();
  const [passwordForm, setPasswordForm] = useState({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [showPasswords, setShowPasswords] = useState({
    old: false,
    new: false,
    confirm: false,
  });
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordForm((prev) => ({ ...prev, [name]: value }));
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    
    // Walidacja
    if (!passwordForm.old_password || !passwordForm.new_password || !passwordForm.confirm_password) {
      toast.error('Wszystkie pola są wymagane');
      return;
    }
    
    if (passwordForm.new_password.length < 6) {
      toast.error('Nowe hasło musi mieć co najmniej 6 znaków');
      return;
    }
    
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast.error('Nowe hasła nie są zgodne');
      return;
    }
    
    if (passwordForm.old_password === passwordForm.new_password) {
      toast.error('Nowe hasło musi być różne od starego');
      return;
    }
    
    setIsChangingPassword(true);
    try {
      await authAPI.changePassword({
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password,
      });
      toast.success('Hasło zostało zmienione pomyślnie');
      setPasswordForm({
        old_password: '',
        new_password: '',
        confirm_password: '',
      });
    } catch (error) {
      const errorMessage = error.response?.data?.old_password?.[0] || 
                          error.response?.data?.new_password?.[0] ||
                          error.response?.data?.non_field_errors?.[0] ||
                          error.response?.data?.detail ||
                          'Błąd podczas zmiany hasła';
      toast.error(errorMessage);
    } finally {
      setIsChangingPassword(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Ustawienia</h2>

      <div className="card p-5">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Wygląd</h3>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-medium text-gray-900 dark:text-gray-100">Tryb ciemny</div>
            <div className="text-sm text-gray-600 dark:text-gray-300">Przełącz wygląd aplikacji</div>
          </div>
          <div className="flex items-center gap-2">
            <select value={theme} onChange={(e)=>setTheme(e.target.value)} className="input-field w-36">
              <option value="light">Jasny</option>
              <option value="dark">Ciemny</option>
            </select>
            <button onClick={toggle} className="btn-secondary">Przełącz</button>
          </div>
        </div>
      </div>

      <div className="card p-5">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Zmiana hasła</h3>
        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          <div>
            <label className="label">Stare hasło</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type={showPasswords.old ? 'text' : 'password'}
                name="old_password"
                value={passwordForm.old_password}
                onChange={handlePasswordChange}
                className="input-field pl-10 pr-10"
                placeholder="Wprowadź stare hasło"
                required
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPasswords((prev) => ({ ...prev, old: !prev.old }))}
              >
                {showPasswords.old ? (
                  <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                ) : (
                  <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                )}
              </button>
            </div>
          </div>

          <div>
            <label className="label">Nowe hasło</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type={showPasswords.new ? 'text' : 'password'}
                name="new_password"
                value={passwordForm.new_password}
                onChange={handlePasswordChange}
                className="input-field pl-10 pr-10"
                placeholder="Wprowadź nowe hasło (min. 6 znaków)"
                required
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
            <label className="label">Potwierdź nowe hasło</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type={showPasswords.confirm ? 'text' : 'password'}
                name="confirm_password"
                value={passwordForm.confirm_password}
                onChange={handlePasswordChange}
                className="input-field pl-10 pr-10"
                placeholder="Potwierdź nowe hasło"
                required
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

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isChangingPassword}
              className="btn-primary"
            >
              {isChangingPassword ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Zmienianie...
                </div>
              ) : (
                'Zmień hasło'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Settings;


