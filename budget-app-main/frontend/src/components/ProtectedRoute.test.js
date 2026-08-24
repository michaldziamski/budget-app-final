import React from 'react';
import { render, screen } from '@testing-library/react';
import ProtectedRoute from './ProtectedRoute';

// Mockujemy react-router-dom, żeby nie polegać na prawdziwej implementacji
jest.mock('react-router-dom', () => ({
  Navigate: ({ to }) => <div>Navigate to {to}</div>,
  useLocation: () => ({ pathname: '/dashboard' }),
}));

// Mock useAuth z AuthContext
jest.mock('../contexts/AuthContext', () => {
  const React = require('react');
  return {
    useAuth: jest.fn(),
  };
});

import { useAuth } from '../contexts/AuthContext';

test('pokazuje ekran ładowania gdy isLoading jest true', () => {
  useAuth.mockReturnValue({
    isAuthenticated: false,
    isLoading: true,
  });

  render(
    <ProtectedRoute>
      <div>Dashboard content</div>
    </ProtectedRoute>
  );

  expect(screen.getByText(/Ładowanie.../i)).toBeInTheDocument();
});

test('przekierowuje niezalogowanego użytkownika na /login', () => {
  useAuth.mockReturnValue({
    isAuthenticated: false,
    isLoading: false,
  });

  render(
    <ProtectedRoute>
      <div>Dashboard content</div>
    </ProtectedRoute>
  );

  expect(screen.getByText(/Navigate to \/login/i)).toBeInTheDocument();
});

test('renderuje dzieci dla zalogowanego użytkownika', () => {
  useAuth.mockReturnValue({
    isAuthenticated: true,
    isLoading: false,
  });

  render(
    <ProtectedRoute>
      <div>Dashboard content</div>
    </ProtectedRoute>
  );

  expect(screen.getByText(/Dashboard content/i)).toBeInTheDocument();
});


