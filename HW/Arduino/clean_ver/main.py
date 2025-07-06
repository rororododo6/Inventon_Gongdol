#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
라즈베리파이 새똥 탐지 시스템 메인 런처 (클린코딩 버전)
"""

import sys
import os
import subprocess
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def display_menu():
    """메뉴 표시"""
    print("\n" + "="*60)
    print("🎯 PI 카메라 자동 청소 시스템 (YOLOv11s)")
    print("="*60)
    print("1. 클린코딩 버전 실행 (권장) ⭐")
    print("2. 클린코딩 버전 (헤드리스 모드)")
    print("3. 클린코딩 버전 (테스트 모드)")
    print("4. 시스템 검사")
    print("5. 기존 PI 카메라 클라이언트")
    print("6. 종료")
    print("="*60)
    print("💡 YOLOv11s 모델 사용 - 높은 정확도와 안정적인 성능")
    print("   - 매니저 패턴 적용")
    print("   - Factory 패턴 적용")
    print("   - 의존성 주입")
    print("   - 강화된 예외 처리")
    print("   - 캐싱 및 성능 최적화")
    print("   - 헤드리스 모드 지원")
    print("   - 적응형 메모리 관리 (3GB 미만 시 자동으로 YOLOv11n 사용)")
    print("="*60)

def run_clean_version(mode="normal"):
    """클린코딩 버전 실행"""
    script_path = os.path.join(os.path.dirname(__file__), "run_system.py")
    
    if not os.path.exists(script_path):
        print(f"❌ {script_path} 파일을 찾을 수 없습니다.")
        return
    
    cmd = [sys.executable, script_path]
    
    if mode == "headless":
        cmd.append("--headless")
        description = "클린코딩 버전 (헤드리스 모드)"
    elif mode == "test":
        cmd.extend(["--test", "--headless"])
        description = "클린코딩 버전 (테스트 모드)"
    elif mode == "check":
        cmd.append("--check-deps")
        description = "시스템 검사"
    else:
        description = "클린코딩 버전"
    
    run_command(cmd, description)

def run_legacy_script(script_name: str, description: str) -> None:
    """기존 스크립트 실행"""
    # 상위 디렉토리에서 스크립트 찾기
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    script_path = os.path.join(parent_dir, "라즈베리파이", script_name)
    
    if not os.path.exists(script_path):
        print(f"❌ {script_path} 파일을 찾을 수 없습니다.")
        return
    
    run_command([sys.executable, script_path], description)

def run_command(cmd: list, description: str) -> None:
    """명령 실행"""
    print(f"\n🚀 {description} 시작...")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        
        if result.returncode == 0:
            print(f"✅ {description} 정상 종료")
        else:
            print(f"⚠️ {description} 비정상 종료 (코드: {result.returncode})")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 실행 중 오류 발생 (코드: {e.returncode})")
        logger.error(f"명령 실행 실패: {' '.join(cmd)}, 오류: {e}")
    except KeyboardInterrupt:
        print(f"\n⏹️ {description} 사용자에 의해 중단됨")
    except FileNotFoundError:
        print(f"❌ Python 인터프리터를 찾을 수 없습니다.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {e}")
        logger.error(f"예상치 못한 오류: {e}")

def validate_choice(choice: str) -> bool:
    """선택값 유효성 검증"""
    return choice.isdigit() and 1 <= int(choice) <= 6

def main():
    """메인 실행 함수"""
    logger.info("자동 청소 시스템 런처 시작")
    
    try:
        while True:
            display_menu()
            
            choice = input("\n선택하세요 (1-6): ").strip()
            
            if not validate_choice(choice):
                print("❌ 잘못된 선택입니다. 1-6 중에서 선택하세요.")
                continue
            
            choice_num = int(choice)
            
            if choice_num == 1:
                run_clean_version("normal")
                
            elif choice_num == 2:
                run_clean_version("headless")
                
            elif choice_num == 3:
                run_clean_version("test")
                
            elif choice_num == 4:
                run_clean_version("check")
                
            elif choice_num == 5:
                run_legacy_script("pi_camera_client.py", "기존 PI 카메라 클라이언트")
                
            elif choice_num == 6:
                print("\n👋 시스템을 종료합니다.")
                logger.info("시스템 정상 종료")
                break
            
            # 계속 진행할지 확인
            if choice_num != 6:
                continue_choice = input("\n다른 모드를 실행하시겠습니까? (y/n): ").strip().lower()
                if continue_choice not in ['y', 'yes', '']:
                    print("👋 시스템을 종료합니다.")
                    break
                    
    except KeyboardInterrupt:
        print("\n\n⏹️ 사용자에 의해 중단됨")
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")
        logger.error(f"시스템 오류: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())