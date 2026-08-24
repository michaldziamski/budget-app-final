import React from 'react';
import { render, screen } from '@testing-library/react';
import Dashboard from './Dashboard';
import { AuthProvider } from '../contexts/AuthContext';
import { ThemeProvider } from '../contexts/ThemeContext';
import { dashboardAPI, analyticsAPI } from '../services/api';

jest.mock('../services/api', () => ({
  dashboardAPI: {
    getDashboard: jest.fn(),
  },
  analyticsAPI: {
    getCategoryExpenses: jest.fn(),
    getMonthlyReport: jest.fn(),
  },
}));

// Prosty wrapper z providerami
const renderDashboard = async () => {
  dashboardAPI.getDashboard.mockResolvedValueOnce({
    data: {
      stats: {
        total_balance: '1000.00',
        total_accounts: 2,
        active_budgets: 1,
        active_savings_goals: 1,
      },
      recent_transactions: [],
      active_budgets: [],
      savings_goals: [],
    },
  });

  analyticsAPI.getCategoryExpenses.mockResolvedValueOnce({ data: [] });
  analyticsAPI.getMonthlyReport.mockResolvedValue({
    data: {
      total_income: '0.00',
      total_expenses: '0.00',
    },
  });

  render(
    <AuthProvider>
      <ThemeProvider>
        <Dashboard />
      </ThemeProvider>
    </AuthProvider>
  );
};

test('renderuje podstawowe sekcje dashboardu', async () => {
  await renderDashboard();

  expect(
    await screen.findByText(/Całkowite saldo/i)
  ).toBeInTheDocument();
  expect(
    screen.getByText(/Aktywne konta/i)
  ).toBeInTheDocument();
  // "Aktywne budżety" pojawia się w karcie statystyk i w nagłówku sekcji,
  // dlatego używamy getAllByText zamiast getByText
  expect(screen.getAllByText(/Aktywne budżety/i).length).toBeGreaterThan(0);
  expect(
    screen.getByText(/Cele oszczędnościowe/i)
  ).toBeInTheDocument();
});


