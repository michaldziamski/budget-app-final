import React, { useEffect, useMemo, useState } from 'react';
import { transactionsAPI, accountsAPI, categoriesAPI } from '../services/api';
import { AlertCircle, Plus, X } from 'lucide-react';
import toast from 'react-hot-toast';
import * as FaIcons from 'react-icons/fa';
import * as Fa6Icons from 'react-icons/fa6';

// Funkcja pomocnicza do renderowania ikony Font Awesome
const renderIcon = (iconClass) => {
  if (!iconClass || typeof iconClass !== 'string') return null;
  
  try {
    // Parsuj klasę ikony (np. "fas fa-utensils" -> "FaUtensils")
    const parts = iconClass.trim().split(' ');
    if (parts.length >= 2) {
      // Znajdź część z "fa-" (np. "fa-utensils")
      const faPart = parts.find(p => p.startsWith('fa-'));
      if (faPart) {
        const iconName = faPart
          .replace('fa-', '')
          .split('-')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join('');
        
        // Spróbuj znaleźć ikonę w Font Awesome 6 (nowsze)
        const Fa6Icon = Fa6Icons[`Fa${iconName}`];
        if (Fa6Icon) return React.createElement(Fa6Icon);
        
        // Spróbuj znaleźć ikonę w Font Awesome 5
        const FaIcon = FaIcons[`Fa${iconName}`];
        if (FaIcon) return React.createElement(FaIcon);
      }
    }
  } catch (e) {
    // Jeśli nie uda się znaleźć ikony, zwróć null
    console.warn('Nie udało się znaleźć ikony:', iconClass, e);
  }
  
  return null;
};

// Komponent wizualnego selektora kategorii z ikonami
const CategoryIconSelector = ({ categories, selectedCategory, onSelect, transactionType }) => {
  // Filtruj kategorie według typu transakcji
  const filteredCategories = categories.filter(cat => {
    if (transactionType === 'expense') return cat.category_type === 'expense';
    if (transactionType === 'income') return cat.category_type === 'income';
    return true;
  });

  return (
    <div className="md:col-span-2">
      <label className="label mb-2">Kategoria</label>
      {filteredCategories.length === 0 ? (
        <div className="text-sm text-gray-500 dark:text-gray-400 p-3 border border-gray-200 dark:border-gray-700 rounded">
          Brak kategorii dla tego typu transakcji
        </div>
      ) : (
        <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2 max-h-64 overflow-y-auto p-2 border border-gray-200 dark:border-gray-700 rounded">
          <button
            type="button"
            onClick={() => onSelect('')}
            className={`flex flex-col items-center justify-center p-3 rounded-lg border-2 transition-all ${
              selectedCategory === ''
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <div className="text-gray-400 text-xs mb-1">Brak</div>
          </button>
          {filteredCategories.map((cat) => {
            const Icon = renderIcon(cat.icon);
            const isSelected = selectedCategory === cat.id;
            return (
              <button
                key={cat.id}
                type="button"
                onClick={() => onSelect(cat.id)}
                className={`flex flex-col items-center justify-center p-3 rounded-lg border-2 transition-all ${
                  isSelected
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
                title={cat.name}
              >
                {Icon ? (
                  <div 
                    className="text-2xl mb-1"
                    style={{ color: cat.color || '#3498db' }}
                  >
                    {Icon}
                  </div>
                ) : (
                  <div 
                    className="w-6 h-6 rounded-full mb-1"
                    style={{ backgroundColor: cat.color || '#3498db' }}
                  />
                )}
                <div className="text-xs text-gray-600 dark:text-gray-400 truncate w-full text-center">
                  {cat.name}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

const TransactionRow = ({ tx, onEdit, onDelete }) => {
  // Fallback: użyj obiektu category/account lub nazwy, jeśli obiekt nie jest dostępny
  const category = tx.category || (tx.category_name ? { name: tx.category_name } : null);
  const account = tx.account || (tx.account_name ? { name: tx.account_name } : null);
  
  // Renderuj ikonę kategorii
  const categoryIcon = category?.icon ? renderIcon(category.icon) : null;
  const categoryColor = category?.color || '#3498db';
  
  return (
    <tr className="border-b dark:border-gray-700 last:border-0">
      <td className="py-2 px-3 text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap">{new Date(tx.date).toLocaleDateString()}</td>
      <td className="py-2 px-3 text-sm font-medium text-gray-900 dark:text-white">{tx.description}</td>
      <td className="py-2 px-3 text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap">{tx.transaction_type === 'income' ? 'Przychód' : tx.transaction_type === 'expense' ? 'Wydatek' : 'Transfer'}</td>
      <td className="py-2 px-3 text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap">
        {category ? (
          <span className="inline-flex items-center gap-2">
            {categoryIcon && (
              <span style={{ color: categoryColor }} className="text-lg">
                {categoryIcon}
              </span>
            )}
            <span>{category.name || tx.category_name || '-'}</span>
          </span>
        ) : (
          '-'
        )}
      </td>
      <td className="py-2 px-3 text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap">
        {tx.transaction_type === 'transfer' && tx.transfer_to_account ? (
          <span>
            {account?.name || tx.account_name || '-'} → {tx.transfer_to_account?.name || tx.transfer_to_account_name || '-'}
          </span>
        ) : (
          account?.name || tx.account_name || '-'
        )}
      </td>
      <td className="py-2 px-3 text-sm text-gray-900 dark:text-white text-right whitespace-nowrap">{Number(tx.amount).toFixed(2)} PLN</td>
      <td className="py-2 px-3 text-right whitespace-nowrap">
        <button onClick={() => onEdit(tx)} className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 mr-3">Edytuj</button>
        <button onClick={() => onDelete(tx)} className="text-danger-600 hover:text-danger-700 dark:text-danger-400 dark:hover:text-danger-300">Usuń</button>
      </td>
    </tr>
  );
};

const TransactionModal = ({ open, onClose, onSubmit, accounts, categories, initialData }) => {
  const [form, setForm] = useState(() => initialData || {
    amount: '',
    transaction_type: 'expense',
    account: '',
    transfer_to_account: '',
    category: '',
    description: '',
    date: new Date().toISOString().slice(0, 10),
  });

  useEffect(() => {
    setForm(initialData || {
      amount: '',
      transaction_type: 'expense',
      account: '',
      transfer_to_account: '',
      category: '',
      description: '',
      date: new Date().toISOString().slice(0, 10),
    });
  }, [initialData, open]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // Walidacja ujemnych kwot
    if (name === 'amount' && value !== '' && Number(value) < 0) {
      toast.error('Nie można wprowadzić ujemnej kwoty');
      return;
    }
    
    // Gdy zmienia się typ transakcji, wyczyść transfer_to_account jeśli nie jest transferem
    if (name === 'transaction_type' && value !== 'transfer') {
      setForm((p) => ({ ...p, [name]: value, transfer_to_account: '' }));
    } else {
      setForm((p) => ({ ...p, [name]: value }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Walidacja przed wysłaniem
    if (form.amount !== '' && Number(form.amount) < 0) {
      toast.error('Nie można wprowadzić ujemnej kwoty');
      return;
    }
    
    // Walidacja transferu
    if (form.transaction_type === 'transfer') {
      if (!form.transfer_to_account) {
        toast.error('Wybierz konto docelowe dla transferu');
        return;
      }
      if (form.account === form.transfer_to_account) {
        toast.error('Nie można transferować na to samo konto');
        return;
      }
    }
    
    await onSubmit(form);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 dark:bg-black/60">
      <div className="bg-white dark:bg-gray-800 w-full max-w-xl rounded-lg shadow-strong">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{initialData ? 'Edytuj transakcję' : 'Dodaj transakcję'}</h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
            <X className="h-5 w-5 text-gray-600 dark:text-gray-300" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Kwota</label>
            <input type="number" step="0.01" name="amount" value={form.amount} onChange={handleChange} className="input-field" required />
          </div>

          <div>
            <label className="label">Typ</label>
            <select name="transaction_type" value={form.transaction_type} onChange={handleChange} className="input-field">
              <option value="expense">Wydatek</option>
              <option value="income">Przychód</option>
              <option value="transfer">Transfer</option>
            </select>
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

          {form.transaction_type === 'transfer' && (
            <div>
              <label className="label">Konto docelowe</label>
              <select 
                name="transfer_to_account" 
                value={form.transfer_to_account} 
                onChange={handleChange} 
                className="input-field" 
                required
              >
                <option value="">Wybierz konto docelowe</option>
                {accounts
                  .filter((a) => a.id !== form.account) // Wyklucz konto źródłowe
                  .map((a) => (
                    <option key={a.id} value={a.id}>{a.name}</option>
                  ))}
              </select>
            </div>
          )}

          {form.transaction_type !== 'transfer' && (
            <CategoryIconSelector
              categories={categories}
              selectedCategory={form.category}
              onSelect={(categoryId) => setForm((p) => ({ ...p, category: categoryId }))}
              transactionType={form.transaction_type}
            />
          )}

          <div className="md:col-span-2">
            <label className="label">Opis</label>
            <input type="text" name="description" value={form.description} onChange={handleChange} className="input-field" required />
          </div>

          <div>
            <label className="label">Data</label>
            <input type="date" name="date" value={form.date} onChange={handleChange} className="input-field" required />
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

const Transactions = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [items, setItems] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [filters, setFilters] = useState({ search: '', account: '', category: '', type: '', date_from: '', date_to: '' });
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);

  const loadBasics = async () => {
    const [{ data: acc }, { data: cat }] = await Promise.all([
      accountsAPI.getAccounts({ is_active: true }),
      categoriesAPI.getCategories({ is_active: true }),
    ]);
    setAccounts(acc?.results || acc || []);
    setCategories(cat?.results || cat || []);
  };

  const loadTransactions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await transactionsAPI.getTransactions({
        search: filters.search || undefined,
        account: filters.account || undefined,
        category: filters.category || undefined,
        type: filters.type || undefined,
        date_from: filters.date_from || undefined,
        date_to: filters.date_to || undefined,
        ordering: '-date,-created_at',
      });
      const transactions = data?.results || data || [];
      setItems(transactions);
    } catch (e) {
      console.error('Błąd ładowania transakcji:', e);
      setError('Nie udało się pobrać transakcji');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    (async () => {
      try {
        await loadBasics();
      } finally {
        await loadTransactions();
      }
    })();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((p) => ({ ...p, [name]: value }));
  };

  const applyFilters = async (e) => {
    e?.preventDefault();
    await loadTransactions();
  };

  const onAdd = () => {
    setEditing(null);
    setModalOpen(true);
  };

  const onEdit = (tx) => {
    setEditing({
      id: tx.id,
      amount: tx.amount,
      transaction_type: tx.transaction_type,
      account: tx.account?.id || tx.account,
      transfer_to_account: tx.transfer_to_account?.id || tx.transfer_to_account || '',
      category: tx.category?.id || '',
      description: tx.description,
      date: tx.date?.slice(0, 10),
    });
    setModalOpen(true);
  };

  const onDelete = async (tx) => {
    if (!window.confirm('Usunąć transakcję?')) return;
    await transactionsAPI.deleteTransaction(tx.id);
    await loadTransactions();
  };

  const submitTransaction = async (form) => {
    const payload = {
      amount: form.amount,
      transaction_type: form.transaction_type,
      account: form.account,
      category: form.transaction_type === 'transfer' ? null : (form.category || null),
      description: form.description,
      date: new Date(form.date).toISOString(),
    };

    // Dodaj transfer_to_account tylko dla transferów
    if (form.transaction_type === 'transfer' && form.transfer_to_account) {
      payload.transfer_to_account = form.transfer_to_account;
    }

    if (editing?.id) {
      await transactionsAPI.updateTransaction(editing.id, payload);
    } else {
      await transactionsAPI.createTransaction(payload);
    }
    setModalOpen(false);
    setEditing(null);
    await loadTransactions();
    await loadBasics(); // Przeładuj konta, aby zaktualizować salda
  };

  const totalIncome = useMemo(() => items.filter(i => i.transaction_type === 'income').reduce((s, i) => s + Number(i.amount), 0), [items]);
  const totalExpense = useMemo(() => items.filter(i => i.transaction_type === 'expense').reduce((s, i) => s + Number(i.amount), 0), [items]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Transakcje</h2>
        <button onClick={onAdd} className="btn-primary inline-flex items-center">
          <Plus className="h-4 w-4 mr-2" /> Dodaj
        </button>
      </div>

      {/* Filters */}
      <form onSubmit={applyFilters} className="card p-4 grid grid-cols-1 md:grid-cols-6 gap-3">
        <input name="search" value={filters.search} onChange={onFilterChange} placeholder="Szukaj opisu..." className="input-field md:col-span-2" />
        <select name="account" value={filters.account} onChange={onFilterChange} className="input-field">
          <option value="">Konto: wszystkie</option>
          {accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
        </select>
        <select name="category" value={filters.category} onChange={onFilterChange} className="input-field">
          <option value="">Kategoria: wszystkie</option>
          {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select name="type" value={filters.type} onChange={onFilterChange} className="input-field">
          <option value="">Typ: wszystkie</option>
          <option value="expense">Wydatek</option>
          <option value="income">Przychód</option>
          <option value="transfer">Transfer</option>
        </select>
        <div className="grid grid-cols-2 gap-2">
          <input type="date" name="date_from" value={filters.date_from} onChange={onFilterChange} className="input-field" />
          <input type="date" name="date_to" value={filters.date_to} onChange={onFilterChange} className="input-field" />
        </div>
        <div className="md:col-span-6 flex justify-end">
          <button type="submit" className="btn-secondary">Filtruj</button>
        </div>
      </form>

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">Przychody</div>
          <div className="text-2xl font-semibold text-green-600">{totalIncome.toFixed(2)} PLN</div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">Wydatki</div>
          <div className="text-2xl font-semibold text-danger-600">{totalExpense.toFixed(2)} PLN</div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">Bilans</div>
          <div className={`text-2xl font-semibold ${totalIncome - totalExpense >= 0 ? 'text-green-600' : 'text-danger-600'}`}>{(totalIncome - totalExpense).toFixed(2)} PLN</div>
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Data</th>
                <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Opis</th>
                <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Typ</th>
                <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Kategoria</th>
                <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Konto</th>
                <th className="text-right py-2 px-3 text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Kwota</th>
                <th className="text-right py-2 px-3 text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Akcje</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-10 text-center text-gray-500 dark:text-gray-400">Ładowanie...</td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan={7} className="py-10 text-center text-danger-600 flex items-center justify-center gap-2">
                    <AlertCircle className="h-5 w-5" /> {error}
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-10 text-center text-gray-500 dark:text-gray-400">Brak danych</td>
                </tr>
              ) : (
                items.map((tx) => (
                  <TransactionRow key={tx.id} tx={tx} onEdit={onEdit} onDelete={onDelete} />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <TransactionModal
        open={modalOpen}
        onClose={() => { setModalOpen(false); setEditing(null); }}
        onSubmit={submitTransaction}
        accounts={accounts}
        categories={categories}
        initialData={editing}
      />
    </div>
  );
};

export default Transactions;


