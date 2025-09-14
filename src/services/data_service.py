#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сервис для загрузки и очистки данных
"""

import pandas as pd
import numpy as np
from typing import Tuple
from ..config.config import Config
from ..models.data_models import GPSPoint, DataProcessor


class DataService:
    """Сервис для работы с GPS данными"""
    
    def __init__(self, config: Config):
        self.config = config
        self.cached_data = {}
    
    def load_data(self, sample_size: int = None) -> pd.DataFrame:
        """Загружает GPS данные из файла с возможностью sampling"""
        cache_key = f'raw_data_{sample_size or "full"}'
        if cache_key in self.cached_data:
            return self.cached_data[cache_key]
        
        print("🔄 Загружаем и обрабатываем данные...")
        
        try:
            # Пробуем загрузить реальные данные
            if sample_size:
                # Быстрая загрузка только части данных
                print(f"📊 Загружаем sample размером {sample_size:,} записей для быстрого старта...")
                df = pd.read_csv(
                    self.config.DATA_PATH,
                    dtype={
                        'randomized_id': 'int64',
                        'lat': 'float32',
                        'lng': 'float32',
                        'alt': 'float32',
                        'spd': 'float32',
                        'azm': 'float32'
                    },
                    nrows=sample_size
                )
            else:
                df = pd.read_csv(
                    self.config.DATA_PATH,
                    dtype={
                        'randomized_id': 'int64',
                        'lat': 'float32',
                        'lng': 'float32',
                        'alt': 'float32',
                        'spd': 'float32',
                        'azm': 'float32'
                    }
                )
            print(f"✅ Загружено {len(df):,} записей")
            
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            # Создаем тестовые данные
            df = self._generate_test_data()
            print(f"⚠️ Используются тестовые данные: {len(df):,} записей")
        
        self.cached_data[cache_key] = df
        return df

    def clean_data(self, df: pd.DataFrame, sample_size: int = None) -> pd.DataFrame:
        """Очищает данные от выбросов"""
        cache_key = f'clean_data_{sample_size or "full"}'
        if cache_key in self.cached_data:
            return self.cached_data[cache_key]
        
        print("🧹 Очистка данных...")
        
        # Фильтруем по координатам Астаны
        bounds = self.config.ASTANA_BOUNDS
        valid_coords = (
            (df['lat'] >= bounds['lat_min']) & (df['lat'] <= bounds['lat_max']) &
            (df['lng'] >= bounds['lng_min']) & (df['lng'] <= bounds['lng_max'])
        )
        df_clean = df[valid_coords].copy()
        
        # Применяем фильтры данных
        filters = self.config.DATA_FILTERS
        
        # Фильтр скорости
        df_clean = df_clean[
            (df_clean['spd'] >= filters['speed_min']) & 
            (df_clean['spd'] <= filters['speed_max'])
        ]
        
        # Фильтр высоты
        df_clean = df_clean[
            (df_clean['alt'] >= filters['altitude_min']) & 
            (df_clean['alt'] <= filters['altitude_max'])
        ]
        
        # Фильтр азимута
        df_clean = df_clean[
            (df_clean['azm'] >= filters['azimuth_min']) & 
            (df_clean['azm'] <= filters['azimuth_max'])
        ]
        
        # Удаляем короткие поездки
        trip_counts = df_clean['randomized_id'].value_counts()
        valid_trips = trip_counts[trip_counts >= filters['min_trip_points']].index
        df_clean = df_clean[df_clean['randomized_id'].isin(valid_trips)]
        
        print(f"✅ Очищено: {len(df_clean):,} записей")
        
        self.cached_data[cache_key] = df_clean
        return df_clean
    
    def get_processed_data(self, sample_size: int = None) -> pd.DataFrame:
        """Получает обработанные данные (загружает и очищает если нужно)"""
        cache_key = f'clean_data_{sample_size or "full"}'
        if cache_key in self.cached_data:
            return self.cached_data[cache_key]
        
        raw_data = self.load_data(sample_size)
        clean_data = self.clean_data(raw_data, sample_size)
        return clean_data
    
    def prepare_ml_data(self, df_clean: pd.DataFrame) -> pd.DataFrame:
        """Подготавливает данные для ML с синтетическими временными метками"""
        print("🤖 Подготавливаем данные для ML...")
        
        df_ml = df_clean.copy()
        
        # Создаем синтетические временные метки
        np.random.seed(self.config.ML_CONFIG['random_state'])
        base_time = pd.Timestamp('2024-01-01 00:00:00')
        time_offsets = np.random.uniform(0, 24*30*60, len(df_ml))  # 30 дней в минутах
        
        df_ml['timestamp'] = [base_time + pd.Timedelta(minutes=offset) for offset in time_offsets]
        df_ml['hour'] = df_ml['timestamp'].dt.hour
        df_ml['day_of_week'] = df_ml['timestamp'].dt.dayofweek
        df_ml['is_weekend'] = df_ml['day_of_week'].isin([5, 6]).astype(int)
        
        return df_ml
    
    def get_basic_stats(self, df_clean: pd.DataFrame) -> dict:
        """Вычисляет базовую статистику"""
        return {
            'total_records': int(df_clean.shape[0]),
            'unique_trips': int(df_clean['randomized_id'].nunique()),
            'avg_speed': float(df_clean['spd'].mean()),
            'coverage_area': float(
                (df_clean['lat'].max() - df_clean['lat'].min()) * 
                (df_clean['lng'].max() - df_clean['lng'].min()) * 111 * 85
            )
        }
    
    def get_speed_distribution(self, df_clean: pd.DataFrame) -> dict:
        """Анализ распределения скоростей"""
        print("📊 Анализ распределения скоростей...")
        
        def categorize_speed(speed):
            speed = float(speed)
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
        
        df_copy = df_clean.copy()
        df_copy['speed_category'] = df_copy['spd'].apply(categorize_speed)
        speed_dist = df_copy['speed_category'].value_counts()
        
        # Конвертируем в словарь с Python типами
        speed_distribution_dict = {
            str(category): int(count) 
            for category, count in speed_dist.items()
        }
        
        print(f"✅ Категории скоростей: {speed_distribution_dict}")
        return speed_distribution_dict
    
    def _generate_test_data(self) -> pd.DataFrame:
        """Генерирует тестовые данные если файл недоступен"""
        np.random.seed(42)
        n_records = 50000
        
        return pd.DataFrame({
            'randomized_id': np.random.randint(1000, 9999, n_records),
            'lat': np.random.uniform(51.05, 51.25, n_records),
            'lng': np.random.uniform(71.3, 71.6, n_records),
            'alt': np.random.uniform(320, 380, n_records),
            'spd': np.random.exponential(25, n_records),
            'azm': np.random.uniform(0, 360, n_records)
        })
    
    def clear_cache(self):
        """Очистка кэша данных"""
        self.cached_data.clear()