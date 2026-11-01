import { OracleResult, Market } from '../types';

interface AllMarketsViewProps {
  analysis: { market: Market; oracle: OracleResult; edge: number }[];
  threshold: number;
}

export function AllMarketsView({ analysis, threshold }: AllMarketsViewProps) {
  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-300">
          📊 Полный анализ всех рынков
        </h2>
        <span className="text-sm text-gray-500">
          Порог: {(threshold * 100).toFixed(0)}% | Показано: {analysis.length}
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="text-left py-3 px-4 text-gray-500 font-medium">Рынок</th>
              <th className="text-center py-3 px-2 text-gray-500 font-medium">Актив</th>
              <th className="text-center py-3 px-2 text-gray-500 font-medium">Рынок %</th>
              <th className="text-center py-3 px-2 text-gray-500 font-medium">Оракул %</th>
              <th className="text-center py-3 px-2 text-gray-500 font-medium">Edge</th>
              <th className="text-center py-3 px-2 text-gray-500 font-medium">Объём</th>
              <th className="text-center py-3 px-2 text-gray-500 font-medium">Дней</th>
              <th className="text-center py-3 px-2 text-gray-500 font-medium">Статус</th>
            </tr>
          </thead>
          <tbody>
            {analysis.map(({ market, oracle, edge }) => {
              const absEdge = Math.abs(edge);
              const isOpportunity = absEdge >= threshold;
              const marketPct = (market.implied_probability * 100).toFixed(1);
              const oraclePct = (oracle.oracle_probability * 100).toFixed(1);
              const edgePct = (edge * 100).toFixed(1);

              return (
                <tr
                  key={market.id}
                  className={`border-b border-gray-800/50 transition-colors ${
                    isOpportunity
                      ? 'bg-emerald-950/20 hover:bg-emerald-950/30'
                      : 'hover:bg-gray-800/30'
                  }`}
                >
                  <td className="py-3 px-4">
                    <div className="max-w-xs">
                      <p className="text-gray-300 text-xs leading-tight truncate" title={market.question}>
                        {market.question}
                      </p>
                    </div>
                  </td>
                  <td className="text-center py-3 px-2">
                    <span className="text-xs font-mono bg-gray-800 px-2 py-0.5 rounded">
                      {market.asset}
                    </span>
                  </td>
                  <td className="text-center py-3 px-2 font-mono text-gray-400">
                    {marketPct}%
                  </td>
                  <td className="text-center py-3 px-2 font-mono text-cyan-400">
                    {oraclePct}%
                  </td>
                  <td className="text-center py-3 px-2">
                    <span className={`font-mono font-bold ${
                      edge > 0 ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                      {edge > 0 ? '+' : ''}{edgePct}%
                    </span>
                  </td>
                  <td className="text-center py-3 px-2 text-gray-500 font-mono text-xs">
                    ${formatVolume(market.volume)}
                  </td>
                  <td className="text-center py-3 px-2 text-gray-500 font-mono text-xs">
                    {oracle.daysToExpiry}
                  </td>
                  <td className="text-center py-3 px-2">
                    {isOpportunity ? (
                      <span className="text-xs bg-emerald-900/50 text-emerald-400 px-2 py-1 rounded-full">
                        🔥 ARB
                      </span>
                    ) : (
                      <span className="text-xs text-gray-600">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-6 p-4 rounded-xl bg-gray-900 border border-gray-800">
        <h3 className="text-sm font-medium text-gray-400 mb-2">📖 Как читать таблицу</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-gray-500">
          <p>• <span className="text-emerald-400">Edge &gt; 0</span> — Оракул считает вероятность ВЫШЕ рынка → BUY YES</p>
          <p>• <span className="text-red-400">Edge &lt; 0</span> — Оракул считает вероятность НИЖЕ рынка → BUY NO</p>
          <p>• <span className="text-emerald-400">🔥 ARB</span> — Абсолютный edge превышает порог ({(threshold * 100).toFixed(0)}%)</p>
          <p>• Объём — суммарный объём торгов на рынке (USD)</p>
        </div>
      </div>
    </div>
  );
}

function formatVolume(volume: number): string {
  if (volume >= 1_000_000) return `${(volume / 1_000_000).toFixed(1)}M`;
  if (volume >= 1_000) return `${(volume / 1_000).toFixed(0)}K`;
  return volume.toFixed(0);
}
