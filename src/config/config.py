#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конфигурационный файл для геоаналитической панели
Содержит все настройки приложения
"""

import os
from typing import Dict, Any


class Config:
    """Базовая конфигурация приложения"""
    
    # Flask настройки
    SECRET_KEY = os.getenv('SECRET_KEY', 'geotracks_analysis_2024')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # Google AI настройки
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyDBiigAcAO-WyJmomxjhWjwolXqIQpvuVM')
    
    # Модели AI (по приоритету)
    AI_MODELS = [
        'gemini-1.5-flash', 
        'gemini-1.5-pro', 
        'gemini-pro', 
        'models/gemini-1.5-flash'
    ]
    
    # AI настройки генерации
    AI_CONFIG = {
        'max_tokens': 400,
        'temperature': 0.7,
        'top_p': 0.8,
        'top_k': 40
    }
    
    # Безопасность AI
    AI_SAFETY_SETTINGS = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    
    # Данные
    DATA_PATH = os.getenv('DATA_PATH', 'geo_locations_astana_hackathon')
    
    # Границы Астаны (для фильтрации)
    ASTANA_BOUNDS = {
        'lat_min': 50.8,
        'lat_max': 51.5,
        'lng_min': 70.9,
        'lng_max': 72.0
    }
    
    # Фильтры данных
    DATA_FILTERS = {
        'speed_min': 0,
        'speed_max': 200,
        'altitude_min': 250,
        'altitude_max': 600,
        'azimuth_min': 0,
        'azimuth_max': 360,
        'min_trip_points': 3
    }
    
    # ML настройки
    ML_CONFIG = {
        'grid_size': 0.02,
        'n_clusters': 10,
        'random_state': 42,
        'isolation_forest_contamination': 0.1,
        'max_sample_points': 5000,
        'rf_n_estimators': 50,
        'rf_max_depth': 10
    }
    
    # Геокодирование
    GEOCODING_CONFIG = {
        'user_agent': 'indrive_geo_analysis',
        'timeout': 10,
        'sleep_delay': 0.5,  # секунды между запросами
        'max_address_length': 60
    }
    
    # Анализ производительности
    PERFORMANCE_CONFIG = {
        'max_heatmap_points': 3000,
        'max_anomaly_points': 2000,
        'max_traffic_points': 5000,
        'top_zones_limit': 10,
        'top_routes_limit': 15
    }
    
    # Экологический анализ
    ECO_CONFIG = {
        'fuel_consumption_per_100km': 8,  # литров
        'co2_per_liter': 2.3,  # кг
        'avg_trip_distance': 5,  # км
        'optimal_speed_min': 50,  # км/ч
        'optimal_speed_max': 60   # км/ч
    }


class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True


class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False


class TestConfig(Config):
    """Конфигурация для тестирования"""
    DEBUG = True
    TESTING = True


# Словарь конфигураций
config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig, 
    'testing': TestConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: str = None) -> Config:
    """Получить конфигурацию по имени"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    return config_dict.get(config_name, DevelopmentConfig)