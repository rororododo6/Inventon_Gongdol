#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PI 카메라와 아두이노 360도 서보모터를 이용한 새똥 탐지 자동 청소 시스템
"""

import json
import serial
import time
import threading
import cv2
import numpy as np
from datetime import datetime
from enum import Enum
from picamera2 import Picamera2
from ultralytics import YOLO
import serial.tools.list_ports
from pathlib import Path
import sys
import os
import queue
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 (비활성화)
os.environ['DISPLAY'] = ':0'

# ====== 시스템 상태 ======
class SystemState(Enum):
    """시스템 상태"""
    NORMAL = "정상 작동"
    WARNING = "알림 후 제한 모드"
    STOPPED = "정지 상태"

# ====== 새똥 탐지 시스템 ======
class BirdPoopDetector:
    def __init__(self, model_path="../AI/detect/train63/weights/best.pt", confidence=0.3):
        """
        새똥 탐지 시스템 초기화
        
        Args:
            model_path: YOLO 모델 경로
            confidence: 탐지 신뢰도 임계값
        """
        self.model_path = model_path
        self.confidence = confidence
        self.model = YOLO(model_path)
        
        # 새똥 탐지 영역 누적 저장
        self.accumulated_areas = []  # 누적된 새똥 영역 저장
        self.frame_dimensions = None  # 프레임 크기 저장
        
        print(f"커스텀 새똥 탐지 모델 로딩 완료!")
        print(f"모델 경로: {model_path}")
        print(f"신뢰도: {confidence}")
    
    def _calculate_iou(self, box1, box2):
        """
        두 박스의 IoU(Intersection over Union) 계산
        
        Args:
            box1: (x1, y1, x2, y2) 
            box2: (x1, y1, x2, y2)
            
        Returns:
            float: IoU 값
        """
        x1_inter = max(box1[0], box2[0])
        y1_inter = max(box1[1], box2[1])
        x2_inter = min(box1[2], box2[2])
        y2_inter = min(box1[3], box2[3])
        
        if x1_inter >= x2_inter or y1_inter >= y2_inter:
            return 0.0
        
        inter_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)
        
        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
        
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0
    
    def _should_merge_areas(self, new_box, existing_box, threshold=0.1):
        """
        새로운 박스와 기존 박스를 병합할지 결정
        
        Args:
            new_box: 새로운 박스
            existing_box: 기존 박스
            threshold: IoU 임계값
            
        Returns:
            bool: 병합 여부
        """
        return self._calculate_iou(new_box, existing_box) > threshold
    
    def _merge_overlapping_areas(self, new_areas):
        """
        새로운 영역들을 기존 누적 영역과 병합
        
        Args:
            new_areas: 새로 탐지된 영역들 [(x1, y1, x2, y2), ...]
        """
        for new_area in new_areas:
            merged = False
            
            # 기존 영역들과 겹치는지 확인
            for i, existing_area in enumerate(self.accumulated_areas):
                if self._should_merge_areas(new_area, existing_area):
                    # 병합: 두 영역을 포함하는 최소 박스 생성
                    merged_box = (
                        min(new_area[0], existing_area[0]),  # x1
                        min(new_area[1], existing_area[1]),  # y1
                        max(new_area[2], existing_area[2]),  # x2
                        max(new_area[3], existing_area[3])   # y2
                    )
                    self.accumulated_areas[i] = merged_box
                    merged = True
                    break
            
            # 겹치는 영역이 없으면 새로 추가
            if not merged:
                self.accumulated_areas.append(new_area)
    
    def _calculate_total_coverage(self):
        """
        누적된 새똥 영역들의 총 커버리지 계산
        
        Returns:
            float: 커버리지 비율 (%)
        """
        if not self.accumulated_areas or not self.frame_dimensions:
            return 0.0
        
        total_area = 0
        frame_area = self.frame_dimensions[0] * self.frame_dimensions[1]
        
        for area in self.accumulated_areas:
            box_area = (area[2] - area[0]) * (area[3] - area[1])
            total_area += box_area
        
        return (total_area / frame_area) * 100 if frame_area > 0 else 0.0
    
    def detect_bird_poop(self, frame):
        """
        새똥 탐지 수행 (누적 방식)
        
        Args:
            frame: 입력 프레임
            
        Returns:
            tuple: (탐지 결과, 탐지 개수, 누적 영역 비율)
        """
        # 프레임 크기 저장
        self.frame_dimensions = (frame.shape[1], frame.shape[0])  # (width, height)
        
        results = self.model(frame, conf=self.confidence)
        
        detection_count = 0
        new_areas = []
        
        for result in results:
            if result.boxes is not None:
                detection_count = len(result.boxes)
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    new_areas.append((x1, y1, x2, y2))
        
        # 새로운 영역들을 누적 영역과 병합
        if new_areas:
            self._merge_overlapping_areas(new_areas)
        
        # 누적 커버리지 계산
        accumulated_coverage = self._calculate_total_coverage()
        
        return results, detection_count, accumulated_coverage
    
    def reset_accumulated_areas(self):
        """
        누적된 새똥 영역 초기화 (청소 후 호출)
        """
        self.accumulated_areas = []
        print("🧹 누적 새똥 영역 초기화 완료")
    
    def get_accumulated_info(self):
        """
        누적된 영역 정보 반환
        
        Returns:
            dict: 누적 영역 정보
        """
        return {
            'total_areas': len(self.accumulated_areas),
            'coverage_ratio': self._calculate_total_coverage(),
            'areas': self.accumulated_areas
        }

# ====== 아두이노 통신 ======
class ArduinoClient:
    def __init__(self, port='/dev/serial0', baudrate=115200, timeout=1):
        """
        아두이노 클라이언트 초기화
        
        Args:
            port: 시리얼 포트 (라즈베리파이 GPIO 14, 15번 하드웨어 UART)
            baudrate: 통신 속도
            timeout: 타임아웃 시간
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.is_connected = False
        
    def connect(self):
        """아두이노에 연결"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            self.is_connected = True
            print(f"아두이노 연결 성공: {self.port}")
            return True
        except serial.SerialException as e:
            print(f"아두이노 연결 실패 {self.port}: {e}")
            return False
    
    def disconnect(self):
        """연결 해제"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False
            print("아두이노 연결 해제")
    
    def send_command(self, command, **kwargs):
        """
        아두이노에 명령 전송
        
        Args:
            command: 명령 타입
            **kwargs: 추가 매개변수
        """
        if not self.is_connected:
            print("아두이노가 연결되지 않았습니다.")
            return None
        
        cmd_data = {"command": command}
        cmd_data.update(kwargs)
        
        try:
            cmd_json = json.dumps(cmd_data) + '\n'
            self.serial_conn.write(cmd_json.encode('utf-8'))
            time.sleep(0.1)
            
            if self.serial_conn.in_waiting:
                response = self.serial_conn.readline().decode('utf-8').strip()
                if response:
                    return json.loads(response)
            return None
        except Exception as e:
            print(f"명령 전송 실패: {e}")
            return None
    
    def get_sensor_data(self):
        """DHT11 센서 데이터 요청"""
        return self.send_command("get_sensor_data")
    
    def control_servo(self, direction):
        """
        360도 서보모터 제어
        
        Args:
            direction: 0(정지), 1(앞으로), -1(뒤로)
        """
        return self.send_command("control_servo", direction=direction)
    
    def stop_servo(self):
        """360도 서보모터 정지"""
        return self.send_command("stop_servo")
    
    # === 새장 화장실 청소 시스템 기능들 ===
    
    def perform_cage_cleaning(self):
        """새장 화장실 청소 수행 (앞으로 3초, 뒤로 3초)"""
        return self.send_command("cage_cleaning")
    
    def reset_emergency_stop(self):
        """긴급 정지 해제"""
        return self.send_command("reset_emergency_stop")
    
    def reset_cleaning_cycles(self):
        """청소 횟수 초기화"""
        return self.send_command("reset_cleaning_cycles")
    
    def system_test(self):
        """시스템 테스트 (LED 깜빡임 + 부저 소리)"""
        return self.send_command("system_test")
    
    def get_system_status(self):
        """상세한 시스템 상태 정보 요청"""
        return self.send_command("get_status")
    
    def check_trash_empty_button(self):
        """쓰레기통 비우기 버튼 상태 확인"""
        return self.send_command("trash_empty_button")

class PiCameraAutoCleaningSystem:
    def __init__(self, resolution=(640, 480), framerate=30, model_path="../AI/detect/train63/weights/best.pt", confidence=0.3):
        """
        PI 카메라 자동 청소 시스템 초기화
        
        Args:
            resolution: 카메라 해상도
            framerate: 프레임레이트
            model_path: YOLO 모델 경로
            confidence: 탐지 신뢰도
        """
        # 시스템 상태 변수
        self.state = SystemState.NORMAL
        self.clean_count = 0
        self.max_clean_count = 10
        self.warning_extra_count = 0
        self.max_warning_extra = 2
        
        # 360도 서보모터 청소 설정
        self.cleaning_duration = 3  # 청소 시간 (3초)
        
        # 쓰레기통 상태 관리
        self.trash_full = False  # 쓰레기통 가득 참 상태
        self.total_cleanings = 0  # 총 청소 횟수 (10번마다 쓰레기통 비우기 필요)
        
        # 온습도 모니터링
        self.last_temp = None
        self.last_humidity = None
        self.sensor_update_interval = 3   # 3초마다 센서 데이터 업데이트
        
        # PI 카메라 초기화
        print("PI 카메라 초기화 중...")
        try:
            self.picam2 = Picamera2()
            
            # 카메라 설정
            camera_config = self.picam2.create_still_configuration(
                main={"size": resolution, "format": "RGB888"}
            )
            self.picam2.configure(camera_config)
            
            # 카메라 시작
            self.picam2.start()
            
            # 카메라 워밍업
            time.sleep(2)
            
            print(f"PI 카메라 초기화 완료! 해상도: {resolution}, FPS: {framerate}")
        except Exception as e:
            raise RuntimeError(f"PI 카메라 초기화 실패: {e}")
        
        # YOLO 탐지기 초기화
        self.detector = BirdPoopDetector(model_path=model_path, confidence=confidence)
        
        # 아두이노 연결 (GPIO UART 우선, USB 시리얼 백업)
        self.arduino = self._connect_arduino()
        
        # 초기 설정
        self.arduino.stop_servo()
        
        print("=== PI 카메라 자동 청소 시스템 초기화 완료 ===")
        print(f"상태: {self.state.value}")
        print(f"청소 카운트: {self.clean_count}/{self.max_clean_count}")
        
    def _connect_arduino(self):
        """아두이노 연결 (GPIO UART 우선, USB 백업)"""
        # 1. GPIO UART 시도
        print("GPIO UART 연결 시도...")
        arduino = ArduinoClient(port='/dev/serial0')
        if arduino.connect():
            return arduino
        
        # 2. USB 시리얼 백업
        print("USB 시리얼 연결 시도...")
        available_ports = list(serial.tools.list_ports.comports())
        if available_ports:
            usb_port = available_ports[0].device
            arduino = ArduinoClient(port=usb_port)
            if arduino.connect():
                return arduino
        
        raise RuntimeError("아두이노 연결에 실패했습니다.")
    
    def _perform_cleaning(self):
        """청소 동작 수행 (앞으로 3초, 뒤로 3초)"""
        print("\n🧹 청소 시작!")
        
        # 앞으로 3초 회전
        print("앞으로 회전 시작...")
        self.arduino.control_servo(1)  # 앞으로
        time.sleep(self.cleaning_duration)
        
        # 뒤로 3초 회전
        print("뒤로 회전 시작...")
        self.arduino.control_servo(-1)  # 뒤로
        time.sleep(self.cleaning_duration)
        
        # 정지
        print("서보모터 정지...")
        self.arduino.stop_servo()
        
        # 총 청소 횟수 증가
        self.total_cleanings += 1
        
        # 10번 청소 후 쓰레기통 가득 참 상태로 설정
        if self.total_cleanings >= 10:
            self.trash_full = True
            print("🗑️ 쓰레기통을 비워주세요! 10번 청소 완료")
        
        print("🧹 청소 완료!")
    
    def _update_sensor_data(self):
        """센서 데이터 업데이트"""
        try:
            sensor_data = self.arduino.get_sensor_data()
            if sensor_data:
                self.last_temp = sensor_data.get('temp', '센서 오류')
                self.last_humidity = sensor_data.get('hum', '센서 오류')
                
                # 쓰레기통 상태 확인
                trash_full = sensor_data.get('trash_full', False)
                trash_empty_btn = sensor_data.get('trash_empty_btn', False)
                
                # 쓰레기통 비우기 버튼이 눌렸으면 상태 초기화
                if trash_empty_btn:
                    self.trash_full = False
                    self.total_cleanings = 0
                    print("✅ 쓰레기통 비우기 완료! 청소 카운트 초기화")
                    
        except Exception as e:
            print(f"센서 데이터 업데이트 실패: {e}")
    
    def _print_status(self, coverage_ratio=0.0):
        """상태 정보 출력"""
        now = datetime.now()
        print(f"\n[{now.strftime('%H:%M:%S')}] === 시스템 상태 ===")
        print(f"상태: {self.state.value}")
        print(f"청소 횟수: {self.clean_count}/{self.max_clean_count}")
        print(f"총 청소 횟수: {self.total_cleanings}")
        
        # 쓰레기통 상태 표시
        if self.trash_full:
            print("🗑️ 쓰레기통 가득 참! 비우기 버튼을 눌러주세요.")
        elif self.total_cleanings >= 8:
            print(f"⚠️ 쓰레기통 비우기까지 {10 - self.total_cleanings}번 남음")
        
        # 10번째 청소 달성 상태 표시
        total_cleaning_count = self.clean_count + self.warning_extra_count
        if total_cleaning_count >= 10:
            print("🏆 10번째 청소 달성 완료!")
        elif total_cleaning_count >= 8:
            print(f"🎯 10번째 청소까지 {10 - total_cleaning_count}번 남음")
        
        # 누적 영역 정보 출력
        accumulated_info = self.detector.get_accumulated_info()
        print(f"누적 새똥 영역: {accumulated_info['total_areas']}개")
        print(f"누적 커버리지: {coverage_ratio:.2f}% (임계값: 50%)")
        
        if coverage_ratio >= 50.0:
            print("🚨 청소 필요! 누적 커버리지가 50%를 초과했습니다.")
        elif coverage_ratio >= 30.0:
            print("⚠️ 주의: 누적 커버리지가 30%를 초과했습니다.")
        elif coverage_ratio >= 10.0:
            print("📊 누적 커버리지가 10%를 초과했습니다.")
        
        # 온습도 정보
        temp_str = f"{self.last_temp}°C" if self.last_temp != '센서 오류' and self.last_temp is not None else "센서 오류"
        humidity_str = f"{self.last_humidity}%" if self.last_humidity != '센서 오류' and self.last_humidity is not None else "센서 오류"
        print(f"🌡️  온도: {temp_str}")
        print(f"💧 습도: {humidity_str}")
        
        # 경고 상태 정보
        if self.state == SystemState.WARNING:
            print(f"⚠️  경고 상태: 추가 청소 {self.warning_extra_count}/{self.max_warning_extra}")
        elif self.state == SystemState.STOPPED:
            print("🛑 시스템 정지: 최대 청소 횟수 도달")
    
    def _check_system_state(self):
        """시스템 상태 확인 및 업데이트"""
        # 최대 청소 횟수 체크
        if self.clean_count >= self.max_clean_count:
            if self.state == SystemState.NORMAL:
                self.state = SystemState.WARNING
                print(f"⚠️  경고: 최대 청소 횟수 도달! 추가 {self.max_warning_extra}회만 더 가능합니다.")
            elif self.state == SystemState.WARNING:
                if self.warning_extra_count >= self.max_warning_extra:
                    self.state = SystemState.STOPPED
                    print("🛑 시스템 정지: 최대 청소 횟수 초과!")
                    return False
        
        return True
    
    def reset_system(self):
        """시스템 상태 초기화"""
        self.state = SystemState.NORMAL
        self.clean_count = 0
        self.warning_extra_count = 0
        
        # 누적 새똥 영역 초기화
        self.detector.reset_accumulated_areas()
        
        # 쓰레기통 상태 초기화
        self.trash_full = False
        self.total_cleanings = 0
        
        self.arduino.reset_cleaning_cycles()
        print("🔄 시스템 상태가 초기화되었습니다.")
    
    def run(self):
        """메인 실행 루프"""
        print("\n🚀 자동 청소 시스템 시작! (헤드리스 모드)")
        print("Ctrl+C로 종료, 10초마다 상태 출력")
        
        last_sensor_update = time.time()
        last_status_print = time.time()
        
        try:
            while True:
                # 시스템 상태 체크
                if not self._check_system_state():
                    print("시스템이 정지되었습니다.")
                    break
                
                # 프레임 캡처
                frame = self.picam2.capture_array()
                
                # 새똥 탐지
                results, detection_count, coverage_ratio = self.detector.detect_bird_poop(frame)
                
                # 탐지 결과 처리
                if detection_count > 0:
                    # 시각화 (헤드리스 모드에서는 표시하지 않음)
                    annotated_frame = results[0].plot()
                
                # 청소 필요 여부 결정 (누적 커버리지 50% 이상)
                if coverage_ratio >= 50.0:
                    # 쓰레기통이 가득 찬 경우 청소 거부
                    if self.trash_full:
                        print("🗑️ 쓰레기통을 비워주세요! 청소를 계속하려면 비우기 버튼을 눌러주세요.")
                    elif self.state == SystemState.NORMAL:
                        self._perform_cleaning()
                        self.clean_count += 1
                        # 청소 후 누적 영역 초기화
                        self.detector.reset_accumulated_areas()
                        # 10번째 청소 시 특별 메시지 출력
                        if self.clean_count == 10:
                            print("\n🎉 축하합니다! 10번째 청소를 완료했습니다!")
                            print("🏆 시스템이 안정적으로 10회 청소를 성공적으로 수행했습니다.")
                            print("🔧 청소 성능이 최적화되었습니다.")
                    elif self.state == SystemState.WARNING:
                        self._perform_cleaning()
                        self.warning_extra_count += 1
                        # 청소 후 누적 영역 초기화
                        self.detector.reset_accumulated_areas()
                        # WARNING 상태에서도 총 청소 횟수에 포함
                        total_cleaning_count = self.clean_count + self.warning_extra_count
                        if total_cleaning_count == 10:
                            print("\n🎉 축하합니다! 총 10번째 청소를 완료했습니다!")
                            print("🏆 시스템이 경고 상태에서도 안정적으로 청소를 수행했습니다.")
                            print("🔧 청소 성능이 최적화되었습니다.")
                    elif self.state == SystemState.STOPPED:
                        print("🛑 시스템 정지 상태: 청소 불가")
                
                # 센서 데이터 업데이트 (3초마다)
                if time.time() - last_sensor_update > self.sensor_update_interval:
                    self._update_sensor_data()
                    last_sensor_update = time.time()
                
                # 상태 출력 (10초마다)
                if time.time() - last_status_print > 10:
                    self._print_status(coverage_ratio)
                    last_status_print = time.time()
                
                # 짧은 대기 (CPU 사용량 조절)
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n프로그램 종료 중...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """리소스 정리"""
        print("시스템 정리 중...")
        
        try:
            # 서보모터 정지
            self.arduino.stop_servo()
            
            # 카메라 정리
            if hasattr(self, 'picam2'):
                self.picam2.stop()
                self.picam2.close()
            
            # 아두이노 연결 해제
            self.arduino.disconnect()
            
        except Exception as e:
            print(f"정리 중 오류: {e}")
        
        print("시스템 정리 완료")

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PI 카메라 새똥 탐지 자동 청소 시스템')
    parser.add_argument('--model', type=str, default='../AI/detect/train63/weights/best.pt', 
                        help='YOLO 모델 경로')
    parser.add_argument('--confidence', type=float, default=0.3, 
                        help='탐지 신뢰도 (0.0-1.0)')
    parser.add_argument('--resolution', type=str, default='640x480', 
                        help='카메라 해상도 (예: 640x480)')
    
    args = parser.parse_args()
    
    # 해상도 파싱
    try:
        width, height = map(int, args.resolution.split('x'))
        resolution = (width, height)
    except ValueError:
        print("잘못된 해상도 형식입니다. 예: 640x480")
        return
    
    # 모델 파일 존재 확인
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"모델 파일을 찾을 수 없습니다: {model_path}")
        return
    
    print("=== PI 카메라 새똥 탐지 시스템 ===")
    print("라즈베리파이 카메라 모듈 + 커스텀 새똥 특화 모델 + 자동 청소")
    print(f"🎯 모델: {args.model}")
    print(f"📊 신뢰도: {args.confidence}")
    print(f"📺 해상도: {resolution}")
    print("🔄 누적 탐지 방식: 새똥 영역을 누적 저장하여 50% 초과 시 청소")
    print("🧹 청소 후 누적 영역 초기화")
    print("🎯 10번째 청소 달성 시 축하 메시지 출력")
    print("🗑️ 10번 청소 후 쓰레기통 비우기 필요 (아두이노 버튼으로 완료 확인)")
    
    try:
        # 시스템 초기화 및 실행
        system = PiCameraAutoCleaningSystem(
            resolution=resolution,
            model_path=args.model,
            confidence=args.confidence
        )
        system.run()
        
    except Exception as e:
        print(f"시스템 오류: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())