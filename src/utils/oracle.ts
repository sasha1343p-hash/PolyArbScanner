import { Market, OracleResult } from '../types';
import { mockCurrentPrices } from '../data/mockData';

/**
 * Модуль "Оракул" — вычисляет "объективную" вероятность
 * на основе текущей цены актива и времени до экспирации.
 * 
 * В реальной версии здесь были бы вызовы Binance API.
 * В веб-версии используем мок-данные.
 */

// Конфигурация оракула
const ORACLE_CONFIG = {
  // Волатильность актива (годовая, для модели)
  volatility: {
    BTC: 0.65,
    ETH: 0.80,
    SOL: 1.10,
  } as Record<string, number>,
  // Минимальное расстояние для уверенности
  minConfidence: 0.3,
  maxConfidence: 0.95,
};

/**
 * Парсит вопрос рынка и извлекает ключевые параметры
 */
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

  // Определяем актив
  const assetPatterns: Record<string, RegExp> = {
    BTC: /bitcoin|btc/i,
    ETH: /ethereum|eth/i,
    SOL: /solana|sol/i,
  };

  for (const [asset, pattern] of Object.entries(assetPatterns)) {
    if (pattern.test(question)) {
      result.asset = asset;
      break;
    }
  }

  // Определяем направление
  if (/below|drop|under|less than/i.test(question)) {
    result.direction = 'below';
  }

  // Извлекаем ценовой порог
  const priceMatch = question.match(/\$?([\d,]+(?:\.\d+)?)\s*(?:k|K|thousand)?/);
  if (priceMatch) {
    let price = parseFloat(priceMatch[1].replace(/,/g, ''));
    // Если есть "k" после числа
    if (/k|K|thousand/i.test(question.substring(priceMatch.index || 0, (priceMatch.index || 0) + 10))) {
      price *= 1000;
    }
    result.strikePrice = price;
  }

  // Более точный парсинг цен с $
  const dollarMatch = question.match(/\$\s*([\d,]+(?:\.\d+)?)\s*(k|K)?/);
  if (dollarMatch) {
    let price = parseFloat(dollarMatch[1].replace(/,/g, ''));
    if (dollarMatch[2]) price *= 1000;
    result.strikePrice = price;
  }

  // Извлекаем дату
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

  // Альтернативный формат даты: "end of 2026", "December 2026"
  const yearMatch = question.match(/(end of|by)\s*(\d{4})/i);
  if (yearMatch && !result.expiryDate) {
    const year = parseInt(yearMatch[2]);
    result.expiryDate = new Date(year, 11, 31);
  }

  return result;
}

/**
 * Вычисляет "объективную" вероятность с использованием
 * упрощенной модели логистического распределения.
 * 
 * Учитывает:
 * - Расстояние текущей цены от страйка
 * - Волатильность актива
 * - Время до экспирации
 */
export function getRealWorldProbability(market: Market): OracleResult {
  const parsed = parseMarketQuestion(market.question);
  
  // Если не удалось распарсить — возвращаем нейтральный результат
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

  // Вычисляем дни до экспирации
  const now = new Date();
  let daysToExpiry = 365; // по умолчанию
  if (parsed.expiryDate) {
    daysToExpiry = Math.max(1, Math.ceil(
      (parsed.expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
    ));
  }

  // Расстояние в процентах от страйка
  const distancePct = (currentPrice - strikePrice) / strikePrice;

  // Annualized volatility scaled to time period
  const timeScaledVol = volatility * Math.sqrt(daysToExpiry / 365);

  // Z-score: насколько далеко текущая цена от страйка в единицах волатильности
  const zScore = distancePct / timeScaledVol;

  // Логистическая функция (сигмоида) для преобразования z-score в вероятность
  let probability: number;
  if (parsed.direction === 'above') {
    // Вероятность того, что цена БУДЕТ выше страйка
    probability = 1 / (1 + Math.exp(-zScore * 1.5));
  } else {
    // Вероятность того, что цена БУДЕТ ниже страйка
    probability = 1 / (1 + Math.exp(zScore * 1.5));
  }

  // Ограничиваем диапазон
  probability = Math.max(0.02, Math.min(0.98, probability));

  // Уверенность зависит от расстояния и времени
  const confidence = Math.min(
    ORACLE_CONFIG.maxConfidence,
    Math.max(ORACLE_CONFIG.minConfidence, Math.abs(zScore) * 0.3 + 0.3)
  );

  // Формируем объяснение
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
      reasoning = `Текущая цена ${parsed.asset} ($${currentPrice.toLocaleString()}) выше порога $${strikePrice.toLocaleString()} на ${(distancePct * 100).toFixed(1)}%. Цена должна упасть. До экспирации ${daysToExpiry} дней.`;
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
