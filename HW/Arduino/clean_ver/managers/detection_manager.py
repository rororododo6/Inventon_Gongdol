#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
새똥 탐지 관리자
단일 책임 원칙에 따라 탐지 관련 로직만 담당
"""

import logging
from typing import Tuple, List, Optional, Union
from dataclasses import dataclass

try:
    from ultralytics import YOLO
    import cv2
    import numpy as np
except ImportError as e:
    logging.error(f"필수 라이브러리 임포트 실패: {e}")
    raise

from ..optimized_config import SystemConfig

@dataclass
class DetectionResult:
    """탐지 결과 데이터 클래스"""
    is_detected: bool
    coverage_ratio: float
    detection_boxes: List[Tuple[int, int, int, int]]
    confidence_scores: List[float]
    detection_count: int
    
    @property
    def has_detections(self) -> bool:
        return self.detection_count > 0

class DetectionError(Exception):
    """탐지 관련 예외"""
    pass

class DetectionManager:
    """새똥 탐지 관리자"""
    
    def __init__(self, 
                 model_path: Optional[str] = None,
                 confidence: Optional[float] = None,
                 target_coverage: Optional[float] = None):
        """
        탐지 관리자 초기화
        
        Args:
            model_path: YOLO 모델 경로
            confidence: 신뢰도 임계값
            target_coverage: 목표 커버리지 비율
        """
        self.logger = logging.getLogger(__name__)
        
        # 설정 적용 (의존성 주입)
        self.model_path = model_path or SystemConfig.YOLO_MODEL_PATH
        self.confidence = confidence or SystemConfig.YOLO_CONFIDENCE
        self.target_coverage = target_coverage or SystemConfig.TARGET_COVERAGE
        
        # 성능 최적화를 위한 변수들
        self.frame_count = 0
        self.cached_result: Optional[DetectionResult] = None
        
        # 모델 초기화
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """YOLO 모델 초기화"""
        try:
            self.logger.info(f"YOLO 모델 로딩 중... (경로: {self.model_path})")
            self.model = YOLO(self.model_path)
            self.logger.info("YOLO 모델 로딩 완료!")
        except Exception as e:
            error_msg = f"YOLO 모델 로딩 실패: {e}"
            self.logger.error(error_msg)
            raise DetectionError(error_msg)
    
    def detect(self, frame: np.ndarray) -> DetectionResult:
        """
        프레임에서 새똥 탐지
        
        Args:
            frame: 입력 프레임 (numpy array)
            
        Returns:
            DetectionResult: 탐지 결과
            
        Raises:
            DetectionError: 탐지 실패 시
        """
        if frame is None or frame.size == 0:
            raise DetectionError("입력 프레임이 유효하지 않습니다")
        
        # 프레임 스킵 최적화
        if self._should_skip_frame():
            return self._get_cached_result()
        
        try:
            return self._perform_detection(frame)
        except Exception as e:
            error_msg = f"탐지 실행 중 오류 발생: {e}"
            self.logger.error(error_msg)
            raise DetectionError(error_msg)
    
    def _should_skip_frame(self) -> bool:
        """프레임 스킵 여부 결정"""
        if not SystemConfig.ENABLE_FRAME_SKIP:
            return False
        
        self.frame_count += 1
        return (self.frame_count % SystemConfig.FRAME_SKIP_INTERVAL != 0 and 
                self.cached_result is not None)
    
    def _get_cached_result(self) -> DetectionResult:
        """캐시된 결과 반환"""
        if self.cached_result is None:
            # 캐시가 없으면 빈 결과 반환
            return DetectionResult(
                is_detected=False,
                coverage_ratio=0.0,
                detection_boxes=[],
                confidence_scores=[],
                detection_count=0
            )
        return self.cached_result
    
    def _perform_detection(self, frame: np.ndarray) -> DetectionResult:
        """실제 탐지 수행"""
        results = self.model(frame, conf=self.confidence, verbose=False)
        
        if not results or len(results) == 0:
            result = DetectionResult(
                is_detected=False,
                coverage_ratio=0.0,
                detection_boxes=[],
                confidence_scores=[],
                detection_count=0
            )
            self.cached_result = result
            return result
        
        # 탐지 결과 처리
        frame_area = frame.shape[0] * frame.shape[1]
        total_detection_area = 0
        detection_boxes = []
        confidence_scores = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # 박스 좌표 추출
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    box_area = (x2 - x1) * (y2 - y1)
                    total_detection_area += box_area
                    
                    # 결과 저장
                    detection_boxes.append((int(x1), int(y1), int(x2), int(y2)))
                    confidence_scores.append(float(box.conf.cpu().numpy()))
        
        # 커버리지 계산
        coverage_ratio = total_detection_area / frame_area
        is_detected = coverage_ratio >= self.target_coverage
        
        result = DetectionResult(
            is_detected=is_detected,
            coverage_ratio=coverage_ratio,
            detection_boxes=detection_boxes,
            confidence_scores=confidence_scores,
            detection_count=len(detection_boxes)
        )
        
        # 결과 캐싱
        self.cached_result = result
        
        self.logger.debug(f"탐지 결과: {result.detection_count}개 발견, "
                         f"커버리지: {coverage_ratio:.2%}")
        
        return result
    
    def visualize_detections(self, frame: np.ndarray, result: DetectionResult) -> np.ndarray:
        """
        탐지 결과를 프레임에 시각화
        
        Args:
            frame: 원본 프레임
            result: 탐지 결과
            
        Returns:
            시각화된 프레임
        """
        if not result.has_detections:
            return frame.copy()
        
        display_frame = frame.copy()
        
        for i, (x1, y1, x2, y2) in enumerate(result.detection_boxes):
            # 경계 상자 그리기
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 신뢰도 표시
            confidence = result.confidence_scores[i] if i < len(result.confidence_scores) else 0.0
            label = f"Bird Poop {confidence:.2f}"
            cv2.putText(display_frame, label, (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return display_frame
    
    def get_detection_summary(self) -> dict:
        """탐지 요약 정보 반환"""
        return {
            "model_path": self.model_path,
            "confidence": self.confidence,
            "target_coverage": self.target_coverage,
            "frame_count": self.frame_count,
            "has_cached_result": self.cached_result is not None
        }
    
    def reset_cache(self) -> None:
        """캐시 초기화"""
        self.cached_result = None
        self.frame_count = 0
        self.logger.debug("탐지 캐시 초기화됨")
    
    def cleanup(self) -> None:
        """리소스 정리"""
        self.reset_cache()
        self.logger.info("DetectionManager 정리 완료") 