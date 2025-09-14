#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сервис для работы с Google AI (Gemini)
"""

from typing import Optional
import google.generativeai as genai
from ..config.config import Config


class AIService:
    """Сервис для работы с искусственным интеллектом"""
    
    def __init__(self, config: Config):
        self.config = config
        self.model = None
        self.available = False
        self._initialize_ai()
    
    def _initialize_ai(self):
        """Инициализация AI клиента"""
        try:
            genai.configure(api_key=self.config.GOOGLE_API_KEY)
            
            # Проверяем доступные модели
            try:
                available_models = [m.name for m in genai.list_models()]
                print(f"📋 Доступные модели: {available_models[:3]}...")
            except:
                print("⚠️ Не удалось получить список моделей")
            
            # Пробуем инициализировать модели по приоритету
            for model_name in self.config.AI_MODELS:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    print(f"✅ Используется модель: {model_name}")
                    self.available = True
                    break
                except Exception as e:
                    print(f"⚠️ Модель {model_name} недоступна: {str(e)[:100]}...")
                    continue
            
            if self.model:
                print("✅ Google AI Studio API инициализирован")
            else:
                print("❌ Не удалось инициализировать ни одну модель")
                
        except Exception as e:
            print(f"⚠️ Google AI Studio API недоступен: {e}")
            self.available = False
    
    def get_analysis(self, 
                    prompt: str, 
                    system_prompt: str = "Ты эксперт по транспортной аналитике и безопасности дорожного движения.",
                    max_tokens: Optional[int] = None) -> str:
        """
        Получает анализ от LLM
        
        Args:
            prompt: Пользовательский промпт
            system_prompt: Системный промпт
            max_tokens: Максимальное количество токенов
            
        Returns:
            Ответ от AI или сообщение об ошибке
        """
        if not self.available or not self.model:
            return "ИИ анализ временно недоступен. Используются стандартные алгоритмы."
        
        try:
            # Используем max_tokens из параметра или конфига
            tokens = max_tokens or self.config.AI_CONFIG['max_tokens']
            
            # Комбинируем промпты
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Генерируем ответ
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=tokens,
                    temperature=self.config.AI_CONFIG['temperature'],
                    top_p=self.config.AI_CONFIG['top_p'],
                    top_k=self.config.AI_CONFIG['top_k']
                ),
                safety_settings=self.config.AI_SAFETY_SETTINGS
            )
            
            if response.text:
                return response.text.strip()
            else:
                return "ИИ не смог сгенерировать ответ. Проверьте промпт или попробуйте позже."
                
        except Exception as e:
            return self._handle_ai_error(str(e))
    
    def _handle_ai_error(self, error_msg: str) -> str:
        """Обработка ошибок AI"""
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
    
    def analyze_safety_data(self, safety_zones: list, detailed_incidents: list) -> str:
        """Анализ данных безопасности с помощью ИИ"""
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

        return self.get_analysis(
            llm_prompt,
            "Ты эксперт по безопасности дорожного движения в городах Казахстана. Анализируй данные о ДТП и предлагай конкретные решения для улучшения безопасности.",
            300
        )
    
    def analyze_driver_optimization(self, peak_hours: list, low_demand_hours: list, optimization_data: list) -> str:
        """Анализ оптимизации водителей с помощью ИИ"""
        llm_prompt = f"""Проанализируй оптимизацию распределения 100 водителей в Астане по 24-часовому циклу:

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

        return self.get_analysis(
            llm_prompt,
            "Ты эксперт по логистике и оптимизации транспортных систем в городах Казахстана. Создавай практичные стратегии для максимизации эффективности работы водителей.",
            350
        )