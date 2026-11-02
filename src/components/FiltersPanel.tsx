import { Filters, MarketCategory } from '../types';

interface FiltersPanelProps {
  filters: Filters;
  onFiltersChange: (filters: Filters) => void;
}

const categories: { value: MarketCategory | 'all'; label: string; icon: string }[] = [
  { value: 'all', label: 'Все категории', icon: '🌐' },
  { value: 'crypto', label: 'Крипто', icon: '₿' },
  { value: 'politics', label: 'Политика', icon: '🏛' },
  { value: 'sports', label: 'Спорт', icon: '⚽' },
  { value: 'culture', label: 'Культура', icon: '🎬' },
];

const sortOptions: { value: Filters['sortBy']; label: string }[] = [
  { value: 'edge', label: 'Edge (расхождение)' },
  { value: 'volume', label: 'Объём торгов' },
  { value: 'market_price', label: 'Цена рынка' },
  { value: 'oracle_price', label: 'Оценка оракула' },
  { value: 'expiry', label: 'Срок экспирации' },
];

export function FiltersPanel({ filters, onFiltersChange }: FiltersPanelProps) {
  const update = (partial: Partial<Filters>) => {
    onFiltersChange({ ...filters, ...partial });
  };

  return (
    <div className="rounded-xl border border-gray-800/50 bg-gray-900/50 p-5 space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-300">Фильтры</h3>
        <button
          onClick={() => onFiltersChange({
            category: 'all',
            minVolume: 0,
            minEdge: 0.10,
            sortBy: 'edge',
            sortDir: 'desc',
          })}
          className="text-[10px] text-gray-500 hover:text-gray-300 transition-colors"
        >
          Сбросить
        </button>
      </div>

      {/* Category Filter */}
      <div>
        <label className="text-xs text-gray-500 uppercase tracking-wider font-medium mb-2 block">
          Категория
        </label>
        <div className="space-y-1">
          {categories.map((cat) => (
            <button
              key={cat.value}
              onClick={() => update({ category: cat.value })}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all ${
                filters.category === cat.value
                  ? 'bg-emerald-900/30 text-emerald-400 border border-emerald-700/40'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50 border border-transparent'
              }`}
            >
              <span className="text-base">{cat.icon}</span>
              <span>{cat.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Min Edge */}
      <div>
        <label className="text-xs text-gray-500 uppercase tracking-wider font-medium mb-2 block">
          Мин. Edge
        </label>
        <div className="flex items-center gap-3">
          <input
            type="range"
            min="0.01"
            max="0.40"
            step="0.01"
            value={filters.minEdge}
            onChange={(e) => update({ minEdge: parseFloat(e.target.value) })}
            className="flex-1 accent-emerald-500"
          />
          <span className="text-sm font-mono text-emerald-400 w-12 text-right">
            {(filters.minEdge * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Min Volume */}
      <div>
        <label className="text-xs text-gray-500 uppercase tracking-wider font-medium mb-2 block">
          Мин. объём
        </label>
        <div className="flex items-center gap-3">
          <input
            type="range"
            min="0"
            max="5000000"
            step="100000"
            value={filters.minVolume}
            onChange={(e) => update({ minVolume: parseInt(e.target.value) })}
            className="flex-1 accent-emerald-500"
          />
          <span className="text-sm font-mono text-purple-400 w-12 text-right">
            {filters.minVolume >= 1000000
              ? `${(filters.minVolume / 1000000).toFixed(1)}M`
              : filters.minVolume >= 1000
              ? `${(filters.minVolume / 1000).toFixed(0)}K`
              : '0'}
          </span>
        </div>
      </div>

      {/* Sort */}
      <div>
        <label className="text-xs text-gray-500 uppercase tracking-wider font-medium mb-2 block">
          Сортировка
        </label>
        <select
          value={filters.sortBy}
          onChange={(e) => update({ sortBy: e.target.value as Filters['sortBy'] })}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-emerald-600 transition-colors"
        >
          {sortOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <div className="flex gap-1 mt-2">
          <button
            onClick={() => update({ sortDir: 'desc' })}
            className={`flex-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              filters.sortDir === 'desc'
                ? 'bg-gray-700 text-white border border-gray-600'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            ↓ По убыванию
          </button>
          <button
            onClick={() => update({ sortDir: 'asc' })}
            className={`flex-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              filters.sortDir === 'asc'
                ? 'bg-gray-700 text-white border border-gray-600'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            ↑ По возрастанию
          </button>
        </div>
      </div>

      {/* Info */}
      <div className="pt-3 border-t border-gray-800/50">
        <p className="text-[10px] text-gray-600 leading-relaxed">
          💡 Edge — разница между оценкой оракула и ценой рынка. Положительный edge означает, что рынок недооценивает событие (BUY YES), отрицательный — переоценивает (BUY NO).
        </p>
      </div>
    </div>
  );
}
