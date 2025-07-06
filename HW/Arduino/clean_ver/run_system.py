#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
라즈베리파이 자동 청소 시스템 실행 스크립트
"""

import os
import sys
import argparse
import logging

def setup_python_path():
    """Python 경로 설정"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # 경로 추가
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

def check_dependencies():
    """의존성 검사"""
    missing_deps = []
    
    # 필수 라이브러리 확인
    required_libs = [
        ('cv2', 'opencv-python'),
        ('numpy', 'numpy'),
        ('ultralytics', 'ultralytics'),
        ('picamera2', 'picamera2 (시스템 패키지)'),
        ('serial', 'pyserial')
    ]
    
    for lib_name, package_name in required_libs:
        try:
            __import__(lib_name)
            print(f"✅ {package_name}")
        except ImportError:
            missing_deps.append(package_name)
            print(f"❌ {package_name} - 설치 필요")
    
    if missing_deps:
        print(f"\n❌ 누락된 의존성: {', '.join(missing_deps)}")
        print("📋 설치 가이드:")
        print("1. 시스템 패키지: sudo apt install python3-picamera2 libcamera-apps")
        print("2. Python 패키지: pip install opencv-python numpy ultralytics pyserial")
        return False
    
    return True

def check_hardware():
    """하드웨어 확인"""
    issues = []
    
    # 카메라 확인
    try:
        from picamera2 import Picamera2
        picam2 = Picamera2()
        picam2.start()
        picam2.stop()
        print("✅ 라즈베리파이 카메라")
    except Exception as e:
        issues.append(f"카메라: {e}")
        print(f"❌ 라즈베리파이 카메라 - {e}")
    
    # 시리얼 포트 확인
    serial_ports = ['/dev/ttyS0', '/dev/ttyACM0', '/dev/ttyUSB0']
    found_port = False
    
    for port in serial_ports:
        if os.path.exists(port):
            print(f"✅ 시리얼 포트: {port}")
            found_port = True
            break
    
    if not found_port:
        issues.append("시리얼 포트를 찾을 수 없습니다")
        print("❌ 시리얼 포트 - 아두이노 연결 확인 필요")
    
    # YOLO 모델 확인
    model_paths = ['yolov11s.pt', 'yolov11n.pt', '../yolov11s.pt', '../yolov11n.pt']
    found_model = False
    model_used = None
    
    for model_path in model_paths:
        if os.path.exists(model_path):
            print(f"✅ YOLO 모델: {model_path}")
            found_model = True
            model_used = model_path
            break
    
    if not found_model:
        issues.append("YOLO 모델 파일을 찾을 수 없습니다")
        print("❌ YOLO 모델 - 다운로드 필요")
        print("💡 YOLOv11s 다운로드: wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov11s.pt")
        print("💡 YOLOv11n 다운로드: wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov11n.pt")
    elif model_used and 'yolov11s.pt' in model_used:
        print("🎯 YOLOv11s 모델 사용 중 - 높은 정확도, 중간 성능")
        # 메모리 사용량 경고
        import psutil
        available_memory = psutil.virtual_memory().available / (1024**3)
        if available_memory < 4.0:
            print("⚠️ 경고: YOLOv11s는 4GB 이상 메모리 권장. 현재 사용 가능:", f"{available_memory:.1f}GB")
    elif model_used and 'yolov11n.pt' in model_used:
        print("⚡ YOLOv11n 모델 사용 중 - 빠른 성능, 기본 정확도")
    
    if issues:
        print(f"\n⚠️ 하드웨어 문제: {len(issues)}개")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    return True

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='라즈베리파이 자동 청소 시스템')
    parser.add_argument('--headless', action='store_true', help='헤드리스 모드 (GUI 없음)')
    parser.add_argument('--test', action='store_true', help='테스트 모드 (스텁 사용)')
    parser.add_argument('--check-deps', action='store_true', help='의존성만 확인')
    parser.add_argument('--check-hardware', action='store_true', help='하드웨어만 확인')
    parser.add_argument('--skip-checks', action='store_true', help='검사 생략하고 바로 실행')
    
    args = parser.parse_args()
    
    # Python 경로 설정
    setup_python_path()
    
    print("🍓 라즈베리파이 자동 청소 시스템")
    print("=" * 50)
    
    # 의존성 확인만
    if args.check_deps:
        check_dependencies()
        return
    
    # 하드웨어 확인만
    if args.check_hardware:
        check_hardware()
        return
    
    # 전체 검사 (생략하지 않는 경우)
    if not args.skip_checks:
        print("\n🔍 의존성 검사...")
        if not check_dependencies():
            print("❌ 의존성 문제로 인해 실행할 수 없습니다.")
            return 1
        
        print("\n🔍 하드웨어 검사...")
        if not check_hardware():
            print("⚠️ 하드웨어 문제가 있지만 테스트 모드로 실행 가능합니다.")
            if not args.test:
                response = input("계속 진행하시겠습니까? (y/n): ")
                if response.lower() not in ['y', 'yes']:
                    return 1
    
    # 시스템 실행
    try:
        print("\n🚀 시스템 시작...")
        
        # 설정 구성
        config = {
            'log_level': 'INFO',
            'headless_mode': args.headless,
            'enable_display': not args.headless,
            'use_stub': args.test
        }
        
        # 시스템 임포트 및 실행
        from clean_ver.pi_camera_client_clean import AutoCleaningSystem
        
        with AutoCleaningSystem(config) as system:
            system.start()
            
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단됨")
        return 0
    except Exception as e:
        print(f"\n❌ 시스템 실행 실패: {e}")
        logging.error(f"시스템 실행 실패: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 