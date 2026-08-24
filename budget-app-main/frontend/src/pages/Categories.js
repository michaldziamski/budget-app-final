import React, { useEffect, useMemo, useState } from 'react';
import { categoriesAPI } from '../services/api';
import { Plus, X } from 'lucide-react';
import * as FaIcons from 'react-icons/fa';
import * as Fa6Icons from 'react-icons/fa6';

// Popularne ikony do wyboru dla kategorii
const POPULAR_ICONS = [
  { class: 'fas fa-utensils', name: 'Jedzenie' },
  { class: 'fas fa-car', name: 'Transport' },
  { class: 'fas fa-home', name: 'Dom' },
  { class: 'fas fa-heartbeat', name: 'Zdrowie' },
  { class: 'fas fa-gamepad', name: 'Rozrywka' },
  { class: 'fas fa-tshirt', name: 'Ubrania' },
  { class: 'fas fa-graduation-cap', name: 'Edukacja' },
  { class: 'fas fa-file-invoice', name: 'Rachunki' },
  { class: 'fas fa-money-bill-wave', name: 'Pieniądze' },
  { class: 'fas fa-laptop', name: 'Praca' },
  { class: 'fas fa-chart-line', name: 'Inwestycje' },
  { class: 'fas fa-dumbbell', name: 'Sport' },
  { class: 'fas fa-gift', name: 'Prezenty' },
  { class: 'fas fa-coffee', name: 'Kawa' },
  { class: 'fas fa-plane', name: 'Podróże' },
  { class: 'fas fa-shopping-cart', name: 'Zakupy' },
  { class: 'fas fa-music', name: 'Muzyka' },
  { class: 'fas fa-book', name: 'Książki' },
  { class: 'fas fa-mobile-alt', name: 'Telefon' },
  { class: 'fas fa-wifi', name: 'Internet' },
  { class: 'fas fa-gas-pump', name: 'Paliwo' },
  { class: 'fas fa-paw', name: 'Zwierzęta' },
  { class: 'fas fa-baby', name: 'Dziecko' },
  { class: 'fas fa-tools', name: 'Narzędzia' },
  { class: 'fas fa-pills', name: 'Leki' },
];

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

// Komponent wizualnego selektora ikon
const IconSelector = ({ selectedIcon, onSelect, color }) => {
  const [showSelector, setShowSelector] = useState(false);

  return (
    <div className="md:col-span-2">
      <label className="label mb-2">Ikona</label>
      <div className="relative">
        <button
          type="button"
          onClick={() => setShowSelector(!showSelector)}
          className="w-full input-field flex items-center justify-between"
        >
          <div className="flex items-center gap-2">
            {selectedIcon ? (
              <>
                <span style={{ color: color || '#3498db' }}>
                  {renderIcon(selectedIcon)}
                </span>
                <span className="text-sm text-gray-600 dark:text-gray-400">{selectedIcon}</span>
              </>
            ) : (
              <span className="text-gray-500 dark:text-gray-400">Wybierz ikonę</span>
            )}
          </div>
          <span className="text-gray-400">▼</span>
        </button>
        
        {showSelector && (
          <>
            <div 
              className="fixed inset-0 z-40" 
              onClick={() => setShowSelector(false)}
            />
            <div className="absolute z-50 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-64 overflow-y-auto p-3">
              <div className="grid grid-cols-6 sm:grid-cols-8 gap-2">
                <button
                  type="button"
                  onClick={() => {
                    onSelect('');
                    setShowSelector(false);
                  }}
                  className={`flex flex-col items-center justify-center p-2 rounded border-2 ${
                    !selectedIcon
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }`}
                  title="Brak ikony"
                >
                  <span className="text-xs text-gray-500">Brak</span>
                </button>
                {POPULAR_ICONS.map((icon) => {
                  const Icon = renderIcon(icon.class);
                  const isSelected = selectedIcon === icon.class;
                  return (
                    <button
                      key={icon.class}
                      type="button"
                      onClick={() => {
                        onSelect(icon.class);
                        setShowSelector(false);
                      }}
                      className={`flex flex-col items-center justify-center p-2 rounded border-2 transition-all ${
                        isSelected
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }`}
                      title={icon.name}
                    >
                      {Icon ? (
                        <span 
                          className="text-xl mb-1"
                          style={{ color: color || '#3498db' }}
                        >
                          {Icon}
                        </span>
                      ) : (
                        <div 
                          className="w-5 h-5 rounded-full mb-1"
                          style={{ backgroundColor: color || '#3498db' }}
                        />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

const CategoryModal = ({ open, onClose, onSubmit, initialData }) => {
  const [form, setForm] = useState(() => initialData || {
    name: '',
    category_type: 'expense',
    color: '#3498db',
    icon: '',
    description: '',
  });

  useEffect(() => {
    setForm(initialData || {
      name: '',
      category_type: 'expense',
      color: '#3498db',
      icon: '',
      description: '',
    });
  }, [initialData, open]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((p) => ({ ...p, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await onSubmit(form);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 dark:bg-black/60">
      <div className="bg-white dark:bg-gray-800 w-full max-w-xl rounded-lg shadow-strong">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{initialData ? 'Edytuj kategorię' : 'Dodaj kategorię'}</h3>
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
            <label className="label">Typ</label>
            <select name="category_type" value={form.category_type} onChange={handleChange} className="input-field">
              <option value="expense">Wydatek</option>
              <option value="income">Przychód</option>
              <option value="transfer">Transfer</option>
            </select>
          </div>

          <div>
            <label className="label">Kolor</label>
            <input type="color" name="color" value={form.color} onChange={handleChange} className="input-field p-1 h-10" />
          </div>

          <IconSelector
            selectedIcon={form.icon}
            onSelect={(iconClass) => setForm((p) => ({ ...p, icon: iconClass }))}
            color={form.color}
          />

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

const Categories = () => {
  const [items, setItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({ search: '', type: '' });
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);

  const loadCategories = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await categoriesAPI.getCategories({
        search: filters.search || undefined,
        category_type: filters.type || undefined,
        ordering: 'name',
      });
      setItems(data?.results || data || []);
    } catch (e) {
      setError('Nie udało się pobrać kategorii');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { loadCategories(); // eslint-disable-next-line
  }, []);

  const onFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((p) => ({ ...p, [name]: value }));
  };

  const applyFilters = async (e) => {
    e?.preventDefault();
    await loadCategories();
  };

  const onAdd = () => { setEditing(null); setModalOpen(true); };
  const onEdit = (cat) => { setEditing(cat); setModalOpen(true); };
  const onDelete = async (cat) => {
    if (!window.confirm('Usunąć kategorię?')) return;
    await categoriesAPI.deleteCategory(cat.id);
    await loadCategories();
  };

  const submitCategory = async (form) => {
    const payload = {
      name: form.name,
      category_type: form.category_type,
      color: form.color || '#3498db',
      icon: form.icon || null,
      description: form.description || '',
    };
    if (editing?.id) {
      await categoriesAPI.updateCategory(editing.id, payload);
    } else {
      await categoriesAPI.createCategory(payload);
    }
    setModalOpen(false);
    setEditing(null);
    await loadCategories();
  };

  const counts = useMemo(() => ({
    expense: items.filter(i => i.category_type === 'expense').length,
    income: items.filter(i => i.category_type === 'income').length,
    transfer: items.filter(i => i.category_type === 'transfer').length,
  }), [items]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Kategorie</h2>
        <button onClick={onAdd} className="btn-primary inline-flex items-center"><Plus className="h-4 w-4 mr-2" /> Dodaj</button>
      </div>

      {/* Filters */}
      <form onSubmit={applyFilters} className="card p-4 grid grid-cols-1 md:grid-cols-4 gap-3">
        <input name="search" value={filters.search} onChange={onFilterChange} placeholder="Szukaj nazwy/opisu..." className="input-field md:col-span-2" />
        <select name="type" value={filters.type} onChange={onFilterChange} className="input-field">
          <option value="">Typ: wszystkie</option>
          <option value="expense">Wydatek</option>
          <option value="income">Przychód</option>
          <option value="transfer">Transfer</option>
        </select>
        <div className="flex items-center justify-end">
          <button type="submit" className="btn-secondary">Filtruj</button>
        </div>
      </form>

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4"><div className="text-sm text-gray-500 dark:text-gray-400">Wydatki</div><div className="text-2xl font-semibold text-gray-900 dark:text-white">{counts.expense}</div></div>
        <div className="card p-4"><div className="text-sm text-gray-500 dark:text-gray-400">Przychody</div><div className="text-2xl font-semibold text-gray-900 dark:text-white">{counts.income}</div></div>
        <div className="card p-4"><div className="text-sm text-gray-500 dark:text-gray-400">Transfery</div><div className="text-2xl font-semibold text-gray-900 dark:text-white">{counts.transfer}</div></div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Ikona</th>
                <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Nazwa</th>
                <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Typ</th>
                <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Kolor</th>
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
                items.map((c) => {
                  const catIcon = c.icon ? renderIcon(c.icon) : null;
                  const catColor = c.color || '#3498db';
                  return (
                    <tr key={c.id} className="border-b dark:border-gray-700 last:border-0">
                      <td className="py-2 px-3 text-sm text-gray-700 dark:text-gray-300">
                        {catIcon ? (
                          <span style={{ color: catColor }} className="text-xl">
                            {catIcon}
                          </span>
                        ) : (
                          <span className="inline-block w-5 h-5 rounded-full" style={{ backgroundColor: catColor }} />
                        )}
                      </td>
                      <td className="py-2 px-3 text-sm font-medium text-gray-900 dark:text-white">{c.name}</td>
                      <td className="py-2 px-3 text-sm text-gray-700 dark:text-gray-300">{c.category_type}</td>
                      <td className="py-2 px-3 text-sm text-gray-700 dark:text-gray-300">
                        <span className="inline-flex items-center gap-2">
                          <span className="inline-block w-4 h-4 rounded" style={{ backgroundColor: catColor }} />
                          {catColor}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-right whitespace-nowrap">
                        <button onClick={() => onEdit(c)} className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 mr-3">Edytuj</button>
                        <button onClick={() => onDelete(c)} className="text-danger-600 hover:text-danger-700 dark:text-danger-400 dark:hover:text-danger-300">Usuń</button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <CategoryModal open={modalOpen} onClose={() => { setModalOpen(false); setEditing(null); }} onSubmit={submitCategory} initialData={editing} />
    </div>
  );
};

export default Categories;


