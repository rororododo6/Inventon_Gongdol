#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
라즈베리파이 새똥 탐지 시스템 메인 런처
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
    print("🎯 PI 카메라 자동 청소 시스템")
    print("="*60)
    print("1. PI 카메라 클라이언트 실행")
    print("2. 종료")
    print("="*60)
    print("💡 클린코딩 버전을 사용하려면 '../clean_ver' 폴더를 확인하세요!")
    print("   더 안정적이고 확장 가능한 버전이 준비되어 있습니다.")
    print("="*60)

def run_script(script_name: str, description: str) -> None:
    """스크립트 실행"""
    print(f"\n🚀 {description} 시작...")
    
    try:
        # 스크립트 존재 확인
        if not os.path.exists(script_name):
            print(f"❌ {script_name} 파일을 찾을 수 없습니다.")
            return
        
        # 스크립트 실행
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=False
        )
        
        if result.returncode == 0:
            print(f"✅ {description} 정상 종료")
        else:
            print(f"⚠️ {description} 비정상 종료 (코드: {result.returncode})")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 실행 중 오류 발생 (코드: {e.returncode})")
        logger.error(f"스크립트 실행 실패: {script_name}, 오류: {e}")
    except KeyboardInterrupt:
        print(f"\n⏹️ {description} 사용자에 의해 중단됨")
    except FileNotFoundError:
        print(f"❌ Python 인터프리터를 찾을 수 없습니다.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {e}")
        logger.error(f"예상치 못한 오류: {e}")

def validate_choice(choice: str) -> bool:
    """선택값 유효성 검증"""
    return choice.isdigit() and 1 <= int(choice) <= 2

def main():
    """메인 실행 함수"""
    logger.info("자동 청소 시스템 런처 시작")
    
    try:
        while True:
            display_menu()
            
            choice = input("\n선택하세요 (1-2): ").strip()
            
            if not validate_choice(choice):
                print("❌ 잘못된 선택입니다. 1-2 중에서 선택하세요.")
                continue
            
            choice_num = int(choice)
            
            if choice_num == 1:
                run_script("pi_camera_client.py", "PI 카메라 클라이언트")
                
            elif choice_num == 2:
                print("\n👋 시스템을 종료합니다.")
                logger.info("시스템 정상 종료")
                break
            
            # 계속 진행할지 확인
            if choice_num != 2:
                continue_choice = input("\n다시 실행하시겠습니까? (y/n): ").strip().lower()
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