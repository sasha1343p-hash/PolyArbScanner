import { ArbitrageOpportunity, ScanResult } from '../types';

/**
 * Модуль "Отчёт" (Reporter)
 */

export function generateTextReport(opportunities: ArbitrageOpportunity[]): string {
  if (opportunities.length === 0) {
    return '⚠️ Арбитражных возможностей не обнаружено при текущем пороге.';
  }

  const lines: string[] = [];
  lines.push('═'.repeat(60));
  lines.push('🔍 ОТЧЁТ СКАНЕРА АРБИТРАЖНЫХ ВОЗМОЖНОСТЕЙ');
  lines.push(`📅 ${new Date().toLocaleString('ru-RU')}`);
  lines.push(`📊 Найдено возможностей: ${opportunities.length}`);
  lines.push('═'.repeat(60));
  lines.push('');

  for (const opp of opportunities) {
    const edgePct = (opp.edge * 100).toFixed(1);
    const marketPct = (opp.market.implied_probability * 100).toFixed(1);
    const oraclePct = (opp.oracle.oracle_probability * 100).toFixed(1);
    const volume = formatVolume(opp.market.volume);

    lines.push('─'.repeat(50));
    lines.push(`🔥 ВОЗМОЖНОСТЬ АРБИТРАЖА [${opp.severity.toUpperCase()}]`);
    lines.push(`📊 Рынок: ${opp.market.question}`);
    lines.push(`💰 Цена рынка: ${marketPct}% | Оценка оракула: ${oraclePct}% | Edge: ${opp.edge > 0 ? '+' : ''}${edgePct}%`);
    lines.push(`📈 Объем: $${volume}`);
    lines.push(`💡 Рекомендация: ${opp.recommendation}`);
    lines.push(`📝 ${opp.oracle.reasoning}`);
    lines.push('');
  }

  lines.push('═'.repeat(60));
  lines.push('⚠️ Это не финансовый совет. Всегда проводите собственный анализ.');
  lines.push('═'.repeat(60));

  return lines.join('\n');
}

export function generateJsonReport(opportunities: ArbitrageOpportunity[]): string {
  const report = {
    timestamp: new Date().toISOString(),
    total_opportunities: opportunities.length,
    opportunities: opportunities.map(opp => ({
      market_id: opp.market.id,
      question: opp.market.question,
      category: opp.market.category,
      market_probability: opp.market.implied_probability,
      oracle_probability: opp.oracle.oracle_probability,
      edge: opp.edge,
      recommendation: opp.recommendation,
      severity: opp.severity,
      volume: opp.market.volume,
      reasoning: opp.oracle.reasoning,
    })),
  };
  return JSON.stringify(report, null, 2);
}

function formatVolume(volume: number): string {
  if (volume >= 1_000_000) {
    return `${(volume / 1_000_000).toFixed(2)}M`;
  } else if (volume >= 1_000) {
    return `${(volume / 1_000).toFixed(0)}K`;
  }
  return volume.toFixed(0);
}

export function createScanResult(
  totalMarkets: number,
  opportunities: ArbitrageOpportunity[],
  errors: string[] = [],
  scanDurationMs: number = 0
): ScanResult {
  return {
    timestamp: new Date().toISOString(),
    totalMarkets,
    opportunities,
    errors,
    scanDurationMs,
  };
}
