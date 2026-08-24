import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { useAuth } from './AuthContext';

const ThemeContext = createContext({ theme: 'light', setTheme: () => {}, toggle: () => {} });

const getPreferred = (userId = null) => {
  // Jeśli jest użytkownik, użyj klucza z user ID
  const key = userId ? `theme_${userId}` : 'theme';
  const saved = localStorage.getItem(key);
  if (saved === 'light' || saved === 'dark') return saved;
  
  // Fallback: sprawdź stary klucz 'theme' (dla kompatybilności wstecznej)
  if (!userId) {
    const oldSaved = localStorage.getItem('theme');
    if (oldSaved === 'light' || oldSaved === 'dark') return oldSaved;
  }
  
  // Dla wylogowanych użytkowników: domyślnie tryb jasny
  if (!userId) {
    return 'light';
  }
  
  // Dla zalogowanych użytkowników: preferencje systemowe jako fallback
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  return prefersDark ? 'dark' : 'light';
};

export const ThemeProvider = ({ children }) => {
  const { user } = useAuth();
  const [theme, setTheme] = useState('light');

  // Załaduj preferencje tematu gdy zmieni się użytkownik
  useEffect(() => {
    const preferred = getPreferred(user?.id);
    setTheme(preferred);
  }, [user?.id]);

  // Zastosuj temat i zapisz w localStorage
  useEffect(() => {
    const root = document.documentElement; // <html>
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    
    // Zapisz z kluczem zawierającym user ID (jeśli użytkownik jest zalogowany)
    if (user?.id) {
      localStorage.setItem(`theme_${user.id}`, theme);
      // Usuń stary globalny klucz jeśli istnieje (dla czystości)
      if (localStorage.getItem('theme')) {
        localStorage.removeItem('theme');
      }
    } else {
      // Jeśli użytkownik nie jest zalogowany, użyj globalnego klucza
      localStorage.setItem('theme', theme);
    }
  }, [theme, user?.id]);

  const value = useMemo(() => ({ 
    theme, 
    setTheme, 
    toggle: () => setTheme((t) => (t === 'dark' ? 'light' : 'dark')) 
  }), [theme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export const useTheme = () => useContext(ThemeContext);


