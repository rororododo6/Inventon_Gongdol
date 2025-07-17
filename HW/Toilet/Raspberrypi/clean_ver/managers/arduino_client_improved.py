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
from threading import Lock
from dataclasses import dataclass

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

        # 명령 대기열 관리를 위한 락
        self.command_lock = Lock()
    
    def connect(self) -> bool:
        """아두이노 연결"""
        try:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                
            self.logger.info(f"아두이노 연결 시도: {self.port} (속도: {self.baudrate})")
            
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            
            # 연결 안정화를 위한 긴 대기 (아두이노 부트로더 대기)
            time.sleep(3.0)  # 2초 → 3초로 증가
            
            # 버퍼 비우기 (여러 번)
            for i in range(3):
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()
                time.sleep(0.5)
            
            self.is_connected = True
            self.logger.info(f"✅ 아두이노 시리얼 연결 성공: {self.port}")
            
            # 연결 테스트 (더 관대한 기준)
            if self._test_connection():
                self.logger.info(f"✅ 아두이노 통신 테스트 성공!")
                return True
            else:
                self.logger.warning(f"⚠️ 시리얼 연결은 되었지만 통신 테스트 실패")
                # 통신 테스트 실패해도 연결 유지 (아두이노가 준비되지 않았을 수 있음)
                return True  # False → True로 변경
                
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
            self.logger.info("아두이노 연결 테스트 시작...")
            
            # 1차 테스트: ping 명령
            response = self._send_simple_command("ping")
            if response and response.get("status") == "ok":
                self.logger.info("✅ ping 테스트 성공")
                return True
            elif response and "pong" in str(response):
                self.logger.info("✅ pong 응답 받음")
                return True
            
            # 2차 테스트: 센서 데이터 요청
            self.logger.info("ping 실패, 센서 데이터로 재테스트...")
            response = self._send_simple_command("sensor")
            if response and ("temperature" in response or "temp" in response):
                self.logger.info("✅ 센서 데이터 테스트 성공")
                return True
            
            # 3차 테스트: 상태 요청
            self.logger.info("센서 테스트 실패, 상태 요청으로 재테스트...")
            response = self._send_simple_command("status")
            if response and ("ready" in response or "status" in response):
                self.logger.info("✅ 상태 테스트 성공")
                return True
            
            self.logger.warning(f"⚠️ 모든 연결 테스트 실패. 마지막 응답: {response}")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 연결 테스트 중 오류: {e}")
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
        
        # 명령 구성 (아두이노 코드와 완전히 호환되는 형식)
        command = {"c": cmd}  # 아두이노 코드에서 "c" 필드를 찾음
        
        if params:
            # 매개변수 추가 (아두이노 코드와 호환)
            for key, value in params.items():
                if key == "direction":
                    command["d"] = value  # direction -> d
                elif key == "state":
                    command["state"] = value  # LED 상태용
                else:
                    command[key] = value
        
        # JSON 길이 검사 (아두이노 버퍼 크기 고려)
        json_str = json.dumps(command, separators=(',', ':'))  # 공백 제거로 압축
        
        if len(json_str) > 64:  # 아두이노 버퍼 크기 고려해서 더 작게
            self.logger.error(f"JSON 너무 길음: {len(json_str)} > 64")
            return None
        
        self.logger.info(f"📝 압축된 JSON: {json_str} (길이: {len(json_str)})")
        
        return self._execute_command(json_str)
    
    def _execute_command(self, json_str: str) -> Optional[Dict]:
        """명령 실행 (재시도 포함)"""
        if not self.serial_conn:
            self.logger.error("시리얼 연결이 없음")
            return None
        
        # 명령 대기열 관리 - 동시에 여러 명령이 전송되는 것을 방지
        with self.command_lock:
            self.stats['sent_commands'] += 1
            self.logger.info(f"📤 아두이노로 명령 전송: {json_str}")
            
            for attempt in range(self.RETRY_COUNT):
                try:
                    # 버퍼 비우기 (더 철저하게)
                    self.serial_conn.reset_input_buffer()
                    self.serial_conn.reset_output_buffer()
                    time.sleep(0.2)  # 0.1초 → 0.2초로 증가
                    
                    # 명령 전송 (확실한 줄바꿈 추가)
                    message = json_str.strip() + '\n'
                    self.serial_conn.write(message.encode('utf-8'))
                    self.serial_conn.flush()
                    
                    self.logger.debug(f"전송 완료 (시도 {attempt + 1}/{self.RETRY_COUNT}): {repr(message)}")
                    
                    # 응답 대기 (아두이노 처리 시간 고려)
                    time.sleep(0.5)  # 0.2초 → 0.5초로 증가
                    
                    # 응답 읽기 (더 오래 대기)
                    response_lines = []
                    start_time = time.time()
                    
                    while time.time() - start_time < 4.0:  # 2초 → 4초로 증가
                        if self.serial_conn.in_waiting > 0:
                            line = self.serial_conn.readline().decode('utf-8').strip()
                            if line:
                                response_lines.append(line)
                                self.logger.debug(f"받은 라인: {line}")
                                
                                # JSON 형태의 응답이면 즉시 처리
                                if line.startswith('{') and line.endswith('}'):
                                    break
                        else:
                            time.sleep(0.1)
                    
                    # 가장 최근 JSON 응답 찾기
                    json_response = None
                    for line in reversed(response_lines):
                        if line.startswith('{') and line.endswith('}'):
                            json_response = line
                            break
                    
                    if json_response:
                        self.logger.info(f"📥 아두이노 JSON 응답: {json_response}")
                        try:
                            response = json.loads(json_response)
                            self.stats['successful_responses'] += 1
                            self.logger.info(f"✅ JSON 파싱 성공: {response}")
                            return response
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"⚠️ JSON 파싱 실패: {json_response} - {e}")
                            self.stats['failed_responses'] += 1
                    elif response_lines:
                        # JSON이 아닌 응답들 로깅
                        self.logger.info(f"📥 아두이노 텍스트 응답: {response_lines}")
                        # 마지막 응답을 기반으로 성공 여부 판단
                        last_response = response_lines[-1].lower()
                        if any(word in last_response for word in ['completed', 'success', 'ok', 'ready']):
                            return {"status": "ok", "raw_response": response_lines}
                    else:
                        self.logger.warning(f"❌ 응답 없음 (시도 {attempt + 1}/{self.RETRY_COUNT})")
                        self.stats['timeouts'] += 1
                    
                    # 재시도 전 더 긴 대기 (아두이노가 안정화될 시간)
                    if attempt < self.RETRY_COUNT - 1:
                        retry_delay = 1.0 * (attempt + 1)  # 0.5초 → 1초로 증가
                        self.logger.info(f"🔄 재시도 대기: {retry_delay}초 (아두이노 안정화 대기)")
                        time.sleep(retry_delay)
                        
                except Exception as e:
                    self.logger.error(f"❌ 통신 오류 (시도 {attempt + 1}): {e}")
                    self.stats['failed_responses'] += 1
            
            self.logger.error(f"❌ 모든 재시도 실패: {json_str}")
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
    
    # ===== 스테핑 모터 메소드들 (CleaningManager 호환성을 위해 추가) =====
    
    def move_stepper(self, steps: int, speed: int = 12) -> Optional[Dict]:
        """
        스테핑 모터 이동 (서보모터로 대체)
        
        Args:
            steps: 이동할 스텝 수 (양수: 앞으로, 음수: 뒤로)
            speed: 속도 (무시됨, 서보모터는 고정 속도)
        """
        # 스테핑 모터 대신 서보모터 사용
        direction = 1 if steps > 0 else -1
        self.logger.info(f"스테핑 모터 명령을 서보모터로 변환: {steps}스텝 → 방향{direction}")
        
        # 서보모터 제어
        result = self.control_servo(direction)
        
        # 일정 시간 후 정지
        import time
        time.sleep(3.0)  # 3초 동작
        self.stop_servo()
        
        return result
    
    def stop_stepper(self) -> Optional[Dict]:
        """스테핑 모터 정지 (서보모터 정지로 대체)"""
        return self.stop_servo()
    
    def disable_stepper(self) -> Optional[Dict]:
        """스테핑 모터 비활성화 (서보모터 정지로 대체)"""
        return self.stop_servo()
    
    def reset_stepper_position(self) -> Optional[Dict]:
        """스테핑 모터 위치 리셋 (서보모터 정지로 대체)"""
        return self.stop_servo()
    
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
    
    def get_connection_stats(self) -> Dict:
        """연결 통계 정보 반환"""
        total_commands = self.stats['sent_commands']
        success_rate = 0
        if total_commands > 0:
            success_rate = (self.stats['successful_responses'] / total_commands) * 100
        
        return {
            "is_connected": self.is_connected,
            "port": self.port,
            "total_commands": total_commands,
            "successful_responses": self.stats['successful_responses'],
            "failed_responses": self.stats['failed_responses'],
            "timeouts": self.stats['timeouts'],
            "success_rate": round(success_rate, 2)
        }
    
    def diagnose_connection(self) -> Dict:
        """아두이노 연결 진단"""
        self.logger.info("🔍 아두이노 연결 진단 시작...")
        
        if not self.is_connected:
            return {"status": "error", "message": "아두이노가 연결되지 않음"}
        
        # 1. 기본 ping 테스트
        ping_result = self._send_simple_command("ping")
        ping_success = ping_result is not None
        
        # 2. 센서 데이터 테스트
        sensor_result = self._send_simple_command("sensor")
        sensor_success = sensor_result is not None
        
        # 3. 상태 확인 테스트
        status_result = self._send_simple_command("status")
        status_success = status_result is not None
        
        stats = self.get_connection_stats()
        
        diagnosis = {
            "overall_status": "healthy" if (ping_success or sensor_success) else "unhealthy",
            "tests": {
                "ping": ping_success,
                "sensor_data": sensor_success,
                "status_check": status_success
            },
            "connection_stats": stats,
            "recommendations": []
        }
        
        # 권장사항 생성
        if stats["success_rate"] < 70:
            diagnosis["recommendations"].append("통신 성공률이 낮습니다. 아두이노 전원과 케이블을 확인하세요.")
        
        if stats["timeouts"] > 5:
            diagnosis["recommendations"].append("타임아웃이 자주 발생합니다. 아두이노 코드가 무한루프에 빠졌을 수 있습니다.")
        
        if not ping_success and not sensor_success:
            diagnosis["recommendations"].append("모든 테스트 실패. 아두이노를 재시작하세요.")
        
        self.logger.info(f"📊 진단 결과: {diagnosis['overall_status']}")
        return diagnosis
    
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