#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
스마트 앵무새 횟대 제어 시스템 (Raspberry Pi 4B 및 picamera2 최적화)
- 커스텀 YOLO 모델을 이용한 새똥 탐지 및 자동 청소
- 아두이노와 GPIO 시리얼 통신 (GPIO 14, 15)
- 오염도 누적, 청소 횟수 카운트, 쓰레기통 관리, 긴급 정지 기능 포함
"""

import serial
import time
import cv2
import numpy as np
import logging
import argparse
from pathlib import Path
from ultralytics import YOLO
from picamera2 import Picamera2

# ================================================================================
# 로깅 설정
# ================================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SmartPerchSystem")

# ================================================================================
# 아두이노 통신 컨트롤러
# ================================================================================
class ArduinoController:
    """아두이노와 시리얼 통신을 담당하는 클래스"""
    def __init__(self, port='/dev/ttyS0', baudrate=9600):
        """
        Args:
            port (str): 라즈베리파이 4B의 GPIO 14(TX), 15(RX)는 '/dev/ttyS0'에 해당합니다.
                        만약 USB로 연결했다면 '/dev/ttyACM0' 또는 '/dev/ttyUSB0'일 수 있습니다.
            baudrate (int): 아두이노 코드와 동일한 9600으로 설정합니다.
        """
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
            time.sleep(2) # 아두이노 리셋 및 안정화 대기
            logger.info(f"아두이노 연결 성공: {self.port}")
        except serial.SerialException as e:
            logger.error(f"아두이노 연결 실패: {e}")
            logger.error("팁: 'sudo raspi-config' -> 3 Interface Options -> I6 Serial Port에서")
            logger.error("    'login shell over serial'은 No, 'serial port hardware'는 Yes로 설정했는지 확인하세요.")
            raise ConnectionError(f"아두이노에 연결할 수 없습니다. 포트({self.port})와 권한을 확인하세요.")

    def send_command(self, command: bytes):
        if self.ser and self.ser.is_open:
            self.ser.write(command)
            logger.info(f"명령 전송 -> {command!r}")

    def read_response(self) -> str | None:
        if self.ser and self.ser.in_waiting > 0:
            try:
                response = self.ser.readline().decode('utf-8').strip()
                if response:
                    logger.info(f"응답 수신 <- {response}")
                    return response
            except UnicodeDecodeError:
                logger.warning("데이터 수신 중 디코딩 오류 발생")
        return None

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            logger.info("아두이노 연결 해제")

# ================================================================================
# 새똥 탐지 및 오염도 관리
# ================================================================================
class DroppingsDetector:
    """YOLO 모델로 새똥을 탐지하고 오염도를 누적/관리하는 클래스"""
    def __init__(self, model_path: str, confidence_threshold: float = 0.5):
        self.model = YOLO(model_path)
        self.confidence = confidence_threshold
        self.accumulated_boxes = []
        logger.info(f"YOLO 모델 로드 완료: {model_path}")

    def detect(self, frame: np.ndarray, is_headless: bool):
        """프레임에서 새똥을 탐지하고, 새로 탐지된 영역을 누적"""
        results = self.model(frame, conf=self.confidence, verbose=False)
        
        annotated_frame = None
        if not is_headless:
            annotated_frame = results[0].plot()
        
        new_detections = []
        for r in results:
            for box in r.boxes:
                if self.model.names[int(box.cls)] == 'poop':
                    new_detections.append(box.xyxy[0].cpu().numpy().astype(int))
        
        if new_detections:
            self._merge_detections(new_detections)
            
        return annotated_frame

    def _merge_detections(self, new_boxes: list):
        if not self.accumulated_boxes:
            self.accumulated_boxes.extend(new_boxes)
            return

        for new_box in new_boxes:
            merged = False
            for i, acc_box in enumerate(self.accumulated_boxes):
                if self._is_overlapping(new_box, acc_box):
                    x1 = min(new_box[0], acc_box[0])
                    y1 = min(new_box[1], acc_box[1])
                    x2 = max(new_box[2], acc_box[2])
                    y2 = max(new_box[3], acc_box[3])
                    self.accumulated_boxes[i] = [x1, y1, x2, y2]
                    merged = True
                    break
            if not merged:
                self.accumulated_boxes.append(new_box)

    def _is_overlapping(self, box1, box2) -> bool:
        return not (box1[2] < box2[0] or box1[0] > box2[2] or box1[3] < box2[1] or box1[1] > box2[3])

    def get_coverage_ratio(self, frame_shape: tuple) -> float:
        if not self.accumulated_boxes:
            return 0.0
        
        frame_area = frame_shape[0] * frame_shape[1]
        total_droppings_area = sum([(box[2] - box[0]) * (box[3] - box[1]) for box in self.accumulated_boxes])
        
        return total_droppings_area / frame_area

    def draw_accumulated_areas(self, frame: np.ndarray):
        if frame is None: return None
        for box in self.accumulated_boxes:
            x1, y1, x2, y2 = map(int, box)
            sub_img = frame[y1:y2, x1:x2]
            red_rect = np.ones(sub_img.shape, dtype=np.uint8) * 255
            red_rect[:,:,0] = 0
            red_rect[:,:,1] = 0
            res = cv2.addWeighted(sub_img, 0.5, red_rect, 0.5, 1.0)
            frame[y1:y2, x1:x2] = res
        return frame

    def reset(self):
        self.accumulated_boxes = []
        logger.info("누적 오염 영역이 초기화되었습니다.")

# ================================================================================
# 메인 시스템
# ================================================================================
class SmartPerchSystem:
    """스마트 앵무새 횟대 시스템의 메인 클래스"""
    def __init__(self, model_path: str, confidence: float, resolution: tuple, is_headless: bool):
        self.arduino = ArduinoController()
        self.detector = DroppingsDetector(model_path, confidence)
        
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(main={"size": resolution})
        self.picam2.configure(config)
        self.picam2.start()
        time.sleep(2.0)
        logger.info(f"picamera2 초기화 및 해상도 설정 완료: {resolution[0]}x{resolution[1]}")

        self.cleaning_count = 0
        self.is_trash_full = False
        self.is_emergency_stopped = False
        self.last_sensor_read_time = time.time()
        self.is_headless = is_headless

    def run(self):
        """시스템 메인 루프 실행"""
        try:
            while True:
                self.handle_arduino_response()
                
                if self.is_emergency_stopped:
                    logger.warning("시스템이 긴급 정지 상태입니다. 해제될 때까지 대기합니다.")
                    time.sleep(1)
                    continue

                frame = self.picam2.capture_array()
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                annotated_frame = self.detector.detect(frame, self.is_headless)
                
                coverage = self.detector.get_coverage_ratio(frame.shape)
                
                if coverage > 0.30:
                    if self.is_trash_full:
                        logger.warning("청소 필요! 하지만 쓰레기통이 가득 찼습니다. 비워주세요!")
                    else:
                        self.perform_cleaning()
                
                if time.time() - self.last_sensor_read_time > 5:
                    self.arduino.send_command(b'6')
                    self.last_sensor_read_time = time.time()
                
                if not self.is_headless:
                    self.display_status(annotated_frame, coverage)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                else:
                    logger.info(f"상태: 정상, 오염도: {coverage:.2%}, 청소횟수: {self.cleaning_count}")
                    time.sleep(1)

        except KeyboardInterrupt:
            logger.info("사용자에 의해 시스템이 중단되었습니다. (Ctrl+C)")
        finally:
            self.cleanup()

    def perform_cleaning(self):
        """청소 시퀀스 실행"""
        logger.info("오염도 30% 초과! 청소 시퀀스를 시작합니다.")
        self.arduino.send_command(b'4')
        
        self.cleaning_count += 1
        logger.info(f"청소 완료. (누적 청소 횟수: {self.cleaning_count}회)")
        
        if self.cleaning_count >= 10:
            self.is_trash_full = True
            logger.warning("쓰레기통을 비워주세요! (10회 청소 완료)")

        self.detector.reset()
        time.sleep(7)

    def handle_arduino_response(self):
        """아두이노 응답 처리"""
        response = self.arduino.read_response()
        if not response:
            return
            
        if "Cleaning cycles reset" in response:
            self.cleaning_count = 0
            self.is_trash_full = False
            logger.info("쓰레기통 비우기 감지! 청소 횟수를 0으로 초기화합니다.")
        
        elif "Emergency stop released" in response:
            self.is_emergency_stopped = False
            logger.info("긴급 정지 상태가 해제되었습니다.")
            
        elif "Emergency stop activated" in response:
            self.is_emergency_stopped = True
            logger.critical("긴급 정지 신호 수신!")

    def display_status(self, frame, coverage):
        """화면에 현재 상태 정보 표시"""
        if frame is None: return

        frame = self.detector.draw_accumulated_areas(frame)
        
        info_y = 30
        def put_text(text, color=(0, 255, 0)):
            nonlocal info_y
            cv2.putText(frame, text, (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            info_y += 25

        put_text(f"Coverage: {coverage:.2%}")
        put_text(f"Cleaning Count: {self.cleaning_count}")

        if self.is_emergency_stopped:
            put_text("STATE: EMERGENCY STOP", (0, 0, 255))
        elif self.is_trash_full:
            put_text("STATE: TRASH FULL", (0, 255, 255))
        else:
            put_text("STATE: NORMAL", (0, 255, 0))

        cv2.imshow("Smart Parrot Perch System", frame)

    def cleanup(self):
        """시스템 종료 시 리소스 정리"""
        logger.info("시스템을 종료합니다.")
        self.arduino.close()
        self.picam2.stop()
        if not self.is_headless:
            cv2.destroyAllWindows()

# ================================================================================
# 스크립트 실행
# ================================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="스마트 앵무새 횟대 시스템")
    parser.add_argument("--model", type=str, default="yolov11s.pt", help="커스텀 학습된 YOLO 모델 파일 경로")
    parser.add_argument("--confidence", type=float, default=0.4, help="탐지 신뢰도 임계값")
    parser.add_argument("--resolution", type=str, default="640x480", help="카메라 해상도 (예: 640x480)")
    parser.add_argument("--headless", action="store_true", help="GUI 없이 헤드리스 모드로 실행합니다.")
    args = parser.parse_args()

    if not Path(args.model).exists():
        logger.error(f"모델 파일을 찾을 수 없습니다: {args.model}")
        exit(1)

    try:
        width, height = map(int, args.resolution.split('x'))
        resolution_tuple = (width, height)
    except ValueError:
        logger.error("해상도 형식이 잘못되었습니다. '너비x높이' 형식으로 입력하세요.")
        exit(1)
    
    try:
        system = SmartPerchSystem(args.model, args.confidence, resolution_tuple, args.headless)
        system.run()
    except Exception as e:
        logger.critical(f"시스템 실행 중 심각한 오류 발생: {e}")
