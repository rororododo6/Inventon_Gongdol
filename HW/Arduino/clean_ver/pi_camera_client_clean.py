#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PI 카메라 자동 청소 시스템 (클린코딩 버전)
YOLOv11s 기반 새똥 탐지 및 자동 청소 시스템
"""

import sys
import os
import cv2
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from clean_ver.factories import SystemFactory, SystemFactoryError
    from clean_ver.managers import DetectionResult, SensorData, CleaningStatus, SystemState
    from clean_ver.optimized_config import SystemConfig
except ImportError as e:
    print(f"❌ 모듈 임포트 실패: {e}")
    print("💡 clean_ver 폴더에서 실행하세요: python3 -m clean_ver.pi_camera_client_clean")
    sys.exit(1)

@dataclass
class SystemStatus:
    """시스템 전체 상태"""
    detection_result: DetectionResult
    sensor_data: SensorData
    cleaning_status: CleaningStatus
    frame_count: int
    running: bool

class AutoCleaningSystemError(Exception):
    """자동 청소 시스템 관련 예외"""
    pass

class AutoCleaningSystem:
    """자동 청소 시스템 메인 클래스"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        자동 청소 시스템 초기화
        
        Args:
            config: 사용자 정의 설정 (선택사항)
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # GUI 디스플레이 설정 (헤드리스 모드 지원)
        self.enable_display = self.config.get('enable_display', True)
        self.headless_mode = self.config.get('headless_mode', False)
        
        # 헤드리스 모드 자동 감지
        if not self.headless_mode and os.getenv('DISPLAY') is None:
            self.logger.warning("🖥️ DISPLAY 환경 변수가 없습니다. 헤드리스 모드로 전환합니다.")
            self.headless_mode = True
            self.enable_display = False
        
        # 상태 변수
        self.running = False
        self.frame_count = 0
        self.system_start_time = 0
        
        # 시스템 팩토리로 구성요소 생성
        self.factory = SystemFactory(config)
        self.components = {}
        
        # 시스템 초기화
        self._initialize_system()
    
    def _initialize_system(self) -> None:
        """시스템 초기화"""
        try:
            self.logger.info("🚀 자동 청소 시스템 초기화 시작...")
            
            # 모든 구성요소 생성
            self.components = self.factory.create_complete_system()
            
            # 시스템 검증
            validation_results = self.factory.validate_system()
            if not validation_results.get('system_healthy', False):
                raise AutoCleaningSystemError(f"시스템 검증 실패: {validation_results}")
            
            self.logger.info("✅ 자동 청소 시스템 초기화 완료!")
            
        except Exception as e:
            error_msg = f"시스템 초기화 실패: {e}"
            self.logger.error(error_msg)
            raise AutoCleaningSystemError(error_msg)
    
    def start(self) -> None:
        """시스템 시작"""
        if self.running:
            self.logger.warning("시스템이 이미 실행 중입니다.")
            return
        
        try:
            self.logger.info("🎯 자동 청소 시스템 시작!")
            self.running = True
            self.system_start_time = time.time()
            
            self._display_system_info()
            self._run_main_loop()
            
        except KeyboardInterrupt:
            self.logger.info("사용자에 의해 중단됨 (Ctrl+C)")
        except Exception as e:
            error_msg = f"시스템 실행 중 오류: {e}"
            self.logger.error(error_msg)
            raise AutoCleaningSystemError(error_msg)
        finally:
            self.stop()
    
    def _display_system_info(self) -> None:
        """시스템 정보 표시"""
        system_info = self.factory.get_system_info()
        yolo_info = system_info.get('yolo_model_info', {})
        memory_info = system_info.get('memory_info', {})
        
        self.logger.info("\n" + "="*50)
        self.logger.info("🎯 PI 카메라 자동 청소 시스템 (YOLOv11s)")
        self.logger.info("="*50)
        
        # YOLO 모델 정보
        current_model = yolo_info.get('current_model', 'Unknown')
        is_yolov11s = yolo_info.get('is_yolov11s', False)
        if is_yolov11s:
            self.logger.info(f"🎯 YOLO 모델: {current_model} (높은 정확도)")
        else:
            self.logger.info(f"⚡ YOLO 모델: {current_model} (빠른 성능)")
        
        self.logger.info(f"📷 카메라 해상도: {system_info['system_config']['camera_resolution']}")
        self.logger.info(f"🧹 최대 청소 횟수: {system_info['system_config']['max_clean_count']}")
        self.logger.info(f"⚡ 프레임 스킵: {system_info['system_config']['frame_skip_interval']}프레임")
        
        # 메모리 정보
        available_memory = memory_info.get('available_gb', 0)
        self.logger.info(f"💾 사용 가능한 메모리: {available_memory:.1f}GB")
        
        # 최적화 정보
        if memory_info.get('optimization_applied', False):
            self.logger.info("📊 메모리 최적화가 적용되었습니다")
        
        self.logger.info("="*50)
        self.logger.info("종료하려면 'q' 키를 누르세요.")
        self.logger.info("시스템 리셋은 'r' 키를 누르세요.")
        self.logger.info("="*50 + "\n")
    
    def _run_main_loop(self) -> None:
        """메인 실행 루프"""
        while self.running:
            try:
                # 시스템 상태 업데이트
                status = self._update_system_status()
                
                # 키보드 입력 처리
                if self._handle_keyboard_input():
                    break
                
                # 청소 결정 및 실행
                self._handle_cleaning_logic(status)
                
                # 화면 업데이트
                self._update_display(status)
                
                # 프레임 지연
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"메인 루프 오류: {e}")
                time.sleep(1)  # 오류 발생 시 잠시 대기
    
    def _update_system_status(self) -> SystemStatus:
        """시스템 상태 업데이트"""
        try:
            # 프레임 캡처
            frame = self.components['camera_manager'].capture_frame()
            
            # 새똥 탐지
            detection_result = self.components['detection_manager'].detect(frame)
            
            # 센서 데이터 읽기
            sensor_data = self.components['sensor_manager'].get_sensor_data()
            
            # 청소 상태 확인
            cleaning_status = self.components['cleaning_manager'].get_status()
            
            self.frame_count += 1
            
            return SystemStatus(
                detection_result=detection_result,
                sensor_data=sensor_data,
                cleaning_status=cleaning_status,
                frame_count=self.frame_count,
                running=self.running
            )
            
        except Exception as e:
            self.logger.error(f"시스템 상태 업데이트 실패: {e}")
            raise
    
    def _handle_keyboard_input(self) -> bool:
        """키보드 입력 처리"""
        if self.headless_mode:
            # 헤드리스 모드에서는 키보드 입력 없음
            return False
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            self.logger.info("종료 요청 받음")
            return True
        elif key == ord('r'):
            self._reset_system()
        elif key == ord('s'):
            self._show_system_stats()
        elif key == ord('h'):
            self._show_help()
        
        return False
    
    def _handle_cleaning_logic(self, status: SystemStatus) -> None:
        """청소 로직 처리"""
        cleaning_manager = self.components['cleaning_manager']
        
        # 청소 수행 여부 결정
        if cleaning_manager.should_perform_cleaning(status.detection_result):
            try:
                success = cleaning_manager.perform_cleaning()
                if success:
                    self.logger.info("청소 완료!")
                else:
                    self.logger.warning("청소 실패")
            except Exception as e:
                self.logger.error(f"청소 실행 중 오류: {e}")
    
    def _update_display(self, status: SystemStatus) -> None:
        """화면 업데이트"""
        if self.headless_mode or not self.enable_display:
            # 헤드리스 모드에서는 GUI 표시하지 않음
            return
        
        try:
            # 프레임 캡처
            frame = self.components['camera_manager'].capture_frame()
            
            # 탐지 결과 시각화
            if status.detection_result.has_detections:
                frame = self.components['detection_manager'].visualize_detections(
                    frame, status.detection_result
                )
            
            # 정보 오버레이 추가
            self._add_info_overlay(frame, status)
            
            # 화면 표시
            cv2.imshow('자동 청소 시스템', frame)
            
        except Exception as e:
            self.logger.error(f"화면 업데이트 실패: {e}")
            # GUI 오류 시 헤드리스 모드로 전환
            self.logger.warning("GUI 오류로 인해 헤드리스 모드로 전환합니다.")
            self.headless_mode = True
            self.enable_display = False
    
    def _add_info_overlay(self, frame, status: SystemStatus) -> None:
        """정보 오버레이 추가"""
        try:
            # 텍스트 설정
            font = cv2.FONT_HERSHEY_SIMPLEX
            color = (0, 255, 0) if status.cleaning_status.is_operational else (0, 0, 255)
            
            # 정보 텍스트들
            info_texts = [
                f"프레임: {status.frame_count}",
                f"탐지: {'발견' if status.detection_result.is_detected else '없음'}",
                f"상태: {status.cleaning_status.state.value}",
                f"청소 횟수: {status.cleaning_status.clean_count}/{status.cleaning_status.max_clean_count}",
            ]
            
            # 센서 정보 추가
            if status.sensor_data.is_valid:
                sensor_display = self.components['sensor_manager'].format_sensor_display(status.sensor_data)
                info_texts.extend([
                    sensor_display['temperature'],
                    sensor_display['humidity']
                ])
            
            # 텍스트 그리기
            for i, text in enumerate(info_texts):
                y_pos = 30 + i * 25
                cv2.putText(frame, text, (10, y_pos), font, 0.6, color, 2)
                
        except Exception as e:
            self.logger.error(f"정보 오버레이 추가 실패: {e}")
    
    def _reset_system(self) -> None:
        """시스템 리셋"""
        try:
            self.components['cleaning_manager'].reset_system()
            self.logger.info("시스템 리셋 완료")
        except Exception as e:
            self.logger.error(f"시스템 리셋 실패: {e}")
    
    def _show_system_stats(self) -> None:
        """시스템 통계 표시"""
        try:
            current_time = time.time()
            uptime = current_time - self.system_start_time
            
            self.logger.info("\n" + "="*30)
            self.logger.info("📊 시스템 통계")
            self.logger.info("="*30)
            self.logger.info(f"실행 시간: {uptime:.1f}초")
            self.logger.info(f"처리된 프레임: {self.frame_count}")
            self.logger.info(f"평균 FPS: {self.frame_count/uptime:.1f}" if uptime > 0 else "평균 FPS: 계산 중...")
            
            # 각 매니저 통계
            detection_stats = self.components['detection_manager'].get_detection_summary()
            cleaning_stats = self.components['cleaning_manager'].get_status_summary()
            sensor_stats = self.components['sensor_manager'].get_status()
            
            self.logger.info(f"탐지 캐시: {'있음' if detection_stats['has_cached_result'] else '없음'}")
            self.logger.info(f"청소 상태: {cleaning_stats['state']}")
            self.logger.info(f"센서 캐시: {'유효' if sensor_stats['is_cache_valid'] else '무효'}")
            self.logger.info("="*30 + "\n")
            
        except Exception as e:
            self.logger.error(f"시스템 통계 표시 실패: {e}")
    
    def _show_help(self) -> None:
        """도움말 표시"""
        self.logger.info("\n" + "="*30)
        self.logger.info("🆘 도움말")
        self.logger.info("="*30)
        self.logger.info("q: 시스템 종료")
        self.logger.info("r: 시스템 리셋")
        self.logger.info("s: 시스템 통계 표시")
        self.logger.info("h: 도움말 표시")
        self.logger.info("="*30 + "\n")
    
    def stop(self) -> None:
        """시스템 정지"""
        if not self.running:
            return
        
        self.logger.info("🛑 시스템 정지 중...")
        self.running = False
        
        try:
            # OpenCV 윈도우 정리 (GUI 모드에서만)
            if self.enable_display and not self.headless_mode:
                cv2.destroyAllWindows()
            
            # 팩토리 정리
            self.factory.cleanup()
            
            # 실행 시간 계산
            if self.system_start_time > 0:
                total_time = time.time() - self.system_start_time
                self.logger.info(f"총 실행 시간: {total_time:.1f}초")
                self.logger.info(f"처리된 프레임: {self.frame_count}")
                if total_time > 0:
                    self.logger.info(f"평균 FPS: {self.frame_count/total_time:.1f}")
            
            self.logger.info("✅ 시스템 정지 완료")
            
        except Exception as e:
            self.logger.error(f"시스템 정지 중 오류: {e}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """시스템 상태 진단"""
        try:
            validation_results = self.factory.validate_system()
            
            health_info = {
                'system_healthy': validation_results.get('system_healthy', False),
                'components_status': validation_results,
                'uptime': time.time() - self.system_start_time if self.system_start_time > 0 else 0,
                'frame_count': self.frame_count,
                'running': self.running
            }
            
            return health_info
            
        except Exception as e:
            self.logger.error(f"시스템 진단 실패: {e}")
            return {'system_healthy': False, 'error': str(e)}
    
    def __enter__(self):
        """Context manager 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.stop()

def main():
    """메인 함수"""
    try:
        # 사용자 설정 (필요시 수정)
        config = {
            'log_level': 'INFO',
            'headless_mode': False,  # True로 설정하면 GUI 없이 실행
            'enable_display': True,  # False로 설정하면 화면 표시 안함
            'use_stub': False,  # True로 설정하면 실제 하드웨어 없이 테스트
            # 'yolo_model_path': 'custom_model.pt',
            # 'camera_resolution': (1280, 720),
        }
        
        # 명령줄 인수 처리
        if len(sys.argv) > 1:
            if '--headless' in sys.argv:
                config['headless_mode'] = True
                config['enable_display'] = False
                print("🖥️ 헤드리스 모드로 실행합니다.")
            elif '--test' in sys.argv:
                config['use_stub'] = True
                print("🔧 테스트 모드로 실행합니다 (스텁 사용).")
        
        # 시스템 실행
        with AutoCleaningSystem(config) as system:
            system.start()
            
    except Exception as e:
        logging.error(f"시스템 실행 실패: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 