#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сервис для выполнения всех видов анализа данных
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from ..config.config import Config
from ..models.data_models import Zone, TrafficGridCell, AnomalyPoint, Route, SafetyZone
from ..services.ai_service import AIService
from ..utils.geocoding import GeoCoder
from ..utils.type_converter import TypeConverter


class AnalysisService:
    """Сервис для выполнения аналитических операций"""
    
    def __init__(self, config: Config, ai_service: AIService):
        self.config = config
        self.ai_service = ai_service
        self.geocoder = GeoCoder(config)
        self.analysis_cache = {}
    
    def create_demand_zones(self, df_clean: pd.DataFrame) -> List[Zone]:
        """Создание зон спроса с помощью кластеризации"""
        if 'demand_zones' in self.analysis_cache:
            return self.analysis_cache['demand_zones']
        
        print("🌍 Получаем реальные адреса зон...")
        
        # Выборка для кластеризации
        sample_coords = df_clean[['lat', 'lng']].sample(
            n=min(self.config.ML_CONFIG['max_sample_points'], len(df_clean)), 
            random_state=self.config.ML_CONFIG['random_state']
        )
        
        # Кластеризация
        kmeans = KMeans(
            n_clusters=self.config.ML_CONFIG['n_clusters'], 
            random_state=self.config.ML_CONFIG['random_state'],
            n_init=10
        )
        zone_labels = kmeans.fit_predict(sample_coords)
        zone_centers = kmeans.cluster_centers_
        
        # Создание зон
        zones = []
        for i, center in enumerate(zone_centers):
            zone_demand = (zone_labels == i).sum()
            lat, lng = TypeConverter.safe_float(center[0]), TypeConverter.safe_float(center[1])
            
            print(f"   Зона {i}: получаем адрес для координат {lat:.4f}, {lng:.4f}")
            address = self.geocoder.get_address(lat, lng)
            
            zones.append(Zone(
                zone_id=int(i),
                lat=lat,
                lng=lng,
                demand=TypeConverter.safe_int(zone_demand),
                percentage=TypeConverter.safe_float(zone_demand / len(sample_coords) * 100),
                address=address
            ))
        
        # Сортируем по спросу
        zones.sort(key=lambda x: x.demand, reverse=True)
        
        self.analysis_cache['demand_zones'] = zones
        return zones
    
    def analyze_traffic_grid(self, df_clean: pd.DataFrame) -> List[TrafficGridCell]:
        """Анализ трафика по сетке"""
        if 'traffic_grid' in self.analysis_cache:
            return self.analysis_cache['traffic_grid']
        
        grid_size = self.config.ML_CONFIG['grid_size']
        lat_min, lat_max = df_clean['lat'].min(), df_clean['lat'].max()
        lng_min, lng_max = df_clean['lng'].min(), df_clean['lng'].max()
        
        lat_bins = np.arange(lat_min, lat_max + grid_size, grid_size)
        lng_bins = np.arange(lng_min, lng_max + grid_size, grid_size)
        
        df_grid = df_clean.copy()
        df_grid['lat_bin'] = pd.cut(df_grid['lat'], bins=lat_bins, labels=False)
        df_grid['lng_bin'] = pd.cut(df_grid['lng'], bins=lng_bins, labels=False)
        
        # Агрегация по сетке
        grid_stats = df_grid.groupby(['lat_bin', 'lng_bin']).agg({
            'spd': ['mean', 'count'],
            'randomized_id': 'nunique'
        }).round(2)
        
        grid_stats.columns = ['avg_speed', 'points_count', 'unique_trips']
        grid_stats = grid_stats.reset_index()
        grid_stats = grid_stats[grid_stats['points_count'] >= 5]
        
        # Добавляем координаты центров
        grid_stats['lat_center'] = grid_stats['lat_bin'].apply(
            lambda x: TypeConverter.safe_float(lat_bins[int(x)] + grid_size/2) if pd.notna(x) else None
        )
        grid_stats['lng_center'] = grid_stats['lng_bin'].apply(
            lambda x: TypeConverter.safe_float(lng_bins[int(x)] + grid_size/2) if pd.notna(x) else None
        )
        
        # Конвертируем в объекты
        cells = []
        for _, row in grid_stats.iterrows():
            if pd.notna(row['lat_center']) and pd.notna(row['lng_center']):
                cells.append(TrafficGridCell(
                    lat_bin=TypeConverter.safe_int(row['lat_bin']),
                    lng_bin=TypeConverter.safe_int(row['lng_bin']),
                    avg_speed=TypeConverter.safe_float(row['avg_speed']),
                    points_count=TypeConverter.safe_int(row['points_count']),
                    unique_trips=TypeConverter.safe_int(row['unique_trips']),
                    lat_center=TypeConverter.safe_float(row['lat_center']),
                    lng_center=TypeConverter.safe_float(row['lng_center'])
                ))
        
        self.analysis_cache['traffic_grid'] = cells
        return cells
    
    def detect_anomalies(self, df_clean: pd.DataFrame) -> List[AnomalyPoint]:
        """Поиск аномальных GPS точек"""
        if 'anomalies' in self.analysis_cache:
            return self.analysis_cache['anomalies']
        
        print("🔍 Анализ аномалий...")
        
        # Простая логика: экстремальные значения
        speed_threshold_high = df_clean['spd'].quantile(0.95)
        speed_threshold_low = df_clean['spd'].quantile(0.05)
        alt_threshold = df_clean['alt'].quantile(0.98)
        
        anomaly_conditions = (
            (df_clean['spd'] > speed_threshold_high) | 
            (df_clean['spd'] < speed_threshold_low) |
            (df_clean['alt'] > alt_threshold)
        )
        
        # Семплируем аномалии
        max_points = self.config.PERFORMANCE_CONFIG['max_anomaly_points']
        anomalies_sample = df_clean[anomaly_conditions].sample(
            n=min(max_points // 2, len(df_clean[anomaly_conditions])), 
            random_state=self.config.ML_CONFIG['random_state']
        )
        
        anomalies = []
        # Аномальные точки
        for _, row in anomalies_sample.iterrows():
            anomalies.append(AnomalyPoint(
                lat=TypeConverter.safe_float(row['lat']),
                lng=TypeConverter.safe_float(row['lng']),
                spd=TypeConverter.safe_float(abs(row['spd'])),
                alt=TypeConverter.safe_float(row['alt']),
                is_anomaly=1
            ))
        
        # Добавляем нормальные точки для контраста
        normal_sample = df_clean[~anomaly_conditions].sample(
            n=max_points // 4, 
            random_state=self.config.ML_CONFIG['random_state']
        )
        for _, row in normal_sample.iterrows():
            anomalies.append(AnomalyPoint(
                lat=TypeConverter.safe_float(row['lat']),
                lng=TypeConverter.safe_float(row['lng']),
                spd=TypeConverter.safe_float(abs(row['spd'])),
                alt=TypeConverter.safe_float(row['alt']),
                is_anomaly=0
            ))
        
        self.analysis_cache['anomalies'] = anomalies
        return anomalies
    
    def analyze_popular_routes(self, df_clean: pd.DataFrame) -> List[Route]:
        """Анализ популярных маршрутов"""
        if 'popular_routes' in self.analysis_cache:
            return self.analysis_cache['popular_routes']
        
        print("🛣️  Анализ популярных маршрутов...")
        
        # Группируем по пользователям
        trip_stats = df_clean.groupby('randomized_id').agg({
            'lat': ['min', 'max', 'count'],
            'lng': ['min', 'max'],
            'spd': 'mean'
        }).reset_index()
        
        trip_stats.columns = ['user_id', 'lat_min', 'lat_max', 'point_count', 'lng_min', 'lng_max', 'avg_speed']
        trip_stats = trip_stats.sort_values('point_count', ascending=False)
        
        # Создаем маршруты
        routes = []
        limit = self.config.PERFORMANCE_CONFIG['top_routes_limit']
        for i, (_, row) in enumerate(trip_stats.head(limit).iterrows()):
            routes.append(Route(
                route_id=i + 1,
                unique_trips=TypeConverter.safe_int(row['point_count']),
                avg_speed=TypeConverter.safe_float(row['avg_speed']),
                lat_span=TypeConverter.safe_float(row['lat_max'] - row['lat_min']),
                lng_span=TypeConverter.safe_float(row['lng_max'] - row['lng_min'])
            ))
        
        self.analysis_cache['popular_routes'] = routes
        return routes
    
    def analyze_safety(self, df_ml: pd.DataFrame) -> dict:
        """Анализ безопасности маршрутов"""
        if 'safety_analysis' in self.analysis_cache:
            return self.analysis_cache['safety_analysis']
        
        try:
            print("🔒 Анализ безопасности маршрутов с ИИ...")
            
            # Определяем опасные зоны по аномальным паттернам
            safety_features = df_ml[['lat', 'lng', 'spd', 'hour']].copy()
            
            # Нормализация и поиск аномалий
            scaler = StandardScaler()
            safety_scaled = scaler.fit_transform(safety_features)
            
            isolation_forest = IsolationForest(
                contamination=self.config.ML_CONFIG['isolation_forest_contamination'], 
                random_state=self.config.ML_CONFIG['random_state']
            )
            anomaly_labels = isolation_forest.fit_predict(safety_scaled)
            
            dangerous_zones_df = df_ml[anomaly_labels == -1].copy()
            
            if len(dangerous_zones_df) == 0:
                return {'error': 'Опасные зоны не обнаружены'}
            
            # Кластеризация опасных зон
            kmeans = KMeans(
                n_clusters=min(5, len(dangerous_zones_df)), 
                random_state=self.config.ML_CONFIG['random_state']
            )
            zone_labels = kmeans.fit_predict(dangerous_zones_df[['lat', 'lng']])
            
            safety_zones = []
            detailed_incidents = []
            
            for i in range(kmeans.n_clusters):
                zone_data = dangerous_zones_df[zone_labels == i]
                
                # Анализ причин опасности
                high_speed_incidents = len(zone_data[zone_data['spd'] > zone_data['spd'].quantile(0.9)])
                night_incidents = len(zone_data[zone_data['hour'].isin([22, 23, 0, 1, 2, 3, 4, 5])])
                
                safety_zone = SafetyZone(
                    zone_id=i,
                    center_lat=TypeConverter.safe_float(zone_data['lat'].mean()),
                    center_lng=TypeConverter.safe_float(zone_data['lng'].mean()),
                    incidents=len(zone_data),
                    high_speed_incidents=high_speed_incidents,
                    night_incidents=night_incidents,
                    avg_speed=TypeConverter.safe_float(zone_data['spd'].mean()),
                    risk_score=TypeConverter.safe_float(min(10, len(zone_data) / 10 + zone_data['spd'].std() / 10))
                )
                safety_zones.append(safety_zone)
                
                # Для ИИ анализа
                detailed_incidents.append({
                    'zone': i + 1,
                    'incidents': len(zone_data),
                    'avg_speed': TypeConverter.safe_float(zone_data['spd'].mean()),
                    'max_speed': TypeConverter.safe_float(zone_data['spd'].max()),
                    'high_speed_rate': TypeConverter.safe_float(high_speed_incidents / len(zone_data) * 100),
                    'night_incidents_rate': TypeConverter.safe_float(night_incidents / len(zone_data) * 100),
                    'peak_hours': [int(h) for h in zone_data['hour'].mode().tolist()[:3]]
                })
            
            # Получаем анализ от ИИ
            llm_analysis = self.ai_service.analyze_safety_data(safety_zones, detailed_incidents)
            
            result = {
                'dangerous_zones': sorted([
                    {
                        'zone_id': zone.zone_id,
                        'center_lat': zone.center_lat,
                        'center_lng': zone.center_lng,
                        'incidents': zone.incidents,
                        'high_speed_incidents': zone.high_speed_incidents,
                        'night_incidents': zone.night_incidents,
                        'avg_speed': zone.avg_speed,
                        'risk_score': zone.risk_score
                    }
                    for zone in safety_zones
                ], key=lambda x: x['risk_score'], reverse=True),
                'total_incidents': len(dangerous_zones_df),
                'llm_safety_analysis': llm_analysis,
                'incident_statistics': detailed_incidents,
                'safety_recommendations': [
                    "Увеличить контроль скорости в выявленных зонах",
                    "Установить дополнительные камеры в ночное время", 
                    "Предупреждать водителей о потенциально опасных участках",
                    "Анализировать паттерны движения для оптимизации маршрутов"
                ]
            }
            
            self.analysis_cache['safety_analysis'] = result
            return result
            
        except Exception as e:
            return {'error': f'Ошибка анализа безопасности: {str(e)}'}
    
    def clear_cache(self):
        """Очистка кэша анализа"""
        self.analysis_cache.clear()