import { Market } from '../types';

// ============================================
// КОНФИГУРАЦИЯ API
// ============================================

const POLYMARKET_API = 'https://gamma-api.polymarket.com/events';
const BINANCE_API = 'https://api.binance.com/api/v3/ticker/price';

// Fallback endpoints для Binance (если основной недоступен)
const BINANCE_FALLBACKS = [
  'https://api1.binance.com/api/v3/ticker/price',
  'https://api2.binance.com/api/v3/ticker/price',
  'https://api3.binance.com/api/v3/ticker/price',
  'https://api4.binance.com/api/v3/ticker/price',
];

// Таймаут запросов (мс)
const REQUEST_TIMEOUT = 10000;

// ============================================
// УТИЛИТЫ
// ============================================

/**
 * Определяет категорию рынка по вопросу
 */
function detectCategory(question: string): Market['category'] {
  const q = question.toLowerCase();
  
  if (/bitcoin|btc|ethereum|eth|solana|sol(?!\w)|crypto|token|defi|nft/i.test(q)) {
    return 'crypto';
  }
  if (/election|president|congress|senate|party|vote|ballot|trump|biden|democrat|republican|eu|parliament|uk|brexit/i.test(q)) {
    return 'politics';
  }
  if (/nba|nfl|mlb|nhl|ufc|boxing|tennis|world cup|superbowl|championship|match|win the|champion|finals|premier league/i.test(q)) {
    return 'sports';
  }
  return 'culture';
}

/**
 * Извлекает актив из вопроса (для крипто-рынков)
 */
function detectAsset(question: string): string | undefined {
  const q = question.toLowerCase();
  if (/bitcoin|\bbtc\b/i.test(q)) return 'BTC';
  if (/ethereum|\beth\b/i.test(q)) return 'ETH';
  if (/solana|\bsol\b/i.test(q)) return 'SOL';
  return undefined;
}

/**
 * Извлекает ценовой порог из вопроса
 */
function detectStrikePrice(question: string): number | undefined {
  const match = question.match(/\$\s*([\d,]+(?:\.\d+)?)\s*(k|K|million|M)?/);
  if (!match) return undefined;
  
  let price = parseFloat(match[1].replace(/,/g, ''));
  if (match[2]) {
    if (match[2].toLowerCase() === 'k') price *= 1000;
    if (match[2].toLowerCase() === 'm' || match[2].toLowerCase() === 'million') price *= 1000000;
  }
  return price;
}

/**
 * Извлекает дату экспирации из вопроса
 */
function detectExpiryDate(question: string): string | undefined {
  const months: Record<string, number> = {
    jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5,
    jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11,
  };
  
  // Формат: "December 31, 2026" или "Dec 31 2026"
  const dateMatch = question.match(
    /(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})?,?\s*(\d{4})/i
  );
  
  if (dateMatch) {
    const month = months[dateMatch[1].toLowerCase().substring(0, 3)];
    const day = dateMatch[2] ? parseInt(dateMatch[2]) : 28;
    const year = parseInt(dateMatch[3]);
    return new Date(year, month, day).toISOString().split('T')[0];
  }
  
  // Формат: "end of 2026" или "by 2026"
  const yearMatch = question.match(/(?:end of|by)\s*(\d{4})/i);
  if (yearMatch) {
    const year = parseInt(yearMatch[1]);
    return new Date(year, 11, 31).toISOString().split('T')[0];
  }
  
  return undefined;
}

/**
 * Запрос с таймаутом
 */
async function fetchWithTimeout(url: string, timeout = REQUEST_TIMEOUT): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
}

// ============================================
// ПОЛУЧЕНИЕ РЫНКОВ С POLYMARKET
// ============================================

export interface FetchResult {
  markets: Market[];
  success: boolean;
  error?: string;
  source: 'live' | 'mock';
  timestamp: string;
}

/**
 * Загружает рынки с Polymarket Gamma API
 */
export async function fetchLiveMarkets(): Promise<FetchResult> {
  const timestamp = new Date().toISOString();
  
  try {
    const url = `${POLYMARKET_API}?limit=100&active=true&closed=false`;
    const response = await fetchWithTimeout(url);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const events = await response.json();
    
    if (!Array.isArray(events)) {
      throw new Error('Неверный формат ответа API');
    }
    
    const markets: Market[] = [];
    
    for (const event of events) {
      const question = event.question || event.title || '';
      if (!question) continue;
      
      const category = detectCategory(question);
      const asset = detectAsset(question);
      const strikePrice = detectStrikePrice(question);
      const expiryDate = detectExpiryDate(question);
      
      // Обрабатываем каждый market внутри event
      const eventMarkets = event.markets || [event];
      
      for (const m of eventMarkets) {
        // Парсим цену YES
        let yesPrice = 0.5;
        try {
          const outcomePrices = m.outcomePrices || m.outcome_prices;
          if (typeof outcomePrices === 'string') {
            const prices = JSON.parse(outcomePrices);
            yesPrice = parseFloat(prices[0]);
          } else if (Array.isArray(outcomePrices)) {
            yesPrice = parseFloat(outcomePrices[0]);
          }
        } catch {
          // Используем значение по умолчанию
        }
        
        if (isNaN(yesPrice) || yesPrice < 0 || yesPrice > 1) {
          yesPrice = 0.5;
        }
        
        // Парсим объём
        let volume = 0;
        try {
          volume = parseFloat(m.volume || m.volumeNum || '0');
        } catch {}
        
        markets.push({
          id: m.conditionId || m.id || `market-${markets.length}`,
          question,
          yes_price: yesPrice,
          implied_probability: yesPrice,
          volume,
          timestamp,
          category,
          asset,
          strikePrice,
          expiryDate,
        });
      }
    }
    
    console.log(`✅ Загружено ${markets.length} рынков с Polymarket`);
    
    return {
      markets,
      success: true,
      source: 'live',
      timestamp,
    };
    
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    console.error('❌ Ошибка загрузки Polymarket:', errorMsg);
    
    return {
      markets: [],
      success: false,
      error: errorMsg,
      source: 'mock',
      timestamp,
    };
  }
}

// ============================================
// ПОЛУЧЕНИЕ ЦЕН КРИПТОВАЛЮТ С BINANCE
// ============================================

export interface PricesResult {
  prices: Record<string, number>;
  success: boolean;
  error?: string;
  source: 'live' | 'mock';
}

/**
 * Загружает текущие цены крипто с Binance
 */
export async function fetchCryptoPrices(): Promise<PricesResult> {
  const symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'];
  const symbolMap: Record<string, string> = {
    BTCUSDT: 'BTC',
    ETHUSDT: 'ETH',
    SOLUSDT: 'SOL',
  };
  
  // Пробуем основной и fallback endpoints
  const endpoints = [BINANCE_API, ...BINANCE_FALLBACKS];
  
  for (const endpoint of endpoints) {
    try {
      const url = `${endpoint}?symbols=${JSON.stringify(symbols)}`;
      const response = await fetchWithTimeout(url, 5000);
      
      if (!response.ok) continue;
      
      const data = await response.json();
      
      if (!Array.isArray(data)) continue;
      
      const prices: Record<string, number> = {};
      
      for (const item of data) {
        const asset = symbolMap[item.symbol];
        if (asset && item.price) {
          prices[asset] = parseFloat(item.price);
        }
      }
      
      if (Object.keys(prices).length > 0) {
        console.log('✅ Загружены цены с Binance:', prices);
        return {
          prices,
          success: true,
          source: 'live',
        };
      }
      
    } catch (error) {
      console.warn(`⚠️  ${endpoint} недоступен, пробуем следующий...`);
      continue;
    }
  }
  
  // Все endpoints недоступны
  const errorMsg = 'Все Binance endpoints недоступны';
  console.error('❌', errorMsg);
  
  return {
    prices: {},
    success: false,
    error: errorMsg,
    source: 'mock',
  };
}

// ============================================
// КОМБИНИРОВАННАЯ ЗАГРУЗКА
// ============================================

export interface LiveDataResult {
  markets: Market[];
  prices: Record<string, number>;
  marketsSource: 'live' | 'mock';
  pricesSource: 'live' | 'mock';
  errors: string[];
  timestamp: string;
}

/**
 * Загружает все данные (рынки + цены) параллельно
 */
export async function fetchAllLiveData(
  fallbackMarkets: Market[],
  fallbackPrices: Record<string, number>
): Promise<LiveDataResult> {
  const timestamp = new Date().toISOString();
  const errors: string[] = [];
  
  const [marketsResult, pricesResult] = await Promise.all([
    fetchLiveMarkets(),
    fetchCryptoPrices(),
  ]);
  
  // Используем реальные данные или fallback на мок
  const markets = marketsResult.success && marketsResult.markets.length > 0
    ? marketsResult.markets
    : fallbackMarkets;
  
  const prices = pricesResult.success && Object.keys(pricesResult.prices).length > 0
    ? pricesResult.prices
    : fallbackPrices;
  
  if (!marketsResult.success) {
    errors.push(`Polymarket: ${marketsResult.error}`);
  }
  
  if (!pricesResult.success) {
    errors.push(`Binance: ${pricesResult.error}`);
  }
  
  return {
    markets,
    prices,
    marketsSource: marketsResult.source,
    pricesSource: pricesResult.source,
    errors,
    timestamp,
  };
}
