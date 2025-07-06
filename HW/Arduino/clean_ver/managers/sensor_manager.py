#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
센서 데이터 관리자
DHT11 센서 데이터 읽기 및 캐싱 담당
"""

import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from threading import Lock

from ..optimized_config import SystemConfig

@dataclass
class SensorData:
    """센서 데이터 클래스"""
    temperature: float
    humidity: float
    timestamp: float
    is_valid: bool = True
    error_message: Optional[str] = None
    
    @property
    def is_temperature_valid(self) -> bool:
        return self.temperature != SystemConfig.SENSOR_ERROR_VALUE
    
    @property
    def is_humidity_valid(self) -> bool:
        return self.humidity != SystemConfig.SENSOR_ERROR_VALUE
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class SensorError(Exception):
    """센서 관련 예외"""
    pass

class SensorManager:
    """센서 데이터 관리자"""
    
    def __init__(self, arduino_client):
        """
        센서 관리자 초기화
        
        Args:
            arduino_client: 아두이노 클라이언트 (의존성 주입)
        """
        self.logger = logging.getLogger(__name__)
        self.arduino_client = arduino_client
        
        # 캐싱 관련
        self._cached_data: Optional[SensorData] = None
        self._last_update_time = 0
        self._update_lock = Lock()
        
        # 설정
        self.update_interval = SystemConfig.SENSOR_UPDATE_INTERVAL
        
        self.logger.info("SensorManager 초기화 완료")
    
    def get_sensor_data(self, force_update: bool = False) -> SensorData:
        """
        센서 데이터 조회 (캐싱 지원)
        
        Args:
            force_update: 강제 업데이트 여부
            
        Returns:
            SensorData: 센서 데이터
        """
        current_time = time.time()
        
        # 캐시된 데이터 사용 가능한지 확인
        if (not force_update and 
            self._cached_data is not None and 
            current_time - self._last_update_time < self.update_interval):
            return self._cached_data
        
        # 새로운 데이터 읽기
        return self._update_sensor_data()
    
    def _update_sensor_data(self) -> SensorData:
        """센서 데이터 업데이트"""
        with self._update_lock:
            try:
                # 아두이노에서 센서 데이터 요청
                response = self.arduino_client.get_sensor_data()
                
                if response is None:
                    return self._create_error_data("아두이노 응답 없음")
                
                # 데이터 파싱
                temperature = response.get('temperature', SystemConfig.SENSOR_ERROR_VALUE)
                humidity = response.get('humidity', SystemConfig.SENSOR_ERROR_VALUE)
                
                # 센서 데이터 생성
                sensor_data = SensorData(
                    temperature=temperature,
                    humidity=humidity,
                    timestamp=time.time(),
                    is_valid=self._validate_sensor_values(temperature, humidity)
                )
                
                # 캐시 업데이트
                self._cached_data = sensor_data
                self._last_update_time = time.time()
                
                self.logger.debug(f"센서 데이터 업데이트: 온도={temperature}°C, 습도={humidity}%")
                
                return sensor_data
                
            except Exception as e:
                error_msg = f"센서 데이터 읽기 실패: {e}"
                self.logger.error(error_msg)
                return self._create_error_data(error_msg)
    
    def _validate_sensor_values(self, temperature: float, humidity: float) -> bool:
        """센서 값 유효성 검증"""
        # 온도 범위 검증 (-40°C ~ 80°C)
        temp_valid = -40 <= temperature <= 80 and temperature != SystemConfig.SENSOR_ERROR_VALUE
        
        # 습도 범위 검증 (0% ~ 100%)
        humidity_valid = 0 <= humidity <= 100 and humidity != SystemConfig.SENSOR_ERROR_VALUE
        
        return temp_valid and humidity_valid
    
    def _create_error_data(self, error_message: str) -> SensorData:
        """에러 데이터 생성"""
        return SensorData(
            temperature=SystemConfig.SENSOR_ERROR_VALUE,
            humidity=SystemConfig.SENSOR_ERROR_VALUE,
            timestamp=time.time(),
            is_valid=False,
            error_message=error_message
        )
    
    def get_cached_data(self) -> Optional[SensorData]:
        """캐시된 데이터 반환 (업데이트 없음)"""
        return self._cached_data
    
    def is_cache_valid(self) -> bool:
        """캐시 유효성 확인"""
        if self._cached_data is None:
            return False
        
        current_time = time.time()
        return current_time - self._last_update_time < self.update_interval
    
    def clear_cache(self) -> None:
        """캐시 초기화"""
        with self._update_lock:
            self._cached_data = None
            self._last_update_time = 0
            self.logger.debug("센서 데이터 캐시 초기화")
    
    def get_status(self) -> Dict[str, Any]:
        """센서 관리자 상태 반환"""
        return {
            "update_interval": self.update_interval,
            "has_cached_data": self._cached_data is not None,
            "cache_age": time.time() - self._last_update_time if self._last_update_time > 0 else 0,
            "is_cache_valid": self.is_cache_valid(),
            "last_data": self._cached_data.to_dict() if self._cached_data else None
        }
    
    def format_sensor_display(self, data: Optional[SensorData] = None) -> Dict[str, str]:
        """센서 데이터를 화면 표시용으로 포맷"""
        if data is None:
            data = self.get_cached_data()
        
        if data is None or not data.is_valid:
            return {
                "temperature": "온도: 센서 오류",
                "humidity": "습도: 센서 오류"
            }
        
        temp_text = f"온도: {data.temperature}°C" if data.is_temperature_valid else "온도: 센서 오류"
        humidity_text = f"습도: {data.humidity}%" if data.is_humidity_valid else "습도: 센서 오류"
        
        return {
            "temperature": temp_text,
            "humidity": humidity_text
        }
    
    def cleanup(self) -> None:
        """리소스 정리"""
        self.clear_cache()
        self.logger.info("SensorManager 정리 완료") 