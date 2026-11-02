interface MetricCardsProps {
  metrics: {
    totalMarkets: number;
    opportunities: number;
    avgEdge: number;
    totalVolume: number;
    highSeverity: number;
    buyYes: number;
    buyNo: number;
  };
}

export function MetricCards({ metrics }: MetricCardsProps) {
  const cards = [
    {
      label: 'Всего возможностей',
      value: metrics.opportunities.toString(),
      icon: '🔥',
      color: 'emerald',
      subtitle: `из ${metrics.totalMarkets} рынков`,
    },
    {
      label: 'Средний Edge',
      value: `${(metrics.avgEdge * 100).toFixed(1)}%`,
      icon: '📊',
      color: 'cyan',
      subtitle: 'расхождение с оракулом',
    },
    {
      label: 'Общий объём',
      value: `$${formatVolume(metrics.totalVolume)}`,
      icon: '💰',
      color: 'purple',
      subtitle: 'ликвидность рынков',
    },
    {
      label: 'Высокий Edge',
      value: metrics.highSeverity.toString(),
      icon: '⚡',
      color: 'amber',
      subtitle: `>25% расхождение`,
    },
    {
      label: 'BUY YES',
      value: metrics.buyYes.toString(),
      icon: '🟢',
      color: 'green',
      subtitle: 'рынок недооценивает',
    },
    {
      label: 'BUY NO',
      value: metrics.buyNo.toString(),
      icon: '🔴',
      color: 'red',
      subtitle: 'рынок переоценивает',
    },
  ];

  const colorMap: Record<string, { bg: string; border: string; text: string }> = {
    emerald: { bg: 'bg-emerald-950/30', border: 'border-emerald-800/40', text: 'text-emerald-400' },
    cyan: { bg: 'bg-cyan-950/30', border: 'border-cyan-800/40', text: 'text-cyan-400' },
    purple: { bg: 'bg-purple-950/30', border: 'border-purple-800/40', text: 'text-purple-400' },
    amber: { bg: 'bg-amber-950/30', border: 'border-amber-800/40', text: 'text-amber-400' },
    green: { bg: 'bg-green-950/30', border: 'border-green-800/40', text: 'text-green-400' },
    red: { bg: 'bg-red-950/30', border: 'border-red-800/40', text: 'text-red-400' },
  };

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {cards.map((card) => {
        const colors = colorMap[card.color];
        return (
          <div
            key={card.label}
            className={`rounded-xl border p-4 ${colors.bg} ${colors.border} transition-all hover:scale-[1.02] hover:shadow-lg hover:shadow-black/20`}
          >
            <div className="flex items-center gap-1.5 mb-2">
              <span className="text-sm">{card.icon}</span>
              <span className="text-[10px] uppercase tracking-wider text-gray-500 font-medium">{card.label}</span>
            </div>
            <div className={`text-2xl font-bold ${colors.text} tracking-tight`}>{card.value}</div>
            <div className="text-[10px] text-gray-600 mt-1">{card.subtitle}</div>
          </div>
        );
      })}
    </div>
  );
}

function formatVolume(volume: number): string {
  if (volume >= 1_000_000) return `${(volume / 1_000_000).toFixed(1)}M`;
  if (volume >= 1_000) return `${(volume / 1_000).toFixed(0)}K`;
  return volume.toFixed(0);
}
