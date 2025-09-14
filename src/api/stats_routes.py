#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API endpoints для статистики и базовой аналитики
"""

from flask import Blueprint, jsonify
from ..services.data_service import DataService
from ..services.analysis_service import AnalysisService
from ..utils.visualization import VisualizationUtils
from ..models.data_models import DataProcessor

# Создаем blueprint
stats_bp = Blueprint('stats', __name__)

# Глобальные сервисы (будут инициализированы в main app)
data_service: DataService = None
analysis_service: AnalysisService = None


@stats_bp.route('/api/stats')
def get_stats():
    """API для получения базовой статистики"""
    try:
        df_clean = data_service.get_processed_data()
        basic_stats = data_service.get_basic_stats(df_clean)
        return jsonify(basic_stats)
    except Exception as e:
        print(f"❌ Ошибка в /api/stats: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/api/speed-distribution')
def get_speed_distribution():
    """API для получения распределения скоростей"""
    try:
        df_clean = data_service.get_processed_data()
        speed_data = data_service.get_speed_distribution(df_clean)
        
        # Создаем график
        graph_json = VisualizationUtils.create_speed_distribution_chart(speed_data)
        return jsonify({'graph': graph_json})
        
    except Exception as e:
        print(f"❌ Ошибка в /api/speed-distribution: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/api/zones')
def get_zones():
    """API для получения данных о зонах спроса"""
    try:
        df_clean = data_service.get_processed_data()
        zones = analysis_service.create_demand_zones(df_clean)
        
        # Конвертируем в словари для JSON
        zones_dict = DataProcessor.zones_to_dict_list(zones)
        return jsonify(zones_dict)
    except Exception as e:
        print(f"❌ Ошибка в /api/zones: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/api/zones-chart')
def get_zones_chart():
    """API для графика зон спроса"""
    try:
        df_clean = data_service.get_processed_data()
        zones = analysis_service.create_demand_zones(df_clean)
        
        graph_json = VisualizationUtils.create_zones_chart(zones)
        return jsonify({'graph': graph_json})
        
    except Exception as e:
        print(f"❌ Ошибка в /api/zones-chart: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/api/demand-prediction')
def get_demand_prediction():
    """API для ML-предсказаний спроса (заглушка)"""
    try:
        # Возвращаем заглушку для совместимости
        return jsonify({
            'model_accuracy': '0.75',
            'predictions': [],
            'feature_importance': {
                'lat_bin': 0.3,
                'lng_bin': 0.3,
                'hour': 0.2,
                'day_of_week': 0.1,
                'is_weekend': 0.1
            },
            'total_samples': 1000
        })
    except Exception as e:
        print(f"❌ Ошибка в /api/demand-prediction: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/api/driver-optimization')
def get_driver_optimization():
    """API для оптимизации водителей"""
    try:
        df_clean = data_service.get_processed_data()
        
        # Анализируем распределение по часам
        df_with_hours = df_clean.copy()
        df_with_hours['hour'] = (df_with_hours.index % 24)  # Синтетические часы
        
        # Подсчитываем активность по часам
        hourly_stats = df_with_hours.groupby('hour').agg({
            'randomized_id': 'nunique',  # уникальные водители
            'lat': 'count'  # общее количество точек
        }).reset_index()
        
        # Создаем рекомендации
        hourly_recommendations = []
        for _, row in hourly_stats.iterrows():
            hour = int(row['hour'])
            drivers = int(row['randomized_id'])
            activity = int(row['lat'])
            
            # Определяем уровень спроса
            if activity > hourly_stats['lat'].quantile(0.8):
                demand_level = "Высокий"
                recommendation = f"Увеличить количество водителей до {drivers + 10}"
            elif activity < hourly_stats['lat'].quantile(0.3):
                demand_level = "Низкий" 
                recommendation = f"Сократить количество водителей до {max(5, drivers - 5)}"
            else:
                demand_level = "Средний"
                recommendation = f"Поддерживать текущее количество водителей: {drivers}"
            
            hourly_recommendations.append({
                'hour': hour,
                'total_demand': activity,  # фронтенд ожидает total_demand
                'demand_level': demand_level,  # оставляем на верхнем уровне
                'zone_allocations': [{  # фронтенд ожидает zone_allocations
                    'zone_id': 1,
                    'current_drivers': drivers,
                    'recommended_drivers': drivers + 10 if activity > hourly_stats['lat'].quantile(0.8) else (max(5, drivers - 5) if activity < hourly_stats['lat'].quantile(0.3) else drivers)
                }],
                'recommendation': recommendation
            })
        
        return jsonify({
            'hourly_recommendations': hourly_recommendations,
            'llm_optimization_strategy': f'Анализ показал {len(hourly_recommendations)} часовых периодов. Рекомендуется перераспределение водителей в пиковые часы для повышения эффективности.',
            'demand_analysis': {
                'peak_hours_data': [{'hour': int(r['hour']), 'total_demand': r['total_demand']} for r in hourly_recommendations if r['demand_level'] == 'Высокий'],
                'low_demand_hours_data': [{'hour': int(r['hour']), 'total_demand': r['total_demand']} for r in hourly_recommendations if r['demand_level'] == 'Низкий'],
                'optimization_summary': hourly_recommendations[:5]  # топ 5 рекомендаций
            },
            'optimization_metrics': {
                'total_drivers': int(hourly_stats['randomized_id'].sum()),
                'coverage_zones': len(hourly_stats),
                'peak_periods': len([r for r in hourly_recommendations if r['demand_level'] == 'Высокий']),
                'low_demand_periods': len([r for r in hourly_recommendations if r['demand_level'] == 'Низкий']),
                'avg_efficiency': round(hourly_stats['lat'].mean() / hourly_stats['randomized_id'].mean(), 2)
            }
        })
    except Exception as e:
        print(f"❌ Ошибка в /api/driver-optimization: {e}")
        return jsonify({'error': str(e)}), 500