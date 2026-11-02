import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ABTester:
    def __init__(self, db_path='polymarket_history.db'):
        self.db_path = db_path
        
    def load_recent_markets(self, days=7):
        """Загружает завершенные рынки за последние N дней"""
        if not os.path.exists(self.db_path):
            logging.error(f"❌ База данных не найдена: {self.db_path}")
            return pd.DataFrame()
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Загружаем завершенные рынки с известными исходами
            markets_df = pd.read_sql_query('''
                SELECT mm.id, mm.question, mm.resolution, mm.end_date,
                       ph.yes_price as last_price,
                       ph.volume as last_volume
                FROM market_metadata mm
                JOIN price_history ph ON mm.id = ph.market_id
                WHERE mm.resolution IS NOT NULL
                  AND mm.end_date > ?
                GROUP BY mm.id
                ORDER BY mm.end_date DESC
            ''', conn, params=(cutoff_date,))
            
            conn.close()
            
            if markets_df.empty:
                logging.warning(f"⚠️  Нет завершенных рынков за последние {days} дней")
                logging.info("💡 Попробуйте увеличить период: python ab_test.py --days 30")
            else:
                logging.info(f"✅ Загружено {len(markets_df)} завершенных рынков")
            
            return markets_df
            
        except Exception as e:
            conn.close()
            logging.error(f"❌ Ошибка загрузки данных: {e}")
            return pd.DataFrame()
    
    def test_heuristic(self, markets_df):
        """Тестирует эвристический оракул"""
        logging.info("Тестирование эвристического оракула...")
        
        results = []
        
        for idx, market in markets_df.iterrows():
            market_id = market['id']
            question = market['question']
            market_price = market['last_price'] if pd.notna(market['last_price']) else 0.5
            actual_resolution = market['resolution']
            
            # Эвристика: используем текущую цену как вероятность
            heuristic_proba = market_price
            
            # Вычисляем edge
            edge = heuristic_proba - market_price
            
            # Определяем, было ли предсказание правильным
            predicted_yes = heuristic_proba > 0.5
            actual_yes = (actual_resolution == 'YES')
            correct = (predicted_yes == actual_yes)
            
            results.append({
                'market_id': market_id,
                'question': question,
                'market_price': market_price,
                'oracle_proba': heuristic_proba,
                'edge': edge,
                'abs_edge': abs(edge),
                'oracle_type': 'heuristic',
                'actual_resolution': actual_resolution,
                'correct': correct
            })
            
            # Прогресс
            if (idx + 1) % 10 == 0:
                logging.info(f"  Обработано {idx + 1}/{len(markets_df)} рынков")
        
        return pd.DataFrame(results)
    
    def test_ml(self, markets_df):
        """Тестирует ML-оракул"""
        logging.info("Тестирование ML-оракула...")
        
        # Загружаем модель
        from ml_oracle import MLOracle, FeatureExtractor
        from ml_oracle.feature_extractor import MarketMetadata
        
        model = MLOracle()
        model_path = 'artifacts/ml_oracle_bundle.pkl'
        
        if not model.load(model_path):
            logging.error("❌ Не удалось загрузить ML модель")
            return pd.DataFrame()
        
        # Загружаем scaler
        scaler_path = model_path.replace('.pkl', '_scaler.pkl')
        extractor = FeatureExtractor()
        if os.path.exists(scaler_path):
            extractor.load_scaler(scaler_path)
            extractor.feature_names = model.feature_names
        
        # Загружаем историю цен для всех рынков
        conn = sqlite3.connect(self.db_path)
        price_df = pd.read_sql_query('''
            SELECT market_id, timestamp, yes_price, volume, liquidity
            FROM price_history
            ORDER BY market_id, timestamp
        ''', conn)
        conn.close()
        
        results = []
        
        for idx, market in markets_df.iterrows():
            market_id = market['id']
            question = market['question']
            market_price = market['last_price'] if pd.notna(market['last_price']) else 0.5
            actual_resolution = market['resolution']
            
            # Получаем историю цен для этого рынка
            market_prices = price_df[price_df['market_id'] == market_id].copy()
            
            if market_prices.empty:
                # Если нет истории, используем рыночную цену
                ml_proba = market_price
                confidence = 0.0
            else:
                # Создаём метаданные
                metadata = MarketMetadata(
                    id=market_id,
                    question=question,
                    end_date=pd.to_datetime(market['end_date']) if pd.notna(market['end_date']) else None,
                )
                
                # Извлекаем признаки
                try:
                    features = extractor.extract_features(market_id, market_prices, metadata)
                    
                    # Получаем предсказание от ML
                    ml_proba, confidence = model.predict_with_confidence(features)
                    
                    if ml_proba is None:
                        ml_proba = market_price
                        confidence = 0.0
                        
                except Exception as e:
                    logging.warning(f"⚠️  Ошибка предсказания для {market_id}: {e}")
                    ml_proba = market_price
                    confidence = 0.0
            
            # Вычисляем edge
            edge = ml_proba - market_price
            
            # Определяем, было ли предсказание правильным
            predicted_yes = ml_proba > 0.5
            actual_yes = (actual_resolution == 'YES')
            correct = (predicted_yes == actual_yes)
            
            results.append({
                'market_id': market_id,
                'question': question,
                'market_price': market_price,
                'oracle_proba': ml_proba,
                'edge': edge,
                'abs_edge': abs(edge),
                'oracle_type': 'ml',
                'actual_resolution': actual_resolution,
                'correct': correct,
                'confidence': confidence
            })
            
            # Прогресс
            if (idx + 1) % 10 == 0:
                logging.info(f"  Обработано {idx + 1}/{len(markets_df)} рынков")
        
        return pd.DataFrame(results)
    
    def compare_results(self, heuristic_df, ml_df):
        """Сравнивает результаты"""
        logging.info("\n" + "=" * 70)
        logging.info("A/B ТЕСТ: ЭВРИСТИКА vs ML")
        logging.info("=" * 70)
        
        if heuristic_df.empty or ml_df.empty:
            logging.error("❌ Нет данных для сравнения")
            return
        
        # Статистики по эвристике
        logging.info("\n📊 ЭВРИСТИКА:")
        logging.info(f"   Всего рынков: {len(heuristic_df)}")
        logging.info(f"   Средний |edge|: {heuristic_df['abs_edge'].mean():.3f}")
        logging.info(f"   Максимальный |edge|: {heuristic_df['abs_edge'].max():.3f}")
        logging.info(f"   Рынков с |edge| > 0.15: {(heuristic_df['abs_edge'] > 0.15).sum()}")
        logging.info(f"   Рынков с |edge| > 0.20: {(heuristic_df['abs_edge'] > 0.20).sum()}")
        
        # Точность эвристики
        heuristic_accuracy = heuristic_df['correct'].mean()
        logging.info(f"   Точность предсказаний: {heuristic_accuracy:.1%}")
        
        # Статистики по ML
        logging.info("\n🤖 ML-ОРАКУЛ:")
        logging.info(f"   Всего рынков: {len(ml_df)}")
        logging.info(f"   Средний |edge|: {ml_df['abs_edge'].mean():.3f}")
        logging.info(f"   Максимальный |edge|: {ml_df['abs_edge'].max():.3f}")
        logging.info(f"   Рынков с |edge| > 0.15: {(ml_df['abs_edge'] > 0.15).sum()}")
        logging.info(f"   Рынков с |edge| > 0.20: {(ml_df['abs_edge'] > 0.20).sum()}")
        
        # Точность ML
        ml_accuracy = ml_df['correct'].mean()
        logging.info(f"   Точность предсказаний: {ml_accuracy:.1%}")
        
        # Средняя уверенность
        if 'confidence' in ml_df.columns:
            avg_confidence = ml_df['confidence'].mean()
            logging.info(f"   Средняя уверенность: {avg_confidence:.1%}")
        
        # Сравнение
        logging.info("\n📈 СРАВНЕНИЕ:")
        
        # Сравнение по edge
        if ml_df['abs_edge'].mean() > heuristic_df['abs_edge'].mean():
            improvement = ml_df['abs_edge'].mean() - heuristic_df['abs_edge'].mean()
            logging.info(f"   ✅ ML находит БОЛЬШЕ возможностей (средний edge выше на {improvement:.3f})")
        else:
            logging.info("   ⚠️  Эвристика находит БОЛЬШЕ возможностей (средний edge выше)")
            logging.info("   💡 ML модель может быть недообучена или данных недостаточно")
        
        # Сравнение по точности
        if ml_accuracy > heuristic_accuracy:
            accuracy_diff = ml_accuracy - heuristic_accuracy
            logging.info(f"   ✅ ML ТОЧНЕЕ (точность выше на {accuracy_diff:.1%})")
        elif ml_accuracy < heuristic_accuracy:
            accuracy_diff = heuristic_accuracy - ml_accuracy
            logging.info(f"   ⚠️  Эвристика ТОЧНЕЕ (точность выше на {accuracy_diff:.1%})")
        else:
            logging.info("   ➖ Точность одинаковая")
        
        # Распределение edge
        logging.info("\n📊 РАСПРЕДЕЛЕНИЕ EDGE:")
        bins = [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 1.0]
        
        heuristic_hist, _ = np.histogram(heuristic_df['abs_edge'], bins=bins)
        ml_hist, _ = np.histogram(ml_df['abs_edge'], bins=bins)
        
        logging.info("   Edge диапазон  | Эвристика | ML")
        logging.info("   " + "-" * 45)
        for i in range(len(bins) - 1):
            logging.info(f"   {bins[i]:.2f} - {bins[i+1]:.2f}      | {heuristic_hist[i]:9} | {ml_hist[i]:2}")
        
        # Топ рынков по edge для ML
        logging.info("\n🏆 ТОП-5 РЫНКОВ ПО EDGE (ML):")
        top_ml = ml_df.nlargest(5, 'abs_edge')
        for idx, row in top_ml.iterrows():
            direction = "BUY YES" if row['edge'] > 0 else "BUY NO"
            correct_mark = "✅" if row['correct'] else "❌"
            logging.info(f"   {correct_mark} {row['market_id']}: edge={row['edge']:+.3f} ({direction})")
            logging.info(f"      {row['question'][:60]}...")
        
        # Топ рынков по уверенности
        if 'confidence' in ml_df.columns:
            logging.info("\n🎯 ТОП-5 РЫНКОВ ПО УВЕРЕННОСТИ (ML):")
            top_conf = ml_df.nlargest(5, 'confidence')
            for idx, row in top_conf.iterrows():
                correct_mark = "✅" if row['correct'] else "❌"
                logging.info(f"   {correct_mark} {row['market_id']}: confidence={row['confidence']:.1%}, edge={row['edge']:+.3f}")
                logging.info(f"      {row['question'][:60]}...")
        
        logging.info("=" * 70)
    
    def run_ab_test(self, days=7):
        """Запускает полный A/B тест"""
        logging.info(f"Загрузка завершенных рынков за последние {days} дней...")
        markets_df = self.load_recent_markets(days)
        
        if markets_df.empty:
            logging.error("❌ Нет данных для A/B теста.")
            logging.info("💡 Создайте тестовую БД: python create_test_db.py")
            return
        
        # Тестируем эвристику
        heuristic_df = self.test_heuristic(markets_df)
        
        # Тестируем ML
        ml_df = self.test_ml(markets_df)
        
        if ml_df.empty:
            logging.error("❌ Не удалось получить предсказания от ML")
            return
        
        # Сравниваем
        self.compare_results(heuristic_df, ml_df)
        
        # Сохраняем результаты
        heuristic_df.to_csv('ab_test_heuristic.csv', index=False)
        ml_df.to_csv('ab_test_ml.csv', index=False)
        logging.info("\n✅ Результаты сохранены в ab_test_heuristic.csv и ab_test_ml.csv")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='A/B тестирование эвристики vs ML')
    parser.add_argument('--days', type=int, default=7, help='Период в днях (по умолчанию: 7)')
    args = parser.parse_args()
    
    tester = ABTester()
    tester.run_ab_test(days=args.days)
