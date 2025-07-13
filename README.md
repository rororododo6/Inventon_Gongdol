# 🐦 새장 화장실 자동 청소 시스템

라즈베리파이4와 아두이노를 이용한 AI 새똥 탐지 및 자동 청소 시스템입니다.

## 🎯 주요 기능

### 🔍 AI 새똥 탐지 (누적 방식)
- **YOLO 커스텀 모델**: 새똥 특화 훈련 모델 사용
- **누적 탐지**: 새똥 영역을 메모리에 누적 저장
- **중복 제거**: IoU 계산으로 겹치는 영역 자동 병합
- **임계값**: 카메라 픽셀 면적의 **50%** 누적 시 청소 시작

### 🧹 자동 청소 시스템
- **360도 서보모터**: MG996R 사용 (앞으로 3초 → 뒤로 3초)
- **PWM 제어**: 1700us(앞), 1300us(뒤), 1500us(정지)
- **청소 후 초기화**: 누적 영역 데이터 완전 삭제

### 🗑️ 쓰레기통 관리
- **10번 청소 후 알림**: "쓰레기통을 비워주세요" 메시지
- **청소 차단**: 쓰레기통 가득 참 시 청소 거부
- **버튼으로 해제**: 아두이노 핀 4번 버튼으로 비우기 완료 확인
- **자동 초기화**: 버튼 누름 시 청소 카운트 리셋

### 📊 상태 모니터링
- **실시간 표시**: 누적 영역 개수, 커버리지 비율
- **경고 시스템**: 30%, 50% 임계값별 알림
- **10번째 청소 축하**: 달성 시 특별 메시지 출력

## 🛠️ 하드웨어 구성

### 라즈베리파이4
- **카메라**: PI 카메라 모듈 (IMX219, 640x480)
- **UART 통신**: GPIO 14(TXD), GPIO 15(RXD)
- **운영체제**: Raspberry Pi OS

### 아두이노 (Arduino Uno/Nano)
- **DHT11 센서**: 핀 2번 (온습도 측정)
- **360도 서보모터**: 핀 9번 (MG996R)
- **긴급 정지 버튼**: 핀 3번 (인터럽트)
- **쓰레기통 비우기 버튼**: 핀 4번 (풀업 저항)
- **상태 LED**: 핀 13번
- **부저**: 핀 11번
- **UART 통신**: 115200 baud

## 📋 시스템 요구사항

### 라즈베리파이
```bash
# 시스템 패키지
sudo apt update && sudo apt install -y \
    python3-picamera2 libcamera-apps v4l-utils \
    libopencv-dev cmake build-essential \
    libcap-dev

# Python 패키지 (uv 사용)
uv add ultralytics torch torchvision opencv-python \
    picamera2 pyserial numpy datetime pathlib \
    pyav python-prctl piexif simplejpeg pidng pykms
```

### 아두이노
```cpp
// 필요한 라이브러리
#include <DHT.h>
#include <Servo.h>
#include <ArduinoJson.h>
```

## 🚀 설치 및 실행

### 1. 환경 설정
```bash
# 프로젝트 루트로 이동
cd /home/parrot1/gongdol/Inventon_Gongdol

# 환경 활성화
source $HOME/.local/bin/env
source .venv/bin/activate
```

### 2. 시스템 실행
```bash
# 라즈베리파이 디렉토리로 이동
cd HW/Toilet/Raspberrypi

# 자동 청소 시스템 실행
python main.py

# 또는 직접 실행
python pi_camera_client.py --model ../AI/detect/train63/weights/best.pt --confidence 0.3
```

### 3. 아두이노 업로드
```bash
# Arduino IDE 또는 PlatformIO로 업로드
# 파일: HW/Toilet/Arduino/src/main.cpp
```

## 📡 통신 프로토콜

### 아두이노 → 라즈베리파이
```json
{
  "type": "sensor_data",
  "temp": 25.5,
  "hum": 60.2,
  "servo_run": false,
  "servo_dir": 0,
  "trash_full": false,
  "trash_empty_btn": false,
  "time": 1234567890
}
```

### 라즈베리파이 → 아두이노
```json
{
  "command": "cage_cleaning"
}

{
  "command": "control_servo",
  "direction": 1
}

{
  "command": "trash_empty_button"
}
```

## 🔄 동작 흐름

1. **새똥 탐지** → 위치/크기 메모리에 누적 저장
2. **영역 병합** → 겹치는 부분 자동 처리 (IoU > 10%)
3. **임계값 확인** → 누적 커버리지 50% 체크
4. **청소 실행** → 360도 서보모터 3초씩 양방향 회전
5. **영역 초기화** → 누적 데이터 완전 삭제
6. **쓰레기통 관리** → 10번 청소 후 비우기 요청

## 📊 상태 메시지

### 일반 상태
```
[14:30:15] === 시스템 상태 ===
상태: 정상 작동
청소 횟수: 3/10
총 청소 횟수: 3
누적 새똥 영역: 2개
누적 커버리지: 35.2% (임계값: 50%)
⚠️ 주의: 누적 커버리지가 30%를 초과했습니다.
```

### 쓰레기통 가득 참
```
총 청소 횟수: 10
🗑️ 쓰레기통 가득 참! 비우기 버튼을 눌러주세요.
🗑️ 쓰레기통을 비워주세요! 청소를 계속하려면 비우기 버튼을 눌러주세요.
```

### 10번째 청소 축하
```
🎉 축하합니다! 10번째 청소를 완료했습니다!
🏆 시스템이 안정적으로 10회 청소를 성공적으로 수행했습니다.
🔧 청소 성능이 최적화되었습니다.
```

## 🔧 문제 해결

### 카메라 문제
```bash
# 카메라 테스트
libcamera-hello --timeout 5000

# 권한 확인
sudo usermod -a -G video $USER
```

### 시리얼 통신 문제
```bash
# 권한 확인
sudo usermod -a -G dialout $USER

# 포트 확인
ls -la /dev/serial*
```

### 서보모터 문제
```bash
# PWM 신호 확인
# 1700us: 앞으로 회전
# 1300us: 뒤로 회전
# 1500us: 정지
```

## 🎯 MG996R 360도 서보모터 사양

- **토크**: 13kg·cm (4.8V), 15kg·cm (6.0V)
- **속도**: 0.19sec/60° (4.8V), 0.15sec/60° (6.0V)
- **전원**: 4.8V-7.2V
- **제어 신호**: 1000-2000μs PWM (20ms 주기)
- **회전**: 연속 회전 가능

## 📂 프로젝트 구조

```
Inventon_Gongdol/
├── HW/
│   └── Toilet/
│       ├── Arduino/
│       │   └── src/
│       │       └── main.cpp
│       └── Raspberrypi/
│           ├── main.py
│           └── pi_camera_client.py
└── AI/
    └── detect/
        └── train63/
            └── weights/
                └── best.pt
```

## 🚀 최신 업데이트

### v2.0.0 (2024)
- ✅ 누적 탐지 방식 구현
- ✅ 50% 임계값 적용
- ✅ 10번 청소 후 쓰레기통 비우기 시스템
- ✅ 아두이노 버튼으로 비우기 완료 확인
- ✅ 실시간 상태 모니터링
- ✅ 10번째 청소 축하 메시지

## 📞 문의

프로젝트에 대한 문의나 기여는 GitHub Issues를 통해 주세요.

---

**개발자**: rororododo6  
**저장소**: https://github.com/rororododo6/Inventon_Gongdol 