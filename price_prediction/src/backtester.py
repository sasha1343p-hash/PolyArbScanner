import pandas as pd
import numpy as np
import joblib
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Backtester:
    def __init__(self, model_path='models/price_movement_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.feature_columns = None
    
    def load_model(self):
        """Загружает модель"""
        if not os.path.exists(self.model_path):
            logging.error(f"❌ Модель не найдена: {self.model_path}")
            return False
        
        bundle = joblib.load(self.model_path)
        self.model = bundle['model']
        self.feature_columns = bundle['feature_columns']
        return True
    
    def backtest(
        self, 
        dataset_path='data/dataset.csv',
        probability_threshold=0.65,  # Покупаем если вероятность > 65%
        initial_capital=1000,
        position_size=50  # Размер одной позиции
    ):
        """
        Бэктестит стратегию на исторических данных.
        
        Стратегия:
        - Если P(рост) > threshold → покупаем
        - Если цена выросла на target_threshold → продаем с прибылью
        - Иначе → убыток
        """
        if not self.load_model():
            return pd.DataFrame()
        
        if not os.path.exists(dataset_path):
            logging.error(f"❌ Файл {dataset_path} не найден")
            return pd.DataFrame()
        
        df = pd.read_csv(dataset_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Предсказания
        X = df[self.feature_columns]
        df['predicted_proba'] = self.model.predict_proba(X)[:, 1]
        
        # Симуляция торговли
        capital = initial_capital
        trades = []
        
        for idx, row in df.iterrows():
            # Решение о покупке
            if row['predicted_proba'] > probability_threshold:
                # Покупаем
                entry_price = row['current_price']
                exit_price = row['future_price']
                
                # P&L
                pnl = position_size * (exit_price - entry_price) / entry_price
                
                capital += pnl
                
                trades.append({
                    'timestamp': row['timestamp'],
                    'market_id': row['market_id'],
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'predicted_proba': row['predicted_proba'],
                    'pnl': pnl,
                    'capital': capital
                })
        
        trades_df = pd.DataFrame(trades)
        
        # Статистика
        logging.info(f"\n{'='*60}")
        logging.info("РЕЗУЛЬТАТЫ БЭКТЕСТИНГА")
        logging.info("="*60)
        logging.info(f"Начальный капитал: ${initial_capital}")
        logging.info(f"Финальный капитал: ${capital:.2f}")
        logging.info(f"Total P&L: ${capital - initial_capital:.2f} ({(capital/initial_capital - 1):.1%})")
        logging.info(f"Всего trades: {len(trades_df)}")
        
        if len(trades_df) > 0:
            winning_trades = len(trades_df[trades_df['pnl'] > 0])
            losing_trades = len(trades_df[trades_df['pnl'] <= 0])
            
            win_rate = winning_trades / len(trades_df)
            avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
            avg_loss = trades_df[trades_df['pnl'] <= 0]['pnl'].mean() if losing_trades > 0 else 0
            
            logging.info(f"Winning trades: {winning_trades} ({win_rate:.1%})")
            logging.info(f"Losing trades: {losing_trades} ({1-win_rate:.1%})")
            logging.info(f"Avg win: ${avg_win:.2f}")
            logging.info(f"Avg loss: ${avg_loss:.2f}")
            
            # Max drawdown
            capital_series = trades_df['capital']
            running_max = capital_series.expanding().max()
            drawdown = (capital_series - running_max) / running_max
            max_drawdown = drawdown.min()
            
            logging.info(f"Max drawdown: {max_drawdown:.1%}")
            
            # Sharpe ratio (упрощенный)
            if len(trades_df) > 1:
                returns = trades_df['pnl'] / position_size
                sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
                logging.info(f"Sharpe ratio (annualized): {sharpe:.2f}")
        
        logging.info("="*60)
        
        return trades_df

if __name__ == "__main__":
    backtester = Backtester()
    trades_df = backtester.backtest(
        probability_threshold=0.65,
        initial_capital=1000,
        position_size=50
    )
    
    if not trades_df.empty:
        os.makedirs('data', exist_ok=True)
        trades_df.to_csv('data/backtest_trades.csv', index=False)
        logging.info("✅ Trades сохранены в data/backtest_trades.csv")
    else:
        logging.warning("⚠️  Нет trades для сохранения")
