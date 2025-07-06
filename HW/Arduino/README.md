# YOLOv11s 기반 새똥 탐지 및 자동 청소 시스템 🐦🧹

라즈베리파이에서 YOLOv11s 모델을 사용하여 새똥을 실시간으로 탐지하고, 아두이노 ULN2003 스테핑 모터를 제어하여 자동 청소를 수행하는 지능형 시스템입니다.

## 🎯 주요 기능

- **실시간 새똥 탐지**: YOLOv11s 딥러닝 모델 기반
- **자동 청소 시스템**: 화면 커버리지 50% 도달 시 자동 작동
- **정밀한 모터 제어**: ULN2003 + 28BYJ-48 스테핑 모터 (5바퀴 앞으로 + 원위치 복귀)
- **지능형 카운터 관리**: 10회 청소 후 알림, 2회 추가 후 정지
- **실시간 환경 모니터링**: DHT11 온습도 센서 데이터 지속 출력
- **상태 관리**: 정상/알림/정지 3단계 상태

## 📂 프로젝트 구조

```
Arduino/
├── 라즈베리파이/              # 🆕 라즈베리파이 전용 폴더
│   ├── main.py                # 메인 런처 (시작점)
│   ├── pi_camera_client.py    # PI 카메라 클라이언트 (권장)
│   ├── gpio_uart_client.py    # GPIO UART 클라이언트
│   ├── demo_test.py          # 테스트 데모
│   └── README.md             # 라즈베리파이 전용 문서
├── src/                      # Arduino 소스 코드
│   └── main.cpp
├── include/                  # Arduino 헤더 파일
│   └── functions.h
├── platformio.ini           # Arduino 프로젝트 설정
├── requirements.txt         # Python 패키지 목록
├── README.md               # 이 파일
└── HARDWARE_CONNECTION.md  # 하드웨어 연결 가이드
```

## 🛠️ 시스템 구성

### 하드웨어
- **라즈베리파이 4**: 메인 제어 보드 (카메라 + AI 처리)
- **Arduino Uno**: 센서/모터 제어 보드
- **라즈베리파이 카메라 모듈**: 실시간 영상 획득
- **DHT11 센서**: 온습도 측정
- **28BYJ-48 스테핑 모터**: 청소 메커니즘
- **ULN2003 드라이버**: 스테핑 모터 제어

### 소프트웨어
- **YOLOv11s**: 객체 탐지 모델
- **OpenCV**: 영상 처리
- **PySerial**: 시리얼 통신
- **Arduino C++**: 펌웨어

## 📦 설치 방법

### 1. 라즈베리파이 설정

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Python 및 pip 설치
sudo apt install python3-pip python3-venv -y

# 가상환경 생성 및 활성화
python3 -m venv yolo_env
source yolo_env/bin/activate

# 프로젝트 클론 및 이동
cd /path/to/your/project

# 패키지 설치
pip install -r requirements.txt

# PI 카메라 모듈 설치
sudo apt install python3-picamera2 libcamera-apps
```

### 2. PI 카메라 활성화

```bash
# 라즈베리파이 설정에서 카메라 활성화
sudo raspi-config
# 3 Interface Options → I1 Camera → Yes

# 시스템 재부팅
sudo reboot

# 카메라 테스트
libcamera-hello
```

### 3. 아두이노 설정

```bash
# PlatformIO 설치 (Arduino IDE 대신 권장)
pip install platformio

# 프로젝트 빌드 및 업로드 (프로젝트 루트에서)
platformio run --target upload
```

## 🔌 하드웨어 연결

### 아두이노 - DHT11 센서
```
DHT11    Arduino Uno
VCC   -> 5V
DATA  -> Digital Pin 2
GND   -> GND
```

### 아두이노 - ULN2003 + 28BYJ-48
```
ULN2003 모듈    Arduino Uno
IN1          -> Digital Pin 5
IN2          -> Digital Pin 6
IN3          -> Digital Pin 7
IN4          -> Digital Pin 8
VCC (5V)     -> 5V
GND          -> GND

28BYJ-48 모터 -> ULN2003 모듈 소켓
```

### 라즈베리파이 - Arduino
```
라즈베리파이 USB -> Arduino USB (시리얼 통신)
```

### 라즈베리파이 - PI 카메라
```
PI 카메라 모듈 -> 라즈베리파이 CSI 포트 (Camera Serial Interface)
```

## 🚀 실행 방법

### 1. 아두이노 펌웨어 업로드
```bash
# 프로젝트 루트에서
platformio run --target upload
```

### 2. 라즈베리파이 시스템 실행
```bash
# 가상환경 활성화
source yolo_env/bin/activate

# 라즈베리파이 폴더로 이동
cd 라즈베리파이/

# 메인 런처 실행 (권장)
python3 main.py

# 또는 직접 실행
python3 pi_camera_client.py    # PI 카메라 시스템 실행 (권장)
python3 gpio_uart_client.py    # GPIO UART 시스템 실행
python3 demo_test.py           # 데모 테스트
```

## 🎮 사용법

### 카메라 창 제어
- **q**: 시스템 종료
- **r**: 시스템 리셋 (쓰레기통 비운 후)
- **s**: 현재 상태 출력

### 시스템 워크플로우

1. **정상 작동 모드**
   - 새똥 탐지 → 화면 50% 커버리지 → 자동 청소
   - 청소 동작: 앞으로 5바퀴 → 원위치 복귀
   - 청소 횟수 카운트: 0/10

2. **알림 모드 (10회 청소 후)**
   - 🚨 "쓰레기통을 비워주세요!" 알림
   - 추가 2회 청소 가능
   - 청소 횟수 카운트: 10+2/10

3. **정지 모드 (12회 청소 후)**
   - ⛔ 시스템 작동 중지
   - 'r' 키로 리셋 필요
   - 청소 횟수 카운트: 0/10으로 초기화

### 온습도 모니터링
- 3초 간격으로 자동 업데이트
- 화면 및 콘솔에 실시간 표시
- 센서 오류 시 "센서 오류" 표시

## 📊 시스템 상태 정보

### 화면 표시 정보
- **State**: 현재 시스템 상태
- **Clean**: 청소 횟수 (현재/최대)
- **Coverage**: 새똥 탐지 커버리지 비율
- **Temp**: 현재 온도 (°C)
- **Humidity**: 현재 습도 (%)

### 콘솔 출력 정보
```
[14:23:45] === 시스템 상태 ===
상태: 정상 작동
청소 횟수: 5/10
새똥 탐지 커버리지: 65.3%
🌡️  온도: 23.5°C
💧 습도: 58%
```

## ⚙️ 설정 변경

### `raspberry_pi_client.py` 주요 설정값

```python
# 청소 설정
self.max_clean_count = 10        # 최대 청소 횟수
self.max_warning_extra = 2       # 알림 후 추가 청소 횟수
self.cleaning_revolutions = 5    # 청소 시 회전 수 (바퀴)
self.cleaning_speed = 12         # 모터 속도 (RPM)

# 탐지 설정
self.target_coverage = 0.5       # 탐지 임계값 (50%)
self.confidence = 0.5            # YOLO 신뢰도

# 센서 설정
self.sensor_update_interval = 3  # 센서 업데이트 간격 (초)
```

## 🔧 문제 해결

### 일반적인 문제

1. **카메라 인식 실패**
   ```bash
   # 카메라 장치 확인
   ls /dev/video*
   
   # 권한 설정
   sudo usermod -a -G video $USER
   ```

2. **아두이노 연결 실패**
   ```bash
   # 시리얼 포트 확인
   ls /dev/ttyUSB* /dev/ttyACM*
   
   # 권한 설정
   sudo usermod -a -G dialout $USER
   ```

3. **YOLO 모델 다운로드 실패**
   ```bash
   # 수동 다운로드
   wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov11n.pt
   ```

4. **메모리 부족 (라즈베리파이)**
   ```bash
   # 스왑 메모리 증가
   sudo dphys-swapfile swapoff
   sudo nano /etc/dphys-swapfile  # CONF_SWAPSIZE=2048
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

### 성능 최적화

1. **GPU 가속 (라즈베리파이 4)**
   ```bash
   # GPU 메모리 할당
   sudo raspi-config
   # Advanced Options > Memory Split > 128
   ```

2. **CPU 성능 모드**
   ```bash
   # 성능 모드 설정
   echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
   ```

## 📈 시스템 모니터링

### 실시간 로그 확인
```bash
# 시스템 리소스 모니터링
htop

# 온도 모니터링
vcgencmd measure_temp
```

### 디버그 모드 실행
```python
# 디버그 정보 활성화
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔄 업데이트 및 유지보수

### 정기 점검 사항
1. **하드웨어 연결 상태** (주 1회)
2. **센서 정확도 검증** (월 1회)
3. **모터 동작 점검** (월 1회)
4. **시스템 로그 확인** (월 1회)

### 업데이트 방법
```bash
# 패키지 업데이트
pip install --upgrade ultralytics opencv-python

# 시스템 업데이트
sudo apt update && sudo apt upgrade
```

## 📞 지원 및 문의

시스템 관련 문의사항이나 개선 제안이 있으시면 언제든지 연락해주세요.

---
**🎉 YOLOv11s 기반 지능형 새똥 청소 시스템으로 깨끗한 환경을 유지하세요!** 

## 🔌 GPIO UART 통신 설정

### 📍 라즈베리파이 GPIO UART 핀
```
GPIO 14 (Pin 8)  - TXD (송신)
GPIO 15 (Pin 10) - RXD (수신)
GND (Pin 6)      - 그라운드
```

### 🔧 하드웨어 연결 방법

#### 🔌 라즈베리파이 ↔ Arduino 직접 연결
```
라즈베리파이      Arduino Uno
┌─────────────┐   ┌─────────────┐
│GPIO 14 (TXD)│──→│  RX (Pin 0) │
│GPIO 15 (RXD)│←──│  TX (Pin 1) │
│    GND      │───│     GND     │
└─────────────┘   └─────────────┘
```

**⚠️ 주의: 전압 레벨 차이**
- 라즈베리파이: 3.3V
- Arduino: 5V
- **전압 분배기 또는 레벨 컨버터 필요**

### 🔧 안전한 연결 방법

#### 1️⃣ 전압 분배기 사용
```
Arduino TX (5V) ──┬── 1kΩ ──┬── 라즈베리파이 RX (3.3V)
                  │         │
                  └─ 2kΩ ───┴── GND
```

#### 2️⃣ 레벨 컨버터 사용 (권장)
```
라즈베리파이 ↔ 레벨 컨버터 ↔ Arduino
  (3.3V)         (3.3V↔5V)      (5V)
```

## ⚙️ 라즈베리파이 설정

### 1️⃣ UART 활성화
```bash
# Raspberry Pi 설정 도구 실행
sudo raspi-config

# 3 Interface Options
# P6 Serial Port
# Would you like a login shell to be accessible over serial? → No
# Would you like the serial port hardware to be enabled? → Yes
```

### 2️⃣ 부팅 설정 수정
```bash
# config.txt 편집
sudo nano /boot/config.txt

# 다음 줄 추가 또는 수정
enable_uart=1
dtoverlay=disable-bt
```

### 3️⃣ 시스템 재부팅
```bash
sudo reboot
```

## 🐍 Python 코드 수정

현재 코드를 GPIO UART 통신으로 수정하겠습니다: 