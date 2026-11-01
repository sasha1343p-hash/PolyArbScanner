import { ArbitrageOpportunity, Filters } from '../types';

interface OpportunitiesTableProps {
  opportunities: ArbitrageOpportunity[];
  filters: Filters;
  onFiltersChange: (filters: Filters) => void;
  onSelectMarket: (id: string | null) => void;
  selectedMarketId: string | null;
}

const categoryIcons: Record<string, string> = {
  crypto: '₿',
  politics: '🏛',
  sports: '⚽',
  culture: '🎬',
};

const categoryLabels: Record<string, string> = {
  crypto: 'Крипто',
  politics: 'Политика',
  sports: 'Спорт',
  culture: 'Культура',
};

export function OpportunitiesTable({
  opportunities,
  onSelectMarket,
  selectedMarketId,
}: OpportunitiesTableProps) {
  if (opportunities.length === 0) {
    return (
      <div className="rounded-xl border border-gray-800/50 bg-gray-900/30 p-12 text-center">
        <div className="text-4xl mb-3">🔍</div>
        <h3 className="text-lg text-gray-400 mb-1">Нет результатов</h3>
        <p className="text-sm text-gray-600">Попробуйте изменить фильтры или снизить порог Edge</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-800/50 bg-gray-900/30 overflow-hidden">
      {/* Table Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800/50 bg-gray-900/50">
        <h3 className="text-sm font-semibold text-gray-300">
          🔥 Возможности ({opportunities.length})
        </h3>
        <div className="text-xs text-gray-600">
          Кликните на строку для деталей
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800/30">
              <th className="text-left py-3 px-4 text-[10px] uppercase tracking-wider text-gray-500 font-medium">Рынок</th>
              <th className="text-center py-3 px-2 text-[10px] uppercase tracking-wider text-gray-500 font-medium">Кат.</th>
              <th className="text-center py-3 px-2 text-[10px] uppercase tracking-wider text-gray-500 font-medium">Рынок</th>
              <th className="text-center py-3 px-2 text-[10px] uppercase tracking-wider text-gray-500 font-medium">Оракул</th>
              <th className="text-center py-3 px-2 text-[10px] uppercase tracking-wider text-gray-500 font-medium">Edge</th>
              <th className="text-center py-3 px-2 text-[10px] uppercase tracking-wider text-gray-500 font-medium">Объём</th>
              <th className="text-center py-3 px-2 text-[10px] uppercase tracking-wider text-gray-500 font-medium">Действие</th>
            </tr>
          </thead>
          <tbody>
            {opportunities.map((opp, idx) => {
              const isSelected = selectedMarketId === opp.market.id;
              const marketPct = (opp.market.implied_probability * 100).toFixed(1);
              const oraclePct = (opp.oracle.oracle_probability * 100).toFixed(1);
              const edgePct = (opp.edge * 100).toFixed(1);
              const isPositive = opp.edge > 0;

              return (
                <tr
                  key={opp.market.id}
                  onClick={() => onSelectMarket(isSelected ? null : opp.market.id)}
                  className={`border-b border-gray-800/20 cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-emerald-950/30 border-l-2 border-l-emerald-500'
                      : 'hover:bg-gray-800/30 border-l-2 border-l-transparent'
                  }`}
                  style={{ animationDelay: `${idx * 30}ms` }}
                >
                  <td className="py-3 px-4">
                    <div className="max-w-[280px]">
                      <p className="text-gray-200 text-xs leading-tight truncate" title={opp.market.question}>
                        {opp.market.question}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                          opp.severity === 'high' ? 'bg-red-900/40 text-red-400' :
                          opp.severity === 'medium' ? 'bg-amber-900/40 text-amber-400' :
                          'bg-yellow-900/40 text-yellow-400'
                        }`}>
                          {opp.severity === 'high' ? '🔴 HIGH' : opp.severity === 'medium' ? '🟡 MED' : '🟢 LOW'}
                        </span>
                        {opp.oracle.daysToExpiry && (
                          <span className="text-[10px] text-gray-600">
                            {opp.oracle.daysToExpiry}д
                          </span>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="text-center py-3 px-2">
                    <span className="text-xs" title={categoryLabels[opp.market.category]}>
                      {categoryIcons[opp.market.category]}
                    </span>
                  </td>
                  <td className="text-center py-3 px-2">
                    <span className="font-mono text-xs text-gray-400">{marketPct}%</span>
                  </td>
                  <td className="text-center py-3 px-2">
                    <span className="font-mono text-xs text-cyan-400">{oraclePct}%</span>
                  </td>
                  <td className="text-center py-3 px-2">
                    <span className={`font-mono text-xs font-bold ${
                      isPositive ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                      {isPositive ? '+' : ''}{edgePct}%
                    </span>
                  </td>
                  <td className="text-center py-3 px-2">
                    <span className="font-mono text-[10px] text-gray-500">
                      ${formatVolume(opp.market.volume)}
                    </span>
                  </td>
                  <td className="text-center py-3 px-2">
                    <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-1 rounded-md ${
                      opp.recommendation === 'BUY YES'
                        ? 'bg-emerald-900/40 text-emerald-400 border border-emerald-700/30'
                        : 'bg-red-900/40 text-red-400 border border-red-700/30'
                    }`}>
                      {opp.recommendation === 'BUY YES' ? '▲' : '▼'} {opp.recommendation}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatVolume(volume: number): string {
  if (volume >= 1_000_000) return `${(volume / 1_000_000).toFixed(1)}M`;
  if (volume >= 1_000) return `${(volume / 1_000).toFixed(0)}K`;
  return volume.toFixed(0);
}
