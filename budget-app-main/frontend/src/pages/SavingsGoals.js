import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { accountsAPI, savingsGoalsAPI, paymentsAPI } from '../services/api';
import { Plus, X, CreditCard, TrendingUp, DollarSign } from 'lucide-react';
import toast from 'react-hot-toast';

const ProgressBar = ({ value }) => {
  const pct = Math.max(0, Math.min(100, Number(value || 0)));
  const color = pct >= 100 ? 'bg-green-500' : pct >= 90 ? 'bg-primary-500' : 'bg-primary-400';
  return (
    <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
      <div className={`${color} h-3`} style={{ width: `${pct}%` }} />
    </div>
  );
};

const GoalModal = ({ open, onClose, onSubmit, accounts, initialData }) => {
  const [form, setForm] = useState(() => initialData || {
    name: '',
    target_amount: '',
    current_amount: 0,
    target_date: new Date(new Date().getFullYear(), new Date().getMonth() + 3, new Date().getDate()).toISOString().slice(0, 10),
    account: '',
    description: '',
  });

  useEffect(() => {
    setForm(initialData || {
      name: '',
      target_amount: '',
      current_amount: 0,
      target_date: new Date(new Date().getFullYear(), new Date().getMonth() + 3, new Date().getDate()).toISOString().slice(0, 10),
      account: '',
      description: '',
    });
  }, [initialData, open]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // Walidacja ujemnych kwot
    if (name.includes('amount') && value !== '' && Number(value) < 0) {
      toast.error('Nie można wprowadzić ujemnej kwoty');
      return;
    }
    
    setForm((p) => ({ ...p, [name]: name.includes('amount') ? Number(value) : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Walidacja przed wysłaniem
    if ((form.target_amount !== '' && Number(form.target_amount) < 0) ||
        (form.current_amount !== '' && Number(form.current_amount) < 0)) {
      toast.error('Nie można wprowadzić ujemnej kwoty');
      return;
    }
    
    await onSubmit(form);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 dark:bg-black/60">
      <div className="bg-white dark:bg-gray-800 w-full max-w-xl rounded-lg shadow-strong">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{initialData ? 'Edytuj cel' : 'Dodaj cel'}</h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
            <X className="h-5 w-5 text-gray-600 dark:text-gray-300" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="label">Nazwa</label>
            <input type="text" name="name" value={form.name} onChange={handleChange} className="input-field" required />
          </div>

          <div>
            <label className="label">Kwota docelowa</label>
            <input type="number" step="0.01" name="target_amount" value={form.target_amount} onChange={handleChange} className="input-field" required />
          </div>

          <div>
            <label className="label">Kwota bieżąca</label>
            <input type="number" step="0.01" name="current_amount" value={form.current_amount} onChange={handleChange} className="input-field" />
          </div>

          <div>
            <label className="label">Termin</label>
            <input type="date" name="target_date" value={form.target_date} onChange={handleChange} className="input-field" required />
          </div>

          <div>
            <label className="label">Konto</label>
            <select name="account" value={form.account} onChange={handleChange} className="input-field" required>
              <option value="">Wybierz konto</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>{a.name}</option>
              ))}
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="label">Opis</label>
            <input type="text" name="description" value={form.description} onChange={handleChange} className="input-field" />
          </div>

          <div className="md:col-span-2 flex justify-end gap-3 mt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Anuluj</button>
            <button type="submit" className="btn-primary">Zapisz</button>
          </div>
        </form>
      </div>
    </div>
  );
};

const SavingsGoals = () => {
  const [items, setItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [searchParams, setSearchParams] = useSearchParams();

  // Predefiniowane kwoty do wpłacania
  const quickAmounts = [50, 100, 200, 500, 1000];

  const loadBasics = async () => {
    const { data } = await accountsAPI.getAccounts();
    setAccounts(data?.results || data || []);
  };

  const loadGoals = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await savingsGoalsAPI.getSavingsGoals();
      setItems(data?.results || data || []);
      
      // Załaduj statystyki dla każdego celu
      const statsPromises = (data?.results || data || []).map(async (goal) => {
        try {
          const statsResponse = await paymentsAPI.getPaymentStatistics(goal.id);
          return { goalId: goal.id, stats: statsResponse.data };
        } catch (e) {
          return { goalId: goal.id, stats: null };
        }
      });
      
      const statsResults = await Promise.all(statsPromises);
      const statsMap = {};
      statsResults.forEach(({ goalId, stats }) => {
        if (stats) statsMap[goalId] = stats;
      });
      setStatistics(statsMap);
    } catch (e) {
      setError('Nie udało się pobrać celów');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    (async () => {
      await loadBasics();
      await loadGoals();
    })();
  }, []);

  // Obsłuż powrót z Stripe (fallback bez webhooków) – zabezpieczenie przed duplikacją
  const hasProcessedReturnRef = useRef(false);
  useEffect(() => {
    (async () => {
      const paymentStatus = searchParams.get('payment');
      const sessionId = searchParams.get('session_id');

      if (paymentStatus === 'success') {
        if (hasProcessedReturnRef.current) return; // zapobiegaj dubletom (StrictMode / podwójny render)
        hasProcessedReturnRef.current = true;
        try {
          if (sessionId) {
            await paymentsAPI.confirmCheckoutSession(sessionId);
          }
          toast.success('Płatność zakończona sukcesem!', { id: 'payment-success' });
        } catch (e) {
          // Nawet jeśli potwierdzenie się nie uda (np. brak webhooka, powtórne potwierdzenie), pokaż pojedynczy sukces
          toast.success('Płatność zakończona sukcesem', { id: 'payment-success' });
        } finally {
          setSearchParams({});
          loadGoals();
        }
      } else if (paymentStatus === 'cancelled') {
        if (hasProcessedReturnRef.current) return;
        hasProcessedReturnRef.current = true;
        toast.error('Płatność została anulowana', { id: 'payment-cancelled' });
        setSearchParams({});
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const onAdd = () => {
    setEditing(null);
    setModalOpen(true);
  };

  const onEdit = (g) => {
    setEditing({
      id: g.id,
      name: g.name,
      target_amount: g.target_amount,
      current_amount: g.current_amount,
      target_date: (g.target_date || '').slice(0, 10),
      account: g.account?.id,
      description: g.description || '',
    });
    setModalOpen(true);
  };

  const onDelete = async (g) => {
    if (!window.confirm('Usunąć cel?')) return;
    await savingsGoalsAPI.deleteSavingsGoal(g.id);
    await loadGoals();
  };

  const submitGoal = async (form) => {
    const payload = {
      name: form.name,
      target_amount: form.target_amount,
      current_amount: form.current_amount,
      target_date: form.target_date,
      account: form.account,
      description: form.description || '',
    };
    if (editing?.id) {
      await savingsGoalsAPI.updateSavingsGoal(editing.id, payload);
    } else {
      await savingsGoalsAPI.createSavingsGoal(payload);
    }
    setModalOpen(false);
    setEditing(null);
    await loadGoals();
  };

  const handlePayment = async (goal, amount) => {
    try {
      toast.loading('Przekierowywanie do płatności...', { id: 'payment' });
      const { data } = await paymentsAPI.createCheckoutSession(goal.id, Number(amount));
      
      // Przekieruj do Stripe Checkout
      window.location.href = data.checkout_url;
    } catch (error) {
      toast.error(error.response?.data?.error || 'Nie udało się utworzyć płatności', { id: 'payment' });
    }
  };

  const totals = useMemo(() => ({
    target: items.reduce((s, g) => s + Number(g.target_amount || 0), 0),
    current: items.reduce((s, g) => s + Number(g.current_amount || 0), 0),
  }), [items]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Cele oszczędnościowe</h2>
        <button onClick={onAdd} className="btn-primary inline-flex items-center">
          <Plus className="h-4 w-4 mr-2" /> Dodaj
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">Suma celów</div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-white">{totals.target.toFixed(2)} PLN</div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">Zebrano</div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-white">{totals.current.toFixed(2)} PLN</div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">Pozostało</div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-white">{(totals.target - totals.current).toFixed(2)} PLN</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {isLoading ? (
          <div className="card p-6 text-center text-gray-500 dark:text-gray-400">Ładowanie...</div>
        ) : error ? (
          <div className="card p-6 text-center text-danger-600">{error}</div>
        ) : items.length === 0 ? (
          <div className="card p-6 text-center text-gray-500 dark:text-gray-400">Brak danych</div>
        ) : (
          items.map((g) => {
            const pct = Number(g.progress_percentage || ((Number(g.current_amount||0)/Number(g.target_amount||1))*100));
            const goalStats = statistics[g.id];
            const currentAmount = Number(g.current_amount || 0);
            const targetAmount = Number(g.target_amount || 0);
            const remaining = targetAmount - currentAmount;
            const isCompleted = Boolean(g.is_completed);
            const isActive = g.is_active !== false; // Default to true if not specified
            
            return (
              <div key={g.id} className="card p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="text-lg font-semibold text-gray-900 dark:text-white">{g.name}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-300">Konto: {g.account?.name}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-300">Termin: {(g.target_date||'').slice(0,10)}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-500 dark:text-gray-400">Cel</div>
                    <div className="text-xl font-semibold text-gray-900 dark:text-white">{Number(g.target_amount).toFixed(2)} PLN</div>
                  </div>
                </div>

                <div className="mt-4">
                  <div className="flex items-center justify-between mb-1 text-sm">
                    <span className="text-gray-600 dark:text-gray-300">Postęp</span>
                    <span className="font-medium text-gray-900 dark:text-white">{pct.toFixed(0)}%</span>
                  </div>
                  <ProgressBar value={pct} />
                  <div className="mt-1 text-sm text-gray-600 dark:text-gray-300">
                    Zebrano: {Number(g.current_amount || 0).toFixed(2)} PLN
                    {remaining > 0 && ` / Pozostało: ${remaining.toFixed(2)} PLN`}
                  </div>
                </div>

                {/* Statystyki wpłat */}
                {goalStats && goalStats.completed_payments > 0 && (
                  <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
                    <div className="flex items-center gap-2 text-sm text-blue-800 dark:text-blue-300">
                      <TrendingUp className="h-4 w-4" />
                      <span className="font-medium">Statystyki wpłat:</span>
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-blue-700 dark:text-blue-300">
                      <div>
                        <span className="font-medium">Łączna kwota:</span> {Number(goalStats.completed_amount).toFixed(2)} PLN
                      </div>
                      <div>
                        <span className="font-medium">Liczba transakcji:</span> {goalStats.completed_payments}
                      </div>
                    </div>
                  </div>
                )}

                {/* Przyciski szybkich wpłat */}
                {!isCompleted && remaining > 0 && isActive && (
                  <div className="mt-4">
                    <div className="text-sm text-gray-600 dark:text-gray-300 mb-2">Szybka wpłata:</div>
                    <div className="flex flex-wrap gap-2">
                      {quickAmounts
                        .filter(amount => amount <= remaining)
                        .slice(0, 4)
                        .map((amount) => (
                          <button
                            key={amount}
                            onClick={() => handlePayment(g, amount)}
                            className="btn-primary text-sm px-3 py-1.5 inline-flex items-center"
                          >
                            <DollarSign className="h-3 w-3 mr-1" />
                            Wpłać {amount} PLN
                          </button>
                        ))}
                      {remaining > quickAmounts[quickAmounts.length - 1] && (
                        <button
                          onClick={() => handlePayment(g, Math.min(remaining, 5000))}
                          className="btn-secondary text-sm px-3 py-1.5"
                        >
                          Wpłać {Math.min(remaining, 5000).toFixed(0)} PLN
                        </button>
                      )}
                    </div>
                  </div>
                )}

                <div className="mt-4 flex flex-wrap gap-3 justify-end items-center">
                  <button onClick={() => onEdit(g)} className="text-primary-600 hover:text-primary-700 text-sm">
                    Edytuj
                  </button>
                  <button onClick={() => onDelete(g)} className="text-danger-600 hover:text-danger-700 text-sm">
                    Usuń
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      <GoalModal
        open={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setEditing(null);
        }}
        onSubmit={submitGoal}
        accounts={accounts}
        initialData={editing}
      />
    </div>
  );
};

export default SavingsGoals;
