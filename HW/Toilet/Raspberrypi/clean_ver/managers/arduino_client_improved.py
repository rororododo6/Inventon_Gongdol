#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개선된 아두이노 클라이언트 - JSON 통신 최적화
ArduinoJson 라이브러리와 호환되는 안정적인 통신
"""

import serial
import json
import time
import logging
from typing import Optional, Dict, Any, Union
from enum import Enum

class CommandType(Enum):
    """아두이노 명령 타입"""
    GET_SENSOR = "sensor"
    MOVE_STEPPER = "stepper"
    CONTROL_SERVO = "servo"
    CAGE_CLEAN = "clean"
    EMERGENCY_STOP = "stop"
    RESET_SYSTEM = "reset"
    GET_STATUS = "status"
    SYSTEM_TEST = "test"

class ArduinoClientImproved:
    """개선된 아두이노 클라이언트"""
    
    # JSON 메시지 최대 길이 (Arduino UNO 메모리 고려)
    MAX_JSON_LENGTH = 128
    
    # 통신 설정
    DEFAULT_TIMEOUT = 2.0
    RETRY_COUNT = 3
    RESPONSE_DELAY = 0.05
    
    def __init__(self, port='/dev/ttyS0', baudrate=115200, timeout=DEFAULT_TIMEOUT):
        """
        개선된 아두이노 클라이언트 초기화
        
        Args:
            port: 시리얼 포트
            baudrate: 통신 속도  
            timeout: 타임아웃
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        self.logger = logging.getLogger(__name__)
        
        # 통신 통계
        self.stats = {
            'sent_commands': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'timeouts': 0
        }
    
    def connect(self) -> bool:
        """아두이노 연결"""
        try:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            
            # 연결 안정화를 위한 대기
            time.sleep(2.0)
            
            # 버퍼 비우기
            self.serial_conn.reset_input_buffer()
            self.serial_conn.reset_output_buffer()
            
            self.is_connected = True
            self.logger.info(f"✅ 아두이노 연결 성공: {self.port}")
            
            # 연결 테스트
            if self._test_connection():
                return True
            else:
                self.disconnect()
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 아두이노 연결 실패: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """연결 해제"""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
            except:
                pass
            finally:
                self.is_connected = False
                self.logger.info("아두이노 연결 해제")
    
    def _test_connection(self) -> bool:
        """연결 테스트"""
        try:
            response = self._send_simple_command("ping")
            return response is not None and response.get("status") == "ok"
        except:
            return False
    
    def _send_simple_command(self, cmd: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        단순화된 명령 전송
        
        Args:
            cmd: 명령어 (짧은 문자열)
            params: 매개변수 (최소화)
        """
        if not self.is_connected:
            self.logger.warning("아두이노가 연결되지 않음")
            return None
        
        # 명령 구성 (최소화된 JSON)
        command = {"c": cmd}  # command -> c (짧게)
        if params:
            # 매개변수도 짧게
            for key, value in params.items():
                if key == "steps":
                    command["s"] = value
                elif key == "speed":
                    command["sp"] = value
                elif key == "direction":
                    command["d"] = value
                elif key == "angle":
                    command["a"] = value
        
        # JSON 길이 검사
        json_str = json.dumps(command)
        if len(json_str) > self.MAX_JSON_LENGTH:
            self.logger.error(f"JSON 너무 길음: {len(json_str)} > {self.MAX_JSON_LENGTH}")
            return None
        
        return self._execute_command(json_str)
    
    def _execute_command(self, json_str: str) -> Optional[Dict]:
        """명령 실행 (재시도 포함)"""
        if not self.serial_conn:
            self.logger.error("시리얼 연결이 없음")
            return None
            
        self.stats['sent_commands'] += 1
        
        for attempt in range(self.RETRY_COUNT):
            try:
                # 버퍼 비우기
                self.serial_conn.reset_input_buffer()
                
                # 명령 전송
                message = json_str + '\n'
                self.serial_conn.write(message.encode('utf-8'))
                self.serial_conn.flush()
                
                self.logger.debug(f"전송: {json_str}")
                
                # 응답 대기
                time.sleep(self.RESPONSE_DELAY)
                
                # 응답 읽기 (타임아웃 포함)
                response_line = self.serial_conn.readline().decode('utf-8').strip()
                
                if response_line:
                    try:
                        response = json.loads(response_line)
                        self.stats['successful_responses'] += 1
                        self.logger.debug(f"응답: {response}")
                        return response
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"JSON 파싱 실패: {response_line} - {e}")
                        self.stats['failed_responses'] += 1
                else:
                    self.logger.warning(f"응답 없음 (시도 {attempt + 1}/{self.RETRY_COUNT})")
                    self.stats['timeouts'] += 1
                
                # 재시도 전 대기
                if attempt < self.RETRY_COUNT - 1:
                    time.sleep(0.1 * (attempt + 1))
                    
            except Exception as e:
                self.logger.error(f"통신 오류 (시도 {attempt + 1}): {e}")
                self.stats['failed_responses'] += 1
        
        return None
    
    # ===== 새장 화장실 청소 시스템 메서드들 =====
    
    def get_sensor_data(self) -> Optional[Dict]:
        """센서 데이터 요청"""
        return self._send_simple_command("sensor")
    
    # 스테핑 모터는 제거됨 - 360도 서보모터만 사용
    
    def control_servo(self, direction: int) -> Optional[Dict]:
        """
        서보 모터 제어
        Args:
            direction: 0=정지, 1=앞으로, -1=뒤로
        """
        return self._send_simple_command("servo", {"direction": direction})
    
    def activate_cleaning_servo(self) -> Optional[Dict]:
        """청소 서보 작동 (앞으로)"""
        return self.control_servo(1)
    
    def stop_servo(self) -> Optional[Dict]:
        """서보 모터 정지"""
        return self.control_servo(0)
    
    def perform_cage_cleaning(self) -> Optional[Dict]:
        """새장 화장실 청소 수행"""
        return self._send_simple_command("clean")
    
    def get_system_status(self) -> Optional[Dict]:
        """시스템 상태 확인"""
        return self._send_simple_command("status")
    
    def reset_emergency_stop(self) -> Optional[Dict]:
        """긴급 정지 해제"""
        return self._send_simple_command("reset")
    
    def reset_cleaning_cycles(self) -> Optional[Dict]:
        """청소 횟수 초기화"""
        return self._send_simple_command("reset_cycles")
    
    def system_test(self) -> Optional[Dict]:
        """시스템 테스트"""
        return self._send_simple_command("test")
    
    def control_led(self, state: bool) -> Optional[Dict]:
        """LED 제어"""
        return self._send_simple_command("led", {"state": state})
    
    def handle_trash_empty(self) -> Optional[Dict]:
        """쓰레기통 비우기 처리 (전류 상태 확인)"""
        return self._send_simple_command("trash")
    
    def check_power_status(self) -> Optional[Dict]:
        """전류 상태 확인 (쓰레기통 시스템)"""
        # 센서 데이터를 통해 전류 상태를 확인
        return self.get_sensor_data()
    
    def ping(self) -> Optional[Dict]:
        """연결 테스트"""
        return self._send_simple_command("ping")
    
    # ===== 유틸리티 메서드들 =====
    
    def get_stats(self) -> Dict[str, Any]:
        """통신 통계 반환"""
        total = self.stats['sent_commands']
        success_rate = (self.stats['successful_responses'] / total * 100) if total > 0 else 0
        
        return {
            **self.stats,
            'success_rate': round(success_rate, 2),
            'connection_status': self.is_connected
        }
    
    def reset_stats(self):
        """통계 초기화"""
        self.stats = {
            'sent_commands': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'timeouts': 0
        }
    
    def __enter__(self):
        """Context manager 진입"""
        if not self.is_connected:
            self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.disconnect()

# ===== 아두이노 코드 예제 =====
"""
Arduino 코드에서 다음과 같이 처리:

#include <ArduinoJson.h>

// JSON 문서 크기 (메모리 절약)
StaticJsonDocument<200> doc;
StaticJsonDocument<100> response;

void setup() {
  Serial.begin(115200);
  // 하드웨어 초기화...
}

void loop() {
  if (Serial.available()) {
    String jsonString = Serial.readStringUntil('\n');
    jsonString.trim();
    
    // JSON 파싱
    DeserializationError error = deserializeJson(doc, jsonString);
    if (error) {
      sendError("JSON 파싱 실패");
      return;
    }
    
    // 명령 처리
    String command = doc["c"];
    if (command == "sensor") {
      handleSensorRequest();
    } else if (command == "stepper") {
      handleStepperCommand();
    } else if (command == "servo") {
      handleServoCommand();
    } else if (command == "clean") {
      handleCleaningCommand();
    } else if (command == "status") {
      handleStatusRequest();
    } else if (command == "ping") {
      sendResponse("ok");
    } else {
      sendError("알 수 없는 명령");
    }
    
    doc.clear();
  }
}

void sendResponse(String status) {
  response.clear();
  response["status"] = status;
  serializeJson(response, Serial);
  Serial.println();
}

void sendError(String message) {
  response.clear();
  response["error"] = message;
  serializeJson(response, Serial);
  Serial.println();
}

void handleSensorRequest() {
  // DHT11 센서 읽기
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  
  response.clear();
  response["temp"] = temp;
  response["hum"] = hum;
  serializeJson(response, Serial);
  Serial.println();
}

void handleStepperCommand() {
  int steps = doc["s"];
  int speed = doc["sp"] | 12; // 기본값 12
  
  // 스테핑 모터 제어
  stepper.setSpeed(speed);
  stepper.step(steps);
  
  sendResponse("done");
}
""" 