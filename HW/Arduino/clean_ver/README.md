# 🐦 새장 화장실 자동 청소 시스템

**라즈베리파이 + Arduino 기반 YOLOv11s 새똥 탐지 및 자동 청소 시스템**

모래 위의 새똥을 자동으로 탐지하고 청소하는 스마트 새장 화장실 시스템입니다.

## 🎯 프로젝트 개요

### 주요 기능
- **YOLOv11s 기반 새똥 탐지**: 라즈베리파이 카메라로 실시간 탐지
- **자동 청소 시스템**: 모래 밀어내기 + 스테핑 모터 동작
- **3단계 청소 모드**: 간단/표준/집중 청소 자동 선택
- **실시간 모니터링**: 온습도, 청소 상태, 시스템 상태 모니터링
- **안전 기능**: 긴급 정지 버튼, 상태 LED, 알림음

### 시스템 구성
```
🐦 새장 화장실
├── 📷 라즈베리파이 카메라 (새똥 탐지)
├── 🧠 라즈베리파이 4 (YOLOv11s 처리)
├── 🔧 Arduino Uno (하드웨어 제어)
├── 🔄 스테핑 모터 (똥 치우기 이동)
├── 🤖 서보모터 (모래 밀어내기)
└── 📊 센서류 (온습도, 상태 모니터링)
```

## 🔧 하드웨어 구성

### Arduino 연결
| 부품 | 핀 | 기능 |
|------|-----|------|
| DHT11 센서 | 2 | 온습도 측정 |
| ULN2003 드라이버 | 5,6,7,8 | 스테핑 모터 제어 |
| 청소 서보모터 | 9 | 모래 밀어내기 |
| 긴급 정지 버튼 | 3 | 안전 정지 (인터럽트) |
| 상태 LED | 13 | 상태 표시 |
| 부저 | 11 | 알림음 |

### 필수 부품
- **라즈베리파이 4** (4GB 이상 권장)
- **Arduino Uno**
- **28BYJ-48 스테핑 모터 + ULN2003 드라이버**
- **SG90 서보모터** (청소용)
- **DHT11 온습도 센서**
- **라즈베리파이 카메라 모듈**
- **긴급 정지 버튼**
- **LED, 부저**

## 📋 청소 프로세스

### 1. 간단한 청소 (SIMPLE)
- 커버리지 < 10%
- 스테핑 모터로만 똥 치우기
- 소요시간: 약 10초

### 2. 표준 청소 (STANDARD)
- 커버리지 10-30%
- 서보로 모래 밀어내기 + 스테핑 모터
- 소요시간: 약 15초

### 3. 집중 청소 (INTENSIVE)
- 커버리지 > 30%
- 전체 청소 프로세스 + 추가 정리
- 소요시간: 약 25초

## 🚀 설치 및 실행

### 1. 의존성 설치
```bash
# 라즈베리파이에서
pip install -r requirements.txt

# Arduino 라이브러리 설치
# - ArduinoJson
# - DHT sensor library
# - Stepper
```

### 2. 시스템 실행
```bash
# 기본 실행
python3 run_system.py

# 헤드리스 모드 (SSH 접속 시)
python3 run_system.py --headless

# 테스트 모드
python3 run_system.py --test --headless

# 시스템 상태 확인
python3 run_system.py --check-hardware
```

### 3. 설정 조정
`optimized_config.py`에서 다음 설정 조정 가능:
- YOLOv11s 모델 설정
- 청소 임계값 조정
- 메모리 최적화 설정

## 📊 성능 정보

### 라즈베리파이 4 기준
- **YOLOv11s**: 3-5 FPS (4GB), 5-8 FPS (8GB)
- **탐지 정확도**: 95% 이상 (최적화된 모델)
- **청소 성공률**: 90% 이상
- **메모리 사용량**: 2.5-3.5GB

### 자동 최적화
- 메모리 부족 시 자동으로 YOLOv11n 사용
- 해상도 동적 조정
- CPU 온도 모니터링

## 🎮 사용법

### 기본 제어
```python
# 시스템 시작
cleaning_system.run()

# 수동 청소 실행
cleaning_manager.perform_cleaning(coverage_ratio=0.25)

# 긴급 정지 해제
cleaning_manager.emergency_stop()

# 청소 통계 확인
stats = cleaning_manager.get_cleaning_stats()
```

### Arduino 명령어
```python
# 새장 화장실 청소 실행
arduino_client.perform_cage_cleaning()

# 서보모터 작동 (모래 밀어내기)
arduino_client.activate_cleaning_servo()

# 스테핑 모터 이동
arduino_client.move_stepper(steps=2048, speed=12)

# 시스템 상태 확인
status = arduino_client.get_system_status()
```

## 📈 모니터링 및 로깅

### 실시간 정보
- 새똥 탐지 상태
- 청소 진행 상황
- 시스템 온도 및 메모리
- Arduino 연결 상태

### 통계 정보
- 총 청소 횟수
- 청소 성공률
- 모드별 사용 빈도
- 시스템 가동 시간

## 🔒 안전 기능

### 긴급 정지 시스템
- 하드웨어 긴급 정지 버튼
- 인터럽트 기반 즉시 정지
- 모든 모터 즉시 정지

### 상태 모니터링
- 시스템 상태 LED
- 청소 완료 알림음
- 오류 상황 경고음

## 🛠️ 문제 해결

### 일반적인 문제
1. **Arduino 연결 안됨**
   - USB 포트 확인
   - 권한 설정 확인
   - 시리얼 포트 확인

2. **카메라 인식 안됨**
   - 라즈베리파이 카메라 활성화
   - 케이블 연결 확인
   - 권한 설정 확인

3. **메모리 부족**
   - 자동으로 YOLOv11n 사용
   - 해상도 조정
   - 스왑 메모리 활성화

### 시스템 리셋
```bash
# 전체 시스템 리셋
python3 run_system.py --reset

# Arduino 리셋
python3 -c "from factories.system_factory import SystemFactory; factory = SystemFactory(); factory.get_arduino_client().reset_emergency_stop()"
```

## 🔄 업데이트 로그

### v1.3.0 (새장 화장실 청소 시스템)
- 물 관련 기능 제거
- 서보모터 기반 모래 밀어내기 추가
- 3단계 청소 모드 구현
- 새장 화장실 특화 청소 로직

### v1.2.0 (YOLOv11s 지원)
- YOLOv11s 모델 지원
- 메모리 최적화 개선
- 적응형 성능 조정

### v1.1.0 (실행 안정성 개선)
- 헤드리스 모드 지원
- 실제 Arduino 연동
- 실행 스크립트 추가

## 📞 지원 및 문의

시스템 사용 중 문제가 발생하거나 개선 사항이 있으시면 언제든지 연락주세요.

---

**🐦 새장 화장실이 더 깨끗하고 건강한 환경을 만들어드립니다!** 