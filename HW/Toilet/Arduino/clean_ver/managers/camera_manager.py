#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
카메라 관리자
PI 카메라 초기화 및 프레임 캡처 담당
"""

import logging
import time
from typing import Optional, Tuple, Dict, Any
import numpy as np

try:
    from picamera2 import Picamera2
    import cv2
except ImportError as e:
    logging.error(f"카메라 라이브러리 임포트 실패: {e}")
    raise

from ..optimized_config import SystemConfig

class CameraError(Exception):
    """카메라 관련 예외"""
    pass

class CameraManager:
    """PI 카메라 관리자"""
    
    def __init__(self, 
                 resolution: Optional[Tuple[int, int]] = None,
                 framerate: Optional[int] = None):
        """
        카메라 관리자 초기화
        
        Args:
            resolution: 카메라 해상도 (width, height)
            framerate: 프레임 레이트
        """
        self.logger = logging.getLogger(__name__)
        
        # 설정 적용
        self.resolution = resolution or SystemConfig.CAMERA_RESOLUTION
        self.framerate = framerate or SystemConfig.CAMERA_FPS
        self.warmup_time = SystemConfig.CAMERA_WARMUP_TIME
        
        # 상태 변수
        self.is_initialized = False
        self.picam2: Optional[Picamera2] = None
        self.frame_count = 0
        
        # 성능 모니터링
        self.capture_times = []
        
        # 카메라 초기화
        self._initialize_camera()
    
    def _initialize_camera(self) -> None:
        """PI 카메라 초기화"""
        try:
            self.logger.info("PI 카메라 초기화 중...")
            
            # Picamera2 객체 생성
            self.picam2 = Picamera2()
            
            # 카메라 설정
            camera_config = self.picam2.create_still_configuration(
                main={"size": self.resolution, "format": "RGB888"}
            )
            self.picam2.configure(camera_config)
            
            # 카메라 시작
            self.picam2.start()
            
            # 카메라 워밍업
            self._warmup_camera()
            
            self.is_initialized = True
            self.logger.info(f"PI 카메라 초기화 완료! 해상도: {self.resolution}, FPS: {self.framerate}")
            
        except Exception as e:
            error_msg = f"PI 카메라 초기화 실패: {e}"
            self.logger.error(error_msg)
            raise CameraError(error_msg)
    
    def _warmup_camera(self) -> None:
        """카메라 워밍업"""
        self.logger.debug(f"카메라 워밍업 중... ({self.warmup_time}초)")
        time.sleep(self.warmup_time)
        
        # 몇 개의 테스트 프레임 캡처
        for _ in range(3):
            try:
                self.picam2.capture_array()
            except Exception:
                pass  # 워밍업 중에는 에러 무시
        
        self.logger.debug("카메라 워밍업 완료")
    
    def capture_frame(self) -> np.ndarray:
        """프레임 캡처"""
        if not self.is_initialized or self.picam2 is None:
            raise CameraError("카메라가 초기화되지 않았습니다")
        
        try:
            frame = self.picam2.capture_array()
            self.frame_count += 1
            return frame
        except Exception as e:
            raise CameraError(f"프레임 캡처 실패: {e}")
    
    def _update_performance_metrics(self, capture_time: float) -> None:
        """성능 메트릭 업데이트"""
        self.capture_times.append(capture_time)
        
        # 최근 100개 프레임만 유지
        if len(self.capture_times) > 100:
            self.capture_times.pop(0)
    
    def get_frame_info(self, frame: np.ndarray) -> Dict[str, Any]:
        """프레임 정보 반환"""
        if frame is None or frame.size == 0:
            return {"error": "Invalid frame"}
        
        return {
            "shape": frame.shape,
            "dtype": str(frame.dtype),
            "size": frame.size,
            "channels": frame.shape[2] if len(frame.shape) == 3 else 1
        }
    
    def validate_frame(self, frame: np.ndarray) -> bool:
        """프레임 유효성 검증"""
        if frame is None:
            return False
        
        if frame.size == 0:
            return False
        
        # 예상 해상도와 일치하는지 확인
        expected_height, expected_width = self.resolution[1], self.resolution[0]
        if frame.shape[:2] != (expected_height, expected_width):
            self.logger.warning(f"예상 해상도 불일치: {frame.shape[:2]} != {(expected_height, expected_width)}")
        
        return True
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        if not self.capture_times:
            return {"error": "No capture data available"}
        
        avg_capture_time = sum(self.capture_times) / len(self.capture_times)
        max_capture_time = max(self.capture_times)
        min_capture_time = min(self.capture_times)
        estimated_fps = 1.0 / avg_capture_time if avg_capture_time > 0 else 0
        
        return {
            "frame_count": self.frame_count,
            "avg_capture_time": avg_capture_time,
            "max_capture_time": max_capture_time,
            "min_capture_time": min_capture_time,
            "estimated_fps": estimated_fps,
            "target_fps": self.framerate,
            "samples": len(self.capture_times)
        }
    
    def get_camera_status(self) -> Dict[str, Any]:
        """카메라 상태 반환"""
        return {
            "is_initialized": self.is_initialized,
            "resolution": self.resolution,
            "framerate": self.framerate,
            "frame_count": self.frame_count,
            "has_camera": self.picam2 is not None
        }
    
    def restart_camera(self) -> None:
        """카메라 재시작"""
        self.logger.info("카메라 재시작 중...")
        
        try:
            # 기존 카메라 정리
            if self.picam2 is not None:
                self.picam2.stop()
                self.picam2 = None
            
            self.is_initialized = False
            
            # 재초기화
            self._initialize_camera()
            
            self.logger.info("카메라 재시작 완료")
            
        except Exception as e:
            error_msg = f"카메라 재시작 실패: {e}"
            self.logger.error(error_msg)
            raise CameraError(error_msg)
    
    def adjust_settings(self, 
                       resolution: Optional[Tuple[int, int]] = None,
                       framerate: Optional[int] = None) -> None:
        """카메라 설정 조정"""
        settings_changed = False
        
        if resolution and resolution != self.resolution:
            self.resolution = resolution
            settings_changed = True
        
        if framerate and framerate != self.framerate:
            self.framerate = framerate
            settings_changed = True
        
        if settings_changed:
            self.logger.info(f"카메라 설정 변경: 해상도={self.resolution}, FPS={self.framerate}")
            self.restart_camera()
    
    def cleanup(self) -> None:
        """리소스 정리"""
        self.logger.info("카메라 리소스 정리 중...")
        
        try:
            if self.picam2 is not None:
                self.picam2.stop()
                self.picam2 = None
            
            self.is_initialized = False
            self.logger.info("카메라 리소스 정리 완료")
            
        except Exception as e:
            self.logger.error(f"카메라 정리 중 오류: {e}")
    
    def __enter__(self):
        """Context manager 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.cleanup() 