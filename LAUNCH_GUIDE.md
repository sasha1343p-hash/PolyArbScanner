# 🚀 Инструкция по запуску PolyArb Scanner

## ✅ Предварительные требования

- [x] Тесты прошли успешно (41/41)
- [x] Модель обучена (`artifacts/ml_oracle_bundle.pkl`)
- [x] База данных создана (`polymarket_history.db`)
- [x] Веб-дашборд собран (`dist/`)

---

## 🎯 Быстрый запуск (рекомендуется)

### Windows

```cmd
start_app.bat
```

Это автоматически запустит:
- ML API сервер на `http://localhost:8000`
- Веб-дашборд на `http://localhost:3000`

### Linux/Mac

```bash
# Терминал 1: ML API сервер
cd polymarket_ml
source venv/bin/activate
python api_server.py

# Терминал 2: Веб-дашборд
npx serve dist -l 3000
```

---

## 🔧 Ручной запуск

### Шаг 1: Запуск ML API сервера

```bash
cd polymarket_ml

# Windows
venv\Scripts\activate
python api_server.py

# Linux/Mac
source venv/bin/activate
python api_server.py
```

**Ожидаемый вывод:**
```
==================================================
PolyArb ML API Server
==================================================
Запуск на http://localhost:8000
Документация: http://localhost:8000/docs
==================================================
✅ Модель загружена
✅ API сервер готов к работе
```

### Шаг 2: Запуск веб-дашборда

Откройте **новый терминал** и выполните:

```bash
# Если serve не установлен
npm install -g serve

# Запуск сервера
npx serve dist -l 3000
```

**Ожидаемый вывод:**
```
┌─────────────────────────────────────────┐
│                                         │
│   Serving!                              │
│                                         │
│   Local:    http://localhost:3000       │
│   Network:  http://192.168.x.x:3000    │
│                                         │
└─────────────────────────────────────────┘
```

### Шаг 3: Открытие в браузере

Откройте **http://localhost:3000** в браузере.

---

## 📊 Проверка работы

### 1. Проверка ML API

Откройте в браузере: **http://localhost:8000/api/health**

Должно вернуться:
```json
{
  "status": "ok",
  "model_loaded": true,
  "database_exists": true
}
```

### 2. Проверка предсказания

Откройте: **http://localhost:8000/docs**

Это откроет Swagger UI с документацией API.

Или выполните запрос:
```bash
curl http://localhost:8000/api/predict/market-001
```

### 3. Проверка веб-дашборда

Откройте: **http://localhost:3000**

Должен отобразиться дашборд с:
- Карточками метрик
- Таблицей возможностей
- Графиком истории edge
- Фильтрами

---

## 🔌 API Endpoints

### GET /api/health
Проверка работоспособности

### GET /api/predict/{market_id}
Предсказание для рынка

**Пример:**
```bash
curl http://localhost:8000/api/predict/market-001
```

**Ответ:**
```json
{
  "market_id": "market-001",
  "probability": 0.673,
  "confidence": 0.821,
  "recommendation": "BUY YES",
  "market_price": 0.65
}
```

### GET /api/markets
Список всех рынков

**Пример:**
```bash
curl http://localhost:8000/api/markets?limit=10
```

---

## 🛠 Устранение неполадок

### Проблема: "ModuleNotFoundError: No module named 'fastapi'"

**Решение:**
```bash
cd polymarket_ml
venv\Scripts\activate  # Windows
# или
source venv/bin/activate  # Linux/Mac

pip install fastapi uvicorn
```

### Проблема: "Модель не загружена"

**Решение:** Запустите обучение модели
```bash
cd polymarket_ml
python ml_oracle.py train
```

### Проблема: "База данных не найдена"

**Решение:** Создайте тестовую БД
```bash
cd polymarket_ml
python create_test_db.py
```

### Проблема: Порт 8000 или 3000 занят

**Решение:** Используйте другой порт
```bash
# ML API
python api_server.py --port 8001

# Веб-дашборд
npx serve dist -l 3001
```

---

## 📝 Логи

Логи ML API сервера сохраняются в:
- `polymarket_ml/logs/ml_oracle.log`

---

## 🔄 Обновление данных

### Переобучение модели

```bash
cd polymarket_ml
python ml_oracle.py train
```

### Обновление базы данных

```bash
cd polymarket_ml
python create_test_db.py
```

---

## 🎉 Готово!

Теперь у вас работает:
- ✅ ML API сервер (FastAPI) на `http://localhost:8000`
- ✅ Веб-дашборд (React) на `http://localhost:3000`
- ✅ Интеграция между ними через API

**Документация API:** http://localhost:8000/docs

---

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи в `polymarket_ml/logs/ml_oracle.log`
2. Проверьте, что модель обучена: `artifacts/ml_oracle_bundle.pkl`
3. Проверьте, что БД создана: `polymarket_history.db`
4. Убедитесь, что порты 8000 и 3000 свободны

**Удачи в арбитраже! 🚀**
