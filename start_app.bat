@echo off
title Геоаналитическая панель Астаны

echo ========================================
echo 🗺️  ГЕОАНАЛИТИЧЕСКАЯ ПАНЕЛЬ АСТАНЫ
echo ========================================
echo.

echo 📦 Проверяем и устанавливаем зависимости...
pip install -r requirements.txt

echo.
echo 🚀 Запускаем Flask приложение...
echo.
echo ✅ После запуска откройте в браузере:
echo 🌐 http://localhost:5000
echo.
echo ⚠️  Для остановки нажмите Ctrl+C
echo.

python app.py

pause