#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPIO UART 통신을 사용하는 YOLOv11s 새똥 탐지 시스템
라즈베리파이 GPIO 핀을 통한 직접 시리얼 통신
"""

try:
    import serial
except ImportError:
    print("pyserial 라이브러리가 설치되지 않았습니다.")
    print("다음 명령어로 설치하세요: pip install pyserial")
    exit(1)

try:
    import cv2
    import numpy as np
    from ultralytics import YOLO
except ImportError:
    print("컴퓨터 비전 라이브러리가 설치되지 않았습니다.")
    print("다음 명령어로 설치하세요:")
    print("pip install ultralytics opencv-python")
    exit(1)

import json
import time
import threading
from datetime import datetime
from enum import Enum

class SystemState(Enum):
    """시스템 상태"""
    NORMAL = "정상 작동"
    WARNING = "알림 후 제한 모드"
    STOPPED = "정지 상태"

class BirdPoopDetector:
    def __init__(self, model_path="yolov11n.pt", confidence=0.5):
        """새똥 탐지기 초기화"""
        print("YOLOv11 모델 로딩 중...")
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.target_coverage = 0.5  # 화면의 50% 커버리지
        print("YOLOv11 모델 로딩 완료!")

    def detect_bird_poop(self, frame):
        """프레임에서 새똥 탐지"""
        results = self.model(frame, conf=self.confidence, verbose=False)
        
        if not results or len(results) == 0:
            return False, 0.0, []
        
        frame_area = frame.shape[0] * frame.shape[1]
        total_detection_area = 0
        detection_boxes = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    box_area = (x2 - x1) * (y2 - y1)
                    total_detection_area += box_area
                    detection_boxes.append((int(x1), int(y1), int(x2), int(y2)))
        
        coverage_ratio = total_detection_area / frame_area
        is_detected = coverage_ratio >= self.target_coverage
        
        return is_detected, coverage_ratio, detection_boxes

class ArduinoGPIOClient:
    def __init__(self, port='/dev/ttyS0', baudrate=115200, timeout=1):
        """
        GPIO UART 통신 아두이노 클라이언트
        
        Args:
            port (str): GPIO UART 포트 (/dev/ttyS0)
            baudrate (int): 통신 속도
            timeout (int): 타임아웃 시간
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.is_connected = False
        
    def connect(self):
        """GPIO UART를 통해 아두이노에 연결"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            self.is_connected = True
            print(f"GPIO UART 연결 성공: {self.port}")
            return True
        except serial.SerialException as e:
            print(f"GPIO UART 연결 실패: {e}")
            print("다음을 확인하세요:")
            print("1. sudo raspi-config에서 UART 활성화")
            print("2. /boot/config.txt에서 enable_uart=1 설정")
            print("3. 하드웨어 연결 상태 (GPIO 14, 15)")
            return False
    
    def disconnect(self):
        """연결 해제"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False
            print("GPIO UART 연결 해제")
    
    def send_command(self, command, **kwargs):
        """GPIO UART를 통해 아두이노에 명령 전송"""
        if not self.is_connected or self.serial_conn is None:
            print("GPIO UART가 연결되지 않았습니다.")
            return None
        
        cmd_data = {"command": command}
        cmd_data.update(kwargs)
        
        try:
            cmd_json = json.dumps(cmd_data) + '\n'
            self.serial_conn.write(cmd_json.encode('utf-8'))
            
            # 응답 대기
            response = self.serial_conn.readline().decode('utf-8').strip()
            if response:
                return json.loads(response)
            return None
            
        except Exception as e:
            print(f"GPIO UART 명령 전송 실패: {e}")
            return None
    
    def get_sensor_data(self):
        """DHT11 센서 데이터 요청"""
        return self.send_command("get_sensor_data")
    
    def move_stepper(self, steps, speed=12):
        """스테핑 모터 이동"""
        return self.send_command("move_stepper", steps=steps, speed=speed)
    
    def stop_stepper(self):
        """스테핑 모터 정지"""
        return self.send_command("stop_stepper")
    
    def disable_stepper(self):
        """스테핑 모터 핀 비활성화 (전력 절약)"""
        return self.send_command("disable_stepper")
    
    def reset_stepper_position(self):
        """스테핑 모터 위치 초기화"""
        return self.send_command("reset_stepper_position")

class GPIOAutoCleaningSystem:
    def __init__(self, camera_id=0):
        """GPIO UART 기반 자동 청소 시스템 초기화"""
        # 시스템 상태 변수
        self.state = SystemState.NORMAL
        self.clean_count = 0
        self.max_clean_count = 10
        self.warning_extra_count = 0
        self.max_warning_extra = 2
        
        # 청소 동작 설정
        self.steps_per_revolution = 2048  # 28BYJ-48 한 바퀴
        self.cleaning_revolutions = 5     # 청소 시 앞으로 5바퀴
        self.cleaning_speed = 12          # RPM
        
        # 온습도 모니터링
        self.last_temp = None
        self.last_humidity = None
        self.sensor_update_interval = 3   # 3초마다 센서 데이터 업데이트
        
        # 카메라 초기화
        print("카메라 초기화 중...")
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            raise RuntimeError("카메라를 열 수 없습니다.")
        print("카메라 초기화 완료!")
        
        # YOLO 탐지기 초기화
        self.detector = BirdPoopDetector()
        
        # GPIO UART 아두이노 연결
        self.arduino = ArduinoGPIOClient(port='/dev/ttyS0')
        
        if not self.arduino.connect():
            print("GPIO UART 연결 실패. USB 시리얼로 대체 시도...")
            # USB 시리얼로 대체
            try:
                import serial.tools.list_ports
                available_ports = list(serial.tools.list_ports.comports())
                if available_ports:
                    usb_port = available_ports[0].device
                    self.arduino = ArduinoGPIOClient(port=usb_port)
                    if not self.arduino.connect():
                        raise RuntimeError("아두이노 연결에 실패했습니다.")
                else:
                    raise RuntimeError("사용 가능한 시리얼 포트가 없습니다.")
            except Exception as e:
                raise RuntimeError(f"아두이노 연결 실패: {e}")
        
        # 초기 설정
        self.arduino.reset_stepper_position()
        self.arduino.disable_stepper()
        
        print("=== GPIO UART 자동 청소 시스템 초기화 완료 ===")
        print(f"상태: {self.state.value}")
        print(f"청소 카운트: {self.clean_count}/{self.max_clean_count}")
        
    def _perform_cleaning(self):
        """청소 동작 수행"""
        print("\n🧹 청소 시작!")
        
        # 앞으로 5바퀴 회전
        total_steps = self.steps_per_revolution * self.cleaning_revolutions
        print(f"앞으로 이동 중... ({self.cleaning_revolutions}바퀴, {total_steps}스텝)")
        
        self.arduino.move_stepper(total_steps, self.cleaning_speed)
        time.sleep(2)  # 동작 완료 대기
        
        # 원위치 복귀
        print("원위치 복귀 중...")
        self.arduino.move_stepper(-total_steps, self.cleaning_speed)
        time.sleep(2)  # 동작 완료 대기
        
        # 전력 절약
        self.arduino.disable_stepper()
        
        print("✅ 청소 완료!")
        
    def _update_sensor_data(self):
        """센서 데이터 업데이트"""
        sensor_data = self.arduino.get_sensor_data()
        if sensor_data:
            temp = sensor_data.get('temperature')
            humidity = sensor_data.get('humidity')
            
            if temp != -999:
                self.last_temp = temp
            if humidity != -999:
                self.last_humidity = humidity
    
    def _print_status(self, coverage_ratio=0.0):
        """현재 상태 출력"""
        current_time = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{current_time}] === 시스템 상태 ===")
        print(f"상태: {self.state.value}")
        print(f"청소 횟수: {self.clean_count}/{self.max_clean_count}")
        
        if self.state == SystemState.WARNING:
            print(f"알림 후 추가 청소: {self.warning_extra_count}/{self.max_warning_extra}")
        
        print(f"새똥 탐지 커버리지: {coverage_ratio:.2%}")
        
        # 온습도 데이터 출력
        if self.last_temp is not None:
            print(f"🌡️  온도: {self.last_temp}°C")
        else:
            print("🌡️  온도: 센서 오류")
            
        if self.last_humidity is not None:
            print(f"💧 습도: {self.last_humidity}%")
        else:
            print("💧 습도: 센서 오류")
    
    def _check_system_state(self):
        """시스템 상태 확인 및 업데이트"""
        if self.state == SystemState.NORMAL:
            if self.clean_count >= self.max_clean_count:
                self.state = SystemState.WARNING
                print("\n🚨 ===== 알림 =====")
                print("쓰레기통을 비워주세요!")
                print("알림 후 2번만 더 작동 가능합니다.")
                print("==================")
                
        elif self.state == SystemState.WARNING:
            if self.warning_extra_count >= self.max_warning_extra:
                self.state = SystemState.STOPPED
                print("\n⛔ ===== 시스템 정지 =====")
                print("쓰레기통을 비워주기 전까지 작동을 중지합니다.")
                print("비워주신 후 'r' 키를 눌러 재시작하세요.")
                print("========================")
    
    def reset_system(self):
        """시스템 리셋 (쓰레기통을 비운 후)"""
        self.state = SystemState.NORMAL
        self.clean_count = 0
        self.warning_extra_count = 0
        print("\n✅ 시스템 리셋 완료!")
        print("정상 작동을 재개합니다.")
    
    def run(self):
        """메인 실행 루프"""
        print("\n🚀 GPIO UART 자동 청소 시스템 시작!")
        print("카메라 창에서 'q' 키로 종료, 'r' 키로 시스템 리셋")
        
        last_sensor_update = 0
        
        try:
            while True:
                # 프레임 읽기
                ret, frame = self.cap.read()
                if not ret:
                    print("카메라 프레임을 읽을 수 없습니다.")
                    break
                
                # 센서 데이터 주기적 업데이트
                current_time = time.time()
                if current_time - last_sensor_update > self.sensor_update_interval:
                    self._update_sensor_data()
                    last_sensor_update = current_time
                
                # 새똥 탐지
                is_detected, coverage_ratio, detection_boxes = self.detector.detect_bird_poop(frame)
                
                # 탐지 결과 시각화
                display_frame = frame.copy()
                for box in detection_boxes:
                    x1, y1, x2, y2 = box
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(display_frame, "Bird Poop", (x1, y1-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # 상태 정보 표시
                status_text = f"State: {self.state.value}"
                cv2.putText(display_frame, status_text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                count_text = f"Clean: {self.clean_count}/{self.max_clean_count}"
                cv2.putText(display_frame, count_text, (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                coverage_text = f"Coverage: {coverage_ratio:.1%}"
                cv2.putText(display_frame, coverage_text, (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # 통신 방식 표시
                comm_text = "GPIO UART Communication"
                cv2.putText(display_frame, comm_text, (10, 120), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                
                # 온습도 정보 표시
                if self.last_temp is not None:
                    temp_text = f"Temp: {self.last_temp}C"
                    cv2.putText(display_frame, temp_text, (10, 150), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                
                if self.last_humidity is not None:
                    humidity_text = f"Humidity: {self.last_humidity}%"
                    cv2.putText(display_frame, humidity_text, (10, 180), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                
                # 프레임 표시
                cv2.imshow('GPIO UART Bird Poop Detection System', display_frame)
                
                # 청소 로직
                if is_detected and self.state != SystemState.STOPPED:
                    self._print_status(coverage_ratio)
                    
                    if self.state == SystemState.NORMAL:
                        self._perform_cleaning()
                        self.clean_count += 1
                        
                    elif self.state == SystemState.WARNING:
                        self._perform_cleaning()
                        self.warning_extra_count += 1
                    
                    self._check_system_state()
                    
                    # 연속 탐지 방지를 위한 대기
                    time.sleep(2)
                
                # 키 입력 처리
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    self.reset_system()
                elif key == ord('s'):
                    self._print_status(coverage_ratio)
                
        except KeyboardInterrupt:
            print("\n프로그램 종료 중...")
            
        finally:
            self.cleanup()
    
    def cleanup(self):
        """리소스 정리"""
        print("시스템 정리 중...")
        
        # 스테핑 모터 정지 및 전력 절약
        if self.arduino.is_connected:
            self.arduino.stop_stepper()
            self.arduino.disable_stepper()
            self.arduino.disconnect()
        
        # 카메라 해제
        if self.cap.isOpened():
            self.cap.release()
        
        cv2.destroyAllWindows()
        print("시스템 정리 완료!")

def main():
    """메인 함수"""
    try:
        print("=== GPIO UART 새똥 탐지 시스템 ===")
        print("라즈베리파이 GPIO를 통한 직접 시리얼 통신")
        
        # 시스템 초기화
        system = GPIOAutoCleaningSystem(camera_id=0)
        
        # 시스템 실행
        system.run()
        
    except Exception as e:
        print(f"시스템 오류: {e}")
        print("다음을 확인하세요:")
        print("1. GPIO UART 설정 (raspi-config)")
        print("2. 하드웨어 연결 상태")
        print("3. 전압 레벨 컨버터 연결")

if __name__ == "__main__":
    main() 