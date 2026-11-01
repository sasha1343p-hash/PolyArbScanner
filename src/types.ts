// Типы данных для сканера арбитражных возможностей

export interface Market {
  id: string;
  question: string;
  yes_price: number;
  implied_probability: number;
  volume: number;
  timestamp: string;
  asset?: string;
  strikePrice?: number;
  expiryDate?: string;
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

export interface AppConfig {
  threshold: number;
  mockMode: boolean;
  outputFormat: 'visual' | 'json' | 'text';
  saveHistory: boolean;
}

export interface ScanResult {
  timestamp: string;
  totalMarkets: number;
  opportunities: ArbitrageOpportunity[];
  errors: string[];
}
