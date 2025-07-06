#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
라즈베리파이 새똥 탐지 시스템 메인 런처
"""

import sys
import os

def main():
    """메인 실행 함수"""
    print("=== 라즈베리파이 새똥 탐지 시스템 ===")
    print("1. PI 카메라 클라이언트 (권장)")
    print("2. GPIO UART 클라이언트")
    print("3. 데모 테스트")
    print("4. 종료")
    
    while True:
        try:
            choice = input("\n실행할 모드를 선택하세요 (1-4): ").strip()
            
            if choice == '1':
                print("\n🚀 PI 카메라 클라이언트 실행 중...")
                os.system("python3 pi_camera_client.py")
                break
            elif choice == '2':
                print("\n🚀 GPIO UART 클라이언트 실행 중...")
                os.system("python3 gpio_uart_client.py")
                break
            elif choice == '3':
                print("\n🚀 데모 테스트 실행 중...")
                os.system("python3 demo_test.py")
                break
            elif choice == '4':
                print("프로그램을 종료합니다.")
                break
            else:
                print("❌ 잘못된 선택입니다. 1-4 중에서 선택하세요.")
                
        except KeyboardInterrupt:
            print("\n\n프로그램을 종료합니다.")
            break
        except Exception as e:
            print(f"오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main() 