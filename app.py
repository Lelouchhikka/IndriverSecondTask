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
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import time
import os
import google.generativeai as genai
import warnings
warnings.filterwarnings('ignore')

# Инициализация Flask приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = 'geotracks_analysis_2024'

# Инициализация Google AI клиента
# Рекомендуется установить переменную окружения GOOGLE_API_KEY
try:
    google_api_key = os.getenv('GOOGLE_API_KEY', 'AIzaSyDBiigAcAO-WyJmomxjhWjwolXqIQpvuVM')
    genai.configure(api_key=google_api_key)
    
    # Сначала проверим доступные модели
    try:
        available_models = [m.name for m in genai.list_models()]
        print(f"📋 Доступные модели: {available_models[:3]}...")  # Показываем первые 3
    except:
        print("⚠️ Не удалось получить список моделей")
    
    # Попробуем разные модели по порядку
    model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro', 'models/gemini-1.5-flash']
    model = None
    
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            print(f"✅ Используется модель: {model_name}")
            break
        except Exception as e:
            print(f"⚠️ Модель {model_name} недоступна: {str(e)[:100]}...")
            continue
    
    if model:
        AI_AVAILABLE = True
        print("✅ Google AI Studio API инициализирован")
    else:
        AI_AVAILABLE = False
        print("❌ Не удалось инициализировать ни одну модель")
        
except Exception as e:
    print(f"⚠️ Google AI Studio API недоступен: {e}")
    AI_AVAILABLE = False
    model = None

cached_data = {}
analysis_results = {}
address_cache = {}  # Кэш для адресов

def get_llm_analysis(prompt, system_prompt="Ты эксперт по транспортной аналитике и безопасности дорожного движения.", max_tokens=400):
    """
    Получает анализ от LLM (Google Gemini)
    """
    if not AI_AVAILABLE or not model:
        return "ИИ анализ временно недоступен. Используются стандартные алгоритмы."
    
    try:
        # Комбинируем системный промпт с пользовательским
        full_prompt = f"{system_prompt}\n\n{prompt}"
        
        # Генерируем ответ с помощью Gemini с улучшенной конфигурацией
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.7,
                top_p=0.8,
                top_k=40
            ),
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
        )
        
        if response.text:
            return response.text.strip()
        else:
            return "ИИ не смог сгенерировать ответ. Проверьте промпт или попробуйте позже."
            
    except Exception as e:
        error_msg = str(e)
        print(f"⚠️ Ошибка Google AI запроса: {error_msg}")
        
        # Специфичные сообщения об ошибках
        if "models/" in error_msg and "not found" in error_msg:
            return "ИИ анализ недоступен: модель не найдена. Попробуйте обновить API."
        elif "quota" in error_msg.lower():
            return "ИИ анализ недоступен: превышен лимит запросов."
        elif "api" in error_msg.lower() and "key" in error_msg.lower():
            return "ИИ анализ недоступен: проблема с API ключом."
        else:
            return f"ИИ анализ недоступен: {error_msg[:100]}..."

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
    
    # Добавляем временные характеристики для ML-модели
    print("🤖 Подготавливаем данные для ML...")
    df_ml = df_clean.copy()
    
    # Создаем синтетические временные метки (имитируем реальное время)
    np.random.seed(42)
    base_time = pd.Timestamp('2024-01-01 00:00:00')
    time_offsets = np.random.uniform(0, 24*30*60, len(df_ml))  # 30 дней в минутах
    df_ml['timestamp'] = [base_time + pd.Timedelta(minutes=offset) for offset in time_offsets]
    df_ml['hour'] = df_ml['timestamp'].dt.hour
    df_ml['day_of_week'] = df_ml['timestamp'].dt.dayofweek
    df_ml['is_weekend'] = df_ml['day_of_week'].isin([5, 6]).astype(int)
    
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
    
    # Инициализируем геокодер для получения реальных адресов
    geolocator = Nominatim(user_agent="indrive_geo_analysis", timeout=10)
    
    def get_real_address(lat, lng):
        """Получает реальный адрес по координатам через OpenStreetMap"""
        # Создаем ключ для кэширования
        cache_key = f"{lat:.4f},{lng:.4f}"
        
        # Проверяем кэш
        if cache_key in address_cache:
            return address_cache[cache_key]
            
        try:
            # Небольшая задержка для избежания rate limiting
            import time
            time.sleep(0.5)
            
            location = geolocator.reverse(f"{lat}, {lng}", language='ru')
            if location and location.address:
                # Обрабатываем адрес для красивого отображения
                address = location.address
                
                # Извлекаем важные части адреса
                parts = address.split(', ')
                filtered_parts = []
                
                for part in parts:
                    # Пропускаем почтовые индексы и страну
                    if not (part.isdigit() and len(part) == 6) and part not in ['Казахстан', 'Kazakhstan']:
                        filtered_parts.append(part)
                
                # Берем первые 3-4 части для краткости
                if len(filtered_parts) > 3:
                    result = ', '.join(filtered_parts[:3])
                else:
                    result = ', '.join(filtered_parts)
                
                # Если адрес получился слишком длинный, сокращаем
                if len(result) > 60:
                    result = result[:57] + '...'
                
                # Сохраняем в кэш
                address_cache[cache_key] = result
                return result
            else:
                fallback = get_fallback_address(lat, lng)
                address_cache[cache_key] = fallback
                return fallback
        except Exception as e:
            print(f"⚠️ Ошибка геокодирования для {lat}, {lng}: {e}")
            fallback = get_fallback_address(lat, lng)
            address_cache[cache_key] = fallback
            return fallback
    
    def get_fallback_address(lat, lng):
        """Определяет район Астаны по координатам (fallback)"""
        # Примерные границы районов Астаны
        if lat >= 51.15 and lng >= 71.45:
            return "Есильский район, пр. Мәңгілік Ел"
        elif lat >= 51.12 and lng <= 71.42:
            return "Алматинский район, ул. Абая" 
        elif lat >= 51.10 and lat <= 51.15 and lng >= 71.40 and lng <= 71.50:
            return "Сарыаркинский район, пр. Туран"
        elif lat >= 51.05 and lat <= 51.12:
            return "Байконурский район, пр. Республики"
        elif lng >= 71.50:
            return "Есильский район, ЖК Highvill"
        elif lng <= 71.35:
            return "Алматинский район, мкр. Мамыр"
        elif lat <= 51.10:
            return "Алматинский район, мкр. Алмагуль"
        elif lat >= 51.18:
            return "Есильский район, ЭКСПО-городок"
        elif 71.42 <= lng <= 71.48:
            return "Центральный район, пл. Республики"
        else:
            return "Сарыаркинский район, мкр. Акбулак"
    
    zones_data = []
    print("🌍 Получаем реальные адреса зон...")
    
    for i, center in enumerate(zone_centers):
        zone_demand = (zone_labels == i).sum()
        lat, lng = float(center[0]), float(center[1])
        
        # Получаем реальный адрес
        print(f"   Зона {i}: получаем адрес для координат {lat:.4f}, {lng:.4f}")
        address = get_real_address(lat, lng)
        
        zones_data.append({
            'zone_id': int(i),
            'lat': lat,
            'lng': lng,
            'demand': int(zone_demand),
            'percentage': float(round(zone_demand / len(sample_coords) * 100, 1)),
            'address': address
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
    
    # ML-модель для предсказания спроса
    print("🤖 Создаем ML-модель предсказания спроса...")
    demand_model_results = build_demand_prediction_model(df_ml)
    results['demand_prediction'] = demand_model_results
    
    # Система безопасности - анализ опасных зон
    print("🔒 Анализ безопасности маршрутов...")
    safety_analysis = analyze_route_safety(df_ml)
    results['safety_analysis'] = safety_analysis
    
    # Оптимизация распределения водителей
    print("🚗 Оптимизация распределения водителей...")
    driver_optimization = optimize_driver_allocation(results['zones'], demand_model_results)
    results['driver_optimization'] = driver_optimization
    
    print("✅ Анализ завершен")
    return results

def build_demand_prediction_model(df_ml):
    """Строит ML-модель для предсказания спроса"""
    try:
        # Создаем сетку для предсказаний
        grid_size = 0.02
        lat_bins = np.arange(df_ml['lat'].min(), df_ml['lat'].max() + grid_size, grid_size)
        lng_bins = np.arange(df_ml['lng'].min(), df_ml['lng'].max() + grid_size, grid_size)
        
        df_grid = df_ml.copy()
        df_grid['lat_bin'] = pd.cut(df_grid['lat'], bins=lat_bins, labels=False)
        df_grid['lng_bin'] = pd.cut(df_grid['lng'], bins=lng_bins, labels=False)
        
        # Агрегируем данные по часам и зонам
        hourly_demand = df_grid.groupby(['lat_bin', 'lng_bin', 'hour']).agg({
            'randomized_id': 'count',
            'spd': 'mean',
            'day_of_week': 'first',
            'is_weekend': 'first'
        }).reset_index()
        
        hourly_demand.columns = ['lat_bin', 'lng_bin', 'hour', 'demand', 'avg_speed', 'day_of_week', 'is_weekend']
        hourly_demand = hourly_demand.dropna()
        
        if len(hourly_demand) < 10:
            return {'error': 'Недостаточно данных для ML-модели'}
        
        # Подготавливаем признаки
        features = ['lat_bin', 'lng_bin', 'hour', 'day_of_week', 'is_weekend', 'avg_speed']
        X = hourly_demand[features].fillna(0)
        y = hourly_demand['demand']
        
        # Обучаем модель
        model = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=10)
        model.fit(X, y)
        
        # Предсказания для следующих часов
        predictions = []
        for hour in range(24):
            for is_weekend in [0, 1]:
                hour_predictions = []
                for i, lat_bin in enumerate(lat_bins[:-1]):
                    for j, lng_bin in enumerate(lng_bins[:-1]):
                        pred_features = [[i, j, hour, 1, is_weekend, 30]]  # средняя скорость 30
                        demand_pred = model.predict(pred_features)[0]
                        
                        if demand_pred > 1:  # фильтруем низкий спрос
                            hour_predictions.append({
                                'lat': float(lat_bin + grid_size/2),
                                'lng': float(lng_bin + grid_size/2),
                                'predicted_demand': float(max(0, demand_pred)),
                                'confidence': float(min(1.0, demand_pred / y.max()))
                            })
                
                predictions.append({
                    'hour': hour,
                    'is_weekend': bool(is_weekend),
                    'predictions': sorted(hour_predictions, key=lambda x: x['predicted_demand'], reverse=True)[:20]
                })
        
        # Важность признаков
        feature_importance = {
            feature: float(importance) 
            for feature, importance in zip(features, model.feature_importances_)
        }
        
        return {
            'model_accuracy': f"{model.score(X, y):.2f}",
            'predictions': predictions,
            'feature_importance': feature_importance,
            'total_samples': len(hourly_demand)
        }
    except Exception as e:
        print(f"❌ Ошибка в ML-модели: {e}")
        return {'error': str(e)}

def analyze_route_safety(df_ml):
    """Анализирует безопасность маршрутов с использованием LLM"""
    try:
        print("🔒 Анализ безопасности маршрутов с ИИ...")
        
        # Определяем опасные зоны по аномальным скоростям и паттернам
        safety_features = df_ml[['lat', 'lng', 'spd', 'hour']].copy()
        
        # Нормализация для кластеризации
        scaler = StandardScaler()
        safety_scaled = scaler.fit_transform(safety_features)
        
        # Поиск аномалий
        isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        anomaly_labels = isolation_forest.fit_predict(safety_scaled)
        
        dangerous_zones = df_ml[anomaly_labels == -1].copy()
        
        if len(dangerous_zones) == 0:
            return {'error': 'Опасные зоны не обнаружены'}
        
        # Группируем опасные зоны
        kmeans = KMeans(n_clusters=min(5, len(dangerous_zones)), random_state=42)
        zone_labels = kmeans.fit_predict(dangerous_zones[['lat', 'lng']])
        
        safety_zones = []
        detailed_incidents = []
        
        for i in range(kmeans.n_clusters):
            zone_data = dangerous_zones[zone_labels == i]
            
            # Анализируем причины опасности
            high_speed_incidents = len(zone_data[zone_data['spd'] > zone_data['spd'].quantile(0.9)])
            night_incidents = len(zone_data[zone_data['hour'].isin([22, 23, 0, 1, 2, 3, 4, 5])])
            
            zone_info = {
                'zone_id': int(i),
                'center_lat': float(zone_data['lat'].mean()),
                'center_lng': float(zone_data['lng'].mean()),
                'incidents': len(zone_data),
                'high_speed_incidents': int(high_speed_incidents),
                'night_incidents': int(night_incidents),
                'avg_speed': float(zone_data['spd'].mean()),
                'risk_score': float(min(10, len(zone_data) / 10 + zone_data['spd'].std() / 10))
            }
            safety_zones.append(zone_info)
            
            # Собираем детальную информацию для LLM анализа
            detailed_incidents.append({
                'zone': i + 1,
                'incidents': int(len(zone_data)),
                'avg_speed': float(round(zone_data['spd'].mean(), 1)),
                'max_speed': float(round(zone_data['spd'].max(), 1)),
                'high_speed_rate': float(round(high_speed_incidents / len(zone_data) * 100, 1)),
                'night_incidents_rate': float(round(night_incidents / len(zone_data) * 100, 1)),
                'peak_hours': [int(h) for h in zone_data['hour'].mode().tolist()[:3]]
            })
        
        # Создаем промпт для LLM анализа
        llm_prompt = f"""Проанализируй данные о {len(safety_zones)} опасных зонах в Астане:

Статистика инцидентов:
"""
        for incident in detailed_incidents:
            llm_prompt += f"""
- Зона {incident['zone']}: {incident['incidents']} инцидентов
  * Средняя скорость: {incident['avg_speed']} км/ч
  * Максимальная скорость: {incident['max_speed']} км/ч  
  * Превышения скорости: {incident['high_speed_rate']}%
  * Ночные инциденты: {incident['night_incidents_rate']}%
  * Пиковые часы: {incident['peak_hours']}
"""

        llm_prompt += """
Кратко проанализируй безопасность:
1. Основные факторы риска
2. Топ-2 приоритетные зоны
3. 3 ключевые меры безопасности

Ответ максимум 3 абзаца для транспортных властей Астаны."""

        # Получаем анализ от LLM
        llm_analysis = get_llm_analysis(
            llm_prompt, 
            "Ты эксперт по безопасности дорожного движения в городах Казахстана. Анализируй данные о ДТП и предлагай конкретные решения для улучшения безопасности.",
            max_tokens=300
        )
        
        return {
            'dangerous_zones': sorted(safety_zones, key=lambda x: x['risk_score'], reverse=True),
            'total_incidents': len(dangerous_zones),
            'llm_safety_analysis': llm_analysis,
            'incident_statistics': detailed_incidents,
            'safety_recommendations': [
                "Увеличить контроль скорости в выявленных зонах",
                "Установить дополнительные камеры в ночное время", 
                "Предупреждать водителей о потенциально опасных участках",
                "Анализировать паттерны движения для оптимизации маршрутов"
            ]
        }
    except Exception as e:
        return {'error': f'Ошибка анализа безопасности: {str(e)}'}

def optimize_driver_allocation(zones_data, demand_predictions):
    """Оптимизирует распределение водителей с использованием LLM"""
    try:
        print("🚗 Оптимизация распределения водителей с ИИ...")
        
        total_drivers = 100  # Общее количество водителей
        
        # Рекомендации по часам
        hourly_recommendations = []
        optimization_data = []
        
        if 'predictions' not in demand_predictions:
            return {'error': 'Нет данных предсказаний для оптимизации'}
        
        # Анализируем спрос по часам для создания стратегии
        peak_hours = []
        low_demand_hours = []
        
        for hour_data in demand_predictions['predictions'][:24]:  # Только будни
            if not hour_data['predictions']:
                continue
                
            hour = hour_data['hour']
            total_predicted = sum(p['predicted_demand'] for p in hour_data['predictions'])
            
            if total_predicted == 0:
                continue
            
            # Классифицируем часы по уровню спроса
            if total_predicted > 50:  # Высокий спрос
                peak_hours.append({
                    'hour': int(hour),
                    'total_demand': float(total_predicted),
                    'top_zones': int(len([p for p in hour_data['predictions'] if p['predicted_demand'] > 5]))
                })
            elif total_predicted < 20:  # Низкий спрос
                low_demand_hours.append({
                    'hour': int(hour),
                    'total_demand': float(total_predicted),
                    'active_zones': int(len([p for p in hour_data['predictions'] if p['predicted_demand'] > 1]))
                })
            
            zone_allocations = []
            for zone_pred in hour_data['predictions'][:10]:  # Топ-10 зон
                allocation_ratio = zone_pred['predicted_demand'] / total_predicted
                recommended_drivers = int(total_drivers * allocation_ratio)
                
                zone_allocations.append({
                    'lat': float(zone_pred['lat']),
                    'lng': float(zone_pred['lng']),
                    'predicted_demand': float(zone_pred['predicted_demand']),
                    'recommended_drivers': int(max(1, recommended_drivers)),
                    'efficiency_score': float(zone_pred['confidence'])
                })
            
            hourly_recommendations.append({
                'hour': hour,
                'zone_allocations': zone_allocations,
                'total_demand': float(total_predicted)
            })
            
            # Собираем данные для LLM анализа
            optimization_data.append({
                'hour': int(hour),
                'demand_level': 'High' if total_predicted > 50 else 'Medium' if total_predicted > 20 else 'Low',
                'total_demand': float(round(total_predicted, 1)),
                'active_zones': int(len(zone_allocations)),
                'peak_zone_demand': float(max([z['predicted_demand'] for z in zone_allocations])) if zone_allocations else 0.0
            })
        
        # Создаем промпт для LLM стратегического анализа
        llm_prompt = f"""Проанализируй оптимизацию распределения {total_drivers} водителей в Астане по 24-часовому циклу:

ДАННЫЕ СПРОСА ПО ЧАСАМ:
"""
        for data in optimization_data:
            llm_prompt += f"• {data['hour']:02d}:00 - Спрос: {data['demand_level']} ({data['total_demand']:.1f}), Активных зон: {data['active_zones']}, Пиковая зона: {data['peak_zone_demand']:.1f}\n"

        llm_prompt += f"""
ПИКОВЫЕ ЧАСЫ ({len(peak_hours)}): {[f"{h['hour']:02d}:00" for h in peak_hours]}
ЧАСЫ НИЗКОГО СПРОСА ({len(low_demand_hours)}): {[f"{h['hour']:02d}:00" for h in low_demand_hours]}

Кратко создай план оптимизации (максимум 3 абзаца):
1. Главные паттерны спроса
2. Топ-3 рекомендации по распределению водителей  
3. Ожидаемая экономическая выгода

Практичные решения для Астаны."""

        # Получаем стратегический анализ от LLM
        llm_strategy = get_llm_analysis(
            llm_prompt, 
            "Ты эксперт по логистике и оптимизации транспортных систем в городах Казахстана. Создавай практичные стратегии для максимизации эффективности работы водителей.",
            max_tokens=350
        )
        
        return {
            'hourly_recommendations': hourly_recommendations,
            'llm_optimization_strategy': llm_strategy,
            'demand_analysis': {
                'peak_hours_data': peak_hours,
                'low_demand_hours_data': low_demand_hours,
                'optimization_summary': optimization_data
            },
            'optimization_metrics': {
                'total_drivers': total_drivers,
                'coverage_zones': len(hourly_recommendations),
                'peak_periods': len(peak_hours),
                'low_demand_periods': len(low_demand_hours),
                'avg_efficiency': np.mean([r['zone_allocations'][0]['efficiency_score'] 
                                         for r in hourly_recommendations if r['zone_allocations']]) if hourly_recommendations else 0
            }
        }
    except Exception as e:
        return {'error': f'Ошибка оптимизации: {str(e)}'}
    
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

@app.route('/api/demand-prediction')
def get_demand_prediction():
    """API для ML-предсказаний спроса"""
    try:
        if 'df_clean' not in cached_data:
            load_and_process_data()
        
        demand_data = analysis_results.get('demand_prediction', {})
        
        if 'error' in demand_data:
            return jsonify({'error': demand_data['error']}), 400
        
        # Возвращаем предсказания для ближайших часов
        current_hour_predictions = []
        if 'predictions' in demand_data:
            for i, hour_data in enumerate(demand_data['predictions'][:6]):  # 6 часов
                if hour_data['predictions']:
                    current_hour_predictions.append({
                        'hour': hour_data['hour'],
                        'predictions': hour_data['predictions'][:10]  # Топ-10
                    })
        
        return jsonify({
            'model_accuracy': demand_data.get('model_accuracy', 'N/A'),
            'predictions': current_hour_predictions,
            'feature_importance': demand_data.get('feature_importance', {}),
            'total_samples': demand_data.get('total_samples', 0)
        })
    except Exception as e:
        print(f"❌ Ошибка в /api/demand-prediction: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/safety-analysis')
def get_safety_analysis():
    """API для анализа безопасности"""
    try:
        if 'df_clean' not in cached_data:
            load_and_process_data()
        
        safety_data = analysis_results.get('safety_analysis', {})
        
        if 'error' in safety_data:
            return jsonify({'error': safety_data['error']}), 400
        
        return jsonify(safety_data)
    except Exception as e:
        print(f"❌ Ошибка в /api/safety-analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/driver-optimization')
def get_driver_optimization():
    """API для оптимизации водителей"""
    try:
        if 'df_clean' not in cached_data:
            load_and_process_data()
        
        optimization_data = analysis_results.get('driver_optimization', {})
        
        if 'error' in optimization_data:
            return jsonify({'error': optimization_data['error']}), 400
        
        return jsonify(optimization_data)
    except Exception as e:
        print(f"❌ Ошибка в /api/driver-optimization: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/eco-analysis')
def get_eco_analysis():
    """API для экологического анализа"""
    try:
        if 'df_clean' not in cached_data:
            load_and_process_data()
        
        df_clean = cached_data['df_clean']
        
        # Расчет выбросов CO2
        # Средний расход топлива: 8л/100км для такси
        # 1л бензина = ~2.3кг CO2
        fuel_consumption_per_100km = 8
        co2_per_liter = 2.3
        
        # Приблизительный расчет расстояний по GPS точкам
        total_trips = df_clean['randomized_id'].nunique()
        avg_trip_distance = 5  # км (средняя поездка)
        total_distance = total_trips * avg_trip_distance
        
        total_fuel = total_distance * fuel_consumption_per_100km / 100
        total_co2 = total_fuel * co2_per_liter
        
        # Анализ по скоростям (экономичная скорость 50-60 км/ч)
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
            'potential_annual_savings_kg': float(round(potential_savings * 365 / 30, 1)),  # экстраполяция на год
            'recommendations': eco_recommendations,
            'trips_analyzed': int(total_trips)
        })
        
    except Exception as e:
        print(f"❌ Ошибка в /api/eco-analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-address')
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

if __name__ == '__main__':
    print("🚀 Запуск геоаналитической панели...")
    print("📊 Загрузка данных может занять некоторое время...")
    
    # Предварительная загрузка данных
    load_and_process_data()
    
    print("✅ Готово! Открывайте http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)