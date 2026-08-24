import React, { useEffect, useMemo, useState } from 'react';
import { notificationsAPI, alertsAPI } from '../services/api';
import { Bell, CheckCircle2, RefreshCcw, Calendar } from 'lucide-react';

const typeLabels = {
  budget_alert: 'Alert budżetowy',
  payment_reminder: 'Przypomnienie o płatności',
  goal_reminder: 'Przypomnienie o celu',
  system: 'Systemowe',
};

const NotificationItem = ({ n, onMarkRead }) => {
  return (
    <div className={`p-4 border rounded-lg ${n.is_read ? 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700' : 'bg-blue-50 dark:bg-blue-900/30 border-blue-100 dark:border-blue-800'}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm text-gray-500 dark:text-gray-400">{typeLabels[n.notification_type] || n.notification_type}</div>
          <div className="text-base font-semibold text-gray-900 dark:text-white">{n.title}</div>
          <div className="text-sm text-gray-700 dark:text-gray-300 mt-1 whitespace-pre-line">{n.message}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">{new Date(n.created_at).toLocaleString()}</div>
        </div>
        <div className="shrink-0">
          {n.is_read ? (
            <span className="inline-flex items-center text-green-600 dark:text-green-400 text-sm"><CheckCircle2 className="h-4 w-4 mr-1" /> Przeczytane</span>
          ) : (
            <button onClick={() => onMarkRead(n)} className="btn-secondary">Oznacz jako przeczytane</button>
          )}
        </div>
      </div>
    </div>
  );
};

const Notifications = () => {
  const [items, setItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [running, setRunning] = useState(false);
  const [runningWeekly, setRunningWeekly] = useState(false);

  const loadNotifications = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await notificationsAPI.getNotifications();
      setItems(data?.results || data || []);
    } catch (e) {
      setError('Nie udało się pobrać powiadomień');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { loadNotifications(); }, []);

  const onMarkRead = async (n) => {
    await notificationsAPI.markAsRead(n.id);
    await loadNotifications();
  };

  const filtered = useMemo(() => {
    if (filter === 'all') return items;
    if (filter === 'unread') return items.filter(i => !i.is_read);
    return items.filter(i => i.notification_type === filter);
  }, [items, filter]);

  const runAlerts = async (type = 'all') => {
    setRunning(true);
    try {
      await alertsAPI.runAlerts(type);
      await loadNotifications();
    } finally {
      setRunning(false);
    }
  };

  const runWeeklySummary = async () => {
    setRunningWeekly(true);
    try {
      await alertsAPI.runAlerts('weekly');
      await loadNotifications();
    } finally {
      setRunningWeekly(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white inline-flex items-center"><Bell className="h-6 w-6 mr-2" /> Powiadomienia</h2>
        <div className="flex gap-2">
          <button onClick={() => runAlerts('all')} className="btn-secondary inline-flex items-center" disabled={running || runningWeekly}>
            <RefreshCcw className={`h-4 w-4 mr-2 ${running ? 'animate-spin' : ''}`} /> Uruchom alerty
          </button>
          <button onClick={runWeeklySummary} className="btn-secondary inline-flex items-center" disabled={running || runningWeekly}>
            <Calendar className={`h-4 w-4 mr-2 ${runningWeekly ? 'animate-spin' : ''}`} /> Generuj podsumowania tygodniowe
          </button>
        </div>
      </div>

      <div className="card p-4 flex flex-wrap gap-2 items-center">
        <select value={filter} onChange={(e)=>setFilter(e.target.value)} className="input-field w-60">
          <option value="all">Wszystkie</option>
          <option value="unread">Nieprzeczytane</option>
          <option value="budget_alert">Alerty budżetowe</option>
          <option value="goal_reminder">Przypomnienia celów</option>
          <option value="payment_reminder">Przypomnienia płatności</option>
          <option value="system">Systemowe</option>
        </select>
      </div>

      {isLoading ? (
        <div className="card p-6 text-center text-gray-500 dark:text-gray-400">Ładowanie...</div>
      ) : error ? (
        <div className="card p-6 text-center text-danger-600">{error}</div>
      ) : filtered.length === 0 ? (
        <div className="card p-6 text-center text-gray-500 dark:text-gray-400">Brak powiadomień</div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filtered.map((n) => (
            <NotificationItem key={n.id} n={n} onMarkRead={onMarkRead} />
          ))}
        </div>
      )}
    </div>
  );
};

export default Notifications;


