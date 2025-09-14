#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для геокод        except Exception as e:
            print(f"⚠️ Ошибка геокодинга {lat}, {lng}: {e}")
            fallback = self._get_fallback_address(lat, lng)
            self.address_cache[cache_key] = fallback
            self._save_cache()  # Сохраняем кэш на диск
            return fallbackния адресов
"""

import time
import pickle
import os
from typing import Optional, Dict, Tuple
from geopy.geocoders import Nominatim
from ..config.config import Config


class GeoCoder:
    """Сервис геокодирования для получения адресов по координатам"""
    
    def __init__(self, config: Config):
        self.config = config
        self.geolocator = Nominatim(
            user_agent=config.GEOCODING_CONFIG['user_agent'],
            timeout=config.GEOCODING_CONFIG['timeout']
        )
        self.cache_file = 'geocoding_cache.pkl'
        self.address_cache: Dict[Tuple[float, float], str] = self._load_cache()
    
    def _load_cache(self) -> Dict[Tuple[float, float], str]:
        """Загрузка кэша из файла"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"⚠️ Ошибка загрузки кэша: {e}")
        return {}
    
    def _save_cache(self):
        """Сохранение кэша в файл"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.address_cache, f)
        except Exception as e:
            print(f"⚠️ Ошибка сохранения кэша: {e}")
    
    def _make_cache_key(self, lat: float, lng: float) -> Tuple[float, float]:
        """Создание ключа кэша с округлением до 4 знаков"""
        return (round(lat, 4), round(lng, 4))
    
    def get_address(self, lat: float, lng: float) -> str:
        """Получает адрес по координатам с кэшированием"""
        cache_key = self._make_cache_key(lat, lng)
        
        # Проверяем кэш
        if cache_key in self.address_cache:
            return self.address_cache[cache_key]
        
        try:
            # Задержка для избежания rate limiting
            time.sleep(self.config.GEOCODING_CONFIG['sleep_delay'])
            
            location = self.geolocator.reverse(f"{lat}, {lng}", language='ru')
            if location and location.address:
                address = self._process_address(location.address)
                self.address_cache[cache_key] = address
                self._save_cache()  # Сохраняем кэш на диск
                return address
            else:
                fallback = self._get_fallback_address(lat, lng)
                self.address_cache[cache_key] = fallback
                self._save_cache()  # Сохраняем кэш на диск
                return fallback
                
        except Exception as e:
            print(f"⚠️ Ошибка геокодирования для {lat}, {lng}: {e}")
            fallback = self._get_fallback_address(lat, lng)
            self.address_cache[cache_key] = fallback
            return fallback
    
    def _process_address(self, address: str) -> str:
        """Обрабатывает адрес для красивого отображения"""
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
        
        # Сокращаем если слишком длинный
        max_length = self.config.GEOCODING_CONFIG['max_address_length']
        if len(result) > max_length:
            result = result[:max_length - 3] + '...'
        
        return result
    
    def _get_fallback_address(self, lat: float, lng: float) -> str:
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
    
    def clear_cache(self):
        """Очистка кэша адресов"""
        self.address_cache.clear()