#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import 테스트 스크립트
"""

print("=== Import 테스트 시작 ===")

try:
    print("1. 기본 라이브러리 import...")
    import serial
    import serial.tools.list_ports
    print("✅ pyserial OK")
except ImportError as e:
    print(f"❌ pyserial 실패: {e}")
    exit(1)

try:
    print("2. picamera2 import...")
    from picamera2 import Picamera2
    print("✅ picamera2 OK")
except ImportError as e:
    print(f"❌ picamera2 실패: {e}")
    exit(1)

try:
    print("3. opencv import...")
    import cv2
    import numpy as np
    print(f"✅ opencv OK (버전: {cv2.__version__})")
except ImportError as e:
    print(f"❌ opencv 실패: {e}")
    exit(1)

try:
    print("4. ultralytics import...")
    from ultralytics import YOLO
    print("✅ ultralytics OK")
except ImportError as e:
    print(f"❌ ultralytics 실패: {e}")
    exit(1)

try:
    print("5. 기타 라이브러리 import...")
    import json
    import time
    import threading
    from datetime import datetime
    from enum import Enum
    import argparse
    print("✅ 기타 라이브러리 OK")
except ImportError as e:
    print(f"❌ 기타 라이브러리 실패: {e}")
    exit(1)

print("\n=== 모든 Import 성공! ===")

# 모델 파일 체크
import os
model_path = "../AI/detect/train63/weights/best.pt"
if os.path.exists(model_path):
    print(f"✅ 모델 파일 존재: {model_path}")
    print(f"📏 파일 크기: {os.path.getsize(model_path)} bytes")
else:
    print(f"❌ 모델 파일 없음: {model_path}")

print("\n=== 테스트 완료 ===") 