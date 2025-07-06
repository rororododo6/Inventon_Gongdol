# 🐦 새장 화장실 자동 청소 시스템 설치 가이드

**라즈베리파이 + Arduino 기반 YOLOv11s 새똥 탐지 및 자동 청소 시스템 설치**

이 가이드는 새장 화장실 청소 시스템을 처음부터 설치하는 방법을 단계별로 설명합니다.

## 📋 준비물 체크리스트

### 🔧 필수 하드웨어
- [ ] **라즈베리파이 4** (4GB 이상 권장, 8GB 최적)
- [ ] **Arduino Uno R3**
- [ ] **28BYJ-48 스테핑 모터** + **ULN2003 드라이버 보드**
- [ ] **SG90 서보모터** (청소용)
- [ ] **DHT11 온습도 센서**
- [ ] **라즈베리파이 카메라 모듈 V2**
- [ ] **긴급 정지 버튼** (푸시 버튼)
- [ ] **5mm LED** (상태 표시용)
- [ ] **부저** (능동형 권장)
- [ ] **점퍼 와이어** (M-M, M-F)
- [ ] **브레드보드** 또는 **PCB 프로토타입 보드**
- [ ] **MicroSD 카드** (32GB 이상, Class 10)
- [ ] **USB 케이블** (Arduino 연결용)

### 🔌 전원 및 연결
- [ ] **라즈베리파이 전원** (5V 3A USB-C)
- [ ] **Arduino 전원** (USB 또는 외부 전원)
- [ ] **서보모터 전원** (5V 별도 공급 권장)
- [ ] **네트워크 케이블** 또는 **WiFi 동글**

### 📦 소프트웨어
- [ ] **Raspberry Pi OS** (Bullseye 이상)
- [ ] **Arduino IDE** (라이브러리 설치용)
- [ ] **Python 3.8+**

## 🛠️ 하드웨어 설치

### 1. Arduino 연결 다이어그램

```
Arduino Uno 핀 연결:
┌─────────────────────────────────────┐
│ 📌 DHT11 센서                        │
│ - VCC → 5V                         │
│ - GND → GND                        │
│ - DATA → Pin 2                     │
│                                    │
│ 📌 ULN2003 스테핑 모터 드라이버        │
│ - IN1 → Pin 5                      │
│ - IN2 → Pin 6                      │
│ - IN3 → Pin 7                      │
│ - IN4 → Pin 8                      │
│ - VCC → 5V                         │
│ - GND → GND                        │
│                                    │
│ 📌 청소 서보모터 (SG90)               │
│ - VCC → 5V (별도 전원 권장)           │
│ - GND → GND                        │
│ - Signal → Pin 9                   │
│                                    │
│ 📌 긴급 정지 버튼                     │
│ - 한쪽 → Pin 3 (인터럽트)             │
│ - 다른쪽 → GND                      │
│                                    │
│ 📌 상태 LED                          │
│ - 양극(+) → Pin 13                  │
│ - 음극(-) → 220Ω 저항 → GND          │
│                                    │
│ 📌 부저                              │
│ - 양극(+) → Pin 11                  │
│ - 음극(-) → GND                     │
└─────────────────────────────────────┘
```

### 2. 스테핑 모터 (28BYJ-48) 연결

```
ULN2003 → Arduino
─────────────────
IN1 → Pin 5
IN2 → Pin 6  
IN3 → Pin 7
IN4 → Pin 8
VCC → 5V
GND → GND

28BYJ-48 모터 → ULN2003 보드 커넥터에 직접 연결
```

### 3. 서보모터 연결 주의사항

⚠️ **중요**: 서보모터는 전력 소모가 크므로 별도 5V 전원 공급을 권장합니다.

```
SG90 서보모터:
- 빨강 (VCC) → 5V 외부 전원
- 검정/갈색 (GND) → 공통 GND
- 주황/노랑 (Signal) → Arduino Pin 9
```

### 4. 라즈베리파이 카메라 모듈 연결

1. 라즈베리파이 전원 **끄기**
2. 카메라 포트 열기 (작은 플라스틱 커넥터)
3. 카메라 케이블 삽입 (파란 부분이 이더넷 포트 방향)
4. 커넥터 잠그기

## 💻 소프트웨어 설치

### 1. 라즈베리파이 OS 설정

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 카메라 활성화
sudo raspi-config
# 3 Interface Options → P1 Camera → Yes → Finish

# 재부팅
sudo reboot
```

### 2. Python 환경 설정

```bash
# Python 패키지 관리자 업데이트
sudo apt install python3-pip python3-venv -y

# 가상환경 생성 (선택사항)
python3 -m venv ~/birdcage_env
source ~/birdcage_env/bin/activate

# 필수 시스템 패키지 설치
sudo apt install python3-opencv python3-numpy python3-picamera2 -y
```

### 3. 프로젝트 의존성 설치

```bash
# 프로젝트 폴더로 이동
cd /path/to/your/project/clean_ver

# Python 패키지 설치
pip3 install -r requirements.txt

# YOLOv11s 모델 다운로드 (자동)
python3 -c "from ultralytics import YOLO; YOLO('yolov11s.pt')"
```

### 4. Arduino 설정

#### Arduino IDE 설치 (Ubuntu/Raspberry Pi)
```bash
# Arduino IDE 설치
sudo apt install arduino -y

# 사용자 권한 추가
sudo usermod -a -G dialout $USER
sudo usermod -a -G tty $USER

# 재로그인 필요
logout
```

#### 필수 라이브러리 설치
Arduino IDE에서 다음 라이브러리 설치:

1. **Tools → Manage Libraries**
2. 다음 라이브러리 검색 및 설치:
   - `ArduinoJson` (by Benoit Blanchon)
   - `DHT sensor library` (by Adafruit)
   - `Stepper` (Arduino 내장)

#### Arduino 코드 업로드
```bash
# Arduino 코드 컴파일 및 업로드
cd /path/to/your/project
arduino --upload src/main.cpp --port /dev/ttyUSB0
```

## 🔧 시스템 구성

### 1. Arduino 연결 확인

```bash
# 시리얼 포트 확인
ls /dev/tty*

# Arduino 연결 테스트
python3 -c "
from clean_ver.factories.system_factory import SystemFactory
factory = SystemFactory()
arduino = factory.get_arduino_client()
print('Arduino 연결:', arduino.get_system_status())
"
```

### 2. 카메라 테스트

```bash
# 카메라 테스트
python3 -c "
from picamera2 import Picamera2
picam2 = Picamera2()
picam2.start()
picam2.capture_file('test.jpg')
picam2.stop()
print('카메라 테스트 완료: test.jpg')
"
```

### 3. YOLOv11s 모델 테스트

```bash
# YOLO 모델 테스트
python3 -c "
from ultralytics import YOLO
model = YOLO('yolov11s.pt')
print('YOLOv11s 모델 로드 성공')
print('모델 정보:', model.info())
"
```

## 🚀 시스템 실행

### 1. 의존성 검사

```bash
cd clean_ver
python3 run_system.py --check-deps
```

### 2. 하드웨어 검사

```bash
python3 run_system.py --check-hardware
```

### 3. 테스트 실행

```bash
# 테스트 모드 (Arduino 스텁 사용)
python3 run_system.py --test --headless

# 실제 하드웨어 테스트
python3 run_system.py --headless
```

### 4. 정식 실행

```bash
# 기본 실행 (GUI 환경)
python3 run_system.py

# 헤드리스 실행 (SSH 환경)
python3 run_system.py --headless
```

## ⚙️ 고급 설정

### 1. 성능 최적화

```bash
# GPU 메모리 분할 설정
sudo nano /boot/config.txt

# 다음 라인 추가/수정
gpu_mem=128
gpu_mem_256=128
gpu_mem_512=128
gpu_mem_1024=128

# 재부팅
sudo reboot
```

### 2. 자동 시작 설정

```bash
# systemd 서비스 파일 생성
sudo nano /etc/systemd/system/birdcage-cleaning.service

# 다음 내용 작성:
[Unit]
Description=Bird Cage Toilet Cleaning System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/project/clean_ver
ExecStart=/usr/bin/python3 run_system.py --headless
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# 서비스 활성화
sudo systemctl enable birdcage-cleaning.service
sudo systemctl start birdcage-cleaning.service
```

### 3. 메모리 최적화

```bash
# 스왑 메모리 설정 (2GB)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile

# CONF_SWAPSIZE=2048로 수정

sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## 🛠️ 문제 해결

### Arduino 연결 문제

```bash
# 포트 권한 확인
ls -l /dev/ttyUSB* /dev/ttyACM*

# 권한 부여
sudo chmod 666 /dev/ttyUSB0

# 그룹 추가 확인
groups $USER
```

### 카메라 문제

```bash
# 카메라 활성화 확인
vcgencmd get_camera

# 카메라 모듈 확인
lsmod | grep bcm2835_v4l2

# 카메라 강제 활성화
sudo modprobe bcm2835-v4l2
```

### 메모리 부족 문제

```bash
# 메모리 사용량 확인
free -h

# 프로세스별 메모리 사용량
ps aux --sort=-%mem | head

# YOLOv11n으로 자동 전환 확인
python3 -c "
from clean_ver.optimized_config import SystemConfig
config = SystemConfig.get_optimized_settings()
print('현재 모델:', config.get('yolo_model_path'))
"
```

### 성능 저하 문제

```bash
# CPU 온도 확인
vcgencmd measure_temp

# CPU 사용률 확인
htop

# 프레임 스킵 조정
python3 -c "
from clean_ver.optimized_config import SystemConfig
print('현재 프레임 스킵:', SystemConfig.FRAME_SKIP_INTERVAL)
"
```

## 📊 시스템 모니터링

### 실시간 상태 확인

```bash
# 시스템 상태 스크립트
cat > monitor_system.py << 'EOF'
#!/usr/bin/env python3
import time
import psutil
from clean_ver.factories.system_factory import SystemFactory

def monitor():
    factory = SystemFactory()
    arduino = factory.get_arduino_client()
    
    while True:
        # 시스템 정보
        cpu_temp = psutil.sensors_temperatures().get('cpu_thermal', [{}])[0].get('current', 0)
        memory = psutil.virtual_memory()
        
        # Arduino 상태
        arduino_status = arduino.get_system_status() if arduino else {}
        
        print(f"""
=== 새장 화장실 청소 시스템 상태 ===
CPU 온도: {cpu_temp:.1f}°C
메모리 사용: {memory.percent:.1f}% ({memory.used // 1024**2}MB / {memory.total // 1024**2}MB)
Arduino 연결: {'✅' if arduino_status else '❌'}
청소 횟수: {arduino_status.get('cleaning_cycles', 0)}
시스템 가동: {arduino_status.get('uptime', 0) // 1000}초
        """)
        
        time.sleep(5)

if __name__ == "__main__":
    monitor()
EOF

python3 monitor_system.py
```

## ✅ 설치 완료 체크리스트

- [ ] 라즈베리파이 OS 설치 및 설정
- [ ] 카메라 모듈 연결 및 테스트
- [ ] Arduino 연결 및 코드 업로드
- [ ] 모든 센서 및 액추에이터 연결
- [ ] Python 의존성 설치
- [ ] YOLOv11s 모델 다운로드
- [ ] 시스템 테스트 실행
- [ ] 정상 동작 확인

## 🎉 설치 완료!

축하합니다! 새장 화장실 자동 청소 시스템 설치가 완료되었습니다.

### 다음 단계
1. **기본 테스트**: `python3 run_system.py --test`
2. **실제 운영**: `python3 run_system.py --headless`
3. **모니터링**: 시스템 상태 주기적 확인
4. **유지보수**: 정기적인 청소 및 점검

### 지원
설치 과정에서 문제가 발생하면 다음을 확인해주세요:
- 하드웨어 연결 상태
- 전원 공급 상태
- 소프트웨어 버전 호환성
- 로그 파일 확인

**🐦 깨끗하고 건강한 새장 환경을 즐기세요!** 