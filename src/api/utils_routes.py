#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API endpoints для экологического анализа и дополнительных утилит
"""

from flask import Blueprint, jsonify, request
from geopy.geocoders import Nominatim
from ..services.data_service import DataService

# Создаем blueprint
utils_bp = Blueprint('utils', __name__)

# Глобальные сервисы
data_service: DataService = None


@utils_bp.route('/api/eco-analysis')
def get_eco_analysis():
    """API для экологического анализа"""
    try:
        df_clean = data_service.get_processed_data()
        
        # Константы для расчета
        fuel_consumption_per_100km = 8  # литров
        co2_per_liter = 2.3  # кг
        avg_trip_distance = 5  # км
        
        # Расчеты
        total_trips = df_clean['randomized_id'].nunique()
        total_distance = total_trips * avg_trip_distance
        total_fuel = total_distance * fuel_consumption_per_100km / 100
        total_co2 = total_fuel * co2_per_liter
        
        # Анализ эффективности скорости
        speed_efficiency = df_clean.copy()
        speed_efficiency['efficiency'] = speed_efficiency['spd'].apply(
            lambda x: 1.0 if 50 <= x <= 60 else (0.8 if 30 <= x <= 80 else 0.6)
        )
        
        avg_efficiency = speed_efficiency['efficiency'].mean()
        potential_savings = (1 - avg_efficiency) * total_co2
        
        eco_recommendations = [
            {
                'title': 'Оптимизация скоростного режима',
                'description': 'Поддержание скорости 50-60 км/ч снижает расход на 15%',
                'potential_saving_kg': float(round(potential_savings * 0.15, 1))
            },
            {
                'title': 'Планирование маршрутов',
                'description': 'Избежание пробок может снизить расход на 20%',
                'potential_saving_kg': float(round(total_co2 * 0.2, 1))
            },
            {
                'title': 'Электрификация парка',
                'description': 'Переход на электромобили снизит выбросы на 70%',
                'potential_saving_kg': float(round(total_co2 * 0.7, 1))
            }
        ]
        
        return jsonify({
            'total_distance_km': float(round(total_distance, 1)),
            'total_co2_kg': float(round(total_co2, 1)),
            'avg_efficiency': float(round(avg_efficiency, 3)),
            'potential_annual_savings_kg': float(round(potential_savings * 365 / 30, 1)),
            'recommendations': eco_recommendations,
            'trips_analyzed': int(total_trips)
        })
        
    except Exception as e:
        print(f"❌ Ошибка в /api/eco-analysis: {e}")
        return jsonify({'error': str(e)}), 500


@utils_bp.route('/api/get-address')
def get_address():
    """API для получения адреса по координатам"""
    try:
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        
        if not lat or not lng:
            return jsonify({'error': 'Необходимы параметры lat и lng'}), 400
        
        # Инициализируем геокодер
        geolocator = Nominatim(user_agent="indrive_geo_analysis", timeout=10)
        
        try:
            location = geolocator.reverse(f"{lat}, {lng}", language='ru')
            if location and location.address:
                return jsonify({
                    'address': location.address,
                    'success': True
                })
            else:
                return jsonify({
                    'address': 'Адрес не найден',
                    'success': False
                })
        except Exception as e:
            return jsonify({
                'address': f'Ошибка геокодирования: {str(e)}',
                'success': False
            })
            
    except Exception as e:
        print(f"❌ Ошибка в /api/get-address: {e}")
        return jsonify({'error': str(e)}), 500


@utils_bp.route('/favicon.ico')
def favicon():
    """Простой favicon endpoint"""
    return '', 204