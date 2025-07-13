# Inventon_Gongdol 🐦

라즈베리파이4 기반 새장 화장실 자동 청소 시스템 및 AI 퍼즐 프로젝트

## 📋 프로젝트 구조

```
Inventon_Gongdol/
├── AI/                     # AI 관련 모듈
│   ├── puzzle/            # 퍼즐 YOLO 모델
│   └── Toilet/            # 화장실 새똥 탐지 모델
├── HW/                    # 하드웨어 관련 모듈
│   ├── puzzle/            # 퍼즐 하드웨어
│   └── Toilet/            # 화장실 하드웨어
│       ├── Arduino/       # 아두이노 코드
│       └── Raspberrypi/   # 라즈베리파이 코드
├── Design/                # 설계 문서
├── uart_test.py          # UART 통신 테스트 스크립트
└── README.md             # 프로젝트 설명서
```

## 🎯 주요 기능

### 🚽 화장실 청소 시스템
- **AI 새똥 탐지**: YOLO 모델을 이용한 실시간 새똥 인식
- **자동 청소**: 360도 서보모터 MG996R을 이용한 자동 청소 메커니즘
- **UART 통신**: 라즈베리파이 ↔ 아두이노 간 GPIO 14,15 통신
- **실시간 모니터링**: 카메라 영상 및 시스템 상태 모니터링

### 🧩 퍼즐 시스템
- **퍼즐 인식**: YOLO 모델을 이용한 퍼즐 조각 인식
- **AI 훈련**: 커스텀 데이터셋을 이용한 모델 훈련

## 🛠️ 하드웨어 요구사항

### 라즈베리파이4 구성
- **메인 보드**: Raspberry Pi 4 Model B
- **카메라**: Pi Camera Module (libcamera 지원)
- **시리얼 통신**: GPIO 14 (TXD), GPIO 15 (RXD)
- **레벨 로직 컨버터**: 3.3V ↔ 5V 변환 (아두이노 통신용)

### 아두이노 구성
- **아두이노 보드**: Arduino Uno/Nano (또는 호환 보드)
- **360도 서보모터**: MG996R (청소 메커니즘)
- **DHT11 센서**: 온습도 모니터링
- **시리얼 통신**: RX, TX 핀 (레벨 로직 컨버터 경유)

### 청소 메커니즘
- **서보모터**: MG996R 360도 연속 회전 서보모터
- **청소 동작**: 앞으로 3초 → 뒤로 3초 → 정지
- **제어 방식**: PWM 신호 (1700us: 앞으로, 1300us: 뒤로, 1500us: 정지)

## 🔧 소프트웨어 요구사항

### 시스템 요구사항
- **OS**: Raspberry Pi OS (Debian 기반)
- **Python**: 3.11 이상
- **패키지 매니저**: uv (권장)

### 주요 라이브러리
- **AI/비전**: `ultralytics`, `torch`, `torchvision`, `opencv-python`
- **카메라**: `picamera2`, `libcamera`
- **시리얼 통신**: `pyserial`
- **기타**: `numpy`, `matplotlib`, `pyyaml`

### 아두이노 라이브러리
- **ArduinoJson**: JSON 통신 처리
- **DHT sensor library**: 온습도 센서
- **Servo**: 360도 서보모터 제어

## 🚀 설치 및 실행

### 1. 시스템 패키지 설치
```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install -y \
    python3-pip python3-venv python3-dev \
    python3-picamera2 libcamera-apps v4l-utils \
    build-essential cmake pkg-config \
    libjpeg-dev libtiff5-dev libpng-dev \
    libavcodec-dev libavformat-dev libswscale-dev \
    libv4l-dev libxvidcore-dev libx264-dev \
    libgtk-3-dev libatlas-base-dev gfortran \
    libcap-dev git curl
```

### 2. uv 패키지 매니저 설치
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

### 3. 프로젝트 환경 설정
```bash
# 프로젝트 클론 (이미 있는 경우 생략)
git clone <repository-url>
cd Inventon_Gongdol

# Python 가상 환경 생성
uv venv --python 3.11 .venv

# 가상 환경 활성화
source .venv/bin/activate

# 의존성 설치
cd HW/Toilet/Raspberrypi
uv pip install -e .
```

### 4. 시스템 권한 설정
```bash
# 시리얼 포트 접근 권한 추가
sudo usermod -a -G dialout $USER

# 재부팅 후 권한 적용
sudo reboot
```

## 📱 실행 방법

### 환경 활성화
```bash
cd /home/parrot1/gongdol/Inventon_Gongdol
source $HOME/.local/bin/env
source .venv/bin/activate
```

### 시스템 실행
```bash
cd HW/Toilet/Raspberrypi
python main.py
```

### UART 통신 테스트
```bash
# 프로젝트 루트에서
python uart_test.py
```

## 🔌 하드웨어 연결

### UART 시리얼 통신 연결
```
라즈베리파이4          레벨 로직 컨버터          아두이노
GPIO 14 (TXD) ──────→ 3.3V → 5V ──────→ RX 핀
GPIO 15 (RXD) ──────← 5V → 3.3V ──────← TX 핀
GND ─────────────────────────────────────── GND
```

### 360도 서보모터 연결
```
아두이노              MG996R 서보모터
Digital Pin 9 ──────→ 신호선 (주황/노랑)
5V ─────────────────→ 전원선 (빨강)
GND ────────────────→ 접지선 (갈색/검정)
```

### 통신 설정
- **포트**: `/dev/serial0`
- **보드레이트**: 115200
- **데이터 비트**: 8
- **패리티**: None
- **스톱 비트**: 1

## 🎮 시스템 사용법

### 1. 화장실 청소 시스템
```bash
# 시스템 실행
python main.py

# 메뉴에서 "1. PI 카메라 클라이언트 실행" 선택
# - 실시간 새똥 탐지 시작
# - 자동 청소 기능 활성화
# - UART 통신을 통한 아두이노 제어
```

### 2. 청소 동작 과정
1. **탐지**: 카메라로 새똥 영역 탐지 (커버리지 3% 이상)
2. **청소 시작**: 360도 서보모터 앞으로 3초 회전
3. **역방향 청소**: 뒤로 3초 회전으로 완전 청소
4. **정지**: 서보모터 정지 후 대기 상태

### 3. 상태 모니터링
- **탐지 상태**: 실시간 새똥 탐지 결과 및 커버리지
- **청소 카운트**: 자동 청소 실행 횟수
- **시스템 상태**: 온도, 습도 센서 정보
- **서보모터 상태**: 회전 방향 및 작동 상태

## 🔧 아두이노 통신 프로토콜

### 명령어 목록
```json
// 센서 데이터 요청
{"command": "get_sensor_data"}

// 서보모터 제어
{"command": "control_servo", "direction": 1}  // 1: 앞으로, -1: 뒤로, 0: 정지

// 서보모터 정지
{"command": "stop_servo"}

// 자동 청소 실행
{"command": "cage_cleaning"}

// 시스템 상태 확인
{"command": "get_status"}
```

### 응답 형식
```json
// 센서 데이터 응답
{
  "type": "sensor_data",
  "temp": 25.5,
  "hum": 60.2,
  "servo_run": true,
  "servo_dir": 1,
  "time": 123456
}

// 상태 정보 응답
{
  "type": "status",
  "ver": "1.3.1",
  "servo_run": false,
  "servo_dir": 0,
  "cycles": 5,
  "max": 100
}
```

## 🔧 개발 및 디버깅

### 로그 확인
```bash
# 시스템 로그 확인
tail -f detection_log.txt

# 아두이노 시리얼 모니터
sudo minicom -D /dev/serial0 -b 115200
```

### 모델 훈련 (AI 모듈)
```bash
# 퍼즐 모델 훈련
cd AI/puzzle
python main.py

# 화장실 모델 훈련
cd AI/Toilet
python calculate_area.py
```

### 서보모터 테스트
```bash
# 아두이노 시리얼 모니터에서 직접 명령 테스트
{"command": "control_servo", "direction": 1}
{"command": "control_servo", "direction": -1}
{"command": "stop_servo"}
```

## 📝 주요 파일 설명

### HW/Toilet/Raspberrypi/
- **`main.py`**: 시스템 메인 런처
- **`pi_camera_client.py`**: 카메라 및 AI 모델 처리
- **`raspberry_pi_client.py`**: 시스템 통합 모듈
- **`test_imports.py`**: 라이브러리 import 테스트

### HW/Toilet/Arduino/
- **`main.cpp`**: 아두이노 메인 코드
- **`functions.h`**: 함수 헤더 파일

### AI/
- **`puzzle/main.py`**: 퍼즐 YOLO 모델 훈련
- **`Toilet/calculate_area.py`**: 새똥 면적 계산 모듈

### 설정 파일
- **`pyproject.toml`**: Python 프로젝트 의존성 관리
- **`uart_test.py`**: UART 통신 테스트 스크립트

## 🚨 문제 해결

### 카메라 관련 오류
```bash
# 카메라 활성화 확인
sudo raspi-config
# Interface Options → Camera → Enable

# 카메라 연결 확인
libcamera-hello --list-cameras
```

### 시리얼 통신 오류
```bash
# 시리얼 포트 확인
ls -la /dev/serial*
ls -la /dev/ttyS*

# 권한 확인
groups $USER  # dialout 그룹 포함 확인
```

### 서보모터 문제
```bash
# 서보모터 연결 확인
# 1. 전원 연결 (5V, GND)
# 2. 신호선 연결 (Digital Pin 9)
# 3. 서보모터 동작 테스트

# 아두이노 시리얼 모니터에서 테스트
{"command": "system_test"}
```

### 라이브러리 import 오류
```bash
# 테스트 실행
python test_imports.py

# 누락된 라이브러리 개별 설치
uv pip install <library-name>
```

## ⚙️ 하드웨어 사양

### MG996R 서보모터 사양
- **토크**: 11kg·cm (4.8V), 13kg·cm (6V)
- **속도**: 0.17초/60° (4.8V), 0.14초/60° (6V)
- **제어 신호**: PWM (20ms 주기)
- **전원**: 4.8V ~ 7.2V
- **무게**: 55g

### 청소 메커니즘 특징
- **연속 회전**: 360도 무제한 회전 가능
- **양방향 제어**: 시계/반시계 방향 제어
- **정밀한 정지**: 1500us 신호로 정확한 정지
- **내구성**: 고토크로 안정적인 청소 작업

## 🤝 기여

프로젝트에 기여하고 싶으시다면:
1. Fork 후 Pull Request 생성
2. 이슈 등록 및 버그 리포트
3. 기능 개선 제안

## 📄 라이선스

MIT License - 자세한 내용은 LICENSE 파일 참조

## 📞 연락처

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.

---

**🍓 Made with ❤️ on Raspberry Pi 4 + MG996R Servo Motor** 