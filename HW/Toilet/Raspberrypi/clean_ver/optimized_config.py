#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
새똥 탐지 시스템 설정 관리
유지보수성을 고려한 중앙 집중식 설정
"""

import os
import psutil

class SystemConfig:
    """시스템 전체 설정"""
    
    # 카메라 설정
    CAMERA_RESOLUTION = (640, 480)
    CAMERA_FPS = 30
    CAMERA_WARMUP_TIME = 2
    
    # 탐지 모델 설정
    YOLO_MODEL_PATH = "/home/parrot1/gongdol/Inventon_Gongdol/HW/Toilet/AI/detect/train63/weights/best.pt"  # 사용자 정의 학습된 모델
    YOLO_CONFIDENCE = 0.6  # 신뢰도 임계값
    YOLO_IOU_THRESHOLD = 0.5  # NMS IOU 임계값
    TARGET_COVERAGE = 0.05  # 더 정확한 모델이므로 커버리지 기준 낮춤
    
    # 성능 최적화 설정 - YOLOv11s에 맞게 조정
    FRAME_SKIP_INTERVAL = 4  # YOLOv11s는 더 무거우므로 프레임 스킵 증가
    ENABLE_FRAME_SKIP = True  # 프레임 스킵 활성화 여부
    
    # 라즈베리파이 메모리 최적화 설정
    @classmethod
    def get_optimized_settings(cls):
        """라즈베리파이 메모리에 따른 최적화 설정"""
        available_memory = psutil.virtual_memory().available / (1024**3)  # GB
        
        if available_memory < 3.0:  # 3GB 미만 - 메모리 부족으로 해상도 낮춤
            return {
                'camera_resolution': (320, 240),
                'frame_skip_interval': 6,  # 더 많이 스킵
                'yolo_model_path': cls.YOLO_MODEL_PATH,  # 사용자 정의 모델 사용
                'yolo_confidence': 0.5,  # 신뢰도 약간 낮춤
                'enable_frame_skip': True,
                'batch_size': 1,
                'warning_message': '⚠️ 메모리 부족으로 해상도 및 프레임레이트 조정됨'
            }
        elif available_memory < 5.0:  # 5GB 미만
            return {
                'camera_resolution': (480, 360),
                'frame_skip_interval': 4,
                'yolo_model_path': cls.YOLO_MODEL_PATH,  # 사용자 정의 모델 사용
                'yolo_confidence': 0.6,
                'enable_frame_skip': True,
                'batch_size': 1,
                'warning_message': '⚠️ 성능 최적화를 위해 해상도 조정됨'
            }
        else:  # 5GB 이상
            return {
                'camera_resolution': (640, 480),
                'frame_skip_interval': 3,
                'yolo_model_path': cls.YOLO_MODEL_PATH,  # 사용자 정의 모델 사용
                'yolo_confidence': 0.6,
                'enable_frame_skip': True,
                'batch_size': 1,
                'warning_message': None
            }
    
    # 센서 설정
    SENSOR_UPDATE_INTERVAL = 3  # 3초마다 센서 데이터 업데이트
    SENSOR_ERROR_VALUE = -999   # 센서 오류 시 반환값
    
    # 청소 동작 설정
    STEPS_PER_REVOLUTION = 2048
    CLEANING_REVOLUTIONS = 5
    CLEANING_SPEED = 12
    CLEANING_COOLDOWN = 2  # 청소 후 대기 시간
    
    # 시스템 상태 설정
    MAX_CLEAN_COUNT = 10
    MAX_WARNING_EXTRA = 2
    
    # 통신 설정 - 라즈베리파이 하드웨어 시리얼 (GPIO 14, 15번 핀)
    # GPIO 14 (TXD) - 데이터 송신
    # GPIO 15 (RXD) - 데이터 수신
    ARDUINO_PORT = '/dev/serial0'  # 라즈베리파이 하드웨어 UART (GPIO 14, 15번)
    ARDUINO_BAUDRATE = 115200
    ARDUINO_TIMEOUT = 2  # 하드웨어 시리얼이므로 조금 더 여유있게
    ARDUINO_BACKUP_PORTS = ['/dev/ttyS0', '/dev/ttyAMA0']  # 백업 포트들
    
    # 하드웨어 시리얼 특화 설정
    SERIAL_WRITE_TIMEOUT = 1
    SERIAL_READ_TIMEOUT = 2
    SERIAL_RETRY_COUNT = 3
    SERIAL_RETRY_DELAY = 0.1
    
    # UART 핀 정의 (참고용)
    UART_TX_PIN = 14  # GPIO 14 - TXD (송신)
    UART_RX_PIN = 15  # GPIO 15 - RXD (수신)
    UART_GROUND_PIN = 6  # GND
    UART_POWER_PIN = 4   # 5V (아두이노 전원용)
    
    # 디버그 설정
    DEBUG_MODE = False
    LOG_LEVEL = "INFO"
    SAVE_DEBUG_IMAGES = False
    
    # 라즈베리파이 특화 설정
    @classmethod
    def is_raspberry_pi(cls):
        """라즈베리파이 여부 확인"""
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read()
                return 'Raspberry Pi' in model
        except:
            return False
    
    @classmethod
    def get_raspberry_pi_model(cls):
        """라즈베리파이 모델 확인"""
        try:
            with open('/proc/device-tree/model', 'r') as f:
                return f.read().strip()
        except:
            return "Unknown"

class PerformanceConfig:
    """성능 최적화 관련 설정"""
    
    # 메모리 최적화
    REUSE_DISPLAY_BUFFER = True
    CLEAR_DETECTION_CACHE = True
    
    # 처리 최적화
    PARALLEL_SENSOR_PROCESSING = False  # 단순함을 위해 기본값 False
    BATCH_SENSOR_REQUESTS = False
    
    # 시각화 최적화
    CONDITIONAL_VISUALIZATION = True  # 탐지된 경우만 시각화
    SIMPLIFIED_UI = False
    
    # 라즈베리파이 온도 관리
    @classmethod
    def get_cpu_temperature(cls):
        """CPU 온도 확인"""
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read()) / 1000.0
                return temp
        except:
            return None
    
    @classmethod
    def should_throttle_performance(cls):
        """성능 제한 여부 확인 (온도 기반)"""
        temp = cls.get_cpu_temperature()
        if temp is None:
            return False
        return temp > 75.0  # 75도 이상 시 성능 제한

class MaintenanceConfig:
    """유지보수 관련 설정"""
    
    # 로깅 설정
    LOG_TO_FILE = True
    LOG_FILE_PATH = "system.log"
    LOG_ROTATION_SIZE = "10MB"
    LOG_RETENTION_DAYS = 7
    
    # 모니터링 설정
    MONITOR_MEMORY_USAGE = True
    MONITOR_PERFORMANCE = True
    PERFORMANCE_LOG_INTERVAL = 60  # 1분마다 성능 로그
    
    # 백업 설정
    AUTO_BACKUP_CONFIG = True
    BACKUP_INTERVAL_DAYS = 1

# 설정 검증 함수
def validate_config():
    """설정값들이 유효한지 검증"""
    errors = []
    
    # 카메라 설정 검증
    if not isinstance(SystemConfig.CAMERA_RESOLUTION, tuple) or len(SystemConfig.CAMERA_RESOLUTION) != 2:
        errors.append("CAMERA_RESOLUTION must be a tuple of (width, height)")
    
    if SystemConfig.CAMERA_FPS <= 0:
        errors.append("CAMERA_FPS must be positive")
    
    # YOLO 설정 검증
    if not (0 < SystemConfig.YOLO_CONFIDENCE <= 1):
        errors.append("YOLO_CONFIDENCE must be between 0 and 1")
    
    if not (0 < SystemConfig.TARGET_COVERAGE <= 1):
        errors.append("TARGET_COVERAGE must be between 0 and 1")
    
    # 성능 설정 검증
    if SystemConfig.FRAME_SKIP_INTERVAL <= 0:
        errors.append("FRAME_SKIP_INTERVAL must be positive")
    
    if SystemConfig.SENSOR_UPDATE_INTERVAL <= 0:
        errors.append("SENSOR_UPDATE_INTERVAL must be positive")
    
    return errors

# 설정 덤프 함수 (디버깅용)
def dump_config():
    """현재 설정을 출력"""
    print("=== 시스템 설정 ===")
    print(f"카메라 해상도: {SystemConfig.CAMERA_RESOLUTION}")
    print(f"카메라 FPS: {SystemConfig.CAMERA_FPS}")
    print(f"YOLO 신뢰도: {SystemConfig.YOLO_CONFIDENCE}")
    print(f"프레임 스킵 간격: {SystemConfig.FRAME_SKIP_INTERVAL}")
    print(f"센서 업데이트 간격: {SystemConfig.SENSOR_UPDATE_INTERVAL}")
    print(f"최대 청소 횟수: {SystemConfig.MAX_CLEAN_COUNT}")
    print(f"디버그 모드: {SystemConfig.DEBUG_MODE}")
    
    # 라즈베리파이 정보
    if SystemConfig.is_raspberry_pi():
        print(f"라즈베리파이 모델: {SystemConfig.get_raspberry_pi_model()}")
        temp = PerformanceConfig.get_cpu_temperature()
        if temp:
            print(f"CPU 온도: {temp:.1f}°C")
    
    # 메모리 정보
    memory = psutil.virtual_memory()
    print(f"사용 가능한 메모리: {memory.available / (1024**3):.1f}GB")
    
    # 최적화 설정 제안
    optimized = SystemConfig.get_optimized_settings()
    print(f"권장 설정: {optimized}")

if __name__ == "__main__":
    # 설정 검증
    errors = validate_config()
    if errors:
        print("❌ 설정 오류:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ 설정 검증 완료")
    
    # 설정 출력
    dump_config() 