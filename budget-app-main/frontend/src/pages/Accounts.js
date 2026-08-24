import React, { useEffect, useMemo, useState } from 'react';
import { accountsAPI } from '../services/api';
import { Plus, X } from 'lucide-react';
import toast from 'react-hot-toast';

const AccountModal = ({ open, onClose, onSubmit, initialData }) => {
  const [form, setForm] = useState(() => initialData || {
    name: '',
    account_type: 'bank',
    balance: 0,
    currency: 'PLN',
    description: '',
  });

  useEffect(() => {
    setForm(initialData || {
      name: '',
      account_type: 'bank',
      balance: 0,
      currency: 'PLN',
      description: '',
    });
  }, [initialData, open]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // Walidacja ujemnych kwot dla salda (dla kont kredytowych może być ujemne, ale dla innych nie)
    // Dla uproszczenia, blokujemy ujemne saldo dla wszystkich typów kont
    if (name === 'balance' && value !== '' && Number(value) < 0) {
      toast.error('Nie można wprowadzić ujemnej kwoty');
      return;
    }
    
    setForm((p) => ({ ...p, [name]: name === 'balance' ? Number(value) : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Walidacja przed wysłaniem
    if (form.balance !== '' && form.balance !== undefined && Number(form.balance) < 0) {
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
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{initialData ? 'Edytuj konto' : 'Dodaj konto'}</h3>
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
            <label className="label">Typ konta</label>
            <select name="account_type" value={form.account_type} onChange={handleChange} className="input-field">
              <option value="bank">Konto bankowe</option>
              <option value="cash">Gotówka</option>
              <option value="credit_card">Karta kredytowa</option>
              <option value="savings">Konto oszczędnościowe</option>
              <option value="investment">Inwestycje</option>
              <option value="other">Inne</option>
            </select>
          </div>

          <div>
            <label className="label">Saldo początkowe</label>
            <input type="number" step="0.01" name="balance" value={form.balance} onChange={handleChange} className="input-field" />
          </div>

          <div>
            <label className="label">Waluta</label>
            <input type="text" name="currency" value={form.currency} onChange={handleChange} className="input-field" />
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

const Accounts = () => {
  const [items, setItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);

  const loadAccounts = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await accountsAPI.getAccounts();
      setItems(data?.results || data || []);
    } catch (e) {
      setError('Nie udało się pobrać kont');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { loadAccounts(); }, []);

  const onAdd = () => { setEditing(null); setModalOpen(true); };
  const onEdit = (acc) => { setEditing(acc); setModalOpen(true); };
  const onDelete = async (acc) => {
    if (!window.confirm('Usunąć konto?')) return;
    await accountsAPI.deleteAccount(acc.id);
    await loadAccounts();
  };

  const submitAccount = async (form) => {
    const payload = {
      name: form.name,
      account_type: form.account_type,
      balance: form.balance,
      currency: form.currency,
      description: form.description || '',
    };
    if (editing?.id) {
      await accountsAPI.updateAccount(editing.id, payload);
    } else {
      await accountsAPI.createAccount(payload);
    }
    setModalOpen(false);
    setEditing(null);
    await loadAccounts();
  };

  const totalBalance = useMemo(() => items.reduce((s, a) => s + Number(a.balance || 0), 0), [items]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Konta</h2>
        <button onClick={onAdd} className="btn-primary inline-flex items-center"><Plus className="h-4 w-4 mr-2" /> Dodaj</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">Liczba kont</div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-white">{items.length}</div>
        </div>
        <div className="card p-4 md:col-span-2">
          <div className="text-sm text-gray-500 dark:text-gray-400">Suma sald (PLN)</div>
          <div className={`text-2xl font-semibold ${totalBalance >= 0 ? 'text-green-600' : 'text-danger-600'}`}>{totalBalance.toFixed(2)} PLN</div>
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Nazwa</th>
                <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Typ</th>
                <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Waluta</th>
                <th className="text-right py-2 px-3 text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Saldo</th>
                <th className="text-right py-2 px-3 text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Akcje</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={5} className="py-10 text-center text-gray-500 dark:text-gray-400">Ładowanie...</td></tr>
              ) : error ? (
                <tr><td colSpan={5} className="py-10 text-center text-danger-600">{error}</td></tr>
              ) : items.length === 0 ? (
                <tr><td colSpan={5} className="py-10 text-center text-gray-500 dark:text-gray-400">Brak danych</td></tr>
              ) : (
                items.map((a) => (
                  <tr key={a.id} className="border-b dark:border-gray-700 last:border-0">
                    <td className="py-2 px-3 text-sm font-medium text-gray-900 dark:text-white">{a.name}</td>
                    <td className="py-2 px-3 text-sm text-gray-700 dark:text-gray-300">{a.account_type}</td>
                    <td className="py-2 px-3 text-sm text-gray-700 dark:text-gray-300">{a.currency || 'PLN'}</td>
                    <td className="py-2 px-3 text-sm text-right text-gray-900 dark:text-white">{Number(a.balance || 0).toFixed(2)} PLN</td>
                    <td className="py-2 px-3 text-right whitespace-nowrap">
                      <button onClick={() => onEdit(a)} className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 mr-3">Edytuj</button>
                      <button onClick={() => onDelete(a)} className="text-danger-600 hover:text-danger-700 dark:text-danger-400 dark:hover:text-danger-300">Usuń</button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <AccountModal open={modalOpen} onClose={() => { setModalOpen(false); setEditing(null); }} onSubmit={submitAccount} initialData={editing} />
    </div>
  );
};

export default Accounts;


