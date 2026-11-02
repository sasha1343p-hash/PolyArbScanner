# 🚀 Инструкция по запуску PolyArb Scanner

## ⚡ Быстрый старт (3 шага)

### 1️⃣ Соберите веб-дашборд

Откройте терминал в корне проекта и выполните:

```bash
npm run build
```

Это создаст папку `dist/` с собранным приложением.

### 2️⃣ Запустите веб-сервер

```bash
npx serve dist
```

Откроется на **http://localhost:3000**

### 3️⃣ Откройте в браузере

Перейдите по адресу: **http://localhost:3000**

---

## 🔧 Альтернативный способ (без npm)

Если не хотите использовать npm, просто откройте файл:

```
dist/index.html
```

в браузере двойным кликом.

---

## 🐍 Запуск ML API (опционально)

Если хотите использовать ML модель через API:

### 1️⃣ Перейдите в папку polymarket_ml

```bash
cd polymarket_ml
```

### 2️⃣ Активируйте виртуальное окружение

**Windows:**
```cmd
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3️⃣ Установите зависимости (если ещё не установлены)

```bash
pip install fastapi uvicorn
```

### 4️⃣ Запустите API сервер

```bash
python api_server.py
```

API будет доступен на **http://localhost:8000**

Документация API: **http://localhost:8000/docs**

---

## 🧪 Проверка работы

### Веб-дашборд
- Откройте **http://localhost:3000**
- Должна отобразиться панель с метриками и таблицей возможностей

### ML API
- Откройте **http://localhost:8000/api/health**
- Должен вернуться JSON: `{"status": "ok", "model_loaded": true, ...}`

### Тест предсказания
```bash
curl http://localhost:8000/api/predict/market-001
```

---

## 🐛 Решение проблем

### Ошибка 404 при открытии http://localhost:3000

**Причина:** Папка `dist/` не создана или пуста

**Решение:**
```bash
npm run build
npx serve dist
```

### Ошибка "ModuleNotFoundError: No module named 'fastapi'"

**Решение:**
```bash
cd polymarket_ml
pip install fastapi uvicorn
```

### Ошибка "Модель не загружена"

**Решение:** Обучите модель
```bash
cd polymarket_ml
python ml_oracle.py train
```

### Порт 3000 или 8000 занят

**Решение:** Используйте другой порт
```bash
# Для веб-дашборда
npx serve dist -p 3001

# Для API
python api_server.py --port 8001
```

---

## 📋 Структура проекта

```
PolyArbScanner/
├── dist/                    # Собранный веб-дашборд (после npm run build)
├── src/                     # Исходный код React приложения
├── polymarket_ml/           # Python ML модуль
│   ├── ml_oracle/          # ML модели
│   ├── api_server.py       # FastAPI сервер
│   └── artifacts/          # Обученные модели
└── tests/                   # Тесты
```

---

## 🎯 Что дальше?

После запуска вы сможете:
- ✅ Видеть арбитражные возможности в реальном времени
- ✅ Получать предсказания от ML модели
- ✅ Анализировать рынки с разными фильтрами
- ✅ Отслеживать историю edge для каждого рынка

**Удачи в арбитраже! 🚀**
