import { Market, ArbitrageOpportunity, OracleResult } from '../types';
import { getRealWorldProbability } from './oracle';

export function findArbitrageOpportunities(
  markets: Market[],
  threshold: number = 0.15,
  livePrices?: Record<string, number>
): ArbitrageOpportunity[] {
  const opportunities: ArbitrageOpportunity[] = [];

  for (const market of markets) {
    try {
      const oracle = getRealWorldProbability(market, livePrices);
      const edge = oracle.oracle_probability - market.implied_probability;
      const absEdge = Math.abs(edge);

      if (absEdge >= threshold) {
        let recommendation: 'BUY YES' | 'BUY NO' | 'HOLD';
        if (edge > 0) {
          recommendation = 'BUY YES';
        } else {
          recommendation = 'BUY NO';
        }

        let severity: 'high' | 'medium' | 'low';
        if (absEdge >= 0.25) {
          severity = 'high';
        } else if (absEdge >= 0.18) {
          severity = 'medium';
        } else {
          severity = 'low';
        }

        opportunities.push({
          market,
          oracle,
          edge: Math.round(edge * 1000) / 1000,
          absEdge,
          recommendation,
          severity,
        });
      }
    } catch (error) {
      console.error(`Ошибка анализа рынка ${market.id}:`, error);
    }
  }

  opportunities.sort((a, b) => b.absEdge - a.absEdge);
  return opportunities;
}

export function analyzeAllMarkets(
  markets: Market[],
  livePrices?: Record<string, number>
): { market: Market; oracle: OracleResult; edge: number }[] {
  return markets.map(market => {
    const oracle = getRealWorldProbability(market, livePrices);
    const edge = oracle.oracle_probability - market.implied_probability;
    return { market, oracle, edge };
  });
}
