#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главное приложение для геоаналитической панели транспортных потоков Астаны
Новая архитектура с модульной структурой
"""

import os
import warnings
from flask import Flask, render_template

# Подавляем предупреждения
warnings.filterwarnings('ignore')

# Импорты нашей архитектуры  
from src.config.config import get_config
from src.services.data_service import DataService
from src.services.ai_service import AIService
from src.services.analysis_service import AnalysisService

# Импорты API blueprints
from src.api.stats_routes import stats_bp
from src.api.analysis_routes import analysis_bp
from src.api.utils_routes import utils_bp

# Инициализируем глобальные сервисы
data_service = None
ai_service = None
analysis_service = None


def create_app(config_name: str = None) -> Flask:
    """Фабрика создания приложения"""
    
    # Получаем конфигурацию
    config = get_config(config_name)
    
    # Создаем Flask приложение
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Инициализируем сервисы
    global data_service, ai_service, analysis_service
    
    print("🚀 Инициализация сервисов...")
    ai_service = AIService(config)
    data_service = DataService(config) 
    analysis_service = AnalysisService(config, ai_service)
    
    # Инжектируем сервисы в blueprints
    _inject_services_to_blueprints()
    
    # Регистрируем blueprints
    app.register_blueprint(stats_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(utils_bp)
    
    # Основные маршруты
    @app.route('/')
    def index():
        """Главная страница дашборда"""
        return render_template('index.html')
    
    return app


def _inject_services_to_blueprints():
    """Инжектирует сервисы в модули blueprints"""
    # Инжекция в stats_routes
    import src.api.stats_routes as stats_module
    stats_module.data_service = data_service
    stats_module.analysis_service = analysis_service
    
    # Инжекция в analysis_routes
    import src.api.analysis_routes as analysis_module
    analysis_module.data_service = data_service
    analysis_module.analysis_service = analysis_service
    
    # Инжекция в utils_routes
    import src.api.utils_routes as utils_module
    utils_module.data_service = data_service


def load_and_cache_data():
    """Предварительная загрузка и кэширование данных"""
    print("📊 Загрузка данных может занять некоторое время...")
    
    try:
        # Быстрая загрузка sample данных для старта
        df_raw = data_service.load_data(sample_size=50000)  # Только 50k записей для быстрого старта
        df_clean = data_service.clean_data(df_raw, sample_size=50000)
        
        # Выполняем базовый анализ для кэширования
        data_service.get_basic_stats(df_clean)
        data_service.get_speed_distribution(df_clean)
        
        print("✅ Данные загружены и проанализированы")
        
    except Exception as e:
        print(f"⚠️ Ошибка предварительной загрузки: {e}")


if __name__ == '__main__':
    # Определяем окружение
    env = os.getenv('FLASK_ENV', 'development')
    
    # Создаем приложение
    app = create_app(env)
    config = get_config(env)
    
    # Предварительная загрузка данных только если не в reloader процессе
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        load_and_cache_data()
        print("✅ Готово! Открывайте http://localhost:5000")
    else:
        print("🚀 Запуск геоаналитической панели...")
        print("📊 Загрузка данных может занять некоторое время...")
    
    # Запускаем приложение
    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT
    )