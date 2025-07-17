#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시스템 팩토리
Factory 패턴으로 시스템 구성요소들을 생성하고 의존성 주입을 관리
"""

import sys
import os
import logging
import importlib.util
from typing import Dict, Any, Optional

# 실제 ArduinoClient 임포트를 위한 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

# 개선된 ArduinoClient 클래스 임포트
try:
    from ..managers.arduino_client_improved import ArduinoClientImproved as ArduinoClient
    USE_REAL_ARDUINO = True
    print("✅ 개선된 ArduinoClient를 사용합니다.")
except ImportError:
    print("⚠️ 개선된 ArduinoClient를 찾을 수 없습니다. 스텁을 사용합니다.")
    USE_REAL_ARDUINO = False

from ..optimized_config import SystemConfig
from ..managers import (
    DetectionManager, DetectionError,
    SensorManager, SensorError,
    CameraManager, CameraError,
    CleaningManager
)

class SystemFactoryError(Exception):
    """시스템 팩토리 관련 예외"""
    pass

class ArduinoClientStub:
    """아두이노 클라이언트 스텁 (테스트용)"""
    def __init__(self, port='/dev/serial0', baudrate=115200, timeout=2):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.is_connected = False
        print(f"🔧 테스트용 ArduinoClientStub 생성됨")
        print(f"   - 포트: {port} (GPIO 14, 15번 하드웨어 시리얼)")
        print(f"   - 속도: {baudrate} bps")
    
    def connect(self):
        self.is_connected = True
        print("🔧 [STUB] 아두이노 하드웨어 시리얼 연결 시뮬레이션")
        print("   - GPIO 14 (TXD) → 아두이노 RX")
        print("   - GPIO 15 (RXD) ← 아두이노 TX")
        return True
    
    def disconnect(self):
        self.is_connected = False
        print("🔧 [STUB] 아두이노 하드웨어 시리얼 연결 해제 시뮬레이션")
    
    def get_sensor_data(self):
        return {"temperature": 25.0, "humidity": 60.0}
    
    def move_stepper(self, steps: int, speed: int):
        print(f"🔧 [STUB] 스테핑 모터 이동 시뮬레이션: {steps}스텝, {speed}RPM")
        return {"status": "success", "steps": steps, "speed": speed}
    
    def stop_stepper(self):
        print("🔧 [STUB] 스테핑 모터 정지 시뮬레이션")
        return {"status": "stopped"}
    
    def disable_stepper(self):
        print("🔧 [STUB] 스테핑 모터 비활성화 시뮬레이션")
        return {"status": "disabled"}
    
    def reset_stepper_position(self):
        print("🔧 [STUB] 스테핑 모터 위치 리셋 시뮬레이션")
        return {"status": "reset"}
    
    def get_system_status(self):
        return {
            "connected": self.is_connected,
            "port": self.port,
            "baudrate": self.baudrate,
            "cleaning_cycles": 0,
            "uptime": 10000
        }
    
    def perform_cage_cleaning(self):
        print("🔧 [STUB] 새장 화장실 전체 청소 시뮬레이션")
        return {"status": "cleaning_completed"}
    
    def activate_cleaning_servo(self):
        print("🔧 [STUB] 청소 서보모터 작동 시뮬레이션")
        return {"status": "servo_activated"}
    
    def emergency_stop(self):
        print("🔧 [STUB] 긴급 정지 시뮬레이션")
        return {"status": "emergency_stopped"}
    
    def reset_emergency_stop(self):
        print("🔧 [STUB] 긴급 정지 해제 시뮬레이션")
        return {"status": "emergency_reset"}
    
    # 누락된 메소드들 추가
    def control_servo(self, direction: int):
        print(f"🔧 [STUB] 서보모터 제어 시뮬레이션: 방향={direction}")
        return {"status": "success", "direction": direction}
    
    def stop_servo(self):
        print("🔧 [STUB] 서보모터 정지 시뮬레이션")
        return {"status": "stopped"}
    
    def system_test(self):
        print("🔧 [STUB] 시스템 테스트 시뮬레이션")
        return {"status": "test_completed"}
    
    def reset_cleaning_cycles(self):
        print("🔧 [STUB] 청소 횟수 리셋 시뮬레이션")
        return {"status": "cycles_reset"}
    
    def handle_trash_empty(self):
        print("🔧 [STUB] 쓰레기통 비우기 처리 시뮬레이션")
        return {"status": "trash_handled"}
    
    def ping(self):
        print("🔧 [STUB] Ping 테스트")
        return {"status": "pong"}
    
    def control_led(self, state: bool):
        print(f"🔧 [STUB] LED 제어 시뮬레이션: {'켜기' if state else '끄기'}")
        return {"status": "led_controlled", "state": state}

class SystemFactory:
    """시스템 구성요소 팩토리"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        시스템 팩토리 초기화
        
        Args:
            config: 사용자 정의 설정 (선택사항)
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self._components = {}
        
        # 로깅 설정
        self._setup_logging()
        
        self.logger.info("SystemFactory 초기화 완료")
    
    def _setup_logging(self) -> None:
        """로깅 설정"""
        log_level = self.config.get('log_level', SystemConfig.LOG_LEVEL)
        
        # 루트 로거 설정
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 특정 모듈 로그 레벨 조정
        logging.getLogger('ultralytics').setLevel(logging.WARNING)
    
    def create_arduino_client(self):
        """아두이노 클라이언트 생성"""
        if 'arduino_client' not in self._components:
            try:
                if USE_REAL_ARDUINO and not self.config.get('use_stub', False):
                    # 실제 ArduinoClient 사용
                    arduino_client = self._try_connect_real_arduino()
                    if arduino_client:
                        self._components['arduino_client'] = arduino_client
                        self.logger.info("✅ 실제 아두이노 클라이언트 연결 성공")
                    else:
                        self.logger.warning("⚠️ 실제 아두이노 연결 실패, 스텁 사용")
                        self._components['arduino_client'] = ArduinoClientStub(
                            port=self.config.get('arduino_port', SystemConfig.ARDUINO_PORT),
                            baudrate=self.config.get('arduino_baudrate', SystemConfig.ARDUINO_BAUDRATE)
                        )
                else:
                    # 스텁 사용 (테스트 모드)
                    self._components['arduino_client'] = ArduinoClientStub(
                        port=self.config.get('arduino_port', SystemConfig.ARDUINO_PORT),
                        baudrate=self.config.get('arduino_baudrate', SystemConfig.ARDUINO_BAUDRATE)
                    )
                    self.logger.info("🔧 테스트용 아두이노 클라이언트 스텁 생성")
                    
            except Exception as e:
                error_msg = f"아두이노 클라이언트 생성 실패: {e}"
                self.logger.error(error_msg)
                # 오류 발생 시 스텁으로 대체
                self._components['arduino_client'] = ArduinoClientStub()
                self.logger.warning("⚠️ 오류로 인해 스텁 사용")
        
        return self._components['arduino_client']
    
    def _try_connect_real_arduino(self):
        """실제 아두이노 연결 시도 (여러 포트 시도)"""
        # 시도할 포트 목록 (우선순위 순)
        ports_to_try = [
            self.config.get('arduino_port', SystemConfig.ARDUINO_PORT),  # 메인 포트 (serial0)
            *SystemConfig.ARDUINO_BACKUP_PORTS  # 백업 포트들
        ]
        
        for port in ports_to_try:
            try:
                self.logger.info(f"🔌 아두이노 연결 시도: {port}")
                arduino_client = ArduinoClient(
                    port=port,
                    baudrate=self.config.get('arduino_baudrate', SystemConfig.ARDUINO_BAUDRATE),
                    timeout=self.config.get('arduino_timeout', SystemConfig.ARDUINO_TIMEOUT)
                )
                
                # 연결 시도
                if arduino_client.connect():
                    self.logger.info(f"✅ 아두이노 연결 성공: {port}")
                    if port == SystemConfig.ARDUINO_PORT:
                        self.logger.info("   - GPIO 14 (TXD), 15 (RXD) 하드웨어 시리얼 사용")
                    return arduino_client
                else:
                    self.logger.warning(f"⚠️ 아두이노 연결 실패: {port}")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ 포트 {port} 연결 시도 중 오류: {e}")
                continue
        
        return None
    
    def create_detection_manager(self) -> DetectionManager:
        """탐지 관리자 생성"""
        if 'detection_manager' not in self._components:
            try:
                # 메모리 기반 최적화 설정 가져오기
                optimized_settings = SystemConfig.get_optimized_settings()
                
                # 설정 주입 (최적화 설정 우선)
                model_path = self.config.get('yolo_model_path') or optimized_settings.get('yolo_model_path', SystemConfig.YOLO_MODEL_PATH)
                confidence = self.config.get('yolo_confidence') or optimized_settings.get('yolo_confidence', SystemConfig.YOLO_CONFIDENCE)
                target_coverage = self.config.get('target_coverage', SystemConfig.TARGET_COVERAGE)
                
                # 최적화 경고 메시지 표시
                warning_msg = optimized_settings.get('warning_message')
                if warning_msg:
                    self.logger.warning(warning_msg)
                    print(f"⚠️ {warning_msg}")
                
                # 모델 정보 로깅
                if 'yolov11s.pt' in model_path:
                    self.logger.info("🎯 YOLOv11s 모델 사용 - 높은 정확도, 중간 성능")
                elif 'yolov11n.pt' in model_path:
                    self.logger.info("⚡ YOLOv11n 모델 사용 - 빠른 성능, 기본 정확도")
                
                self._components['detection_manager'] = DetectionManager(
                    model_path=model_path,
                    confidence=confidence,
                    target_coverage=target_coverage
                )
                self.logger.info("탐지 관리자 생성 완료")
            except Exception as e:
                error_msg = f"탐지 관리자 생성 실패: {e}"
                self.logger.error(error_msg)
                raise SystemFactoryError(error_msg)
        
        return self._components['detection_manager']
    
    def create_sensor_manager(self) -> SensorManager:
        """센서 관리자 생성"""
        if 'sensor_manager' not in self._components:
            try:
                # 아두이노 클라이언트 의존성 주입
                arduino_client = self.create_arduino_client()
                
                self._components['sensor_manager'] = SensorManager(arduino_client)
                self.logger.info("센서 관리자 생성 완료")
            except Exception as e:
                error_msg = f"센서 관리자 생성 실패: {e}"
                self.logger.error(error_msg)
                raise SystemFactoryError(error_msg)
        
        return self._components['sensor_manager']
    
    def create_camera_manager(self) -> CameraManager:
        """카메라 관리자 생성"""
        if 'camera_manager' not in self._components:
            try:
                # 메모리 기반 최적화 설정 가져오기
                optimized_settings = SystemConfig.get_optimized_settings()
                
                # 설정 주입 (최적화 설정 우선)
                resolution = self.config.get('camera_resolution') or optimized_settings.get('camera_resolution', SystemConfig.CAMERA_RESOLUTION)
                framerate = self.config.get('camera_fps', SystemConfig.CAMERA_FPS)
                
                # 해상도 정보 로깅
                self.logger.info(f"📷 카메라 해상도: {resolution}")
                if resolution != SystemConfig.CAMERA_RESOLUTION:
                    self.logger.info("📊 메모리 최적화를 위해 해상도가 조정되었습니다")
                
                self._components['camera_manager'] = CameraManager(
                    resolution=resolution,
                    framerate=framerate
                )
                self.logger.info("카메라 관리자 생성 완료")
            except Exception as e:
                error_msg = f"카메라 관리자 생성 실패: {e}"
                self.logger.error(error_msg)
                raise SystemFactoryError(error_msg)
        
        return self._components['camera_manager']
    
    def create_cleaning_manager(self) -> CleaningManager:
        """청소 관리자 생성"""
        if 'cleaning_manager' not in self._components:
            try:
                # 의존성 주입: 아두이노 클라이언트와 탐지 관리자
                arduino_client = self.create_arduino_client()
                detection_manager = self.create_detection_manager()
                
                self._components['cleaning_manager'] = CleaningManager(
                    arduino_client=arduino_client,
                    detection_manager=detection_manager  # 누적 영역 리셋을 위해 전달
                )
                self.logger.info("청소 관리자 생성 완료")
            except Exception as e:
                error_msg = f"청소 관리자 생성 실패: {e}"
                self.logger.error(error_msg)
                raise SystemFactoryError(error_msg)
        
        return self._components['cleaning_manager']
    
    def create_complete_system(self) -> Dict[str, Any]:
        """완전한 시스템 생성 (모든 구성요소)"""
        try:
            self.logger.info("완전한 시스템 생성 시작...")
            
            # 모든 구성요소 생성
            system_components = {
                'detection_manager': self.create_detection_manager(),
                'sensor_manager': self.create_sensor_manager(),
                'camera_manager': self.create_camera_manager(),
                'cleaning_manager': self.create_cleaning_manager(),
                'arduino_client': self.create_arduino_client()
            }
            
            self.logger.info("완전한 시스템 생성 완료!")
            return system_components
            
        except Exception as e:
            error_msg = f"완전한 시스템 생성 실패: {e}"
            self.logger.error(error_msg)
            raise SystemFactoryError(error_msg)
    
    def get_system_info(self) -> Dict[str, Any]:
        """시스템 정보 반환"""
        # 최적화 설정 가져오기
        optimized_settings = SystemConfig.get_optimized_settings()
        
        # YOLO 모델 정보 생성
        model_path = self.config.get('yolo_model_path') or optimized_settings.get('yolo_model_path', SystemConfig.YOLO_MODEL_PATH)
        
        # 모델 유형 판별
        model_info = self._get_model_info(model_path)
        
        return {
            'factory_config': self.config,
            'created_components': list(self._components.keys()),
            'system_config': {
                'yolo_model_path': SystemConfig.YOLO_MODEL_PATH,
                'camera_resolution': SystemConfig.CAMERA_RESOLUTION,
                'camera_fps': SystemConfig.CAMERA_FPS,
                'max_clean_count': SystemConfig.MAX_CLEAN_COUNT,
                'enable_frame_skip': SystemConfig.ENABLE_FRAME_SKIP,
                'frame_skip_interval': SystemConfig.FRAME_SKIP_INTERVAL
            },
            'optimized_settings': optimized_settings,
            'yolo_model_info': model_info,
            'memory_info': {
                'available_gb': __import__('psutil').virtual_memory().available / (1024**3),
                'optimization_applied': optimized_settings.get('warning_message') is not None
            }
        }
    
    def _get_model_info(self, model_path: str) -> Dict[str, Any]:
        """모델 정보 생성"""
        if 'best.pt' in model_path:
            return {
                'type': 'custom',
                'name': '사용자 정의 학습 모델',
                'accuracy': 'High (새똥 탐지 특화)',
                'performance': 'Optimized',
                'current_model': model_path,
                'is_custom': True,
                'confidence': SystemConfig.YOLO_CONFIDENCE
            }
        elif 'yolov11s.pt' in model_path:
            return {
                'type': 'pretrained',
                'name': 'YOLOv11s',
                'accuracy': 'Medium',
                'performance': 'Medium',
                'current_model': model_path,
                'is_custom': False,
                'confidence': SystemConfig.YOLO_CONFIDENCE
            }
        elif 'yolov11n.pt' in model_path:
            return {
                'type': 'pretrained', 
                'name': 'YOLOv11n',
                'accuracy': 'Low',
                'performance': 'High',
                'current_model': model_path,
                'is_custom': False,
                'confidence': SystemConfig.YOLO_CONFIDENCE
            }
        else:
            return {
                'type': 'unknown',
                'name': os.path.basename(model_path),
                'accuracy': 'Unknown',
                'performance': 'Unknown',
                'current_model': model_path,
                'is_custom': False,
                'confidence': SystemConfig.YOLO_CONFIDENCE
            }
    
    def validate_system(self) -> Dict[str, bool]:
        """시스템 유효성 검증"""
        validation_results = {}
        
        try:
            # 각 구성요소 검증
            validation_results['detection_manager'] = self._validate_detection_manager()
            validation_results['sensor_manager'] = self._validate_sensor_manager()
            validation_results['camera_manager'] = self._validate_camera_manager()
            validation_results['cleaning_manager'] = self._validate_cleaning_manager()
            
            # 전체 시스템 상태
            validation_results['system_healthy'] = all(validation_results.values())
            
        except Exception as e:
            self.logger.error(f"시스템 검증 중 오류: {e}")
            validation_results['system_healthy'] = False
        
        return validation_results
    
    def _validate_detection_manager(self) -> bool:
        """탐지 관리자 검증"""
        try:
            dm = self.create_detection_manager()
            # 모델 로드 상태 확인
            return hasattr(dm, 'model') and dm.model is not None
        except Exception:
            return False
    
    def _validate_sensor_manager(self) -> bool:
        """센서 관리자 검증"""
        try:
            sm = self.create_sensor_manager()
            # 아두이노 클라이언트 연결 확인
            return sm.arduino_client is not None
        except Exception:
            return False
    
    def _validate_camera_manager(self) -> bool:
        """카메라 관리자 검증"""
        try:
            cm = self.create_camera_manager()
            # 카메라 초기화 상태 확인
            return cm.is_initialized
        except Exception:
            return False
    
    def _validate_cleaning_manager(self) -> bool:
        """청소 관리자 검증"""
        try:
            clm = self.create_cleaning_manager()
            # 아두이노 클라이언트 연결 확인
            return clm.arduino_client is not None
        except Exception:
            return False
    
    def cleanup(self) -> None:
        """팩토리 정리"""
        self.logger.info("SystemFactory 정리 시작...")
        
        # 모든 구성요소 정리
        for name, component in self._components.items():
            try:
                if hasattr(component, 'cleanup'):
                    component.cleanup()
                    self.logger.debug(f"{name} 정리 완료")
            except Exception as e:
                self.logger.error(f"{name} 정리 실패: {e}")
        
        self._components.clear()
        self.logger.info("SystemFactory 정리 완료")
    
    def __enter__(self):
        """Context manager 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.cleanup() 