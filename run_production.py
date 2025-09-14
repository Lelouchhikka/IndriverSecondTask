#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска приложения в production режиме
"""

import os
import sys
from app_new import create_app, load_and_cache_data

def run_production():
    """Запуск приложения в production режиме"""
    
    # Устанавливаем production окружение
    os.environ['FLASK_ENV'] = 'production'
    
    print("🚀 Запуск production сервера...")
    
    # Создаем приложение
    app = create_app('production')
    
    # Загружаем данные
    load_and_cache_data()
    
    print("✅ Production сервер готов!")
    print("🌐 Приложение доступно на http://0.0.0.0:5000")
    
    # Запускаем
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    run_production()