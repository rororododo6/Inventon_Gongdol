#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
라즈베리파이에서 아두이노와 시리얼 통신하는 클라이언트
DHT22 센서 데이터 수신 및 DC모터 제어 기능 포함
"""

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("pyserial 라이브러리가 설치되지 않았습니다.")
    print("다음 명령어로 설치하세요: pip install pyserial")
    exit(1)

import json
import time
import threading
from datetime import datetime

class ArduinoClient:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200, timeout=1):
        """
        아두이노 클라이언트 초기화
        
        Args:
            port (str): 시리얼 포트 (라즈베리파이에서는 보통 /dev/ttyUSB0 또는 /dev/ttyACM0)
            baudrate (int): 통신 속도
            timeout (int): 타임아웃 시간
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.is_connected = False
        self.data_callback = None
        
    def connect(self):
        """아두이노에 연결"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            self.is_connected = True
            print(f"아두이노에 연결되었습니다. 포트: {self.port}")
            return True
        except serial.SerialException as e:
            print(f"연결 실패: {e}")
            return False
    
    def disconnect(self):
        """연결 해제"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False
            print("연결이 해제되었습니다.")
    
    def send_command(self, command, **kwargs):
        """
        아두이노에 명령 전송
        
        Args:
            command (str): 명령 타입
            **kwargs: 추가 매개변수
        """
        if not self.is_connected or self.serial_conn is None:
            print("연결되지 않았습니다.")
            return None
        
        # JSON 명령 생성
        cmd_data = {"command": command}
        cmd_data.update(kwargs)
        
        try:
            # 명령 전송
            cmd_json = json.dumps(cmd_data) + '\n'
            self.serial_conn.write(cmd_json.encode('utf-8'))
            print(f"명령 전송: {cmd_json.strip()}")
            
            # 응답 대기
            response = self.serial_conn.readline().decode('utf-8').strip()
            if response:
                return json.loads(response)
            return None
            
        except Exception as e:
            print(f"명령 전송 실패: {e}")
            return None
    
    def get_sensor_data(self):
        """DHT22 센서 데이터 요청"""
        return self.send_command("get_sensor_data")
    
    def set_led(self, state):
        """
        LED 상태 설정
        
        Args:
            state (int): 0 (OFF) 또는 1 (ON)
        """
        return self.send_command("set_led", state=state)
    
    def set_motor(self, speed, direction):
        """
        DC모터 제어
        
        Args:
            speed (int): 모터 속도 (0-255)
            direction (int): 방향 (1: 정방향, -1: 역방향, 0: 정지)
        """
        return self.send_command("set_motor", speed=speed, direction=direction)
    
    def stop_motor(self):
        """DC모터 정지"""
        return self.send_command("stop_motor")
    
    def get_status(self):
        """아두이노 상태 정보 요청"""
        return self.send_command("get_status")
    
    def start_data_monitoring(self, callback=None):
        """
        데이터 모니터링 시작
        
        Args:
            callback (function): 데이터 수신 시 호출할 콜백 함수
        """
        self.data_callback = callback
        
        def monitor_thread():
            while self.is_connected and self.serial_conn is not None:
                try:
                    # 타입 체커를 위한 assertion
                    assert self.serial_conn is not None
                    if self.serial_conn.in_waiting:
                        line = self.serial_conn.readline().decode('utf-8').strip()
                        if line:
                            try:
                                data = json.loads(line)
                                if self.data_callback:
                                    self.data_callback(data)
                                else:
                                    self._print_data(data)
                            except json.JSONDecodeError:
                                print(f"잘못된 JSON: {line}")
                except Exception as e:
                    print(f"모니터링 오류: {e}")
                    break
                time.sleep(0.1)
        
        # 모니터링 스레드 시작
        thread = threading.Thread(target=monitor_thread, daemon=True)
        thread.start()
        print("데이터 모니터링이 시작되었습니다.")
    
    def _print_data(self, data):
        """데이터 출력"""
        if data.get("type") == "sensor_data":
            print(f"[{datetime.now().strftime('%H:%M:%S')}] DHT22 센서 데이터:")
            temp = data.get('temperature', 'N/A')
            hum = data.get('humidity', 'N/A')
            if temp != -999:
                print(f"  온도: {temp}°C")
            else:
                print(f"  온도: 센서 오류")
            if hum != -999:
                print(f"  습도: {hum}%")
            else:
                print(f"  습도: 센서 오류")
            print(f"  모터 속도: {data.get('motor_speed', 'N/A')}")
            print(f"  모터 동작: {'실행 중' if data.get('motor_running') else '정지'}")
        elif data.get("type") == "status":
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 상태 정보:")
            print(f"  업타임: {data.get('uptime', 'N/A')}ms")
            print(f"  사용 가능한 메모리: {data.get('free_memory', 'N/A')} bytes")
            print(f"  DHT22 연결: {'연결됨' if data.get('dht22_connected') else '연결 안됨'}")
            print(f"  모터 속도: {data.get('motor_speed', 'N/A')}")
            print(f"  모터 동작: {'실행 중' if data.get('motor_running') else '정지'}")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {data}")

def main():
    """메인 함수 - 사용 예제"""
    # 사용 가능한 시리얼 포트 찾기
    available_ports = list(serial.tools.list_ports.comports())
    
    if not available_ports:
        print("사용 가능한 시리얼 포트가 없습니다.")
        print("아두이노가 연결되어 있는지 확인하세요.")
        return
    
    print("사용 가능한 시리얼 포트:")
    for i, port in enumerate(available_ports):
        print(f"  {i+1}. {port.device} - {port.description}")
    
    # 첫 번째 포트 사용 (또는 사용자가 선택할 수 있음)
    selected_port = available_ports[0].device
    print(f"\n선택된 포트: {selected_port}")
    
    # 아두이노 클라이언트 생성
    client = ArduinoClient(port=selected_port)
    
    try:
        # 연결
        if not client.connect():
            return
        
        # 데이터 모니터링 시작
        client.start_data_monitoring()
        
        # 명령 예제
        print("\n=== 명령 테스트 ===")
        
        # LED 켜기
        print("\n1. LED 켜기")
        client.set_led(1)
        time.sleep(1)
        
        # DHT22 센서 데이터 요청
        print("\n2. DHT22 센서 데이터 요청")
        sensor_data = client.get_sensor_data()
        if sensor_data:
            temp = sensor_data.get('temperature')
            hum = sensor_data.get('humidity')
            if temp != -999:
                print(f"온도: {temp}°C")
            if hum != -999:
                print(f"습도: {hum}%")
        
        # DC모터 정방향 회전 (속도 128)
        print("\n3. DC모터 정방향 회전 (속도 128)")
        client.set_motor(128, 1)
        time.sleep(3)
        
        # DC모터 역방향 회전 (속도 200)
        print("\n4. DC모터 역방향 회전 (속도 200)")
        client.set_motor(200, -1)
        time.sleep(3)
        
        # DC모터 정지
        print("\n5. DC모터 정지")
        client.stop_motor()
        
        # 상태 정보 요청
        print("\n6. 상태 정보 요청")
        status = client.get_status()
        if status:
            print(f"업타임: {status.get('uptime')}ms")
            print(f"DHT22 연결: {'연결됨' if status.get('dht22_connected') else '연결 안됨'}")
        
        # LED 끄기
        print("\n7. LED 끄기")
        client.set_led(0)
        
        # 계속 모니터링
        print("\n10초간 자동 데이터 수신 대기...")
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\n프로그램 종료...")
        # 프로그램 종료 시 모터 정지
        client.stop_motor()
        client.set_led(0)
    finally:
        client.disconnect()

if __name__ == "__main__":
    main() 