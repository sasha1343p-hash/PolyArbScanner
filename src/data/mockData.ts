import { Market, EdgeHistory } from '../types';

// Мок-данные крипто-рынков Polymarket
export const mockMarkets: Market[] = [
  {
    id: 'btc-70k-dec26',
    question: 'Will Bitcoin be above $70,000 on December 31, 2026?',
    yes_price: 0.65,
    implied_probability: 0.65,
    volume: 2450000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'crypto',
    asset: 'BTC',
    strikePrice: 70000,
    expiryDate: '2026-12-31',
  },
  {
    id: 'eth-4k-jun26',
    question: 'Will Ethereum exceed $4,000 by June 30, 2026?',
    yes_price: 0.42,
    implied_probability: 0.42,
    volume: 1870000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'crypto',
    asset: 'ETH',
    strikePrice: 4000,
    expiryDate: '2026-06-30',
  },
  {
    id: 'btc-100k-mar26',
    question: 'Will BTC reach $100,000 before March 1, 2026?',
    yes_price: 0.78,
    implied_probability: 0.78,
    volume: 5230000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'crypto',
    asset: 'BTC',
    strikePrice: 100000,
    expiryDate: '2026-03-01',
  },
  {
    id: 'eth-5k-dec26',
    question: 'Will Ethereum be above $5,000 at end of 2026?',
    yes_price: 0.35,
    implied_probability: 0.35,
    volume: 980000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'crypto',
    asset: 'ETH',
    strikePrice: 5000,
    expiryDate: '2026-12-31',
  },
  {
    id: 'btc-50k-mar26',
    question: 'Will Bitcoin drop below $50,000 before March 2026?',
    yes_price: 0.18,
    implied_probability: 0.18,
    volume: 3100000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'crypto',
    asset: 'BTC',
    strikePrice: 50000,
    expiryDate: '2026-03-01',
  },
  {
    id: 'sol-200-jun26',
    question: 'Will Solana be above $200 by June 2026?',
    yes_price: 0.52,
    implied_probability: 0.52,
    volume: 1240000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'crypto',
    asset: 'SOL',
    strikePrice: 200,
    expiryDate: '2026-06-30',
  },
  {
    id: 'btc-80k-jun26',
    question: 'Will BTC price be above $80,000 on June 30, 2026?',
    yes_price: 0.58,
    implied_probability: 0.58,
    volume: 4100000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'crypto',
    asset: 'BTC',
    strikePrice: 80000,
    expiryDate: '2026-06-30',
  },
  {
    id: 'eth-3k-mar26',
    question: 'Will Ethereum stay above $3,000 until March 2026?',
    yes_price: 0.71,
    implied_probability: 0.71,
    volume: 2050000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'crypto',
    asset: 'ETH',
    strikePrice: 3000,
    expiryDate: '2026-03-01',
  },
  {
    id: 'btc-120k-dec26',
    question: 'Will Bitcoin reach $120,000 by end of 2026?',
    yes_price: 0.28,
    implied_probability: 0.28,
    volume: 6780000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'crypto',
    asset: 'BTC',
    strikePrice: 120000,
    expiryDate: '2026-12-31',
  },
  {
    id: 'sol-300-dec26',
    question: 'Will Solana exceed $300 before December 2026?',
    yes_price: 0.22,
    implied_probability: 0.22,
    volume: 890000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'crypto',
    asset: 'SOL',
    strikePrice: 300,
    expiryDate: '2026-12-31',
  },
  {
    id: 'us-pres-2028',
    question: 'Will the 2028 US Presidential election have a third-party candidate on all 50 state ballots?',
    yes_price: 0.12,
    implied_probability: 0.12,
    volume: 890000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'politics',
    expiryDate: '2028-11-05',
  },
  {
    id: 'eu-parliament-2026',
    question: 'Will the EU pass the AI Regulation Act before July 2026?',
    yes_price: 0.73,
    implied_probability: 0.73,
    volume: 1560000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'politics',
    expiryDate: '2026-07-01',
  },
  {
    id: 'uk-election-2029',
    question: 'Will the Conservative Party win the next UK general election?',
    yes_price: 0.31,
    implied_probability: 0.31,
    volume: 2340000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'politics',
    expiryDate: '2029-05-01',
  },
  {
    id: 'nba-finals-2026',
    question: 'Will the Boston Celtics win the 2026 NBA Finals?',
    yes_price: 0.34,
    implied_probability: 0.34,
    volume: 4560000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'sports',
    expiryDate: '2026-06-30',
  },
  {
    id: 'world-cup-2026',
    question: 'Will Brazil win the 2026 FIFA World Cup?',
    yes_price: 0.18,
    implied_probability: 0.18,
    volume: 7890000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'sports',
    expiryDate: '2026-07-19',
  },
  {
    id: 'superbowl-2027',
    question: 'Will the Kansas City Chiefs win Super Bowl LXI (2027)?',
    yes_price: 0.22,
    implied_probability: 0.22,
    volume: 5430000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'sports',
    expiryDate: '2027-02-14',
  },
  {
    id: 'oscar-2027',
    question: 'Will a Marvel movie win Best Picture at the 2027 Oscars?',
    yes_price: 0.08,
    implied_probability: 0.08,
    volume: 1230000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'culture',
    expiryDate: '2027-03-15',
  },
  {
    id: 'tesla-robotaxi',
    question: 'Will Tesla launch a commercial robotaxi service in 2026?',
    yes_price: 0.45,
    implied_probability: 0.45,
    volume: 3210000,
    timestamp: '2026-01-15T10:30:00Z',
    category: 'culture',
    expiryDate: '2026-12-31',
  },
];

// Симулированные текущие цены
export const mockCurrentPrices: Record<string, number> = {
  BTC: 84500,
  ETH: 3250,
  SOL: 178,
};

// Генерация истории edge для каждого рынка (7 дней)
function generateEdgeHistory(marketId: string, baseEdge: number): EdgeHistory {
  const points = [];
  const now = new Date();
  
  for (let i = 6; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    
    // Добавляем случайность к базовому edge
    const noise = (Math.sin(i * 2.5 + marketId.length) * 0.08) + 
                  (Math.cos(i * 1.3 + marketId.length * 0.5) * 0.05);
    const edge = baseEdge + noise;
    const oraclePrice = 0.5 + edge / 2;
    const marketPrice = 0.5 - edge / 2;
    
    points.push({
      date: date.toISOString().split('T')[0],
      edge: Math.round(edge * 1000) / 1000,
      marketPrice: Math.max(0.01, Math.min(0.99, Math.round(marketPrice * 1000) / 1000)),
      oraclePrice: Math.max(0.01, Math.min(0.99, Math.round(oraclePrice * 1000) / 1000)),
    });
  }
  
  return { marketId, points };
}

// Предгенерированная история для рынков
export const mockEdgeHistory: Record<string, EdgeHistory> = {
  'btc-70k-dec26': generateEdgeHistory('btc-70k-dec26', 0.17),
  'eth-4k-jun26': generateEdgeHistory('eth-4k-jun26', 0.21),
  'btc-100k-mar26': generateEdgeHistory('btc-100k-mar26', -0.12),
  'eth-5k-dec26': generateEdgeHistory('eth-5k-dec26', 0.28),
  'btc-50k-mar26': generateEdgeHistory('btc-50k-mar26', -0.15),
  'sol-200-jun26': generateEdgeHistory('sol-200-jun26', 0.19),
  'btc-80k-jun26': generateEdgeHistory('btc-80k-jun26', 0.16),
  'eth-3k-mar26': generateEdgeHistory('eth-3k-mar26', -0.09),
  'btc-120k-dec26': generateEdgeHistory('btc-120k-dec26', 0.24),
  'sol-300-dec26': generateEdgeHistory('sol-300-dec26', 0.18),
  'us-pres-2028': generateEdgeHistory('us-pres-2028', -0.05),
  'eu-parliament-2026': generateEdgeHistory('eu-parliament-2026', -0.11),
  'uk-election-2029': generateEdgeHistory('uk-election-2029', 0.14),
  'nba-finals-2026': generateEdgeHistory('nba-finals-2026', 0.22),
  'world-cup-2026': generateEdgeHistory('world-cup-2026', -0.08),
  'superbowl-2027': generateEdgeHistory('superbowl-2027', 0.15),
  'oscar-2027': generateEdgeHistory('oscar-2027', -0.03),
  'tesla-robotaxi': generateEdgeHistory('tesla-robotaxi', 0.20),
};
