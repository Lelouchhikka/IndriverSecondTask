#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для преобразования типов данных
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List


class TypeConverter:
    """Утилиты для конвертации типов данных в JSON-совместимые"""
    
    @staticmethod
    def convert_numpy_types(obj: Any) -> Any:
        """Рекурсивно конвертирует numpy типы в нативные Python типы"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: TypeConverter.convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [TypeConverter.convert_numpy_types(item) for item in obj]
        elif hasattr(obj, 'item'):  # numpy scalars
            return obj.item()
        else:
            return obj
    
    @staticmethod
    def safe_float(value: Any) -> float:
        """Безопасное преобразование в float"""
        if pd.isna(value):
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def safe_int(value: Any) -> int:
        """Безопасное преобразование в int"""
        if pd.isna(value):
            return 0
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def clean_for_json(data: Dict[str, Any]) -> Dict[str, Any]:
        """Очищает данные для JSON сериализации"""
        return TypeConverter.convert_numpy_types(data)