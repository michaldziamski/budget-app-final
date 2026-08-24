import React, { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { dashboardAPI, analyticsAPI } from '../services/api';
import {
  Wallet,
  Target,
  AlertCircle,
  CreditCard,
  PieChart,
} from 'lucide-react';
import { PieChart as RechartsPieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import * as FaIcons from 'react-icons/fa';
import * as Fa6Icons from 'react-icons/fa6';

// Funkcja pomocnicza do renderowania ikony Font Awesome
const renderIcon = (iconClass) => {
  if (!iconClass || typeof iconClass !== 'string') return null;
  
  try {
    const parts = iconClass.trim().split(' ');
    if (parts.length >= 2) {
      const faPart = parts.find(p => p.startsWith('fa-'));
      if (faPart) {
        const iconName = faPart
          .replace('fa-', '')
          .split('-')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join('');
        
        const Fa6Icon = Fa6Icons[`Fa${iconName}`];
        if (Fa6Icon) return React.createElement(Fa6Icon);
        
        const FaIcon = FaIcons[`Fa${iconName}`];
        if (FaIcon) return React.createElement(FaIcon);
      }
    }
  } catch (e) {
    console.warn('Nie udało się znaleźć ikony:', iconClass, e);
  }
  
  return null;
};

const Dashboard = () => {
  const { user } = useAuth();
  const { theme } = useTheme();
  const [dashboardData, setDashboardData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [categoryExpenses, setCategoryExpenses] = useState([]);
  const [monthlyBars, setMonthlyBars] = useState([]);
  
  // Kolory dla wykresów w zależności od trybu
  const isDark = theme === 'dark';
  const gridColor = isDark ? '#4B5563' : '#E5E7EB'; // gray-600 / gray-200
  const axisColor = isDark ? '#9CA3AF' : '#6B7280'; // gray-400 / gray-500
  const axisLineColor = isDark ? '#6B7280' : '#D1D5DB'; // gray-500 / gray-300
  const tooltipBg = isDark ? '#1F2937' : '#FFFFFF'; // gray-800 / white
  const tooltipText = isDark ? '#F3F4F6' : '#111827'; // gray-100 / gray-900
  const tooltipBorder = isDark ? '#374151' : '#E5E7EB'; // gray-700 / gray-200

  useEffect(() => {
    loadDashboardData();
    loadAnalytics();
  }, []);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      const response = await dashboardAPI.getDashboard();
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      setError('Błąd ładowania danych dashboardu');
    } finally {
      setIsLoading(false);
    }
  };

  const loadAnalytics = async () => {
    try {
      // Ostatnie 30 dni dla wykresu kołowego
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - 30);
      const fmt = (d) => d.toISOString().slice(0, 10);
      const catResp = await analyticsAPI.getCategoryExpenses({ date_from: fmt(start), date_to: fmt(end) });
      setCategoryExpenses(catResp.data || []);

      // Ostatnie 6 miesięcy dla wykresu słupkowego (przychody vs wydatki)
      const bars = [];
      const now = new Date();
      for (let i = 5; i >= 0; i--) {
        const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
        const year = d.getFullYear();
        const month = d.getMonth() + 1;
        // eslint-disable-next-line no-await-in-loop
        const rep = await analyticsAPI.getMonthlyReport(year, month);
        bars.push({
          month: d.toLocaleString('pl-PL', { month: 'short' }),
          przychody: Number(rep.data.total_income || 0),
          wydatki: Number(rep.data.total_expenses || 0),
        });
      }
      setMonthlyBars(bars);
    } catch (e) {
      // Nie blokuj całego dashboardu jeśli analityka zawiedzie
      // Utrzymaj domyślne puste wykresy
    }
  };

  // Dane do wykresów (rzeczywiste) – muszą być zdefiniowane przed jakimikolwiek wczesnymi returnami
  const pieChartData = useMemo(() => {
    const palette = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316'];
    return (categoryExpenses || []).map((item, idx) => ({
      name: item.category_name,
      value: Number(item.total_amount || 0),
      color: item.category_color || palette[idx % palette.length],
      icon: item.category_icon || null,
    }));
  }, [categoryExpenses]);

  const barChartData = useMemo(() => monthlyBars, [monthlyBars]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="mx-auto h-12 w-12 text-danger-500" />
        <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Błąd ładowania</h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{error}</p>
        <button
          onClick={loadDashboardData}
          className="mt-4 btn-primary"
        >
          Spróbuj ponownie
        </button>
      </div>
    );
  }

  const stats = dashboardData?.stats || {};
  const recentTransactions = dashboardData?.recent_transactions || [];
  const activeBudgets = dashboardData?.active_budgets || [];
  const savingsGoals = dashboardData?.savings_goals || [];


  const StatCard = ({ title, value, icon: Icon, color, trend }) => (
    <div className="card p-6">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-300">{title}</p>
          <p className="text-2xl font-semibold text-gray-900 dark:text-white">{value}</p>
        </div>
      </div>
      {trend && (
        <div className="mt-4 flex items-center">
          <span className={`text-sm ${trend > 0 ? 'text-success-600' : 'text-danger-600'}`}>
            {trend > 0 ? '+' : ''}{trend}%
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">vs poprzedni miesiąc</span>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Witaj, {user?.username}!
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Oto przegląd Twoich finansów
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Całkowite saldo"
          value={`${stats.total_balance || 0} PLN`}
          icon={Wallet}
          color="bg-primary-500"
        />
        <StatCard
          title="Aktywne konta"
          value={stats.total_accounts || 0}
          icon={CreditCard}
          color="bg-success-500"
        />
        <StatCard
          title="Aktywne budżety"
          value={stats.active_budgets || 0}
          icon={PieChart}
          color="bg-warning-500"
        />
        <StatCard
          title="Cele oszczędnościowe"
          value={stats.active_savings_goals || 0}
          icon={Target}
          color="bg-danger-500"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie Chart - Wydatki według kategorii */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Wydatki według kategorii
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RechartsPieChart>
                <Pie
                  data={pieChartData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                >
                  {pieChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{
                    backgroundColor: tooltipBg,
                    border: `1px solid ${tooltipBorder}`,
                    borderRadius: '0.5rem',
                    color: tooltipText,
                  }}
                  labelStyle={{
                    color: tooltipText,
                  }}
                  content={({ active, payload }) => {
                    if (active && payload && payload[0]) {
                      const data = payload[0].payload;
                      const icon = data.icon ? renderIcon(data.icon) : null;
                      return (
                        <div style={{ backgroundColor: tooltipBg, borderColor: tooltipBorder, color: tooltipText }} className="p-3 border rounded shadow-lg">
                          <div className="flex items-center gap-2">
                            {icon && (
                              <span style={{ color: data.color }} className="text-lg">
                                {icon}
                              </span>
                            )}
                            <span className="font-medium">{data.name}</span>
                          </div>
                          <div className="text-sm mt-1" style={{ color: isDark ? '#9CA3AF' : '#4B5563' }}>
                            {Number(data.value).toFixed(2)} PLN
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend 
                  content={({ payload }) => (
                    <div className="flex flex-wrap gap-3 justify-center mt-4">
                      {payload?.map((entry, index) => {
                        const data = entry.payload;
                        const icon = data?.icon ? renderIcon(data.icon) : null;
                        return (
                          <div key={index} className="flex items-center gap-2 text-sm" style={{ color: isDark ? '#E5E7EB' : '#111827' }}>
                            <div 
                              className="w-3 h-3 rounded" 
                              style={{ backgroundColor: entry.color }}
                            />
                            {icon && (
                              <span style={{ color: entry.color }} className="text-sm">
                                {icon}
                              </span>
                            )}
                            <span>{data?.name || entry.value}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                />
              </RechartsPieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Bar Chart - Przychody vs Wydatki */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Przychody vs Wydatki
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis 
                  dataKey="month" 
                  stroke={axisLineColor}
                  tick={{ fill: axisColor }}
                />
                <YAxis 
                  stroke={axisLineColor}
                  tick={{ fill: axisColor }}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: tooltipBg,
                    border: `1px solid ${tooltipBorder}`,
                    borderRadius: '0.5rem',
                    color: tooltipText,
                  }}
                  labelStyle={{
                    color: tooltipText,
                  }}
                />
                <Legend 
                  wrapperStyle={{
                    color: isDark ? '#E5E7EB' : '#111827',
                  }}
                />
                <Bar dataKey="przychody" fill="#10b981" name="Przychody" />
                <Bar dataKey="wydatki" fill="#ef4444" name="Wydatki" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Transactions and Budgets */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Transactions */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Ostatnie transakcje
            </h3>
            <a
              href="/transactions"
              className="text-sm text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
            >
              Zobacz wszystkie
            </a>
          </div>
          <div className="space-y-3">
            {recentTransactions.length > 0 ? (
              recentTransactions.map((transaction) => {
                const category = transaction.category || (transaction.category_name ? { name: transaction.category_name } : null);
                const categoryIcon = category?.icon ? renderIcon(category.icon) : null;
                const categoryColor = category?.color || '#3498db';
                return (
                  <div
                    key={transaction.id}
                    className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-b-0"
                  >
                    <div className="flex items-center gap-2 flex-1">
                      {categoryIcon && (
                        <span style={{ color: categoryColor }} className="text-lg">
                          {categoryIcon}
                        </span>
                      )}
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {transaction.description}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(transaction.date).toLocaleDateString('pl-PL')}
                          {category && ` • ${category.name || transaction.category_name}`}
                        </p>
                      </div>
                    </div>
                    <span
                      className={`text-sm font-medium ${
                        transaction.transaction_type === 'income'
                          ? 'text-success-600'
                          : 'text-danger-600'
                      }`}
                    >
                      {transaction.transaction_type === 'income' ? '+' : '-'}
                      {transaction.amount} PLN
                    </span>
                  </div>
                );
              })
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                Brak ostatnich transakcji
              </p>
            )}
          </div>
        </div>

        {/* Active Budgets */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Aktywne budżety
            </h3>
            <a
              href="/budgets"
              className="text-sm text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
            >
              Zobacz wszystkie
            </a>
          </div>
          <div className="space-y-3">
            {activeBudgets.length > 0 ? (
              activeBudgets.map((budget) => (
                <div key={budget.id} className="py-2">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {budget.name}
                    </p>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {budget.usage_percentage?.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        budget.usage_percentage > 100
                          ? 'bg-danger-500'
                          : budget.usage_percentage > 80
                          ? 'bg-warning-500'
                          : 'bg-success-500'
                      }`}
                      style={{
                        width: `${Math.min(budget.usage_percentage || 0, 100)}%`,
                      }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {budget.spent_amount} / {budget.amount} PLN
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                Brak aktywnych budżetów
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Savings Goals */}
      {savingsGoals.length > 0 && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Cele oszczędnościowe
            </h3>
            <a
              href="/savings-goals"
              className="text-sm text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
            >
              Zobacz wszystkie
            </a>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {savingsGoals.map((goal) => (
              <div key={goal.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 dark:text-white">{goal.name}</h4>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{goal.description}</p>
                <div className="mt-3">
                  <div className="flex justify-between text-sm text-gray-900 dark:text-white">
                    <span>{goal.current_amount} PLN</span>
                    <span>{goal.target_amount} PLN</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-1">
                    <div
                      className="bg-primary-500 h-2 rounded-full"
                      style={{
                        width: `${Math.min(goal.progress_percentage || 0, 100)}%`,
                      }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {goal.progress_percentage?.toFixed(1)}% ukończone
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
