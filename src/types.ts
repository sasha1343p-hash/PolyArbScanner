// Типы данных для сканера арбитражных возможностей

export type MarketCategory = 'crypto' | 'politics' | 'sports' | 'culture';

export interface Market {
  id: string;
  question: string;
  yes_price: number;
  implied_probability: number;
  volume: number;
  timestamp: string;
  category: MarketCategory;
  asset?: string;
  strikePrice?: number;
  expiryDate?: string;
  endDate?: string;
}

export interface OracleResult {
  marketId: string;
  oracle_probability: number;
  confidence: number;
  reasoning: string;
  currentPrice?: number;
  daysToExpiry?: number;
}

export interface ArbitrageOpportunity {
  market: Market;
  oracle: OracleResult;
  edge: number;
  absEdge: number;
  recommendation: 'BUY YES' | 'BUY NO' | 'HOLD';
  severity: 'high' | 'medium' | 'low';
}

export interface EdgeHistoryPoint {
  date: string;
  edge: number;
  marketPrice: number;
  oraclePrice: number;
}

export interface EdgeHistory {
  marketId: string;
  points: EdgeHistoryPoint[];
}

export interface Filters {
  category: MarketCategory | 'all';
  minVolume: number;
  minEdge: number;
  sortBy: 'edge' | 'volume' | 'market_price' | 'oracle_price' | 'expiry';
  sortDir: 'asc' | 'desc';
}

export interface ScanResult {
  timestamp: string;
  totalMarkets: number;
  opportunities: ArbitrageOpportunity[];
  errors: string[];
  scanDurationMs: number;
}
