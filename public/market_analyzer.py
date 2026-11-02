# ============================================
# market_analyzer.py — Сканер арбитражных возможностей
# Polymarket Prediction Markets Analyzer
# ============================================

"""
Модуль для поиска неэффективностей на предиктивных рынках.
Сравнивает вероятности Polymarket с оценками "Оракула"
на основе внешних данных (цены Binance).

Запуск:
    python market_analyzer.py                    # стандартный запуск
    python market_analyzer.py --threshold 0.10   # снизить порог
    python market_analyzer.py --mock             # на мок-данных
    python market_analyzer.py --output json      # вывод в JSON
"""

import argparse
import json
import logging
import math
import re
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

# Попытка импорта requests (для реального режима)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️  Библиотека 'requests' не установлена. pip install requests")

# ============================================
# КОНФИГУРАЦИЯ
# ============================================

CONFIG = {
    # API endpoints
    "polymarket_api": "https://gamma-api.polymarket.com/events",
    "binance_api": "https://api.binance.com/api/v3/ticker/price",
    
    # Таймауты (секунды)
    "request_timeout": 10,
    "rate_limit_delay": 0.15,  # 10 запросов/сек максимум
    
    # Пороги анализа
    "default_threshold": 0.15,
    "min_volume": 10000,
    
    # Волатильность активов (годовая)
    "volatility": {
        "BTC": 0.65,
        "ETH": 0.80,
        "SOL": 1.10,
    },
    
    # Крипто-символы для Binance
    "binance_symbols": {
        "BTC": "BTCUSDT",
        "ETH": "ETHUSDT",
        "SOL": "SOLUSDT",
    },
    
    # База данных
    "db_path": "markets.db",
    
    # Логирование
    "log_level": "INFO",
    "log_file": "scanner.log",
}

# ============================================
# ЛОГИРОВАНИЕ
# ============================================

logging.basicConfig(
    level=getattr(logging, CONFIG["log_level"]),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(CONFIG["log_file"], encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ============================================
# МОДУЛЬ: СКАНЕР (Scanner)
# ============================================

class MarketScanner:
    """Сканирует Polymarket и сохраняет данные в SQLite."""
    
    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode
        self.db_path = CONFIG["db_path"]
        self._init_db()
    
    def _init_db(self) -> None:
        """Инициализирует базу данных."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS markets (
                    id TEXT PRIMARY KEY,
                    question TEXT,
                    yes_price REAL,
                    implied_probability REAL,
                    volume REAL,
                    timestamp DATETIME
                )
            """)
            conn.commit()
            conn.close()
            logger.info(f"✅ База данных инициализирована: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
    
    def fetch_markets(self) -> List[Dict]:
        """Получает рынки с Polymarket API."""
        if self.mock_mode:
            return self._get_mock_markets()
        
        if not HAS_REQUESTS:
            logger.error("requests не установлен, переключаюсь на mock")
            return self._get_mock_markets()
        
        try:
            params = {
                "limit": 50,
                "active": True,
                "closed": False,
            }
            response = requests.get(
                CONFIG["polymarket_api"],
                params=params,
                timeout=CONFIG["request_timeout"]
            )
            response.raise_for_status()
            events = response.json()
            
            markets = []
            for event in events:
                # Фильтруем крипто-рынки
                question = event.get("question", "")
                if not re.search(r'bitcoin|btc|ethereum|eth|solana|sol|crypto', 
                                question, re.IGNORECASE):
                    continue
                
                for market_data in event.get("markets", []):
                    try:
                        outcome_prices = market_data.get("outcomePrices", "[0.5]")
                        if isinstance(outcome_prices, str):
                            prices = outcome_prices.strip("[]").split(",")
                            yes_price = float(prices[0])
                        else:
                            yes_price = float(outcome_prices[0])
                    except (ValueError, IndexError):
                        yes_price = 0.5
                    
                    market = {
                        "id": market_data.get("conditionId", event.get("id", "")),
                        "question": question,
                        "yes_price": yes_price,
                        "implied_probability": yes_price,
                        "volume": float(market_data.get("volume", 0) or 0),
                        "timestamp": datetime.now().isoformat(),
                    }
                    markets.append(market)
                
                time.sleep(CONFIG["rate_limit_delay"])
            
            logger.info(f"📡 Загружено {len(markets)} крипто-рынков")
            return markets
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки рынков: {e}")
            logger.info("⚠️  Переключаюсь на мок-данные")
            return self._get_mock_markets()
    
    def save_to_db(self, markets: List[Dict]) -> None:
        """Сохраняет рынки в SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for m in markets:
                cursor.execute("""
                    INSERT OR REPLACE INTO markets 
                    (id, question, yes_price, implied_probability, volume, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (m["id"], m["question"], m["yes_price"], 
                      m["implied_probability"], m["volume"], m["timestamp"]))
            conn.commit()
            conn.close()
            logger.info(f"💾 Сохранено {len(markets)} записей в БД")
        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка сохранения в БД: {e}")
    
    def load_from_db(self) -> List[Dict]:
        """Загружает свежие рынки из БД."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, question, yes_price, implied_probability, volume, timestamp
                FROM markets ORDER BY timestamp DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            return [
                {
                    "id": r[0], "question": r[1], "yes_price": r[2],
                    "implied_probability": r[3], "volume": r[4], "timestamp": r[5]
                }
                for r in rows
            ]
        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка чтения из БД: {e}")
            return []
    
    @staticmethod
    def _get_mock_markets() -> List[Dict]:
        """Возвращает мок-данные для тестирования."""
        return [
            {
                "id": "btc-70k-dec26",
                "question": "Will Bitcoin be above $70,000 on December 31, 2026?",
                "yes_price": 0.65,
                "implied_probability": 0.65,
                "volume": 2450000,
                "timestamp": datetime.now().isoformat(),
            },
            {
                "id": "eth-4k-jun26",
                "question": "Will Ethereum exceed $4,000 by June 30, 2026?",
                "yes_price": 0.42,
                "implied_probability": 0.42,
                "volume": 1870000,
                "timestamp": datetime.now().isoformat(),
            },
            {
                "id": "btc-100k-mar26",
                "question": "Will BTC reach $100,000 before March 1, 2026?",
                "yes_price": 0.78,
                "implied_probability": 0.78,
                "volume": 5230000,
                "timestamp": datetime.now().isoformat(),
            },
            {
                "id": "eth-5k-dec26",
                "question": "Will Ethereum be above $5,000 at end of 2026?",
                "yes_price": 0.35,
                "implied_probability": 0.35,
                "volume": 980000,
                "timestamp": datetime.now().isoformat(),
            },
            {
                "id": "btc-50k-mar26",
                "question": "Will Bitcoin drop below $50,000 before March 2026?",
                "yes_price": 0.18,
                "implied_probability": 0.18,
                "volume": 3100000,
                "timestamp": datetime.now().isoformat(),
            },
            {
                "id": "sol-200-jun26",
                "question": "Will Solana be above $200 by June 2026?",
                "yes_price": 0.52,
                "implied_probability": 0.52,
                "volume": 1240000,
                "timestamp": datetime.now().isoformat(),
            },
        ]


# ============================================
# МОДУЛЬ: ОРАКУЛ (Oracle)
# ============================================

class Oracle:
    """Вычисляет 'объективную' вероятность на основе внешних данных."""
    
    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode
        # Мок-цены для тестирования
        self._mock_prices: Dict[str, float] = {"BTC": 84500, "ETH": 3250, "SOL": 178}
    
    def get_current_price(self, asset: str) -> Optional[float]:
        """Получает текущую цену актива."""
        if self.mock_mode:
            return self._mock_prices.get(asset)
        
        if not HAS_REQUESTS:
            return self._mock_prices.get(asset)
        
        try:
            symbol = CONFIG["binance_symbols"].get(asset)
            if not symbol:
                return None
            
            response = requests.get(
                CONFIG["binance_api"],
                params={"symbol": symbol},
                timeout=CONFIG["request_timeout"]
            )
            response.raise_for_status()
            data = response.json()
            return float(data["price"])
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения цены {asset}: {e}")
            return self._mock_prices.get(asset)
    
    def parse_question(self, question: str) -> Dict[str, Any]:
        """Парсит вопрос рынка."""
        result: Dict[str, Any] = {
            "asset": None,
            "strike_price": None,
            "direction": "above",
            "expiry_date": None,
        }
        
        # Определяем актив
        asset_patterns = {
            "BTC": r'bitcoin|btc',
            "ETH": r'ethereum|eth(?!ereum)',
            "SOL": r'solana|(?<!\w)sol(?!\w)',
        }
        for asset, pattern in asset_patterns.items():
            if re.search(pattern, question, re.IGNORECASE):
                result["asset"] = asset
                break
        
        # Направление
        if re.search(r'below|drop|under|less than', question, re.IGNORECASE):
            result["direction"] = "below"
        
        # Ценовой порог (с $)
        price_match = re.search(r'\$\s*([\d,]+(?:\.\d+)?)\s*(k|K)?', question)
        if price_match:
            price = float(price_match.group(1).replace(',', ''))
            if price_match.group(2):
                price *= 1000
            result["strike_price"] = price
        
        # Дата экспирации
        months = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
        }
        date_match = re.search(
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})?,?\s*(\d{4})',
            question, re.IGNORECASE
        )
        if date_match:
            month = months.get(date_match.group(1)[:3].lower(), 12)
            day = int(date_match.group(2)) if date_match.group(2) else 31
            year = int(date_match.group(3))
            try:
                result["expiry_date"] = datetime(year, month, day)
            except ValueError:
                pass
        
        # Альтернативный формат даты
        if not result["expiry_date"]:
            year_match = re.search(r'(?:end of|by)\s*(\d{4})', question, re.IGNORECASE)
            if year_match:
                year = int(year_match.group(1))
                result["expiry_date"] = datetime(year, 12, 31)
        
        return result
    
    def get_real_world_probability(self, market: Dict) -> Dict:
        """Вычисляет объективную вероятность."""
        parsed = self.parse_question(market["question"])
        
        if not parsed["asset"] or not parsed["strike_price"]:
            return {
                "market_id": market["id"],
                "oracle_probability": 0.5,
                "confidence": 0.1,
                "reasoning": "Не удалось распарсить вопрос",
            }
        
        current_price = self.get_current_price(parsed["asset"])
        if current_price is None:
            return {
                "market_id": market["id"],
                "oracle_probability": 0.5,
                "confidence": 0.1,
                "reasoning": f"Не удалось получить цену {parsed['asset']}",
            }
        
        strike = parsed["strike_price"]
        volatility = CONFIG["volatility"].get(parsed["asset"], 0.7)
        
        # Дни до экспирации
        now = datetime.now()
        if parsed["expiry_date"]:
            days_to_expiry = max(1, (parsed["expiry_date"] - now).days)
        else:
            days_to_expiry = 365
        
        # Расстояние от страйка (%)
        distance_pct = (current_price - strike) / strike
        
        # Масштабированная волатильность
        time_scaled_vol = volatility * math.sqrt(days_to_expiry / 365)
        
        # Z-score
        z_score = distance_pct / time_scaled_vol if time_scaled_vol > 0 else 0
        
        # Сигмоида -> вероятность
        if parsed["direction"] == "above":
            probability = 1 / (1 + math.exp(-z_score * 1.5))
        else:
            probability = 1 / (1 + math.exp(z_score * 1.5))
        
        probability = max(0.02, min(0.98, probability))
        
        # Уверенность
        confidence = min(0.95, max(0.3, abs(z_score) * 0.3 + 0.3))
        
        # Объяснение
        direction_text = "ВЫШЕ" if current_price > strike else "НИЖЕ"
        reasoning = (
            f"Текущая цена {parsed['asset']} (${current_price:,.0f}) "
            f"{direction_text} порога ${strike:,.0f}. "
            f"До экспирации {days_to_expiry} дней."
        )
        
        return {
            "market_id": market["id"],
            "oracle_probability": round(probability, 3),
            "confidence": round(confidence, 3),
            "reasoning": reasoning,
            "current_price": current_price,
            "days_to_expiry": days_to_expiry,
        }


# ============================================
# МОДУЛЬ: ДЕТЕКТОР (Anomaly Detector)
# ============================================

class AnomalyDetector:
    """Находит арбитражные возможности."""
    
    def __init__(self, oracle: Oracle):
        self.oracle = oracle
    
    def find_opportunities(
        self, markets: List[Dict], threshold: float = None
    ) -> List[Dict]:
        """Находит рынки с существенным расхождением."""
        if threshold is None:
            threshold = CONFIG["default_threshold"]
        
        opportunities = []
        
        for market in markets:
            try:
                oracle_result = self.oracle.get_real_world_probability(market)
                edge = oracle_result["oracle_probability"] - market["implied_probability"]
                abs_edge = abs(edge)
                
                if abs_edge >= threshold:
                    recommendation = "BUY YES" if edge > 0 else "BUY NO"
                    
                    if abs_edge >= 0.25:
                        severity = "high"
                    elif abs_edge >= 0.18:
                        severity = "medium"
                    else:
                        severity = "low"
                    
                    opportunities.append({
                        "market": market,
                        "oracle": oracle_result,
                        "edge": round(edge, 3),
                        "abs_edge": abs_edge,
                        "recommendation": recommendation,
                        "severity": severity,
                    })
            except Exception as e:
                logger.error(f"Ошибка анализа {market['id']}: {e}")
        
        # Сортировка по убыванию edge
        opportunities.sort(key=lambda x: x["abs_edge"], reverse=True)
        
        logger.info(f"🔍 Найдено {len(opportunities)} возможностей (порог: {threshold*100:.0f}%)")
        return opportunities


# ============================================
# МОДУЛЬ: ОТЧЁТ (Reporter)
# ============================================

class Reporter:
    """Генерирует отчёты."""
    
    @staticmethod
    def generate_text_report(opportunities: List[Dict]) -> str:
        """Генерирует текстовый отчёт."""
        if not opportunities:
            return "⚠️  Арбитражных возможностей не обнаружено."
        
        lines = []
        lines.append("=" * 60)
        lines.append("🔍 ОТЧЁТ СКАНЕРА АРБИТРАЖНЫХ ВОЗМОЖНОСТЕЙ")
        lines.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"📊 Найдено возможностей: {len(opportunities)}")
        lines.append("=" * 60)
        lines.append("")
        
        for opp in opportunities:
            m = opp["market"]
            o = opp["oracle"]
            edge_pct = opp["edge"] * 100
            market_pct = m["implied_probability"] * 100
            oracle_pct = o["oracle_probability"] * 100
            vol = m["volume"]
            
            lines.append("-" * 50)
            lines.append(f"🔥 ВОЗМОЖНОСТЬ АРБИТРАЖА [{opp['severity'].upper()}]")
            lines.append(f"📊 Рынок: {m['question']}")
            lines.append(
                f"💰 Цена рынка: {market_pct:.1f}% | "
                f"Оценка оракула: {oracle_pct:.1f}% | "
                f"Edge: {'+' if edge_pct > 0 else ''}{edge_pct:.1f}%"
            )
            lines.append(f"📈 Объем: ${vol:,.0f}")
            lines.append(f"💡 Рекомендация: {opp['recommendation']}")
            lines.append(f"📝 {o['reasoning']}")
            lines.append("")
        
        lines.append("=" * 60)
        lines.append("⚠️  Это не финансовый совет. Проводите собственный анализ.")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_json_report(opportunities: List[Dict]) -> str:
        """Генерирует JSON-отчёт."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_opportunities": len(opportunities),
            "opportunities": [
                {
                    "market_id": opp["market"]["id"],
                    "question": opp["market"]["question"],
                    "market_probability": opp["market"]["implied_probability"],
                    "oracle_probability": opp["oracle"]["oracle_probability"],
                    "edge": opp["edge"],
                    "recommendation": opp["recommendation"],
                    "severity": opp["severity"],
                    "volume": opp["market"]["volume"],
                }
                for opp in opportunities
            ],
        }
        return json.dumps(report, indent=2, ensure_ascii=False)


# ============================================
# ТОЧКА ВХОДА
# ============================================

def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(
        description="PolyArb Scanner — Сканер арбитражных возможностей"
    )
    parser.add_argument(
        "--threshold", type=float, default=CONFIG["default_threshold"],
        help=f"Минимальный edge для отчёта (по умолчанию: {CONFIG['default_threshold']})"
    )
    parser.add_argument(
        "--output", choices=["text", "json"], default="text",
        help="Формат вывода (по умолчанию: text)"
    )
    parser.add_argument(
        "--save-history", action="store_true",
        help="Сохранить историю в БД"
    )
    parser.add_argument(
        "--mock", action="store_true",
        help="Использовать мок-данные (без API-вызовов)"
    )
    args = parser.parse_args()
    
    logger.info("🚀 Запуск PolyArb Scanner...")
    logger.info(f"   Порог: {args.threshold*100:.0f}% | Режим: {'MOCK' if args.mock else 'LIVE'}")
    
    # 1. Сканирование
    scanner = MarketScanner(mock_mode=args.mock)
    markets = scanner.fetch_markets()
    
    if not markets:
        logger.error("❌ Не удалось получить данные рынков")
        sys.exit(1)
    
    # 2. Сохранение (опционально)
    if args.save_history:
        scanner.save_to_db(markets)
    
    # 3. Анализ
    oracle = Oracle(mock_mode=args.mock)
    detector = AnomalyDetector(oracle)
    opportunities = detector.find_opportunities(markets, args.threshold)
    
    # 4. Отчёт
    reporter = Reporter()
    if args.output == "json":
        print(reporter.generate_json_report(opportunities))
    else:
        print(reporter.generate_text_report(opportunities))
    
    logger.info("✅ Сканирование завершено")


if __name__ == "__main__":
    main()
