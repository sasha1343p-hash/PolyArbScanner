import { Market, OracleResult } from '../types';
import { mockCurrentPrices } from '../data/mockData';

/**
 * Модуль "Оракул" — вычисляет "объективную" вероятность
 */

const ORACLE_CONFIG = {
  volatility: {
    BTC: 0.65,
    ETH: 0.80,
    SOL: 1.10,
  } as Record<string, number>,
  // "Объективные" вероятности для некрипто-рынков (мок)
  oracleOverrides: {
    'us-pres-2028': 0.08,
    'eu-parliament-2026': 0.82,
    'uk-election-2029': 0.45,
    'nba-finals-2026': 0.56,
    'world-cup-2026': 0.10,
    'superbowl-2027': 0.37,
    'oscar-2027': 0.05,
    'tesla-robotaxi': 0.65,
  } as Record<string, number>,
  minConfidence: 0.3,
  maxConfidence: 0.95,
};

export function parseMarketQuestion(question: string): {
  asset: string | null;
  strikePrice: number | null;
  direction: 'above' | 'below';
  expiryDate: Date | null;
} {
  const result = {
    asset: null as string | null,
    strikePrice: null as number | null,
    direction: 'above' as 'above' | 'below',
    expiryDate: null as Date | null,
  };

  const assetPatterns: Record<string, RegExp> = {
    BTC: /bitcoin|btc/i,
    ETH: /ethereum|eth(?!ereum)/i,
    SOL: /solana|(?<!\w)sol(?!\w)/i,
  };

  for (const [asset, pattern] of Object.entries(assetPatterns)) {
    if (pattern.test(question)) {
      result.asset = asset;
      break;
    }
  }

  if (/below|drop|under|less than/i.test(question)) {
    result.direction = 'below';
  }

  const dollarMatch = question.match(/\$\s*([\d,]+(?:\.\d+)?)\s*(k|K)?/);
  if (dollarMatch) {
    let price = parseFloat(dollarMatch[1].replace(/,/g, ''));
    if (dollarMatch[2]) price *= 1000;
    result.strikePrice = price;
  }

  const monthMap: Record<string, number> = {
    jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5,
    jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11,
  };

  const dateMatch = question.match(
    /(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})?,?\s*(\d{4})/i
  );
  if (dateMatch) {
    const month = monthMap[dateMatch[1].toLowerCase().substring(0, 3)];
    const day = dateMatch[2] ? parseInt(dateMatch[2]) : 1;
    const year = parseInt(dateMatch[3]);
    result.expiryDate = new Date(year, month, day);
  }

  if (!result.expiryDate) {
    const yearMatch = question.match(/(end of|by)\s*(\d{4})/i);
    if (yearMatch) {
      const year = parseInt(yearMatch[2]);
      result.expiryDate = new Date(year, 11, 31);
    }
  }

  return result;
}

export function getRealWorldProbability(market: Market): OracleResult {
  // Проверка на предопределённые вероятности для некрипто-рынков
  if (ORACLE_CONFIG.oracleOverrides[market.id] !== undefined) {
    const oracleProb = ORACLE_CONFIG.oracleOverrides[market.id];
    const edge = oracleProb - market.implied_probability;
    const confidence = Math.min(0.95, Math.max(0.3, Math.abs(edge) * 2 + 0.4));
    
    let reasoning = '';
    if (Math.abs(edge) > 0.1) {
      reasoning = `Анализ внешних данных показывает вероятность ~${(oracleProb * 100).toFixed(0)}%. Рынок оценивает в ${(market.implied_probability * 100).toFixed(0)}%.`;
    } else {
      reasoning = `Внешние данные согласуются с ценой рынка. Вероятность ~${(oracleProb * 100).toFixed(0)}%.`;
    }

    return {
      marketId: market.id,
      oracle_probability: oracleProb,
      confidence,
      reasoning,
      daysToExpiry: market.expiryDate
        ? Math.max(1, Math.ceil((new Date(market.expiryDate).getTime() - Date.now()) / 86400000))
        : 365,
    };
  }

  const parsed = parseMarketQuestion(market.question);
  
  if (!parsed.asset || !parsed.strikePrice) {
    return {
      marketId: market.id,
      oracle_probability: 0.5,
      confidence: 0.1,
      reasoning: 'Не удалось распарсить вопрос рынка',
    };
  }

  const currentPrice = mockCurrentPrices[parsed.asset] || 0;
  const strikePrice = parsed.strikePrice;
  const volatility = ORACLE_CONFIG.volatility[parsed.asset] || 0.7;

  const now = new Date();
  let daysToExpiry = 365;
  if (parsed.expiryDate) {
    daysToExpiry = Math.max(1, Math.ceil(
      (parsed.expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
    ));
  }

  const distancePct = (currentPrice - strikePrice) / strikePrice;
  const timeScaledVol = volatility * Math.sqrt(daysToExpiry / 365);
  const zScore = distancePct / timeScaledVol;

  let probability: number;
  if (parsed.direction === 'above') {
    probability = 1 / (1 + Math.exp(-zScore * 1.5));
  } else {
    probability = 1 / (1 + Math.exp(zScore * 1.5));
  }

  probability = Math.max(0.02, Math.min(0.98, probability));
  const confidence = Math.min(
    ORACLE_CONFIG.maxConfidence,
    Math.max(ORACLE_CONFIG.minConfidence, Math.abs(zScore) * 0.3 + 0.3)
  );

  let reasoning = '';
  if (parsed.direction === 'above') {
    if (currentPrice > strikePrice) {
      reasoning = `Текущая цена ${parsed.asset} ($${currentPrice.toLocaleString()}) ВЫШЕ порога $${strikePrice.toLocaleString()} на ${(distancePct * 100).toFixed(1)}%. До экспирации ${daysToExpiry} дней.`;
    } else {
      reasoning = `Текущая цена ${parsed.asset} ($${currentPrice.toLocaleString()}) НИЖЕ порога $${strikePrice.toLocaleString()} на ${Math.abs(distancePct * 100).toFixed(1)}%. До экспирации ${daysToExpiry} дней.`;
    }
  } else {
    if (currentPrice < strikePrice) {
      reasoning = `Текущая цена ${parsed.asset} ($${currentPrice.toLocaleString()}) УЖЕ ниже порога $${strikePrice.toLocaleString()}. До экспирации ${daysToExpiry} дней.`;
    } else {
      reasoning = `Текущая цена ${parsed.asset} ($${currentPrice.toLocaleString()}) выше порога $${strikePrice.toLocaleString()} на ${(distancePct * 100).toFixed(1)}%. До экспирации ${daysToExpiry} дней.`;
    }
  }

  return {
    marketId: market.id,
    oracle_probability: Math.round(probability * 1000) / 1000,
    confidence: Math.round(confidence * 1000) / 1000,
    reasoning,
    currentPrice,
    daysToExpiry,
  };
}
