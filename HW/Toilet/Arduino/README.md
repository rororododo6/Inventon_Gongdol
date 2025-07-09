# 🐦 새장 화장실 자동 청소 시스템 - Arduino 펌웨어

**Arduino Uno 기반 하드웨어 제어 펌웨어 v1.3.1**

라즈베리파이와 시리얼 통신으로 연동하여 새똥 청소를 위한 하드웨어를 제어하는 Arduino 펌웨어입니다.

## 🎯 주요 기능

- **🌡️ 환경 모니터링**: DHT11 온습도 센서 실시간 데이터 수집
- **🔄 정밀 모터 제어**: ULN2003 + 28BYJ-48 스테핑 모터 제어
- **🧹 자동 청소 시스템**: 3단계 청소 프로세스 (서보모터 + 스테핑모터)
- **🚨 안전 시스템**: 긴급 정지 버튼, 상태 LED, 알림 부저
- **📡 실시간 통신**: 라즈베리파이와 115200 baud 시리얼 통신
- **🔧 완전한 제어**: JSON 기반 명령어 시스템

## 📂 프로젝트 구조

```
Arduino/
├── src/                     # 📁 소스 코드
│   └── main.cpp            # 🎯 메인 Arduino 펌웨어
├── include/                # 📁 헤더 파일
│   ├── README             # 헤더 폴더 설명
│   └── functions.h        # 🔧 함수 선언
├── lib/                   # 📁 라이브러리 폴더
├── platformio.ini         # ⚙️ PlatformIO 프로젝트 설정
├── requirements.txt       # 🐍 Python 요구사항 (라즈베리파이용)
├── HARDWARE_CONNECTION.md # 🔌 하드웨어 연결 가이드
└── README.md             # 📖 이 파일
```

## 🔌 하드웨어 구성

### Arduino 핀 배치
| 핀 번호 | 연결 부품 | 기능 |
|---------|-----------|------|
| **2** | DHT11 센서 | 온습도 측정 |
| **3** | 긴급 정지 버튼 | 안전 정지 (인터럽트) |
| **5** | ULN2003 IN1 | 스테핑 모터 제어 |
| **6** | ULN2003 IN2 | 스테핑 모터 제어 |
| **7** | ULN2003 IN3 | 스테핑 모터 제어 |
| **8** | ULN2003 IN4 | 스테핑 모터 제어 |
| **9** | SG90 서보모터 | 모래 밀어내기 |
| **11** | 부저 | 상태 알림음 |
| **13** | 상태 LED | 시스템 상태 표시 |

### 필수 부품 리스트
- **Arduino Uno** (메인 제어 보드)
- **DHT11 온습도 센서**
- **28BYJ-48 스테핑 모터 + ULN2003 드라이버 보드**
- **SG90 서보모터** (청소용)
- **긴급 정지 푸시 버튼**
- **5mm LED** (상태 표시용)
- **부저** (알림음용)
- **점퍼 와이어 및 브레드보드**

## 🚀 설치 및 업로드

### 1. PlatformIO 설치 (권장)
```bash
# PlatformIO CLI 설치
pip install platformio

# 또는 VS Code에서 PlatformIO IDE 확장 설치
```

### 2. 라이브러리 의존성
`platformio.ini`에서 자동 설치됩니다:
- **ArduinoJson** v7.0.0: JSON 통신
- **AccelStepper** v1.64: 스테핑 모터 제어
- **Servo** v1.2.1: 서보모터 제어  
- **DHT sensor library** v1.4.4: 온습도 센서
- **Stepper** v1.1.3: 기본 스테핑 모터

### 3. 펌웨어 업로드
```bash
# 프로젝트 빌드 및 업로드
platformio run --target upload

# 시리얼 모니터 실행
platformio device monitor

# 또는 Arduino IDE 사용
# File → Open → Arduino 폴더 선택
# Tools → Board → Arduino Uno
# Sketch → Upload
```

## 🎮 청소 시스템 동작

### 3단계 청소 프로세스
```
1️⃣ 서보모터 작동 (모래 밀어내기)
   ├── 0° → 90° → 0° (20회 반복)
   └── 소요시간: 약 20초

2️⃣ 대기 시간 (안정화)
   └── 1초 대기

3️⃣ 스테핑 모터 작동 (똥 치우기)
   ├── 앞으로 3바퀴 회전 (6144 스텝)
   ├── 1초 대기
   └── 원위치 복귀 (-6144 스텝)
```

### 시스템 상태 관리
- **정상 상태**: 청소 명령 수행 가능
- **긴급 정지**: 모든 모터 즉시 정지
- **청소 카운터**: 최대 100회 청소 제한
- **에러 처리**: 센서 오류 시 기본값 반환

## 📡 통신 프로토콜

### 시리얼 통신 설정
- **Baud Rate**: 115200
- **Data Bits**: 8
- **Stop Bits**: 1
- **Parity**: None
- **Buffer Size**: 512 bytes

### JSON 명령어 형식
```json
{
  "command": "명령어_타입",
  "value": 매개변수_값
}
```

### 지원 명령어 목록

#### 🌡️ 센서 데이터
```json
// 온습도 데이터 요청
{"command": "get_sensor_data"}

// 응답 예시
{
  "temperature": 23.5,
  "humidity": 58.0,
  "stepPosition": 0,
  "stepperSpeed": 10,
  "stepperRunning": false,
  "timestamp": 12345678
}
```

#### 💡 LED 제어
```json
{"command": "led_on"}     // LED 켜기
{"command": "led_off"}    // LED 끄기
```

#### 🔄 스테핑 모터 제어
```json
{"command": "stepper_move", "value": 2048}    // 2048스텝 이동
{"command": "stepper_speed", "value": 15}     // 속도 15 RPM 설정
{"command": "stepper_stop"}                   // 모터 정지
{"command": "stepper_reset"}                  // 위치 초기화
{"command": "stepper_disable"}                // 모터 비활성화
```

#### 🧹 청소 시스템
```json
{"command": "cage_cleaning"}        // 전체 청소 프로세스 실행
{"command": "cleaning_servo"}       // 서보모터만 작동
{"command": "reset_cleaning_cycles"} // 청소 횟수 초기화
```

#### 🚨 안전 시스템
```json
{"command": "emergency_reset"}      // 긴급 정지 해제
{"command": "system_test"}          // 하드웨어 테스트
```

### 상태 메시지
```json
// 시스템 상태 정보
{
  "status": "ready",
  "emergency_stop": false,
  "cleaning_cycles": 5,
  "cleaning_servo_active": false,
  "last_cleaning": 1234567890,
  "free_memory": 1234
}
```

## 🔧 설정 및 튜닝

### 모터 설정 상수
```cpp
// 스테핑 모터 설정
const byte DEFAULT_SPEED = 10;        // 기본 속도 (RPM)
const byte CLEANING_SPEED = 12;       // 청소 속도 (RPM)
const int CLEANING_ROTATIONS = 3;     // 청소 시 회전 수
const int CLEANING_DELAY = 1000;      // 청소 단계 간 대기

// 서보모터 설정
const int SERVO_90_PULSE = 1500;      // 90도 PWM 신호
const int SERVO_0_PULSE = 1000;       // 0도 PWM 신호
const byte SERVO_REPEAT_COUNT = 20;   // 반복 횟수
const int SERVO_HOLD_TIME = 1000;     // 위치 유지 시간
```

### 센서 설정
```cpp
const unsigned long SENSOR_UPDATE_INTERVAL = 3000;  // 3초마다 자동 전송
const unsigned long EMERGENCY_REPORT_INTERVAL = 5000; // 긴급 상태 5초마다 보고
```

## 🎵 부저 및 LED 신호

### 시작 신호
- **LED**: 3회 깜빡임
- **부저**: 1000Hz, 200ms

### 청소 완료 신호
- **부저**: 1200Hz, 300ms

### 시스템 테스트 신호
- **LED**: 2회 깜빡임
- **부저**: 800Hz → 1200Hz (각 100ms)

## 🔍 문제 해결

### 일반적인 문제

#### 1. 업로드 실패
```bash
# 포트 확인
ls /dev/ttyUSB* /dev/ttyACM*

# 권한 설정
sudo usermod -a -G dialout $USER

# 다른 프로그램에서 포트 사용 중이면 종료
sudo lsof | grep ttyUSB
```

#### 2. 시리얼 통신 안됨
```cpp
// 시리얼 모니터에서 확인
Arduino Ready for Raspberry Pi Communication
DHT11 Sensor and ULN2003 Stepper Motor Control Available
Bird Cage Toilet Cleaning System Enabled
Emergency Stop System Active
```

#### 3. DHT11 센서 오류
- 연결 확인: VCC(5V), DATA(2번핀), GND
- 센서 교체 고려
- 에러 시 기본값(-999) 반환

#### 4. 스테핑 모터 작동 안됨
- ULN2003 전원 연결 확인 (5V)
- 핀 연결 확인: IN1(5), IN2(6), IN3(7), IN4(8)
- 모터와 드라이버 연결 확인

#### 5. 서보모터 작동 안됨  
- 전원 확인 (5V)
- 신호선 연결 확인 (9번 핀)
- PWM 신호 확인

### 디버깅 방법

#### 시리얼 모니터 활용
```bash
# PlatformIO 시리얼 모니터
platformio device monitor

# 또는 screen 사용
screen /dev/ttyUSB0 115200
```

#### 메모리 사용량 확인
```json
{"command": "get_sensor_data"}
// 응답에서 free_memory 값 확인
```

#### 시스템 테스트
```json
{"command": "system_test"}
// LED 깜빡임과 부저음으로 하드웨어 상태 확인
```

## 📊 성능 정보

### 메모리 사용량
- **프로그램 메모리**: ~15KB / 32KB
- **SRAM**: ~1.2KB / 2KB  
- **여유 SRAM**: ~800 bytes

### 응답 시간
- **센서 데이터**: ~10ms
- **LED 제어**: ~1ms
- **스테핑 모터**: ~5ms (명령 수신)
- **전체 청소**: ~45초

### 전력 소비
- **대기 상태**: ~150mA
- **청소 중**: ~600mA (스테핑 모터 작동 시)

## 🔄 업데이트 및 유지보수

### 정기 점검 사항
1. **하드웨어 연결 상태** (주 1회)
2. **센서 정확도 확인** (월 1회)  
3. **모터 동작 점검** (월 1회)
4. **긴급 정지 버튼 테스트** (월 1회)

### 펌웨어 업데이트
```bash
# 최신 코드 받기
git pull origin main

# 빌드 및 업로드
platformio run --target upload
```

### 백업 및 복원
```bash
# 설정 백업
cp platformio.ini platformio.ini.backup

# 펌웨어 백업 (hex 파일)
cp .pio/build/uno/firmware.hex firmware_backup.hex
```

## 🔗 관련 문서

- **하드웨어 연결**: `HARDWARE_CONNECTION.md`
- **라즈베리파이 코드**: `../Raspberrypi/`
- **전체 시스템**: `../README.md`
- **PlatformIO 문서**: https://docs.platformio.org/

## 🆕 버전 정보

### v1.3.1 (현재) - Bird Cage Toilet Cleaning System
- 새장 화장실 청소 시스템으로 완전 전환
- 3단계 청소 프로세스 구현
- JSON 기반 통신 프로토콜 안정화
- 긴급 정지 시스템 강화
- 메모리 최적화 및 성능 개선

### v1.2.0  
- YOLOv11s 연동 최적화
- 스테핑 모터 정밀도 향상
- DHT11 센서 안정성 개선

### v1.1.0
- 기본 청소 시스템 구현
- 시리얼 통신 프로토콜 확립

---

**🎉 Arduino 기반 스마트 새장 화장실 청소 시스템으로 자동화된 환경을 만나보세요!** 

## 📞 기술 지원

Arduino 펌웨어 관련 문의사항이나 하드웨어 연결 문제가 있으시면 언제든지 연락해주세요.

**💡 팁**: 라즈베리파이와의 연동은 `../Raspberrypi/clean_ver/` 폴더의 최신 클라이언트를 사용하세요! 