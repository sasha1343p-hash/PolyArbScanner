# ⚡ Установка за 3 минуты

## 🎯 Самый простой способ

### Windows

1. Откройте папку `polymarket_ml`
2. **Двойной клик на `setup.bat`**
3. Ждите 3-5 минут
4. Готово! ✅

---

### Linux / macOS

```bash
cd polymarket_ml
python3 setup_crossplatform.py
```

---

## 🚀 Запуск

### После установки выполните:

**Windows:**
```cmd
start_all.bat
```

**Linux / macOS:**
```bash
chmod +x start_all.sh
./start_all.sh
```

---

## 📊 Что откроется

- 🌐 **Веб-дашборд**: http://localhost:3000
- 🔮 **ML API**: http://localhost:8000

---

## 🎮 Команды

```bash
# Предсказание
python ml_oracle.py predict market-001

# Проверка дрейфа
python ml_oracle.py drift-check

# Важность признаков
python ml_oracle.py feature-importance
```

---

## ❓ Проблемы?

### Python не найден
→ Установите с [python.org](https://python.org) (отметьте "Add to PATH")

### Ошибки при установке
→ Удалите папку `venv` и запустите `setup.bat` заново

### Порт занят
→ Используйте другой порт: `serve dist -l 4000`

---

**Всё! Теперь у вас работает ML Oracle! 🎉**
