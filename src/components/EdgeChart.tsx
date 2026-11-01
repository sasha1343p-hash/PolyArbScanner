import { useMemo } from 'react';
import { Market } from '../types';
import { mockEdgeHistory } from '../data/mockData';

interface EdgeChartProps {
  marketId: string | null;
  markets: Market[];
  onSelectMarket: (id: string) => void;
}

export function EdgeChart({ marketId, markets, onSelectMarket }: EdgeChartProps) {
  const history = marketId ? mockEdgeHistory[marketId] : null;
  const market = marketId ? markets.find(m => m.id === marketId) : null;

  // Все доступные рынки с историей
  const availableMarkets = useMemo(() =>
    markets.filter(m => mockEdgeHistory[m.id]).slice(0, 8),
    [markets]
  );

  if (!history || !market) {
    return (
      <div className="rounded-xl border border-gray-800/50 bg-gray-900/30 p-8 text-center">
        <p className="text-sm text-gray-500">Выберите рынок для просмотра истории Edge</p>
      </div>
    );
  }

  const points = history.points;
  const width = 600;
  const height = 200;
  const padding = { top: 20, right: 20, bottom: 30, left: 45 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  // Scale
  const allEdges = points.map(p => p.edge);
  const minEdge = Math.min(...allEdges, 0);
  const maxEdge = Math.max(...allEdges, 0);
  const edgeRange = maxEdge - minEdge || 0.1;
  const edgePadding = edgeRange * 0.15;

  const scaleX = (i: number) => padding.left + (i / (points.length - 1)) * chartW;
  const scaleY = (val: number) => {
    const normalized = (val - (minEdge - edgePadding)) / (edgeRange + edgePadding * 2);
    return padding.top + chartH - normalized * chartH;
  };

  // Build path
  const linePath = points.map((p, i) => {
    const x = scaleX(i);
    const y = scaleY(p.edge);
    return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
  }).join(' ');

  // Area path
  const areaPath = linePath +
    ` L ${scaleX(points.length - 1)} ${scaleY(0)}` +
    ` L ${scaleX(0)} ${scaleY(0)} Z`;

  // Zero line Y position
  const zeroY = scaleY(0);

  // Grid lines
  const gridLines = [minEdge - edgePadding, 0, maxEdge + edgePadding].map(val => ({
    y: scaleY(val),
    label: `${(val * 100).toFixed(0)}%`,
  }));

  return (
    <div className="rounded-xl border border-gray-800/50 bg-gray-900/30 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800/50 bg-gray-900/50">
        <div>
          <h3 className="text-sm font-semibold text-gray-300">📈 История Edge — 7 дней</h3>
          <p className="text-[10px] text-gray-500 mt-0.5 truncate max-w-[300px]">{market.question}</p>
        </div>
        {/* Market selector */}
        <select
          value={marketId || ''}
          onChange={(e) => onSelectMarket(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1 text-xs text-gray-300 focus:outline-none focus:border-emerald-600 max-w-[180px] truncate"
        >
          {availableMarkets.map(m => (
            <option key={m.id} value={m.id}>
              {m.question.substring(0, 40)}...
            </option>
          ))}
        </select>
      </div>

      {/* Chart */}
      <div className="p-4">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto" preserveAspectRatio="xMidYMid meet">
          {/* Grid */}
          {gridLines.map((line, i) => (
            <g key={i}>
              <line
                x1={padding.left}
                y1={line.y}
                x2={width - padding.right}
                y2={line.y}
                stroke={line.label === '0%' ? '#374151' : '#1f2937'}
                strokeWidth={line.label === '0%' ? 1.5 : 0.5}
                strokeDasharray={line.label === '0%' ? 'none' : '4 4'}
              />
              <text
                x={padding.left - 8}
                y={line.y + 3}
                textAnchor="end"
                className="text-[9px] fill-gray-600"
              >
                {line.label}
              </text>
            </g>
          ))}

          {/* Area fill */}
          <path
            d={areaPath}
            fill="url(#edgeGradient)"
            opacity={0.3}
          />

          {/* Line */}
          <path
            d={linePath}
            fill="none"
            stroke="#10b981"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Data points */}
          {points.map((p, i) => (
            <g key={i}>
              <circle
                cx={scaleX(i)}
                cy={scaleY(p.edge)}
                r={4}
                fill={p.edge >= 0 ? '#10b981' : '#ef4444'}
                stroke="#0a0a0f"
                strokeWidth={2}
              />
              {/* Date label */}
              <text
                x={scaleX(i)}
                y={height - 5}
                textAnchor="middle"
                className="text-[8px] fill-gray-600"
              >
                {p.date.substring(5)}
              </text>
            </g>
          ))}

          {/* Gradient definition */}
          <defs>
            <linearGradient id="edgeGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      {/* Stats below chart */}
      <div className="grid grid-cols-3 gap-px bg-gray-800/30 border-t border-gray-800/50">
        <div className="bg-gray-900/50 p-3 text-center">
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Текущий Edge</div>
          <div className={`text-lg font-bold font-mono ${
            points[points.length - 1].edge >= 0 ? 'text-emerald-400' : 'text-red-400'
          }`}>
            {(points[points.length - 1].edge * 100).toFixed(1)}%
          </div>
        </div>
        <div className="bg-gray-900/50 p-3 text-center">
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">7д Мин</div>
          <div className="text-lg font-bold font-mono text-gray-400">
            {(Math.min(...allEdges) * 100).toFixed(1)}%
          </div>
        </div>
        <div className="bg-gray-900/50 p-3 text-center">
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">7д Макс</div>
          <div className="text-lg font-bold font-mono text-gray-400">
            {(Math.max(...allEdges) * 100).toFixed(1)}%
          </div>
        </div>
      </div>
    </div>
  );
}
