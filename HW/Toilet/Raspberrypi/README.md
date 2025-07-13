# 🍓 새장 화장실 자동 청소 시스템 - 라즈베리파이

**라즈베리파이 4 기반 AI 새똥 탐지 및 시스템 제어**

YOLO 커스텀 모델을 이용한 새똥 누적 탐지와 Arduino 하드웨어 제어 시스템입니다.

> 📖 **전체 프로젝트 개요**: [`../../../README.md`](../../../README.md)  
> 📖 **하드웨어 전체 가이드**: [`../README.md`](../README.md)

## 🎯 주요 기능

### 🔍 AI 새똥 탐지 시스템
- **YOLO 커스텀 모델**: train63 데이터셋으로 훈련된 새똥 전용 모델
- **누적 탐지 방식**: 탐지된 영역을 메모리에 누적 저장
- **IoU 기반 병합**: 겹치는 영역 자동 제거 (IoU > 10%)
- **50% 임계값**: 누적 커버리지 50% 도달 시 자동 청소

### 🤖 Arduino 하드웨어 제어
- **UART 통신**: 115200 baud 시리얼 통신
- **JSON 프로토콜**: 구조화된 명령/응답 시스템
- **실시간 모니터링**: 온습도, 모터 상태, 청소 횟수
- **안전 시스템**: 긴급 정지, 상태 확인, 에러 처리

### 📊 성능 최적화
- **동적 해상도**: 640x480 ↔ 320x240 자동 조정
- **메모리 관리**: 모델 자동 전환 (커스텀 → YOLOv11n/s)
- **CPU 모니터링**: 온도 기반 성능 조절
- **헤드리스 모드**: SSH 접속 시 최적화

## 📂 프로젝트 구조

```
Raspberrypi/
├── clean_ver/                   # ✨ 최신 클린코딩 버전 (권장)
│   ├── run_system.py           # 메인 시스템 실행기
│   ├── pi_camera_client_clean.py  # 최적화된 카메라 클라이언트
│   ├── optimized_config.py     # 성능 최적화 설정
│   ├── main.py                 # 클린 버전 런처
│   ├── factories/              # 팩토리 패턴 구현
│   └── managers/               # 시스템 관리자들
├── main.py                     # 🚀 메뉴 기반 시스템 런처
├── pi_camera_client.py         # 📦 레거시 카메라 클라이언트
├── uart_test.py                # 🧪 시리얼 통신 테스트
├── quick-start.sh              # ⚡ 빠른 시작 스크립트
├── setup-env.sh                # 🔧 환경 설정 스크립트
├── Makefile                    # 📋 빌드 및 실행 관리
├── pyproject.toml              # 📦 Python 프로젝트 설정
└── README.md                   # 📖 이 파일
```

## 🚀 빠른 시작

### ⚡ 추천 실행 방법 (uv 사용)

```bash
# 1. 환경 설정
source $HOME/.local/bin/env

# 2. 클린 버전 실행 (최신 권장)
uv run clean-system

# 3. 헤드리스 모드 (SSH 접속 시)
uv run clean-system --headless

# 4. 테스트 모드 (하드웨어 없이)
uv run clean-system --test --headless
```

### 🎛️ Makefile 사용 (더 편리)

```bash
make run              # 일반 실행
make run-headless     # 헤드리스 모드 (SSH 권장)
make run-test         # 테스트 모드
make check            # 시스템 검사
make setup            # 의존성 설치
make help             # 도움말
```

### 📜 빠른 시작 스크립트

```bash
./quick-start.sh      # 대화형 빠른 시작
./setup-env.sh        # 전체 환경 설정
```

## 📋 버전 비교

### ✨ Clean Ver (권장)
- **위치**: `clean_ver/` 폴더
- **특징**: 최신 최적화 버전
- **성능**: 메모리 자동 최적화, 3-8 FPS
- **안정성**: 팩토리 패턴, 예외 처리 강화
- **모니터링**: 실시간 시스템 상태 표시
- **실행**: `uv run clean-system`

### 📦 Legacy Ver
- **위치**: 루트 폴더
- **특징**: 개발 초기 버전
- **용도**: 호환성 확인, 참고용
- **실행**: `python main.py`

## 🛠️ 설치 및 설정

### 🚀 자동 설치 (권장)

```bash
# 전체 환경 자동 설치
./setup-env.sh

# 또는 Makefile 사용
make install
```

### 🔧 수동 설치

#### 1. uv 패키지 관리자 설치
```bash
# uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# 프로젝트 의존성 설치
uv sync
```

#### 2. 시스템 패키지 설치
```bash
# 필수 시스템 패키지
sudo apt update && sudo apt install -y \
    python3-picamera2 libcamera-apps \
    python3-dev build-essential

# 카메라 활성화
sudo raspi-config
# 3 Interface Options → I1 Camera → Yes
sudo reboot
```

#### 3. 권한 설정
```bash
# 사용자 그룹 추가
sudo usermod -a -G video,dialout,gpio $USER

# 재로그인 또는 재부팅
sudo reboot
```

## 🎮 사용법

### 키보드 제어
- **q**: 시스템 종료
- **r**: 시스템 리셋 (청소 후)
- **s**: 현재 상태 확인
- **SPACE**: 수동 청소 실행
- **h**: 도움말 표시

### 실행 옵션
```bash
# 기본 실행
uv run clean-system

# 헤드리스 모드 (SSH 접속 시)
uv run clean-system --headless

# 테스트 모드 (하드웨어 없이)
uv run clean-system --test

# 디버그 모드
uv run clean-system --debug

# 커스텀 모델 사용
uv run clean-system --model /path/to/model.pt

# 신뢰도 임계값 변경
uv run clean-system --confidence 0.4
```

## 📊 성능 지표

### 라즈베리파이 4 기준
- **커스텀 새똥 모델**: 3-6 FPS, 98% 이상 탐지 정확도
- **YOLOv11s**: 3-5 FPS (4GB), 5-8 FPS (8GB)
- **YOLOv11n**: 5-10 FPS (자동 전환 시)
- **메모리 사용**: 2.5-3.5GB
- **응답 시간**: 탐지 → 청소 시작 < 2초

### 자동 최적화 기능
- **메모리 부족 시**: 모델 자동 전환 (커스텀 → YOLOv11n)
- **CPU 과열 시**: 해상도 자동 조정 (640x480 → 320x240)
- **성능 저하 시**: 프레임 스킵 및 버퍼 최적화

## 🔗 Arduino 연동

### 시리얼 통신 설정
```python
# 통신 설정
SERIAL_PORT = '/dev/serial0'  # 기본 UART
BAUD_RATE = 115200
TIMEOUT = 1.0
```

### 명령 전송 예시
```python
# 청소 명령 전송
send_command({"command": "cage_cleaning"})

# 센서 데이터 요청
send_command({"command": "get_sensor_data"})

# 긴급 정지 해제
send_command({"command": "emergency_reset"})
```

### 상태 모니터링
```python
# 실시간 상태 확인
{
  "temperature": 25.5,
  "humidity": 60.2,
  "cleaning_cycles": 3,
  "emergency_stop": false,
  "stepperRunning": false
}
```

## 🔍 문제 해결

### 일반적인 문제

#### 1. 카메라 인식 안됨
```bash
# 카메라 테스트
libcamera-hello --timeout 5000

# 권한 확인
sudo usermod -a -G video $USER
sudo reboot
```

#### 2. 시리얼 통신 안됨
```bash
# 포트 확인
ls -la /dev/serial*

# 통신 테스트
python uart_test.py

# 권한 확인
sudo usermod -a -G dialout $USER
```

#### 3. 성능 저하
```bash
# 헤드리스 모드 사용
make run-headless

# 메모리 확인
free -h

# CPU 온도 확인
vcgencmd measure_temp
```

### 성능 최적화

#### 메모리 최적화
```bash
# 스왑 메모리 설정
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

#### GPU 메모리 할당
```bash
# GPU 메모리 증가
sudo raspi-config
# 7 Advanced Options → A3 Memory Split → 128

# 또는 직접 편집
echo 'gpu_mem=128' | sudo tee -a /boot/config.txt
```

## 🧪 테스트 및 디버깅

### 시스템 테스트
```bash
# 하드웨어 테스트
python uart_test.py

# 카메라 테스트
python test_imports.py

# 전체 시스템 테스트
make run-test
```

### 디버그 모드
```bash
# 디버그 로그 활성화
uv run clean-system --debug

# 로그 파일 확인
tail -f detection_log.txt
```

### 성능 모니터링
```bash
# 시스템 리소스 모니터링
htop

# GPU 메모리 확인
vcgencmd get_mem arm && vcgencmd get_mem gpu

# 온도 모니터링
watch -n 1 vcgencmd measure_temp
```

## 📁 관련 문서

- **Arduino 펌웨어**: [`../Arduino/README.md`](../Arduino/README.md)
- **하드웨어 연결**: [`../Arduino/HARDWARE_CONNECTION.md`](../Arduino/HARDWARE_CONNECTION.md)
- **하드웨어 전체**: [`../README.md`](../README.md)
- **전체 프로젝트**: [`../../../README.md`](../../../README.md)

---

**🎯 라즈베리파이 목표**: 안정적이고 정확한 AI 새똥 탐지 시스템 구현  
**🛠️ 개발 환경**: Raspberry Pi OS, Python 3.9+, uv 패키지 관리자 