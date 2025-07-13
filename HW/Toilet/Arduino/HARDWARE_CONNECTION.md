# 🔌 새장 화장실 자동 청소 시스템 - 하드웨어 연결 가이드

**라즈베리파이 4 + Arduino Uno 기반 MG996R 360도 서보모터 청소 시스템**

AI 새똥 탐지 및 자동 청소 시스템의 완전한 하드웨어 연결 및 설치 가이드입니다.

> 📖 **전체 프로젝트 개요**: [`../../../README.md`](../../../README.md)  
> 📖 **하드웨어 전체 가이드**: [`../README.md`](../README.md)  
> 📖 **Arduino 펌웨어 가이드**: [`README.md`](README.md)  
> 📖 **라즈베리파이 시스템**: [`../Raspberrypi/README.md`](../Raspberrypi/README.md)

## 🎯 실제 구현된 시스템 구성

### 🔗 전체 연결 구조 (main.cpp 기준)
```
┌─────────────────────────────────────────────────────────────────┐
│                    라즈베리파이 4 (메인 시스템)                    │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│ │   PI 카메라     │  │   YOLO 커스텀   │  │   시스템 제어   │ │
│ │   (CSI 포트)    │  │   모델 탐지     │  │   (Python)      │ │
│ └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                 │               │
│                                        GPIO 14/15 (UART)       │
└─────────────────────────────────────────────────┼───────────────┘
                                                  │
                                            시리얼 통신
                                            (115200 baud)
                                                  │
┌─────────────────────────────────────────────────┼───────────────┐
│                   Arduino Uno (하드웨어 제어)   │               │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│ │   DHT11 센서    │  │   MG996R 360도  │  │   긴급 정지     │ │
│ │   (D2)          │  │   서보모터 (D9) │  │   버튼 (D3)     │ │
│ │   온습도 측정   │  │   청소 장치     │  │   안전 시스템   │ │
│ └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                               │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│ │   쓰레기통      │  │   상태 LED      │  │   알림 부저     │ │
│ │   비우기 (D4)   │  │   (D13)         │  │   (D11)         │ │
│ └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 📋 실제 사용된 하드웨어 (main.cpp 기준)

### 🖥️ 메인 시스템
| 부품 | 모델 | 수량 | 용도 |
|------|------|------|------|
| 라즈베리파이 4 | 4GB 이상 권장 | 1 | AI 탐지 및 시스템 제어 |
| MicroSD 카드 | 64GB 이상, Class 10 | 1 | 운영체제 및 데이터 저장 |
| 전원 어댑터 | 5V 3A USB-C | 1 | 라즈베리파이 전원 공급 |
| PI 카메라 모듈 | v2/v3 (1080p) | 1 | 새똥 탐지 영상 입력 |
| 카메라 케이블 | 15핀 CSI | 1 | 카메라 ↔ 라즈베리파이 연결 |

### 🔧 하드웨어 제어 (실제 구현)
| 부품 | 모델 | 수량 | 용도 |
|------|------|------|------|
| Arduino Uno | R3 | 1 | 하드웨어 제어 보드 |
| DHT11 센서 | 온습도 센서 | 1 | 환경 모니터링 |
| **MG996R 서보모터** | **360도 연속회전 서보** | **1** | **청소 장치 (메인)** |

### 🚨 안전 및 상태 표시 (실제 구현)
| 부품 | 모델 | 수량 | 용도 |
|------|------|------|------|
| 긴급 정지 버튼 | 택트 스위치 | 1 | 긴급 정지 (D3) |
| 쓰레기통 비우기 버튼 | 택트 스위치 | 1 | 쓰레기통 관리 (D4) |
| LED | 5mm 빨간색 | 1 | 시스템 상태 표시 (D13) |
| 부저 | 액티브 부저 | 1 | 알림음 (D11) |

### 🔌 연결 부품
| 부품 | 수량 | 용도 |
|------|------|------|
| 점퍼 와이어 (M-M) | 15개 | Arduino 내부 연결 |
| 점퍼 와이어 (M-F) | 5개 | 센서 연결 |
| 브레드보드 | 1개 | 프로토타이핑 |
| 저항 10kΩ | 3개 | 풀업 저항 (DHT11, 버튼 2개) |
| 저항 220Ω | 1개 | LED 전류 제한 |

## 🔌 실제 핀 배치 (main.cpp 정확한 구현)

### 📍 Arduino Uno 핀 사용 현황
| 핀 번호 | 부품 | 기능 | 코드 상의 정의 |
|---------|------|------|----------------|
| **D2** | DHT11 센서 | 온습도 데이터 읽기 | `#define DHTPIN 2` |
| **D3** | 긴급 정지 버튼 | 인터럽트 (풀업 저항) | `#define EMERGENCY_STOP_PIN 3` |
| **D4** | 쓰레기통 비우기 버튼 | 디지털 입력 (풀업 저항) | `#define TRASH_EMPTY_BUTTON_PIN 4` |
| **D9** | **MG996R 360도 서보모터** | **PWM 신호 (청소 장치)** | `#define CLEANING_SERVO_PIN 9` |
| **D11** | 알림 부저 | PWM 신호 (상태 알림음) | `#define BUZZER_PIN 11` |
| **D13** | 상태 LED | 디지털 출력 (시스템 상태) | `#define STATUS_LED_PIN 13` |

### 📊 전원 연결 정리
| 전원 | 연결 부품 |
|------|----------|
| **5V** | DHT11 VCC, MG996R VCC, 풀업 저항 |
| **GND** | DHT11 GND, MG996R GND, 버튼 2개, LED, 부저 |

## 🔄 MG996R 360도 서보모터 청소 시스템 (실제 구현)

### 🎯 청소 프로세스 (main.cpp `performCageCleaning()`)
```
1단계: 앞으로 3초 회전
├── PWM 신호: 1700us
├── 지속 시간: 3초
└── 코드: controlServo(1)

2단계: 뒤로 3초 회전  
├── PWM 신호: 1300us
├── 지속 시간: 3초
└── 코드: controlServo(-1)

3단계: 정지
├── PWM 신호: 1500us
├── 청소 카운터 증가
└── 코드: stopServo()
```

### 🔧 PWM 신호 제어 (main.cpp 기준)
```cpp
// 서보모터 제어 상수 (ServoConfig namespace)
const int SERVO_STOP = 1500;           // 정지 위치 (1500us)
const int SERVO_FORWARD = 1700;        // 앞으로 회전 (1700us)
const int SERVO_BACKWARD = 1300;       // 뒤로 회전 (1300us)
const unsigned long CLEANING_DURATION = 3000;  // 청소 시간 (3초)
```

## 🗑️ 쓰레기통 관리 시스템 (실제 구현)

### 📊 10회 청소 후 관리 (main.cpp 기준)
```cpp
// 10번 청소 후 쓰레기통 가득 참 상태로 설정
if (systemStatus.cleaning_cycles >= 10) {
    systemStatus.trash_full = true;
    Serial.println(F("{\"alert\":\"TRASH_FULL_AFTER_10_CLEANINGS\"}"));
}
```

### 🔄 쓰레기통 비우기 프로세스
1. **10번 청소 완료** → 자동으로 `trash_full = true`
2. **쓰레기통 비우기 버튼 (D4) 누름** → `handleTrashEmptyButton()`
3. **청소 카운터 리셋** → `cleaning_cycles = 0`
4. **시스템 재시작** → 정상 청소 재개

## 🔌 상세 연결 가이드

### 1️⃣ 라즈베리파이 4 설정

#### 📦 라즈베리파이 준비
```bash
# 1. Raspberry Pi OS 설치 (Raspberry Pi Imager 사용)
# 2. SSH 및 카메라 활성화
sudo raspi-config
# 3 Interface Options → I1 Camera → Yes
# 3 Interface Options → I2 SSH → Yes

# 3. 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 4. 필수 패키지 설치
sudo apt install -y python3-picamera2 libcamera-apps python3-dev
```

#### 📷 PI 카메라 모듈 연결
```
PI 카메라 모듈 → 라즈베리파이 CSI 포트 (Camera Serial Interface)
```

**연결 방법:**
1. 라즈베리파이 전원 끄기
2. CSI 포트의 플라스틱 클립 들어올리기
3. 카메라 플렉스 케이블의 **금속 접점이 아래를 향하도록** 삽입
4. 플라스틱 클립 다시 눌러서 고정
5. 전원 켜기

**카메라 테스트:**
```bash
# 카메라 연결 확인
libcamera-hello --timeout 5000

# 사진 촬영 테스트
libcamera-still -o test.jpg
```

### 2️⃣ Arduino Uno 연결

#### 🔗 라즈베리파이 ↔ Arduino 연결
```
라즈베리파이 → Arduino
GPIO 14 (TXD) → RX (D0)
GPIO 15 (RXD) → TX (D1)
GND → GND (공통 접지)
```

**시리얼 통신 설정:**
```bash
# 시리얼 포트 확인
ls -la /dev/serial*

# 권한 설정
sudo usermod -a -G dialout $USER

# 부팅 시 시리얼 콘솔 비활성화
sudo raspi-config
# 3 Interface Options → I6 Serial Port → No (로그인 shell) → Yes (시리얼 포트 하드웨어)
```

### 3️⃣ DHT11 온습도 센서 연결 (D2)

#### 📊 DHT11 센서 → Arduino 연결
```
DHT11 센서     Arduino Uno
┌─────────┐   ┌─────────────┐
│   VCC   │──→│     5V      │
│   DATA  │──→│Digital Pin 2│ (10kΩ 풀업 저항 연결)
│   GND   │──→│     GND     │
└─────────┘   └─────────────┘
```

**풀업 저항 연결:**
```
Digital Pin 2 ──┬── DHT11 DATA
                │
               10kΩ
                │
               5V
```

### 4️⃣ MG996R 360도 서보모터 연결 (D9) - 메인 청소 장치

#### 🔄 MG996R 서보모터 → Arduino 연결
```
MG996R 서보모터  Arduino Uno
┌─────────────┐  ┌─────────────┐
│   VCC (빨강) │←─│     5V      │
│   GND (갈색) │←─│     GND     │
│ Signal (주황)│←─│Digital Pin 9│
└─────────────┘  └─────────────┘
```

**MG996R 360도 서보모터 사양:**
- **토크**: 13kg·cm (4.8V), 15kg·cm (6.0V)
- **속도**: 0.19sec/60° (4.8V), 0.15sec/60° (6.0V)
- **전원**: 4.8V-7.2V
- **제어**: 1000-2000μs PWM (20ms 주기)
- **회전**: 연속 회전 가능

**실제 구현된 PWM 제어 (main.cpp):**
- **1700us**: 앞으로 회전 (3초간)
- **1300us**: 뒤로 회전 (3초간)
- **1500us**: 정지

### 5️⃣ 안전 및 상태 표시 장치 연결

#### 🚨 긴급 정지 버튼 연결 (D3)
```
긴급 정지 버튼   Arduino Uno
┌─────────────┐ ┌─────────────┐
│   한쪽 핀   │─┬─│Digital Pin 3│ (인터럽트 핀)
│            │ │ │            │
│   다른 핀   │─┼─│     GND     │
│            │ │ │            │
└─────────────┘ │ └─────────────┘
                │
               10kΩ (풀업 저항)
                │
               5V
```

#### 🗑️ 쓰레기통 비우기 버튼 연결 (D4)
```
쓰레기통 버튼    Arduino Uno
┌─────────────┐ ┌─────────────┐
│   한쪽 핀   │─┬─│Digital Pin 4│
│            │ │ │            │
│   다른 핀   │─┼─│     GND     │
│            │ │ │            │
└─────────────┘ │ └─────────────┘
                │
               10kΩ (풀업 저항)
                │
               5V
```

#### 💡 상태 LED 연결 (D13)
```
상태 LED        Arduino Uno
┌─────────────┐ ┌─────────────┐
│   애노드(+) │←┤220Ω 저항├──│Digital Pin 13│
│   캐소드(-) │←────────────│     GND     │
└─────────────┘ └─────────────┘
```

#### 🔊 알림 부저 연결 (D11)
```
알림 부저       Arduino Uno
┌─────────────┐ ┌─────────────┐
│   양극(+)   │←──│Digital Pin 11│
│   음극(-)   │←──│     GND     │
└─────────────┘ └─────────────┘
```

## 🔬 연결 테스트 및 검증

### 1️⃣ 하드웨어 테스트 순서

#### 📋 라즈베리파이 테스트
```bash
# 1. 카메라 연결 확인
libcamera-hello --timeout 3000

# 2. 시리얼 통신 확인
ls -la /dev/serial*

# 3. GPIO 핀 상태 확인
gpio readall
```

#### 🔌 Arduino 테스트
```bash
# 1. Arduino 연결 확인
ls /dev/ttyUSB* /dev/ttyACM*

# 2. 펌웨어 업로드
cd /home/parrot1/gongdol/Inventon_Gongdol/HW/Toilet/Arduino
platformio run --target upload

# 3. 시리얼 모니터
platformio device monitor
```

### 2️⃣ 개별 부품 테스트 (JSON 명령어)

#### 🌡️ DHT11 센서 테스트
```json
예상 시리얼 출력:
{
  "temperature": 25.5,
  "humidity": 60.2,
  "servoRunning": false,
  "servoDirection": 0,
  "trashFull": false,
  "trashEmptyButtonPressed": false,
  "timestamp": 1234567890
}
```

#### 🔄 MG996R 서보모터 테스트
```bash
# 라즈베리파이에서 테스트 명령 전송
cd /home/parrot1/gongdol/Inventon_Gongdol/HW/Toilet/Raspberrypi
python uart_test.py

# 또는 직접 명령 전송
echo '{"command": "cage_cleaning"}' > /dev/serial0

# 개별 방향 테스트
echo '{"command": "control_servo", "direction": 1}' > /dev/serial0   # 앞으로
echo '{"command": "control_servo", "direction": -1}' > /dev/serial0  # 뒤로
echo '{"command": "servo_stop"}' > /dev/serial0                      # 정지
```

#### 🗑️ 쓰레기통 관리 테스트
```bash
# 청소 횟수 초기화
echo '{"command": "reset_cleaning_cycles"}' > /dev/serial0

# 쓰레기통 비우기 버튼 테스트
echo '{"command": "trash_empty_button"}' > /dev/serial0
```

## 🎯 실제 시스템 동작 (main.cpp 기준)

### 🔄 청소 프로세스 흐름
```
새똥 탐지 (라즈베리파이)
        ↓
{"command": "cage_cleaning"} 전송
        ↓
1단계: MG996R 앞으로 3초 (1700us PWM)
        ↓
2단계: MG996R 뒤로 3초 (1300us PWM)  
        ↓
3단계: 정지 (1500us PWM)
        ↓
청소 카운터 증가 (cleaning_cycles++)
        ↓
10회 달성 시 trash_full = true
        ↓
쓰레기통 비우기 버튼 대기
```

### 📊 시스템 상태 모니터링
```json
시스템 상태 JSON 응답:
{
  "status": "ready",
  "emergency_stop": false,
  "cleaning_cycles": 5,
  "cleaning_servo_active": false,
  "last_cleaning": 1234567890,
  "trash_full": false,
  "free_memory": 1500
}
```

## ⚠️ 주의사항 및 안전 가이드

### 🔒 전기 안전
- ⚡ **전원 차단 후 연결 작업 필수**
- 🔌 **극성 확인**: VCC(+), GND(-) 올바른 연결
- 🛡️ **단락 방지**: 와이어 절연 상태 확인
- 🔋 **전류 제한**: LED는 반드시 저항과 함께 연결
- ⚠️ **MG996R 전원**: 충분한 전류 공급 (최소 1A 권장)

### 🔧 기계적 안전
- 🔩 **서보모터 고정**: MG996R 진동으로 인한 이탈 방지
- 📷 **카메라 고정**: 흔들림으로 인한 탐지 오류 방지
- 🔌 **케이블 정리**: 동물이 케이블에 걸리지 않도록 정리
- 🛠️ **정기 점검**: 나사 풀림, 케이블 마모 등 확인

### 💡 성능 최적화
- 🌡️ **방열판 부착**: 라즈베리파이 CPU 과열 방지
- ⚡ **안정적 전원**: 5V 3A 이상 고품질 전원 어댑터 사용
- 🔌 **공통 접지**: 모든 GND를 한 점에서 연결하여 노이즈 감소
- 📶 **케이블 길이**: 신호 손실 최소화를 위해 최단 거리 연결

## 🔍 문제 해결 가이드

### 📷 PI 카메라 문제

#### 카메라 인식 안됨
```bash
# 카메라 상태 확인
vcgencmd get_camera

# 카메라 인터페이스 활성화
sudo raspi-config
# 3 Interface Options → I1 Camera → Yes

# 권한 확인
sudo usermod -a -G video $USER
sudo reboot
```

### 🔌 Arduino 통신 문제

#### 시리얼 포트 인식 안됨
```bash
# 포트 확인
ls -la /dev/serial* /dev/ttyUSB* /dev/ttyACM*

# 권한 설정
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/serial0

# 통신 테스트
echo '{"command": "get_sensor_data"}' > /dev/serial0
```

### 🔄 MG996R 서보모터 문제

#### 서보모터 동작 안됨
- **전원 공급 확인**: 5V 충분한 전류 (1A 이상)
- **신호선 연결**: Digital Pin 9 연결 확인
- **PWM 신호 확인**: 1000-2000μs 범위 신호

#### 서보모터 떨림 현상
```cpp
// 코드에서 확인할 설정
const int SERVO_CYCLE_TIME = 20;       // PWM 주기 (20ms)
const unsigned long CLEANING_DURATION = 3000;  // 청소 시간 (3초)
```

### 🌡️ DHT11 센서 문제

#### 센서 데이터 읽기 실패
- **전원 공급 확인**: 5V 안정적 공급
- **데이터 핀 연결**: Digital Pin 2 연결 확인
- **풀업 저항**: 10kΩ 저항 연결 확인

### 🚨 버튼 문제

#### 긴급 정지 버튼 인식 안됨
```cpp
// 풀업 저항 설정 확인 (코드)
pinMode(EMERGENCY_STOP_PIN, INPUT_PULLUP);

// 버튼 상태 확인
if (digitalRead(EMERGENCY_STOP_PIN) == LOW) {
    // 긴급 정지 동작
}
```

## 🎉 최종 시스템 통합 테스트

### ✅ 단계별 테스트 체크리스트

#### 1단계: 하드웨어 연결 점검
- [ ] 모든 전원 연결 확인 (5V, GND)
- [ ] 시리얼 통신 연결 확인 (GPIO 14/15)
- [ ] DHT11 센서 연결 확인 (D2)
- [ ] MG996R 서보모터 연결 확인 (D9)
- [ ] 안전 버튼 연결 확인 (D3, D4)
- [ ] 상태 표시 장치 연결 확인 (D11, D13)

#### 2단계: 펌웨어 업로드
```bash
cd /home/parrot1/gongdol/Inventon_Gongdol/HW/Toilet/Arduino
platformio run --target upload
```

#### 3단계: 시스템 실행
```bash
cd /home/parrot1/gongdol/Inventon_Gongdol/HW/Toilet/Raspberrypi
uv run clean-system
```

#### 4단계: 기능 검증
- [ ] 카메라 영상 정상 출력
- [ ] AI 새똥 탐지 동작
- [ ] 시리얼 통신 데이터 수신
- [ ] MG996R 앞으로 회전 (1700us)
- [ ] MG996R 뒤로 회전 (1300us)
- [ ] MG996R 정지 (1500us)
- [ ] 긴급 정지 버튼 동작
- [ ] 쓰레기통 비우기 버튼 동작
- [ ] 10회 청소 후 쓰레기통 가득 참 알림
- [ ] 상태 LED 및 부저 동작

## 📁 관련 문서 및 리소스

### 📖 프로젝트 문서
- **전체 프로젝트 개요**: [`../../../README.md`](../../../README.md)
- **하드웨어 전체 가이드**: [`../README.md`](../README.md)
- **Arduino 펌웨어**: [`README.md`](README.md)
- **라즈베리파이 시스템**: [`../Raspberrypi/README.md`](../Raspberrypi/README.md)

### 🔧 기술 참고 자료
- **Arduino 공식 문서**: https://www.arduino.cc/reference/en/
- **라즈베리파이 공식 문서**: https://www.raspberrypi.org/documentation/
- **DHT11 센서 라이브러리**: https://github.com/adafruit/DHT-sensor-library
- **MG996R 서보모터 가이드**: https://components101.com/servo-motor-basics-pinout-datasheet

---

**🎯 하드웨어 연결 목표**: MG996R 360도 서보모터 기반 안정적 청소 시스템 구축  
**🛠️ 지원 환경**: Arduino IDE 1.8.19+, PlatformIO Core 6.0+, Raspberry Pi OS  
**📌 펌웨어 버전**: v1.3.1 (Bird Cage Toilet Cleaning System) 