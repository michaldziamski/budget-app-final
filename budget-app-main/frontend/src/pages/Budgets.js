import React, { useEffect, useMemo, useState } from 'react';
import { budgetsAPI, categoriesAPI } from '../services/api';
import { Plus, X } from 'lucide-react';
import toast from 'react-hot-toast';

const ProgressBar = ({ value }) => {
  const pct = Math.max(0, Math.min(100, Number(value || 0)));
  const color = pct >= 100 ? 'bg-danger-500' : pct >= 80 ? 'bg-warning-500' : 'bg-primary-500';
  return (
    <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
      <div className={`${color} h-3`} style={{ width: `${pct}%` }} />
    </div>
  );
};

const BudgetModal = ({ open, onClose, onSubmit, categories, initialData }) => {
  const [form, setForm] = useState(() => initialData || {
    name: '',
    category: '',
    amount: '',
    period: 'monthly',
    start_date: new Date().toISOString().slice(0, 10),
    end_date: new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).toISOString().slice(0, 10),
  });

  useEffect(() => {
    setForm(initialData || {
      name: '',
      category: '',
      amount: '',
      period: 'monthly',
      start_date: new Date().toISOString().slice(0, 10),
      end_date: new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).toISOString().slice(0, 10),
    });
  }, [initialData, open]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // Walidacja ujemnych kwot
    if (name === 'amount' && value !== '' && Number(value) < 0) {
      toast.error('Nie można wprowadzić ujemnej kwoty');
      return;
    }
    
    setForm((p) => ({ ...p, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Walidacja przed wysłaniem
    if (form.amount !== '' && Number(form.amount) < 0) {
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
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{initialData ? 'Edytuj budżet' : 'Dodaj budżet'}</h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
            <X className="h-5 w-5 text-gray-600 dark:text-gray-300" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="label">Nazwa</label>
            <input type="text" name="name" value={form.name} onChange={handleChange} className="input-field" required />
          </div>

          <div className="md:col-span-2">
            <label className="label">Kategoria</label>
            <select name="category" value={form.category} onChange={handleChange} className="input-field" required>
              <option value="">Wybierz kategorię</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Kwota</label>
            <input type="number" step="0.01" name="amount" value={form.amount} onChange={handleChange} className="input-field" required />
          </div>

          <div>
            <label className="label">Okres</label>
            <select name="period" value={form.period} onChange={handleChange} className="input-field">
              <option value="monthly">Miesięczny</option>
              <option value="weekly">Tygodniowy</option>
              <option value="yearly">Roczny</option>
            </select>
          </div>

          <div>
            <label className="label">Start</label>
            <input type="date" name="start_date" value={form.start_date} onChange={handleChange} className="input-field" required />
          </div>

          <div>
            <label className="label">Koniec</label>
            <input type="date" name="end_date" value={form.end_date} onChange={handleChange} className="input-field" required />
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

const Budgets = () => {
  const [items, setItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [categories, setCategories] = useState([]);

  const loadBasics = async () => {
    const { data } = await categoriesAPI.getCategories({ category_type: 'expense' });
    setCategories(data?.results || data || []);
  };

  const loadBudgets = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await budgetsAPI.getBudgets();
      setItems(data?.results || data || []);
    } catch (e) {
      setError('Nie udało się pobrać budżetów');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { (async () => { await loadBasics(); await loadBudgets(); })(); }, []);

  const onAdd = () => { setEditing(null); setModalOpen(true); };
  const onEdit = (b) => { setEditing({ ...b, category: b.category?.id }); setModalOpen(true); };
  const onDelete = async (b) => { if (!window.confirm('Usunąć budżet?')) return; await budgetsAPI.deleteBudget(b.id); await loadBudgets(); };

  const submitBudget = async (form) => {
    const payload = {
      name: form.name,
      category: form.category,
      amount: form.amount,
      period: form.period,
      start_date: form.start_date,
      end_date: form.end_date,
    };
    if (editing?.id) {
      await budgetsAPI.updateBudget(editing.id, payload);
    } else {
      await budgetsAPI.createBudget(payload);
    }
    setModalOpen(false);
    setEditing(null);
    await loadBudgets();
  };

  const totalPlanned = useMemo(() => items.reduce((s, i) => s + Number(i.amount || 0), 0), [items]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Budżety</h2>
        <button onClick={onAdd} className="btn-primary inline-flex items-center"><Plus className="h-4 w-4 mr-2" /> Dodaj</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">Liczba budżetów</div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-white">{items.length}</div>
        </div>
        <div className="card p-4 md:col-span-2">
          <div className="text-sm text-gray-500 dark:text-gray-400">Suma kwot</div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-white">{totalPlanned.toFixed(2)} PLN</div>
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
          items.map((b) => (
            <div key={b.id} className="card p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-lg font-semibold text-gray-900 dark:text-white">{b.name}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-300">Kategoria: {b.category?.name}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-300">Okres: {b.period}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-300">{b.start_date} — {b.end_date}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500 dark:text-gray-400">Kwota</div>
                  <div className="text-xl font-semibold text-gray-900 dark:text-white">{Number(b.amount).toFixed(2)} PLN</div>
                </div>
              </div>

              <div className="mt-4">
                <div className="flex items-center justify-between mb-1 text-sm">
                  <span className="text-gray-600 dark:text-gray-300">Wykorzystanie</span>
                  <span className="font-medium text-gray-900 dark:text-white">{Number(b.usage_percentage || 0).toFixed(0)}%</span>
                </div>
                <ProgressBar value={b.usage_percentage} />
                <div className="mt-1 text-sm text-gray-600 dark:text-gray-300">Wydano: {Number(b.spent_amount || 0).toFixed(2)} PLN, Pozostało: {Number(b.remaining_amount || 0).toFixed(2)} PLN</div>
              </div>

              <div className="mt-4 flex justify-end gap-3">
                <button onClick={() => onEdit(b)} className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300">Edytuj</button>
                <button onClick={() => onDelete(b)} className="text-danger-600 hover:text-danger-700 dark:text-danger-400 dark:hover:text-danger-300">Usuń</button>
              </div>
            </div>
          ))
        )}
      </div>

      <BudgetModal
        open={modalOpen}
        onClose={() => { setModalOpen(false); setEditing(null); }}
        onSubmit={submitBudget}
        categories={categories}
        initialData={editing}
      />
    </div>
  );
};

export default Budgets;


