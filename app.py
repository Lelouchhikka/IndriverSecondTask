#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask веб-приложение для геоаналитической панели транспортных потоков Астаны
Создает интерактивный дашборд для просмотра результатов анализа GPS-треков
"""

from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import folium
from folium.plugins import HeatMap
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from geopy.distance import geodesic
import warnings
warnings.filterwarnings('ignore')

# Инициализация Flask приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = 'geotracks_analysis_2024'

# Глобальные переменные для кэширования данных
cached_data = {}
analysis_results = {}

def load_and_process_data():
    """Загружает и обрабатывает данные при первом запуске"""
    global cached_data, analysis_results
    
    if 'df_clean' in cached_data:
        return cached_data
    
    print("🔄 Загружаем и обрабатываем данные...")
    
    # Загружаем данные
    data_path = "geo_locations_astana_hackathon"
    try:
        df = pd.read_csv(data_path, 
                        dtype={
                            'randomized_id': 'int64',
                            'lat': 'float32',
                            'lng': 'float32',
                            'alt': 'float32',
                            'spd': 'float32',
                            'azm': 'float32'
                        })
        
        print(f"✅ Загружено {len(df):,} записей")
        
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        # Создаем тестовые данные если файл не найден
        np.random.seed(42)
        n_records = 50000
        df = pd.DataFrame({
            'randomized_id': np.random.randint(1000, 9999, n_records),
            'lat': np.random.uniform(51.05, 51.25, n_records),
            'lng': np.random.uniform(71.3, 71.6, n_records),
            'alt': np.random.uniform(320, 380, n_records),
            'spd': np.random.exponential(25, n_records),
            'azm': np.random.uniform(0, 360, n_records)
        })
        print(f"⚠️ Используются тестовые данные: {len(df):,} записей")
    
    # Очищаем данные
    df_clean = clean_data(df)
    cached_data['df_clean'] = df_clean
    
    # Выполняем базовый анализ
    analysis_results.update(perform_analysis(df_clean))
    
    print("✅ Данные загружены и проанализированы")
    return cached_data

def clean_data(df):
    """Очищает данные от выбросов"""
    print("🧹 Очистка данных...")
    
    # Фильтруем по координатам Астаны
    valid_coords = (
        (df['lat'] >= 50.8) & (df['lat'] <= 51.5) &
        (df['lng'] >= 70.9) & (df['lng'] <= 72.0)
    )
    df_clean = df[valid_coords].copy()
    
    # Фильтруем по скорости (исключаем отрицательные значения)
    df_clean = df_clean[(df_clean['spd'] >= 0) & (df_clean['spd'] <= 200)]
    
    # Фильтруем по высоте
    df_clean = df_clean[(df_clean['alt'] >= 250) & (df_clean['alt'] <= 600)]
    
    # Фильтруем по азимуту
    df_clean = df_clean[(df_clean['azm'] >= 0) & (df_clean['azm'] <= 360)]
    
    # Удаляем короткие поездки
    trip_counts = df_clean['randomized_id'].value_counts()
    valid_trips = trip_counts[trip_counts >= 3].index
    df_clean = df_clean[df_clean['randomized_id'].isin(valid_trips)]
    
    print(f"✅ Очищено: {len(df_clean):,} записей")
    return df_clean

def perform_analysis(df_clean):
    """Выполняет основной анализ данных"""
    results = {}
    
    # Базовая статистика (конвертируем numpy типы в Python типы)
    results['basic_stats'] = {
        'total_records': int(len(df_clean)),
        'unique_trips': int(df_clean['randomized_id'].nunique()),
        'avg_speed': float(round(df_clean['spd'].mean(), 2)),
        'coverage_area': float(round((df_clean['lat'].max() - df_clean['lat'].min()) * 
                              (df_clean['lng'].max() - df_clean['lng'].min()) * 111 * 85, 1))
    }
    
    # Анализ скоростей
    def categorize_speed(speed):
        speed = float(speed)  # Убеждаемся, что это число
        if speed == 0:
            return 'Стоп'
        elif speed < 10:
            return 'Очень медленно'
        elif speed < 30:
            return 'Медленно'  
        elif speed < 50:
            return 'Умеренно'
        elif speed < 70:
            return 'Быстро'
        else:
            return 'Очень быстро'
    
    print("📊 Анализ распределения скоростей...")
    df_clean_copy = df_clean.copy()
    df_clean_copy['speed_category'] = df_clean_copy['spd'].apply(categorize_speed)
    speed_dist = df_clean_copy['speed_category'].value_counts()
    
    # Конвертируем в словарь с Python типами
    speed_distribution_dict = {}
    for category, count in speed_dist.items():
        speed_distribution_dict[str(category)] = int(count)
    
    results['speed_distribution'] = speed_distribution_dict
    print(f"✅ Категории скоростей: {speed_distribution_dict}")
    
    # Создание зон спроса (упрощенная версия)
    sample_coords = df_clean[['lat', 'lng']].sample(n=min(5000, len(df_clean)), random_state=42)
    kmeans = KMeans(n_clusters=10, random_state=42, n_init=10)
    zone_labels = kmeans.fit_predict(sample_coords)
    zone_centers = kmeans.cluster_centers_
    
    zones_data = []
    for i, center in enumerate(zone_centers):
        zone_demand = (zone_labels == i).sum()
        zones_data.append({
            'zone_id': int(i),
            'lat': float(center[0]),
            'lng': float(center[1]),
            'demand': int(zone_demand),
            'percentage': float(round(zone_demand / len(sample_coords) * 100, 1))
        })
    
    results['zones'] = sorted(zones_data, key=lambda x: x['demand'], reverse=True)
    
    # Анализ трафика по сетке
    grid_size = 0.02
    lat_min, lat_max = df_clean['lat'].min(), df_clean['lat'].max()
    lng_min, lng_max = df_clean['lng'].min(), df_clean['lng'].max()
    
    lat_bins = np.arange(lat_min, lat_max + grid_size, grid_size)
    lng_bins = np.arange(lng_min, lng_max + grid_size, grid_size)
    
    df_grid = df_clean.copy()
    df_grid['lat_bin'] = pd.cut(df_grid['lat'], bins=lat_bins, labels=False)
    df_grid['lng_bin'] = pd.cut(df_grid['lng'], bins=lng_bins, labels=False)
    
    grid_stats = df_grid.groupby(['lat_bin', 'lng_bin']).agg({
        'spd': ['mean', 'count'],
        'randomized_id': 'nunique'
    }).round(2)
    
    grid_stats.columns = ['avg_speed', 'points_count', 'unique_trips']
    grid_stats = grid_stats.reset_index()
    grid_stats = grid_stats[grid_stats['points_count'] >= 5]
    
    # Добавляем координаты центров
    grid_stats['lat_center'] = grid_stats['lat_bin'].apply(
        lambda x: float(lat_bins[int(x)] + grid_size/2) if pd.notna(x) else None
    )
    grid_stats['lng_center'] = grid_stats['lng_bin'].apply(
        lambda x: float(lng_bins[int(x)] + grid_size/2) if pd.notna(x) else None
    )
    
    # Конвертируем в обычные типы Python для JSON сериализации
    grid_records = []
    for _, row in grid_stats.iterrows():
        if pd.notna(row['lat_center']) and pd.notna(row['lng_center']):
            grid_records.append({
                'lat_bin': int(row['lat_bin']),
                'lng_bin': int(row['lng_bin']),
                'avg_speed': float(row['avg_speed']),
                'points_count': int(row['points_count']),
                'unique_trips': int(row['unique_trips']),
                'lat_center': float(row['lat_center']),
                'lng_center': float(row['lng_center'])
            })
    
    results['traffic_grid'] = grid_records
    
    # Создание данных для аномалий (упрощенный алгоритм)
    print("🔍 Анализ аномалий...")
    # Используем простую логику: точки с экстремальными скоростями или высотами
    speed_threshold_high = df_clean['spd'].quantile(0.95)  # 95-й перцентиль
    speed_threshold_low = df_clean['spd'].quantile(0.05)   # 5-й перцентиль
    alt_threshold = df_clean['alt'].quantile(0.98) if 'alt' in df_clean.columns else float('inf')
    
    anomaly_conditions = (
        (df_clean['spd'] > speed_threshold_high) | 
        (df_clean['spd'] < speed_threshold_low) |
        (df_clean['alt'] > alt_threshold if 'alt' in df_clean.columns else False)
    )
    
    anomalies_sample = df_clean[anomaly_conditions].sample(
        n=min(1000, len(df_clean[anomaly_conditions])), 
        random_state=42
    )
    
    anomalies_data = []
    for _, row in anomalies_sample.iterrows():
        anomalies_data.append({
            'lat': float(row['lat']),
            'lng': float(row['lng']),
            'spd': float(abs(row['spd'])),  # Используем абсолютное значение
            'alt': float(row['alt']) if 'alt' in row else 0.0,
            'is_anomaly': 1
        })
    
    # Добавляем немного нормальных точек для контраста
    normal_sample = df_clean[~anomaly_conditions].sample(n=500, random_state=42)
    for _, row in normal_sample.iterrows():
        anomalies_data.append({
            'lat': float(row['lat']),
            'lng': float(row['lng']),
            'spd': float(abs(row['spd'])),  # Используем абсолютное значение
            'alt': float(row['alt']) if 'alt' in row else 0.0,
            'is_anomaly': 0
        })
    
    results['anomalies_data'] = anomalies_data
    
    # Создание данных для популярных маршрутов
    print("🛣️  Анализ популярных маршрутов...")
    # Группируем по пользователям и создаем упрощенные "маршруты"
    trip_stats = df_clean.groupby('randomized_id').agg({
        'lat': ['min', 'max', 'count'],
        'lng': ['min', 'max'],
        'spd': 'mean'
    }).reset_index()
    
    # Упрощаем названия колонок
    trip_stats.columns = ['user_id', 'lat_min', 'lat_max', 'point_count', 'lng_min', 'lng_max', 'avg_speed']
    
    # Сортируем по количеству точек (популярность)
    trip_stats = trip_stats.sort_values('point_count', ascending=False)
    
    popular_routes = []
    for i, (_, row) in enumerate(trip_stats.head(20).iterrows()):
        popular_routes.append({
            'route_id': i + 1,
            'unique_trips': int(row['point_count']),
            'avg_speed': float(row['avg_speed']),
            'lat_span': float(row['lat_max'] - row['lat_min']),
            'lng_span': float(row['lng_max'] - row['lng_min'])
        })
    
    results['popular_routes'] = popular_routes
    
    print("✅ Анализ завершен")
    return results

@app.route('/')
def index():
    """Главная страница дашборда"""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """Простой favicon endpoint"""
    return '', 204

@app.route('/api/stats')
def get_stats():
    """API для получения базовой статистики"""
    try:
        if 'df_clean' not in cached_data:
            load_and_process_data()
        
        return jsonify(analysis_results['basic_stats'])
    except Exception as e:
        print(f"❌ Ошибка в /api/stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/speed-distribution')
def get_speed_distribution():
    """API для получения распределения скоростей"""
    try:
        if 'df_clean' not in cached_data:
            load_and_process_data()
        
        speed_data = analysis_results['speed_distribution']
        
        if not speed_data or len(speed_data) == 0:
            return jsonify({'error': 'Нет данных о распределении скоростей'}), 400
        
        # Проверяем, что у нас есть корректные данные
        categories = list(speed_data.keys())
        values = [int(v) for v in speed_data.values()]
        
        if sum(values) == 0:
            return jsonify({'error': 'Все значения скоростей равны нулю'}), 400
        
        # Создаем график с Plotly
        fig = px.pie(
            values=values,
            names=categories,
            title="Распределение поездок по скоростным категориям",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate='%{label}<br>%{value} поездок<br>%{percent}<extra></extra>'
        )
        
        fig.update_layout(
            height=400,
            margin=dict(t=50, r=30, b=50, l=50),
            showlegend=True
        )
        
        graphJSON = json.dumps(fig, cls=PlotlyJSONEncoder)
        return jsonify({'graph': graphJSON})
        
    except Exception as e:
        print(f"❌ Ошибка в /api/speed-distribution: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/zones')
def get_zones():
    """API для получения данных о зонах спроса"""
    try:
        if 'df_clean' not in cached_data:
            load_and_process_data()
        
        return jsonify(analysis_results['zones'])
    except Exception as e:
        print(f"❌ Ошибка в /api/zones: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/traffic-heatmap')
def get_traffic_heatmap():
    """API для создания тепловой карты"""
    try:
        if 'df_clean' not in cached_data:
            load_and_process_data()
        
        df_clean = cached_data['df_clean']
        
        # Семплируем данные для производительности
        df_sample = df_clean.sample(n=min(3000, len(df_clean)), random_state=42)
        
        # Координаты для тепловой карты (конвертируем в float)
        heat_data = [[float(row['lat']), float(row['lng'])] for idx, row in df_sample.iterrows()]
        
        # Центр карты
        center_lat = float(df_clean['lat'].mean())
        center_lng = float(df_clean['lng'].mean())
        
        # Создаем карту
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=11,
            tiles='OpenStreetMap'
        )
        
        # Добавляем тепловую карту
        HeatMap(
            heat_data,
            min_opacity=0.2,
            max_zoom=15,
            radius=15,
            blur=20,
            gradient={
                0.0: 'blue',
                0.3: 'cyan', 
                0.6: 'lime',
                0.8: 'yellow',
                1.0: 'red'
            }
        ).add_to(m)
        
        # Добавляем маркеры зон спроса
        for zone in analysis_results['zones'][:5]:  # Топ-5 зон
            folium.Marker(
                [zone['lat'], zone['lng']],
                popup=f"Зона {zone['zone_id']}: {zone['percentage']}% спроса",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
        
        return m._repr_html_()
    except Exception as e:
        print(f"❌ Ошибка в /api/traffic-heatmap: {e}")
        return f"<div class='alert alert-danger'>Ошибка загрузки карты: {str(e)}</div>"

@app.route('/api/traffic-scatter')
def get_traffic_scatter():
    """API для scatter plot трафика"""
    try:
        if 'df_clean' not in cached_data:
            load_and_process_data()
        
        traffic_data = analysis_results['traffic_grid']
        
        if not traffic_data:
            return jsonify({'error': 'Нет данных о трафике'}), 400
        
        # Создаем DataFrame для Plotly
        df_traffic = pd.DataFrame(traffic_data)
        
        if df_traffic.empty or len(df_traffic) < 2:
            return jsonify({'error': 'Недостаточно данных для построения графика'}), 400
        
        fig = px.scatter(
            df_traffic,
            x='lng_center',
            y='lat_center',
            size='points_count',
            color='avg_speed',
            title="Карта скоростей и плотности трафика",
            labels={
                'lng_center': 'Долгота', 
                'lat_center': 'Широта', 
                'avg_speed': 'Средняя скорость (км/ч)', 
                'points_count': 'Количество точек'
            },
            color_continuous_scale='RdYlGn',
            size_max=20,
            hover_data=['unique_trips']
        )
        
        fig.update_layout(
            height=450,
            margin=dict(t=50, r=30, b=50, l=50),
            xaxis_title="Долгота",
            yaxis_title="Широта"
        )
        
        graphJSON = json.dumps(fig, cls=PlotlyJSONEncoder)
        return jsonify({'graph': graphJSON})
        
    except Exception as e:
        print(f"❌ Ошибка в /api/traffic-scatter: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/zones-chart')
def get_zones_chart():
    """API для графика зон спроса"""
    try:
        if 'df_clean' not in cached_data:
            load_and_process_data()
        
        zones_data = analysis_results['zones'][:10]  # Топ-10 зон
        
        if not zones_data:
            return jsonify({'error': 'Нет данных о зонах'}), 400
        
        # Симулируем рекомендуемое количество водителей
        total_drivers = 100
        for zone in zones_data:
            zone['recommended_drivers'] = max(1, int(zone['percentage'] / 100 * total_drivers))
        
        # Подготавливаем данные для графика
        zone_names = [f"Зона {z['zone_id']}" for z in zones_data]
        demand_values = [z['demand'] for z in zones_data]
        
        # Проверяем корректность данных
        if not zone_names or not demand_values or len(zone_names) != len(demand_values):
            return jsonify({'error': 'Некорректные данные для построения графика'}), 400
        
        fig = px.bar(
            x=zone_names,
            y=demand_values,
            title="Топ-10 зон по спросу",
            labels={'x': 'Зоны', 'y': 'Количество поездок'},
            color=demand_values,
            color_continuous_scale='viridis',
            text=demand_values
        )
        
        # Настраиваем layout для стабильной работы
        fig.update_layout(
            showlegend=False,
            xaxis_tickangle=-45,
            height=400,
            margin=dict(t=50, r=30, b=100, l=50)
        )
        
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        
        graphJSON = json.dumps(fig, cls=PlotlyJSONEncoder)
        return jsonify({'graph': graphJSON})
        
    except Exception as e:
        print(f"❌ Ошибка в /api/zones-chart: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/anomalies')
def get_anomalies():
    """API для визуализации аномалий"""
    try:
        if 'df_clean' not in cached_data:
            load_and_process_data()
        
        anomalies_data = analysis_results.get('anomalies_data', [])
        
        if not anomalies_data or len(anomalies_data) < 5:
            return jsonify({'error': 'Недостаточно данных об аномалиях'}), 400
        
        # Создаем DataFrame для Plotly
        df_anomalies = pd.DataFrame(anomalies_data)
        
        # Ограничиваем количество точек для лучшей производительности
        if len(df_anomalies) > 2000:
            df_anomalies = df_anomalies.sample(n=2000, random_state=42)
        
        # Фиксируем отрицательные значения скорости для размера точек
        df_anomalies['size_value'] = df_anomalies['spd'].apply(lambda x: max(1, abs(x)))
        
        # Создаем scatter plot с цветовой кодировкой аномалий
        fig = px.scatter(
            df_anomalies,
            x='lng',
            y='lat',
            color='is_anomaly',
            size='size_value',
            title="Карта аномальных GPS точек",
            labels={
                'lng': 'Долгота',
                'lat': 'Широта', 
                'is_anomaly': 'Аномалия',
                'spd': 'Скорость (км/ч)'
            },
            color_discrete_map={0: 'blue', 1: 'red'},
            size_max=15,
            opacity=0.7,
            hover_data=['spd', 'alt']
        )
        
        fig.update_layout(
            height=450,
            margin=dict(t=50, r=30, b=50, l=50),
            xaxis_title="Долгота",
            yaxis_title="Широта"
        )
        
        graphJSON = json.dumps(fig, cls=PlotlyJSONEncoder)
        return jsonify({'graph': graphJSON})
        
    except Exception as e:
        print(f"❌ Ошибка в /api/anomalies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/popular-routes')
def get_popular_routes():
    """API для визуализации популярных маршрутов"""
    try:
        if 'df_clean' not in cached_data:
            load_and_process_data()
        
        routes_data = analysis_results.get('popular_routes', [])
        
        if not routes_data or len(routes_data) < 3:
            return jsonify({'error': 'Недостаточно данных о популярных маршрутах'}), 400
        
        # Берем топ-15 маршрутов
        top_routes = routes_data[:15]
        route_names = [f"Маршрут {i+1}" for i in range(len(top_routes))]
        route_counts = [int(route['unique_trips']) for route in top_routes]
        
        fig = px.bar(
            x=route_names,
            y=route_counts,
            title="Топ-15 популярных маршрутов",
            labels={'x': 'Маршруты', 'y': 'Количество уникальных поездок'},
            color=route_counts,
            color_continuous_scale='plasma'
        )
        
        fig.update_layout(
            height=450,
            margin=dict(t=50, r=30, b=80, l=50),
            xaxis_title="Маршруты",
            yaxis_title="Количество поездок",
            xaxis={'tickangle': 45}
        )
        
        graphJSON = json.dumps(fig, cls=PlotlyJSONEncoder)
        return jsonify({'graph': graphJSON})
        
    except Exception as e:
        print(f"❌ Ошибка в /api/popular-routes: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Запуск геоаналитической панели...")
    print("📊 Загрузка данных может занять некоторое время...")
    
    # Предварительная загрузка данных
    load_and_process_data()
    
    print("✅ Готово! Открывайте http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)