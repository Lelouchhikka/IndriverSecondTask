#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для визуализации данных
"""

import json
import folium
from folium.plugins import HeatMap
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
from typing import List, Dict, Any
import pandas as pd
from ..models.data_models import Zone, TrafficGridCell, AnomalyPoint, Route


class VisualizationUtils:
    """Утилиты для создания графиков и карт"""
    
    @staticmethod
    def create_speed_distribution_chart(speed_data: Dict[str, int]) -> str:
        """Создает круговую диаграмму распределения скоростей"""
        if not speed_data or len(speed_data) == 0:
            return json.dumps({'error': 'Нет данных о распределении скоростей'})
        
        categories = list(speed_data.keys())
        values = [int(v) for v in speed_data.values()]
        
        if sum(values) == 0:
            return json.dumps({'error': 'Все значения скоростей равны нулю'})
        
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
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    @staticmethod
    def create_zones_chart(zones: List[Zone]) -> str:
        """Создает график зон спроса"""
        top_zones = zones[:10]  # Топ-10 зон
        
        if not top_zones:
            return json.dumps({'error': 'Нет данных о зонах'})
        
        zone_names = [f"Зона {z.zone_id}" for z in top_zones]
        demand_values = [z.demand for z in top_zones]
        
        if not zone_names or not demand_values:
            return json.dumps({'error': 'Некорректные данные для построения графика'})
        
        fig = px.bar(
            x=zone_names,
            y=demand_values,
            title="Топ-10 зон по спросу",
            labels={'x': 'Зоны', 'y': 'Количество поездок'},
            color=demand_values,
            color_continuous_scale='viridis',
            text=demand_values
        )
        
        fig.update_layout(
            showlegend=False,
            xaxis_tickangle=-45,
            height=400,
            margin=dict(t=50, r=30, b=100, l=50)
        )
        
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    @staticmethod
    def create_traffic_scatter(traffic_cells: List[TrafficGridCell]) -> str:
        """Создает scatter plot трафика"""
        if not traffic_cells:
            return json.dumps({'error': 'Нет данных о трафике'})
        
        df_traffic = pd.DataFrame([{
            'lng_center': cell.lng_center,
            'lat_center': cell.lat_center,
            'points_count': cell.points_count,
            'avg_speed': cell.avg_speed,
            'unique_trips': cell.unique_trips
        } for cell in traffic_cells])
        
        if df_traffic.empty or len(df_traffic) < 2:
            return json.dumps({'error': 'Недостаточно данных для построения графика'})
        
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
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    @staticmethod
    def create_anomalies_scatter(anomalies: List[AnomalyPoint]) -> str:
        """Создает scatter plot аномалий"""
        if not anomalies or len(anomalies) < 5:
            return json.dumps({'error': 'Недостаточно данных об аномалиях'})
        
        # Ограничиваем количество точек
        if len(anomalies) > 2000:
            import random
            random.seed(42)
            anomalies = random.sample(anomalies, 2000)
        
        df_anomalies = pd.DataFrame([{
            'lng': point.lng,
            'lat': point.lat,
            'is_anomaly': point.is_anomaly,
            'size_value': max(1, abs(point.spd)),
            'spd': point.spd,
            'alt': point.alt
        } for point in anomalies])
        
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
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    @staticmethod
    def create_routes_chart(routes: List[Route]) -> str:
        """Создает график популярных маршрутов"""
        if not routes or len(routes) < 3:
            return json.dumps({'error': 'Недостаточно данных о популярных маршрутах'})
        
        top_routes = routes[:15]  # Топ-15
        route_names = [f"Маршрут {route.route_id}" for route in top_routes]
        route_counts = [route.unique_trips for route in top_routes]
        
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
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    @staticmethod
    def create_heatmap(df_sample: pd.DataFrame, zones: List[Zone]) -> str:
        """Создает тепловую карту"""
        try:
            # Координаты для тепловой карты
            heat_data = [[float(row['lat']), float(row['lng'])] for _, row in df_sample.iterrows()]
            
            # Центр карты
            center_lat = float(df_sample['lat'].mean())
            center_lng = float(df_sample['lng'].mean())
            
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
            for zone in zones[:5]:  # Топ-5 зон
                folium.Marker(
                    [zone.lat, zone.lng],
                    popup=f"Зона {zone.zone_id}: {zone.percentage}% спроса",
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(m)
            
            return m._repr_html_()
        except Exception as e:
            return f"<div class='alert alert-danger'>Ошибка загрузки карты: {str(e)}</div>"