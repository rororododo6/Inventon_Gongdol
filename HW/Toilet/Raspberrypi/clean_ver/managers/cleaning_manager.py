#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
새장 화장실 청소 관리자 모듈

새똥 탐지 시 모래 위의 똥을 치워주는 청소 동작을 관리하는 클래스
"""

import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

class SystemState(Enum):
    """시스템 상태"""
    NORMAL = "정상 작동"
    WARNING = "알림 후 제한 모드"
    STOPPED = "정지 상태"

class CleaningMode(Enum):
    """청소 모드"""
    SIMPLE = "simple"      # 간단한 청소 (스테핑 모터만)
    STANDARD = "standard"  # 표준 청소 (서보 + 스테핑 모터)
    INTENSIVE = "intensive" # 집중 청소 (서보 + 스테핑 모터 + 추가 정리)

@dataclass
class CleaningResult:
    """청소 결과 데이터"""
    success: bool
    mode: CleaningMode
    duration: float
    steps_moved: int
    servo_used: bool
    error_message: Optional[str] = None

@dataclass
class CleaningStatus:
    """청소 상태 데이터"""
    is_cleaning: bool
    current_mode: Optional[CleaningMode]
    progress: float  # 0.0 ~ 1.0
    last_cleaning_time: Optional[float]
    total_cleanings: int
    successful_cleanings: int
    failed_cleanings: int
    emergency_stopped: bool = False

class CleaningError(Exception):
    """청소 관련 예외"""
    pass

class CleaningManager:
    """새장 화장실 청소 관리자 클래스"""
    
    def __init__(self, arduino_client):
        """초기화"""
        self.arduino_client = arduino_client
        self.logger = logging.getLogger(__name__)
        
        # 청소 설정
        self.cleaning_mode = CleaningMode.STANDARD
        self.steps_per_revolution = 2048
        self.default_cleaning_revolutions = 3
        self.default_speed = 12
        
        # 청소 통계
        self.total_cleanings = 0
        self.successful_cleanings = 0
        self.failed_cleanings = 0
        
        self.logger.info("새장 화장실 청소 관리자 초기화 완료")
    
    def set_cleaning_mode(self, mode: CleaningMode):
        """청소 모드 설정"""
        self.cleaning_mode = mode
        self.logger.info(f"청소 모드 설정: {mode.value}")
    
    def perform_cleaning(self, coverage_ratio: float = 0.0) -> CleaningResult:
        """
        새장 화장실 청소 수행
        
        Args:
            coverage_ratio: 새똥 커버리지 비율 (0.0 ~ 1.0)
            
        Returns:
            CleaningResult: 청소 결과
        """
        start_time = time.time()
        self.total_cleanings += 1
        
        try:
            # 시스템 상태 확인
            if not self._check_system_ready():
                return CleaningResult(
                    success=False,
                    mode=self.cleaning_mode,
                    duration=0.0,
                    steps_moved=0,
                    servo_used=False,
                    error_message="시스템이 준비되지 않았습니다"
                )
            
            # 커버리지에 따른 청소 모드 자동 조정
            adjusted_mode = self._adjust_cleaning_mode(coverage_ratio)
            
            # 청소 수행
            result = self._execute_cleaning(adjusted_mode)
            
            # 결과 처리
            if result.success:
                self.successful_cleanings += 1
                self.logger.info(f"청소 완료: {adjusted_mode.value} 모드, 소요시간: {result.duration:.2f}초")
            else:
                self.failed_cleanings += 1
                self.logger.error(f"청소 실패: {result.error_message}")
            
            return result
            
        except Exception as e:
            self.failed_cleanings += 1
            error_msg = f"청소 중 오류 발생: {str(e)}"
            self.logger.error(error_msg)
            
            return CleaningResult(
                success=False,
                mode=self.cleaning_mode,
                duration=time.time() - start_time,
                steps_moved=0,
                servo_used=False,
                error_message=error_msg
            )
    
    def _check_system_ready(self) -> bool:
        """시스템 준비 상태 확인"""
        try:
            # Arduino 상태 확인
            if not self.arduino_client:
                return False
            
            # 상태 정보 요청
            status = self.arduino_client.get_system_status()
            if not status:
                return False
            
            # 긴급 정지 상태 확인
            if status.get('emergency_stop', False):
                self.logger.warning("긴급 정지 상태입니다")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"시스템 상태 확인 실패: {str(e)}")
            return False
    
    def _adjust_cleaning_mode(self, coverage_ratio: float) -> CleaningMode:
        """커버리지 비율에 따른 청소 모드 자동 조정"""
        if coverage_ratio < 0.1:  # 10% 미만: 간단한 청소
            return CleaningMode.SIMPLE
        elif coverage_ratio < 0.3:  # 30% 미만: 표준 청소
            return CleaningMode.STANDARD
        else:  # 30% 이상: 집중 청소
            return CleaningMode.INTENSIVE
    
    def _execute_cleaning(self, mode: CleaningMode) -> CleaningResult:
        """청소 모드에 따른 실제 청소 수행"""
        start_time = time.time()
        steps_moved = 0
        servo_used = False
        
        try:
            if mode == CleaningMode.SIMPLE:
                # 간단한 청소: 스테핑 모터만 사용
                result = self._perform_simple_cleaning()
                steps_moved = result.get('steps_moved', 0)
                
            elif mode == CleaningMode.STANDARD:
                # 표준 청소: 서보 + 스테핑 모터
                result = self._perform_standard_cleaning()
                steps_moved = result.get('steps_moved', 0)
                servo_used = result.get('servo_used', False)
                
            elif mode == CleaningMode.INTENSIVE:
                # 집중 청소: 전체 청소 프로세스
                result = self._perform_intensive_cleaning()
                steps_moved = result.get('steps_moved', 0)
                servo_used = result.get('servo_used', False)
            
            duration = time.time() - start_time
            
            return CleaningResult(
                success=True,
                mode=mode,
                duration=duration,
                steps_moved=steps_moved,
                servo_used=servo_used
            )
            
        except Exception as e:
            return CleaningResult(
                success=False,
                mode=mode,
                duration=time.time() - start_time,
                steps_moved=steps_moved,
                servo_used=servo_used,
                error_message=str(e)
            )
    
    def _perform_simple_cleaning(self) -> Dict[str, Any]:
        """간단한 청소 (스테핑 모터만)"""
        self.logger.info("간단한 청소 시작 - 스테핑 모터로 모래 위 똥 치우기")
        
        # 스테핑 모터로 똥 치우기
        total_steps = self.steps_per_revolution * self.default_cleaning_revolutions
        
        # 앞으로 이동 (똥 치우기)
        response = self.arduino_client.move_stepper(total_steps, self.default_speed)
        if not response:
            raise Exception("스테핑 모터 이동 실패 (앞으로)")
        
        time.sleep(1)  # 잠시 대기
        
        # 뒤로 복귀
        response = self.arduino_client.move_stepper(-total_steps, self.default_speed)
        if not response:
            raise Exception("스테핑 모터 이동 실패 (뒤로)")
        
        # 전력 절약
        self.arduino_client.disable_stepper()
        
        return {'steps_moved': total_steps}
    
    def _perform_standard_cleaning(self) -> Dict[str, Any]:
        """표준 청소 (서보 + 스테핑 모터)"""
        self.logger.info("표준 청소 시작 - 모래 밀어내기 + 스테핑 모터")
        
        # 1단계: 모래 밀어내기
        response = self.arduino_client.activate_cleaning_servo()
        if not response:
            raise Exception("청소 서보 작동 실패")
        
        # 2단계: 스테핑 모터로 똥 치우기
        total_steps = self.steps_per_revolution * self.default_cleaning_revolutions
        response = self.arduino_client.move_stepper(total_steps, self.default_speed)
        if not response:
            raise Exception("스테핑 모터 이동 실패")
        
        time.sleep(1)
        
        # 3단계: 원위치 복귀
        response = self.arduino_client.move_stepper(-total_steps, self.default_speed)
        if not response:
            raise Exception("스테핑 모터 복귀 실패")
        
        return {'steps_moved': total_steps, 'servo_used': True}
    
    def _perform_intensive_cleaning(self) -> Dict[str, Any]:
        """집중 청소 (전체 청소 프로세스)"""
        self.logger.info("집중 청소 시작 - 전체 새장 화장실 청소")
        
        # Arduino의 전체 청소 프로세스 사용
        response = self.arduino_client.perform_cage_cleaning()
        if not response:
            raise Exception("전체 청소 프로세스 실패")
        
        # 추가 정리 작업 (더 넓은 범위)
        extra_steps = self.steps_per_revolution * 2
        self.arduino_client.move_stepper(extra_steps, self.default_speed)
        time.sleep(1)
        self.arduino_client.move_stepper(-extra_steps, self.default_speed)
        
        return {
            'steps_moved': extra_steps,
            'servo_used': True
        }
    
    def get_cleaning_stats(self) -> Dict[str, Any]:
        """청소 통계 반환"""
        success_rate = (self.successful_cleanings / self.total_cleanings * 100) if self.total_cleanings > 0 else 0
        
        return {
            'total_cleanings': self.total_cleanings,
            'successful_cleanings': self.successful_cleanings,
            'failed_cleanings': self.failed_cleanings,
            'success_rate': round(success_rate, 2),
            'current_mode': self.cleaning_mode.value
        }
    
    def emergency_stop(self) -> bool:
        """긴급 정지 해제"""
        try:
            self.arduino_client.reset_emergency_stop()
            self.logger.info("긴급 정지 해제")
            return True
        except Exception as e:
            self.logger.error(f"긴급 정지 해제 실패: {str(e)}")
            return False
    
    def reset_cleaning_cycles(self) -> bool:
        """청소 횟수 초기화"""
        try:
            self.arduino_client.reset_cleaning_cycles()
            self.total_cleanings = 0
            self.successful_cleanings = 0
            self.failed_cleanings = 0
            self.logger.info("청소 횟수 초기화 완료")
            return True
        except Exception as e:
            self.logger.error(f"청소 횟수 초기화 실패: {str(e)}")
            return False
    
    def get_status(self) -> CleaningStatus:
        """현재 청소 상태 반환"""
        return CleaningStatus(
            is_cleaning=False,  # 실제 구현에서는 청소 중 상태를 추적
            current_mode=self.cleaning_mode,
            progress=1.0,  # 완료 상태
            last_cleaning_time=time.time(),  # 마지막 청소 시간
            total_cleanings=self.total_cleanings,
            successful_cleanings=self.successful_cleanings,
            failed_cleanings=self.failed_cleanings,
            emergency_stopped=False
        ) 