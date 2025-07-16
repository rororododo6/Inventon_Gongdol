#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
라즈베리파이 하드웨어 시리얼 설정 도우미
GPIO 14번(TXD), 15번(RXD) 핀을 사용한 아두이노 통신 설정
"""

import os
import sys
import subprocess
import serial
import time

def check_serial_ports():
    """시리얼 포트 상태 확인"""
    print("🔌 시리얼 포트 상태 확인:")
    print("=" * 50)
    
    ports_to_check = [
        ('/dev/serial0', 'GPIO 하드웨어 시리얼 (권장)'),
        ('/dev/ttyAMA0', 'Mini UART'),
        ('/dev/ttyS0', 'PL011 UART'),
        ('/dev/ttyACM0', 'USB 시리얼 (Arduino)'),
        ('/dev/ttyUSB0', 'USB-시리얼 컨버터')
    ]
    
    found_ports = []
    
    for port, description in ports_to_check:
        if os.path.exists(port):
            try:
                # 심볼릭 링크인 경우 실제 경로 확인
                real_path = os.path.realpath(port)
                print(f"✅ {port} → {real_path}")
                print(f"   {description}")
                found_ports.append(port)
            except Exception as e:
                print(f"⚠️ {port} 확인 중 오류: {e}")
        else:
            print(f"❌ {port} 없음")
    
    return found_ports

def check_user_permissions():
    """사용자 권한 확인"""
    print("\n👤 사용자 권한 확인:")
    print("=" * 50)
    
    try:
        # 현재 사용자의 그룹 확인
        groups = subprocess.run(['groups'], capture_output=True, text=True)
        user_groups = groups.stdout.strip().split()
        
        required_groups = ['dialout', 'tty']
        missing_groups = []
        
        for group in required_groups:
            if group in user_groups:
                print(f"✅ {group} 그룹 권한 있음")
            else:
                print(f"❌ {group} 그룹 권한 없음")
                missing_groups.append(group)
        
        if missing_groups:
            print(f"\n💡 권한 추가 명령:")
            for group in missing_groups:
                print(f"   sudo usermod -a -G {group} $USER")
            print("   재로그인 후 적용됨")
            
        return len(missing_groups) == 0
        
    except Exception as e:
        print(f"❌ 권한 확인 실패: {e}")
        return False

def test_serial_connection(port='/dev/serial0', baudrate=115200):
    """시리얼 연결 테스트"""
    print(f"\n🧪 시리얼 연결 테스트:")
    print("=" * 50)
    print(f"포트: {port}")
    print(f"속도: {baudrate} bps")
    print(f"GPIO: 14(TXD), 15(RXD)")
    
    try:
        # 시리얼 포트 열기
        ser = serial.Serial(port, baudrate, timeout=2)
        print(f"✅ 포트 열기 성공")
        print(f"   - 포트: {ser.port}")
        print(f"   - 속도: {ser.baudrate}")
        print(f"   - 타임아웃: {ser.timeout}초")
        
        # 간단한 통신 테스트
        print(f"📡 통신 테스트 중...")
        test_data = b'{"test": "ping"}\n'
        ser.write(test_data)
        time.sleep(0.5)
        
        if ser.in_waiting > 0:
            response = ser.readline()
            print(f"✅ 응답 수신: {response}")
        else:
            print(f"⚠️ 응답 없음 (아두이노 미연결 또는 프로그램 없음)")
        
        ser.close()
        return True
        
    except serial.SerialException as e:
        print(f"❌ 시리얼 포트 오류: {e}")
        return False
    except PermissionError:
        print(f"❌ 권한 오류: 사용자 그룹 확인 필요")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

def check_raspi_config():
    """라즈베리파이 설정 확인"""
    print(f"\n⚙️ 라즈베리파이 설정 확인:")
    print("=" * 50)
    
    config_items = [
        ('/boot/config.txt', 'enable_uart=1', 'UART 활성화'),
        ('/boot/cmdline.txt', 'console=serial', '시리얼 콘솔')
    ]
    
    issues = []
    
    for file_path, search_term, description in config_items:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                if search_term in content:
                    if 'console=serial' in search_term:
                        print(f"⚠️ {description}: 발견됨 (비활성화 권장)")
                        issues.append(f"시리얼 콘솔 비활성화 필요")
                    else:
                        print(f"✅ {description}: 활성화됨")
                else:
                    if 'enable_uart' in search_term:
                        print(f"❌ {description}: 비활성화됨")
                        issues.append(f"UART 활성화 필요")
                    else:
                        print(f"✅ {description}: 없음 (정상)")
            else:
                print(f"❌ {file_path} 파일 없음")
                
        except Exception as e:
            print(f"❌ {file_path} 확인 실패: {e}")
    
    return issues

def show_setup_guide():
    """설정 가이드 표시"""
    print(f"\n📖 하드웨어 시리얼 설정 가이드:")
    print("=" * 50)
    print("1. 라즈베리파이 설정:")
    print("   sudo raspi-config")
    print("   → 3 Interface Options")
    print("   → P6 Serial")
    print("   → Login shell over serial: No")
    print("   → Serial port hardware: Yes")
    print()
    print("2. 사용자 권한 추가:")
    print("   sudo usermod -a -G dialout $USER")
    print("   sudo usermod -a -G tty $USER")
    print("   logout  # 재로그인 필요")
    print()
    print("3. 아두이노 연결:")
    print("   라즈베리파이 → Arduino")
    print("   GPIO 14 (TXD) → Pin 0 (RX)")
    print("   GPIO 15 (RXD) ← Pin 1 (TX)")
    print("   GPIO 6  (GND) ↔ GND")
    print("   GPIO 4  (5V)  → VIN")
    print()
    print("4. 재부팅:")
    print("   sudo reboot")

def main():
    """메인 함수"""
    print("🍓 라즈베리파이 하드웨어 시리얼 설정 도우미")
    print("=" * 50)
    print("GPIO 14번(TXD), 15번(RXD) 핀을 사용한 아두이노 통신 설정")
    print()
    
    # 1. 시리얼 포트 확인
    found_ports = check_serial_ports()
    
    # 2. 사용자 권한 확인
    permission_ok = check_user_permissions()
    
    # 3. 라즈베리파이 설정 확인
    config_issues = check_raspi_config()
    
    # 4. 시리얼 연결 테스트
    if '/dev/serial0' in found_ports and permission_ok:
        test_serial_connection()
    elif '/dev/serial0' not in found_ports:
        print(f"\n⚠️ /dev/serial0 포트가 없습니다.")
        print("   라즈베리파이 설정에서 시리얼 포트를 활성화하세요.")
    elif not permission_ok:
        print(f"\n⚠️ 사용자 권한이 부족합니다.")
        print("   dialout, tty 그룹에 사용자를 추가하세요.")
    
    # 5. 종합 결과
    print(f"\n📋 종합 결과:")
    print("=" * 50)
    
    if found_ports and permission_ok and not config_issues:
        print("✅ 하드웨어 시리얼 설정 완료!")
        print("   아두이노를 연결하고 테스트하세요.")
    else:
        print("⚠️ 설정이 필요합니다:")
        if not found_ports:
            print("   - 시리얼 포트 활성화")
        if not permission_ok:
            print("   - 사용자 권한 추가")
        if config_issues:
            for issue in config_issues:
                print(f"   - {issue}")
        print()
        show_setup_guide()

if __name__ == "__main__":
    main() 