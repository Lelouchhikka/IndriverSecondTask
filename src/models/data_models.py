#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модели данных для геоаналитической системы
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum
import pandas as pd


class SpeedCategory(Enum):
    """Категории скоростей"""
    STOP = "Стоп"
    VERY_SLOW = "Очень медленно" 
    SLOW = "Медленно"
    MODERATE = "Умеренно"
    FAST = "Быстро"
    VERY_FAST = "Очень быстро"


@dataclass
class GPSPoint:
    """Модель GPS точки"""
    randomized_id: int
    lat: float
    lng: float
    alt: float
    spd: float
    azm: float
    
    def categorize_speed(self) -> SpeedCategory:
        """Категоризация скорости"""
        if self.spd == 0:
            return SpeedCategory.STOP
        elif self.spd < 10:
            return SpeedCategory.VERY_SLOW
        elif self.spd < 30:
            return SpeedCategory.SLOW
        elif self.spd < 50:
            return SpeedCategory.MODERATE
        elif self.spd < 70:
            return SpeedCategory.FAST
        else:
            return SpeedCategory.VERY_FAST


@dataclass
class Zone:
    """Модель зоны спроса"""
    zone_id: int
    lat: float
    lng: float
    demand: int
    percentage: float
    address: str


@dataclass 
class TrafficGridCell:
    """Ячейка сетки трафика"""
    lat_bin: int
    lng_bin: int
    avg_speed: float
    points_count: int
    unique_trips: int
    lat_center: float
    lng_center: float


@dataclass
class AnomalyPoint:
    """Аномальная точка"""
    lat: float
    lng: float
    spd: float
    alt: float
    is_anomaly: int


@dataclass
class Route:
    """Модель маршрута"""
    route_id: int
    unique_trips: int
    avg_speed: float
    lat_span: float
    lng_span: float


@dataclass
class SafetyZone:
    """Опасная зона"""
    zone_id: int
    center_lat: float
    center_lng: float
    incidents: int
    high_speed_incidents: int
    night_incidents: int
    avg_speed: float
    risk_score: float


@dataclass
class DemandPrediction:
    """Предсказание спроса"""
    lat: float
    lng: float
    predicted_demand: float
    confidence: float


@dataclass
class HourlyDemand:
    """Почасовой спрос"""
    hour: int
    is_weekend: bool
    predictions: List[DemandPrediction]


@dataclass
class DriverAllocation:
    """Распределение водителей"""
    lat: float
    lng: float
    predicted_demand: float
    recommended_drivers: int
    efficiency_score: float


@dataclass
class BasicStats:
    """Базовая статистика"""
    total_records: int
    unique_trips: int
    avg_speed: float
    coverage_area: float


@dataclass
class EcoAnalysis:
    """Экологический анализ"""
    total_distance_km: float
    total_co2_kg: float
    avg_efficiency: float
    potential_annual_savings_kg: float
    trips_analyzed: int


class DataProcessor:
    """Процессор данных для конвертации между форматами"""
    
    @staticmethod
    def dataframe_to_gps_points(df: pd.DataFrame) -> List[GPSPoint]:
        """Конвертация DataFrame в список GPS точек"""
        return [
            GPSPoint(
                randomized_id=row['randomized_id'],
                lat=row['lat'],
                lng=row['lng'], 
                alt=row['alt'],
                spd=row['spd'],
                azm=row['azm']
            )
            for _, row in df.iterrows()
        ]
    
    @staticmethod
    def gps_points_to_dataframe(points: List[GPSPoint]) -> pd.DataFrame:
        """Конвертация списка GPS точек в DataFrame"""
        return pd.DataFrame([
            {
                'randomized_id': p.randomized_id,
                'lat': p.lat,
                'lng': p.lng,
                'alt': p.alt,
                'spd': p.spd,
                'azm': p.azm
            }
            for p in points
        ])
    
    @staticmethod
    def zones_to_dict_list(zones: List[Zone]) -> List[Dict[str, Any]]:
        """Конвертация зон в список словарей для JSON"""
        return [
            {
                'zone_id': zone.zone_id,
                'lat': zone.lat,
                'lng': zone.lng,
                'demand': zone.demand,
                'percentage': zone.percentage,
                'address': zone.address
            }
            for zone in zones
        ]
    
    @staticmethod
    def traffic_grid_to_dict_list(cells: List[TrafficGridCell]) -> List[Dict[str, Any]]:
        """Конвертация сетки трафика в список словарей"""
        return [
            {
                'lat_bin': cell.lat_bin,
                'lng_bin': cell.lng_bin,
                'avg_speed': cell.avg_speed,
                'points_count': cell.points_count,
                'unique_trips': cell.unique_trips,
                'lat_center': cell.lat_center,
                'lng_center': cell.lng_center
            }
            for cell in cells
        ]