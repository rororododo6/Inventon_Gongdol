# 🍓 라즈베리파이 새똥 탐지 시스템

라즈베리파이 전용 YOLOv11s 기반 새똥 탐지 및 자동 청소 시스템입니다.

## 📂 파일 구조

```
라즈베리파이/
├── main.py                 # 메인 런처 (시작점)
├── pi_camera_client.py     # PI 카메라 클라이언트 (권장)
├── gpio_uart_client.py     # GPIO UART 클라이언트
├── demo_test.py           # 테스트 데모
└── README.md              # 이 파일
```

## 🚀 실행 방법

### 1. 간단한 실행 (권장)
```bash
cd 라즈베리파이/
python3 main.py
```

### 2. 직접 실행
```bash
cd 라즈베리파이/
python3 pi_camera_client.py    # PI 카메라 사용
python3 gpio_uart_client.py    # GPIO UART 사용  
python3 demo_test.py           # 테스트 모드
```

## 🎯 각 클라이언트별 특징

### PI 카메라 클라이언트 (권장)
- **카메라**: 라즈베리파이 카메라 모듈 v2/v3
- **통신**: USB 시리얼 (Arduino)
- **성능**: 최적화됨
- **안정성**: 높음

### GPIO UART 클라이언트
- **카메라**: USB 카메라
- **통신**: GPIO UART (/dev/ttyS0)
- **성능**: 보통
- **안정성**: 보통

### 데모 테스트
- **카메라**: USB 카메라
- **YOLO**: 없음 (키보드 시뮬레이션)
- **용도**: 하드웨어 테스트

## 📋 필요 조건

### 하드웨어
- 라즈베리파이 4 (4GB 이상)
- 라즈베리파이 카메라 모듈 v2/v3
- Arduino Uno + DHT11 + ULN2003 + 28BYJ-48

### 소프트웨어
```bash
# 시스템 패키지
sudo apt install python3-picamera2 libcamera-apps

# Python 패키지
pip install -r ../requirements.txt
```

## 🔧 설정

### 1. PI 카메라 활성화
```bash
sudo raspi-config
# 3 Interface Options → I1 Camera → Yes
sudo reboot
```

### 2. YOLO 모델 다운로드
```bash
cd ..
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov11n.pt
```

### 3. Arduino 펌웨어 업로드
```bash
cd ..
platformio run --target upload
```

## 🎮 사용법

### 키보드 단축키
- **q**: 시스템 종료
- **r**: 시스템 리셋 (쓰레기통 비운 후)
- **s**: 현재 상태 출력
- **SPACE**: 데모 모드에서 탐지 시뮬레이션

### 시스템 상태
1. **정상 작동**: 새똥 탐지 시 자동 청소
2. **알림 모드**: 10회 청소 후 알림 (2회 추가 가능)
3. **정지 모드**: 12회 청소 후 정지 (리셋 필요)

## 🔍 트러블슈팅

### 카메라 문제
```bash
# 카메라 테스트
libcamera-hello --timeout 5000
```

### 시리얼 통신 문제
```bash
# 포트 확인
ls /dev/ttyUSB* /dev/ttyACM*

# 권한 설정
sudo usermod -a -G dialout $USER
```

### YOLO 모델 문제
```bash
# 모델 다운로드 확인
ls -la ../yolov11n.pt
```

## 📞 지원

문제가 발생하면 상위 폴더의 `README.md`와 `HARDWARE_CONNECTION.md`를 참고하세요. 