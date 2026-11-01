import { ArbitrageOpportunity } from '../types';

interface DashboardProps {
  opportunities: ArbitrageOpportunity[];
  threshold: number;
}

export function Dashboard({ opportunities, threshold }: DashboardProps) {
  if (opportunities.length === 0) {
    return (
      <div className="text-center py-20">
        <div className="text-6xl mb-4">🤷</div>
        <h2 className="text-xl text-gray-400 mb-2">Арбитражных возможностей не найдено</h2>
        <p className="text-gray-600">
          Попробуйте снизить порог edge (сейчас: {(threshold * 100).toFixed(0)}%)
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Stats Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <StatCard
          icon="🔥"
          label="Возможностей"
          value={opportunities.length.toString()}
          color="emerald"
        />
        <StatCard
          icon="📈"
          label="Макс. Edge"
          value={`${(Math.max(...opportunities.map(o => Math.abs(o.edge))) * 100).toFixed(1)}%`}
          color="cyan"
        />
        <StatCard
          icon="💰"
          label="Общий объём"
          value={`$${formatVolume(opportunities.reduce((s, o) => s + o.market.volume, 0))}`}
          color="purple"
        />
        <StatCard
          icon="⚡"
          label="Ср. Edge"
          value={`${(opportunities.reduce((s, o) => s + Math.abs(o.edge), 0) / opportunities.length * 100).toFixed(1)}%`}
          color="amber"
        />
      </div>

      {/* Opportunities Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {opportunities.map((opp) => (
          <OpportunityCard key={opp.market.id} opportunity={opp} />
        ))}
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, color }: { icon: string; label: string; value: string; color: string }) {
  const colorClasses: Record<string, string> = {
    emerald: 'from-emerald-900/30 to-emerald-900/10 border-emerald-800/50',
    cyan: 'from-cyan-900/30 to-cyan-900/10 border-cyan-800/50',
    purple: 'from-purple-900/30 to-purple-900/10 border-purple-800/50',
    amber: 'from-amber-900/30 to-amber-900/10 border-amber-800/50',
  };

  return (
    <div className={`rounded-xl border p-4 bg-gradient-to-br ${colorClasses[color]}`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">{icon}</span>
        <span className="text-xs text-gray-400 uppercase tracking-wide">{label}</span>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  );
}

function OpportunityCard({ opportunity: opp }: { opportunity: ArbitrageOpportunity }) {
  const edgePct = (opp.edge * 100).toFixed(1);
  const marketPct = (opp.market.implied_probability * 100).toFixed(1);
  const oraclePct = (opp.oracle.oracle_probability * 100).toFixed(1);
  const isPositive = opp.edge > 0;

  const severityColors = {
    high: 'border-red-500/50 bg-red-950/20',
    medium: 'border-amber-500/50 bg-amber-950/20',
    low: 'border-yellow-500/50 bg-yellow-950/20',
  };

  const severityBadge = {
    high: 'bg-red-900/50 text-red-400',
    medium: 'bg-amber-900/50 text-amber-400',
    low: 'bg-yellow-900/50 text-yellow-400',
  };

  return (
    <div className={`rounded-xl border p-5 ${severityColors[opp.severity]} transition-all hover:scale-[1.01]`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${severityBadge[opp.severity]}`}>
              {opp.severity === 'high' ? '🔴 HIGH' : opp.severity === 'medium' ? '🟡 MEDIUM' : '🟢 LOW'}
            </span>
            <span className="text-xs text-gray-500 font-mono">{opp.market.asset}</span>
          </div>
          <h3 className="text-sm font-medium text-gray-200 leading-tight">
            {opp.market.question}
          </h3>
        </div>
      </div>

      {/* Probability Comparison */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="text-center p-2 rounded-lg bg-gray-800/50">
          <div className="text-xs text-gray-500 mb-1">Рынок</div>
          <div className="text-lg font-bold text-gray-300">{marketPct}%</div>
        </div>
        <div className="text-center p-2 rounded-lg bg-gray-800/50">
          <div className="text-xs text-gray-500 mb-1">Оракул</div>
          <div className="text-lg font-bold text-cyan-400">{oraclePct}%</div>
        </div>
        <div className="text-center p-2 rounded-lg bg-gray-800/50">
          <div className="text-xs text-gray-500 mb-1">Edge</div>
          <div className={`text-lg font-bold ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
            {isPositive ? '+' : ''}{edgePct}%
          </div>
        </div>
      </div>

      {/* Visual Bar */}
      <div className="mb-4">
        <div className="relative h-6 bg-gray-800 rounded-full overflow-hidden">
          {/* Market probability */}
          <div
            className="absolute top-0 left-0 h-full bg-gray-600/50 rounded-full"
            style={{ width: `${marketPct}%` }}
          />
          {/* Oracle probability */}
          <div
            className={`absolute top-0 left-0 h-full rounded-full ${
              isPositive ? 'bg-gradient-to-r from-emerald-600 to-emerald-400' : 'bg-gradient-to-r from-red-600 to-red-400'
            }`}
            style={{ width: `${oraclePct}%`, opacity: 0.7 }}
          />
          {/* Edge indicator */}
          <div
            className="absolute top-0 h-full w-0.5 bg-white"
            style={{ left: `${marketPct}%` }}
          />
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-gray-600">0%</span>
          <span className="text-xs text-gray-600">100%</span>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-700/50">
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span>📈 ${formatVolume(opp.market.volume)}</span>
          <span>📅 {opp.oracle.daysToExpiry} дн.</span>
        </div>
        <div className={`px-3 py-1 rounded-lg text-sm font-bold ${
          opp.recommendation === 'BUY YES'
            ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-700/50'
            : 'bg-red-900/50 text-red-400 border border-red-700/50'
        }`}>
          💡 {opp.recommendation}
        </div>
      </div>

      {/* Reasoning */}
      <div className="mt-3 p-2 rounded-lg bg-gray-800/30">
        <p className="text-xs text-gray-500 leading-relaxed">
          📝 {opp.oracle.reasoning}
        </p>
      </div>
    </div>
  );
}

function formatVolume(volume: number): string {
  if (volume >= 1_000_000) {
    return `${(volume / 1_000_000).toFixed(2)}M`;
  } else if (volume >= 1_000) {
    return `${(volume / 1_000).toFixed(0)}K`;
  }
  return volume.toFixed(0);
}
