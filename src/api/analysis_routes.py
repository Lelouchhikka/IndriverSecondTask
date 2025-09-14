#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API endpoints для анализа трафика и аномалий
"""

from flask import Blueprint, jsonify
from ..services.data_service import DataService
from ..services.analysis_service import AnalysisService
from ..utils.visualization import VisualizationUtils
from ..models.data_models import DataProcessor

# Создаем blueprint
analysis_bp = Blueprint('analysis', __name__)

# Глобальные сервисы (будут инициализированы в main app)
data_service: DataService = None
analysis_service: AnalysisService = None


@analysis_bp.route('/api/traffic-patterns')
def get_traffic_patterns():
    """API для получения паттернов трафика"""
    try:
        df_clean = data_service.get_processed_data()
        
        # Получаем базовую статистику по зонам
        zones_data = {
            'esil': len(df_clean[df_clean['latitude'].between(51.0, 51.2)]),
            'saryarka': len(df_clean[df_clean['latitude'].between(50.8, 51.0)]), 
            'almaty': len(df_clean[df_clean['latitude'].between(50.6, 50.8)]),
            'total_points': len(df_clean)
        }
        
        return jsonify({'zones': zones_data})
        
    except Exception as e:
        print(f"❌ Ошибка в /api/traffic-patterns: {e}")
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/api/heatmap')
def get_heatmap_data():
    """API для данных тепловой карты"""
    try:
        df_clean = data_service.get_processed_data()
        
        # Группируем по координатам для тепловой карты
        zones = {
            'esil': len(df_clean[df_clean['latitude'] > 51.1]),
            'saryarka': len(df_clean[(df_clean['latitude'] >= 50.9) & (df_clean['latitude'] <= 51.1)]),
            'almaty': len(df_clean[df_clean['latitude'] < 50.9]),
            'baikonur': len(df_clean[df_clean['longitude'] > 71.5])
        }
        
        return jsonify({'zones': zones})
        
    except Exception as e:
        print(f"❌ Ошибка в /api/heatmap: {e}")
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/api/traffic-heatmap')
def get_traffic_heatmap():
    """API для создания тепловой карты"""
    try:
        df_clean = data_service.get_processed_data()
        zones = analysis_service.create_demand_zones(df_clean)
        
        # Семплируем данные для производительности
        df_sample = df_clean.sample(n=min(3000, len(df_clean)), random_state=42)
        
        # Создаем карту
        heatmap_html = VisualizationUtils.create_heatmap(df_sample, zones)
        return heatmap_html
        
    except Exception as e:
        print(f"❌ Ошибка в /api/traffic-heatmap: {e}")
        return f"<div class='alert alert-danger'>Ошибка загрузки карты: {str(e)}</div>"


@analysis_bp.route('/api/traffic-scatter')
def get_traffic_scatter():
    """API для scatter plot трафика"""
    try:
        df_clean = data_service.get_processed_data()
        traffic_cells = analysis_service.analyze_traffic_grid(df_clean)
        
        graph_json = VisualizationUtils.create_traffic_scatter(traffic_cells)
        return jsonify({'graph': graph_json})
        
    except Exception as e:
        print(f"❌ Ошибка в /api/traffic-scatter: {e}")
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/api/anomalies')
def get_anomalies():
    """API для визуализации аномалий"""
    try:
        df_clean = data_service.get_processed_data()
        anomalies = analysis_service.detect_anomalies(df_clean)
        
        graph_json = VisualizationUtils.create_anomalies_scatter(anomalies)
        return jsonify({'graph': graph_json})
        
    except Exception as e:
        print(f"❌ Ошибка в /api/anomalies: {e}")
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/api/popular-routes')
def get_popular_routes():
    """API для визуализации популярных маршрутов"""
    try:
        df_clean = data_service.get_processed_data()
        routes = analysis_service.analyze_popular_routes(df_clean)
        
        graph_json = VisualizationUtils.create_routes_chart(routes)
        return jsonify({'graph': graph_json})
        
    except Exception as e:
        print(f"❌ Ошибка в /api/popular-routes: {e}")
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/api/safety-analysis')
def get_safety_analysis():
    """API для анализа безопасности"""
    try:
        df_clean = data_service.get_processed_data()
        df_ml = data_service.prepare_ml_data(df_clean)
        
        safety_data = analysis_service.analyze_safety(df_ml)
        
        if 'error' in safety_data:
            return jsonify({'error': safety_data['error']}), 400
        
        return jsonify(safety_data)
    except Exception as e:
        print(f"❌ Ошибка в /api/safety-analysis: {e}")
        return jsonify({'error': str(e)}), 500