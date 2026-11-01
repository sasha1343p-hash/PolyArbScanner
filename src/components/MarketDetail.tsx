import { Market, OracleResult } from '../types';

interface MarketDetailProps {
  market: Market;
  oracle: OracleResult;
  edge: number;
  onClose: () => void;
}

export function MarketDetail({ market, oracle, edge, onClose }: MarketDetailProps) {
  const marketPct = (market.implied_probability * 100).toFixed(1);
  const oraclePct = (oracle.oracle_probability * 100).toFixed(1);
  const edgePct = (edge * 100).toFixed(1);
  const isPositive = edge > 0;

  return (
    <div className="rounded-xl border border-emerald-800/40 bg-gradient-to-br from-emerald-950/20 to-gray-900/50 overflow-hidden animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between px-5 py-4 border-b border-gray-800/50">
        <div className="flex-1 pr-4">
          <h3 className="text-sm font-semibold text-white leading-tight">{market.question}</h3>
          <div className="flex items-center gap-3 mt-2">
            <span className="text-xs text-gray-500">ID: <code className="text-gray-400">{market.id}</code></span>
            <span className="text-xs text-gray-500">Категория: <span className="text-gray-400 capitalize">{market.category}</span></span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-gray-500 hover:text-white hover:bg-gray-800 transition-all"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Left: Probabilities */}
        <div className="space-y-4">
          <h4 className="text-xs uppercase tracking-wider text-gray-500 font-medium">Сравнение вероятностей</h4>
          
          {/* Visual comparison */}
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-gray-400">Рынок (Polymarket)</span>
                <span className="font-mono text-gray-300">{marketPct}%</span>
              </div>
              <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-gray-600 to-gray-500 rounded-full transition-all duration-500"
                  style={{ width: `${marketPct}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-cyan-400">Оракул (наш расчёт)</span>
                <span className="font-mono text-cyan-400">{oraclePct}%</span>
              </div>
              <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-cyan-600 to-cyan-400 rounded-full transition-all duration-500"
                  style={{ width: `${oraclePct}%` }}
                />
              </div>
            </div>
          </div>

          {/* Edge indicator */}
          <div className={`p-3 rounded-lg border ${
            isPositive ? 'bg-emerald-950/30 border-emerald-800/40' : 'bg-red-950/30 border-red-800/40'
          }`}>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">Расхождение (Edge)</span>
              <span className={`text-lg font-bold font-mono ${
                isPositive ? 'text-emerald-400' : 'text-red-400'
              }`}>
                {isPositive ? '+' : ''}{edgePct}%
              </span>
            </div>
            <p className="text-[10px] text-gray-500 mt-1">
              {isPositive
                ? 'Рынок недооценивает вероятность → BUY YES'
                : 'Рынок переоценивает вероятность → BUY NO'}
            </p>
          </div>
        </div>

        {/* Right: Details */}
        <div className="space-y-4">
          <h4 className="text-xs uppercase tracking-wider text-gray-500 font-medium">Детали</h4>
          
          <div className="grid grid-cols-2 gap-3">
            <DetailItem label="Объём торгов" value={`$${formatVolume(market.volume)}`} />
            <DetailItem label="До экспирации" value={oracle.daysToExpiry ? `${oracle.daysToExpiry} дн.` : '—'} />
            {oracle.currentPrice && (
              <DetailItem label="Текущая цена" value={`$${oracle.currentPrice.toLocaleString()}`} />
            )}
            <DetailItem label="Уверенность" value={`${(oracle.confidence * 100).toFixed(0)}%`} />
          </div>

          {/* Reasoning */}
          <div className="p-3 rounded-lg bg-gray-800/30 border border-gray-800/50">
            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Обоснование оракула</div>
            <p className="text-xs text-gray-300 leading-relaxed">{oracle.reasoning}</p>
          </div>

          {/* Disclaimer */}
          <div className="p-2 rounded-lg bg-amber-950/20 border border-amber-800/30">
            <p className="text-[10px] text-amber-400/70 leading-relaxed">
              ⚠️ Это автоматическая оценка, не финансовый совет. Всегда проводите собственный анализ перед принятием решений.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-2.5 rounded-lg bg-gray-800/30 border border-gray-800/30">
      <div className="text-[10px] text-gray-500 uppercase tracking-wider">{label}</div>
      <div className="text-sm font-mono text-gray-200 mt-0.5">{value}</div>
    </div>
  );
}

function formatVolume(volume: number): string {
  if (volume >= 1_000_000) return `${(volume / 1_000_000).toFixed(2)}M`;
  if (volume >= 1_000) return `${(volume / 1_000).toFixed(0)}K`;
  return volume.toFixed(0);
}
