#include <Arduino.h>  // Arduino 헤더 파일
#include <ArduinoJson.h>  // JSON 라이브러리
#include <DHT.h>  // DHT 센서 라이브러리
#include <Stepper.h>  // 스테핑 모터 라이브러리
#include "functions.h"  // 함수 헤더 파일

// 시스템 정보
#define SYSTEM_VERSION "1.3.0"
#define SYSTEM_NAME "Bird Cage Toilet Cleaning System"

// 통신 관련 변수들
const unsigned long BAUD_RATE = 115200UL;  // 통신 속도
const unsigned int BUFFER_SIZE = 512U;  // 버퍼 크기
char inputBuffer[BUFFER_SIZE];  // 입력 버퍼
int bufferIndex = 0;  // 버퍼 인덱스

// DHT11 센서 설정
#define DHTPIN 2        // DHT11 센서 연결 핀
#define DHTTYPE DHT11   // DHT11 센서 타입
DHT dht(DHTPIN, DHTTYPE);  // DHT 센서 객체 생성

// ULN2003 + 28BYJ-48 스테핑 모터 설정
#define STEPS_PER_REVOLUTION 2048  // 28BYJ-48의 한 바퀴 스텝 수 (기어비 64:1 적용)
#define STEPPER_PIN1 5    // ULN2003 IN1 핀
#define STEPPER_PIN2 6    // ULN2003 IN2 핀
#define STEPPER_PIN3 7    // ULN2003 IN3 핀
#define STEPPER_PIN4 8    // ULN2003 IN4 핀

// 청소 시스템 하드웨어 핀 설정
#define CLEANING_SERVO_PIN 9      // 청소 서보모터 핀 (모래 밀어내기)
#define EMERGENCY_STOP_PIN 3      // 긴급 정지 버튼 핀 (인터럽트 핀)
#define STATUS_LED_PIN 13         // 상태 LED 핀
#define BUZZER_PIN 11             // 부저 핀

// 청소 시스템 설정값
#define CLEANING_SERVO_ANGLE 90   // 청소 서보 각도
#define CLEANING_SERVO_DURATION 2000  // 청소 서보 작동 시간 (ms)
#define MAX_CLEANING_CYCLES 100   // 최대 청소 횟수 (새장 화장실용)

// 스테핑 모터 객체 생성 (ULN2003 핀 순서: IN1, IN3, IN2, IN4)
Stepper stepper(STEPS_PER_REVOLUTION, STEPPER_PIN1, STEPPER_PIN3, STEPPER_PIN2, STEPPER_PIN4);

// 시스템 상태 구조체
struct SystemStatus {
  bool emergency_stop;          // 긴급 정지 상태
  bool cleaning_servo_active;   // 청소 서보 작동 상태
  int cleaning_cycles;          // 청소 횟수
  unsigned long last_cleaning;  // 마지막 청소 시간
  unsigned long system_uptime;  // 시스템 가동 시간
};

// 센서 데이터 구조체
struct SensorData {
  float temperature;  // 온도
  float humidity;  // 습도
  long stepPosition;  // 현재 스텝 위치
  int stepperSpeed;  // 스테핑 모터 속도 (RPM)
  bool stepperRunning;  // 스테핑 모터 실행 여부
  unsigned long timestamp;  // 데이터 수집 시간
};

SensorData sensorData;  // 센서 데이터 구조체 인스턴스
SystemStatus systemStatus;  // 시스템 상태 구조체 인스턴스

// JSON 문서 생성
JsonDocument doc;  // JSON 문서 객체 생성

// 함수 선언
void readSensorData();  // 센서 데이터 읽기
void sendSensorData();  // 센서 데이터 전송
void sendStatus();  // 상태 정보 전송
void processCommand(const char* command);  // 명령 처리
void setLED(int state);  // LED 제어
void moveStepper(int steps, int speed);  // 스테핑 모터 이동
void stopStepper();  // 스테핑 모터 정지
void setStepperSpeed(int speed);  // 스테핑 모터 속도 설정
void resetStepperPosition();  // 스테핑 모터 위치 초기화
void disableStepperPins();  // 스테핑 모터 핀 비활성화 (전력 절약)
void performCageCleaning();  // 새장 화장실 청소 수행
void activateCleaningServo();  // 청소 서보 작동 (모래 밀어내기)
void handleEmergencyStop();  // 긴급 정지 처리
void playBuzzer(int frequency, int duration);  // 부저 소리
void blinkStatusLED(int times);  // 상태 LED 깜빡임
int freeMemory();  // 사용 가능한 메모리 반환

void setup() {  // 설정
  // 시리얼 통신 초기화
  Serial.begin(BAUD_RATE);  // 통신 속도 설정
  
  // DHT11 센서 초기화
  dht.begin();  // DHT 센서 초기화
  
  // 핀 모드 설정
  pinMode(CLEANING_SERVO_PIN, OUTPUT);      // 청소 서보 핀 출력 설정
  pinMode(STATUS_LED_PIN, OUTPUT);          // 상태 LED 핀 출력 설정
  pinMode(BUZZER_PIN, OUTPUT);              // 부저 핀 출력 설정
  pinMode(EMERGENCY_STOP_PIN, INPUT_PULLUP);  // 긴급 정지 핀 풀업 입력 설정
  
  // 긴급 정지 인터럽트 설정
  attachInterrupt(digitalPinToInterrupt(EMERGENCY_STOP_PIN), handleEmergencyStop, FALLING);
  
  // 출력 핀 초기화
  digitalWrite(CLEANING_SERVO_PIN, LOW);
  digitalWrite(STATUS_LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);
  
  // ULN2003 스테핑 모터 초기 속도 설정 (기본 10 RPM)
  stepper.setSpeed(10);  // 28BYJ-48에 적합한 속도
  
  // 초기 데이터 설정
  sensorData.temperature = 0.0;  // 온도 초기값
  sensorData.humidity = 0.0;  // 습도 초기값
  sensorData.stepPosition = 0;  // 스텝 위치 초기값
  sensorData.stepperSpeed = 10;  // 스테핑 모터 속도 초기값 (RPM)
  sensorData.stepperRunning = false;  // 스테핑 모터 실행 여부 초기값
  sensorData.timestamp = millis();  // 데이터 수집 시간 초기값
  
  // 시스템 상태 초기화
  systemStatus.emergency_stop = false;
  systemStatus.cleaning_servo_active = false;
  systemStatus.cleaning_cycles = 0;
  systemStatus.last_cleaning = 0;
  systemStatus.system_uptime = millis();
  
  // 시스템 시작 알림
  blinkStatusLED(3);  // 3번 깜빡임
  playBuzzer(1000, 200);  // 부저 소리
  
  Serial.println("=== " + String(SYSTEM_NAME) + " v" + String(SYSTEM_VERSION) + " ===");
  Serial.println("Arduino Ready for Raspberry Pi Communication");
  Serial.println("DHT11 Sensor and ULN2003 Stepper Motor Control Available");
  Serial.println("Bird Cage Toilet Cleaning System Enabled");
  Serial.println("Emergency Stop System Active");
  
  // 초기 센서 확인
  readSensorData();
}

void loop() {  // 루프
  // 긴급 정지 상태 확인
  if (systemStatus.emergency_stop) {
    // 긴급 정지 상태에서는 센서 데이터만 전송
    static unsigned long lastEmergencyReport = 0;
    if (millis() - lastEmergencyReport > 5000) {  // 5초마다 긴급 정지 상태 보고
      Serial.println("{\"alert\": \"EMERGENCY_STOP_ACTIVE\", \"message\": \"시스템이 긴급 정지 상태입니다.\"}");
      lastEmergencyReport = millis();
    }
    delay(1000);
    return;
  }
  
  // 라즈베리파이로부터 명령 수신
  if (Serial.available()) {
    char incomingChar = Serial.read();  // 수신 문자 읽기
    
    if (incomingChar == '\n') {
      inputBuffer[bufferIndex] = '\0';  // 버퍼 끝 표시
      processCommand(inputBuffer);  // 명령 처리
      bufferIndex = 0;  // 버퍼 인덱스 초기화
    } else if (bufferIndex < BUFFER_SIZE - 1) {
      inputBuffer[bufferIndex] = incomingChar;  // 버퍼에 문자 저장
      bufferIndex++;  // 버퍼 인덱스 증가
    }
  }
  
  // 주기적으로 센서 데이터 전송 (3초마다)
  static unsigned long lastSendTime = 0;
  if (millis() - lastSendTime > 3000) {
    readSensorData();  // 센서 데이터 읽기
    sendSensorData();  // 센서 데이터 전송
    lastSendTime = millis();  // 마지막 전송 시간 업데이트
  }
  
  // 시스템 상태 업데이트
  systemStatus.system_uptime = millis();
  
  delay(100);  // 100ms 대기
}

// 라즈베리파이로부터 받은 명령 처리
void processCommand(const char* command) {  // 명령 처리
  // 긴급 정지 상태에서는 reset_emergency_stop 명령만 처리
  if (systemStatus.emergency_stop && strstr(command, "reset_emergency_stop") == NULL) {
    Serial.println("{\"error\": \"EMERGENCY_STOP_ACTIVE\", \"message\": \"긴급 정지 상태에서는 reset_emergency_stop 명령만 사용 가능합니다.\"}");
    return;
  }
  
  // JSON 파싱
  DeserializationError error = deserializeJson(doc, command);
  
  if (error) {  // JSON 파싱 실패 시
    Serial.println("{\"error\": \"JSON parsing failed\", \"details\": \"" + String(error.c_str()) + "\"}");
    return;  // 함수 종료
  }
  
  // 명령 타입 확인
  const char* cmdType = doc["command"];  // 명령 타입
  
  if (strcmp(cmdType, "get_sensor_data") == 0) {  // 센서 데이터 요청 명령
    readSensorData();  // 센서 데이터 읽기
    sendSensorData();  // 센서 데이터 전송
  }
  else if (strcmp(cmdType, "set_led") == 0) {  // LED 상태 변경 명령
    int ledState = doc["state"];  // LED 상태 확인
    setLED(ledState);  // LED 상태 설정
    Serial.println("{\"response\": \"LED state changed\", \"state\": " + String(ledState) + "}");
  }
  else if (strcmp(cmdType, "move_stepper") == 0) {  // 스테핑 모터 이동 명령
    int steps = doc["steps"];  // 이동할 스텝 수 (양수: 시계방향, 음수: 반시계방향)
    int speed = doc["speed"];  // 속도 (RPM)
    moveStepper(steps, speed);  // 스테핑 모터 이동
    Serial.println("{\"response\": \"Stepper moved\", \"steps\": " + String(steps) + ", \"speed\": " + String(speed) + "}");
  }
  else if (strcmp(cmdType, "set_stepper_speed") == 0) {  // 스테핑 모터 속도 설정 명령
    int speed = doc["speed"];  // 속도 (RPM)
    setStepperSpeed(speed);  // 스테핑 모터 속도 설정
    Serial.println("{\"response\": \"Stepper speed changed\", \"speed\": " + String(speed) + "}");
  }
  else if (strcmp(cmdType, "stop_stepper") == 0) {  // 스테핑 모터 정지 명령
    stopStepper();  // 스테핑 모터 정지
    Serial.println("{\"response\": \"Stepper stopped\"}");
  }
  else if (strcmp(cmdType, "reset_stepper_position") == 0) {  // 스테핑 모터 위치 초기화 명령
    resetStepperPosition();  // 스테핑 모터 위치 초기화
    Serial.println("{\"response\": \"Stepper position reset\"}");
  }
  else if (strcmp(cmdType, "disable_stepper") == 0) {  // 스테핑 모터 핀 비활성화 명령
    disableStepperPins();  // 스테핑 모터 핀 비활성화
    Serial.println("{\"response\": \"Stepper pins disabled\"}");
  }
  else if (strcmp(cmdType, "cage_cleaning") == 0) {  // 새장 화장실 청소 명령
    performCageCleaning();  // 새장 화장실 청소 수행
    Serial.println("{\"response\": \"Cage cleaning completed\", \"cycles\": " + String(systemStatus.cleaning_cycles) + "}");
  }
  else if (strcmp(cmdType, "activate_cleaning_servo") == 0) {  // 청소 서보 작동 명령
    activateCleaningServo();
    Serial.println("{\"response\": \"Cleaning servo activated\"}");
  }
  else if (strcmp(cmdType, "reset_emergency_stop") == 0) {  // 긴급 정지 해제 명령
    systemStatus.emergency_stop = false;
    digitalWrite(STATUS_LED_PIN, LOW);  // 상태 LED 끄기
    Serial.println("{\"response\": \"Emergency stop reset\", \"status\": \"normal\"}");
  }
  else if (strcmp(cmdType, "reset_cleaning_cycles") == 0) {  // 청소 횟수 초기화 명령
    systemStatus.cleaning_cycles = 0;
    Serial.println("{\"response\": \"Cleaning cycles reset\", \"cycles\": 0}");
  }
  else if (strcmp(cmdType, "get_status") == 0) {  // 상태 정보 요청 명령
    sendStatus();  // 상태 정보 전송
  }
  else if (strcmp(cmdType, "system_test") == 0) {  // 시스템 테스트 명령
    Serial.println("{\"response\": \"System test started\"}");
    blinkStatusLED(2);
    playBuzzer(800, 100);
    delay(200);
    playBuzzer(1200, 100);
    Serial.println("{\"response\": \"System test completed\"}");
  }
  else {  // 알 수 없는 명령
    Serial.println("{\"error\": \"Unknown command\", \"received\": \"" + String(cmdType) + "\"}");
  }
}

// DHT11 센서에서 데이터 읽기
void readSensorData() {  // 센서 데이터 읽기
  // 온도 읽기
  float temp = dht.readTemperature();  // 온도 읽기
  if (isnan(temp)) {   // 온도 읽기 실패 시
    sensorData.temperature = -999; // 에러 표시
  } else {  // 온도 읽기 성공 시
    sensorData.temperature = temp;  // 온도 저장
  }
  
  // 습도 읽기
  float hum = dht.readHumidity();  // 습도 읽기
  if (isnan(hum)) {  // 습도 읽기 실패 시
    sensorData.humidity = -999; // 에러 표시
  } else {  // 습도 읽기 성공 시
    sensorData.humidity = hum;  // 습도 저장
  }
  
  sensorData.timestamp = millis();  // 데이터 수집 시간 업데이트
}

// 센서 데이터 전송
void sendSensorData() {  // 센서 데이터 전송
  // JSON으로 데이터 포맷팅
  doc.clear();  
  doc["type"] = "sensor_data";  // 데이터 타입
  doc["temperature"] = sensorData.temperature;  // 온도
  doc["humidity"] = sensorData.humidity;  // 습도
  doc["step_position"] = sensorData.stepPosition;  // 스텝 위치
  doc["stepper_speed"] = sensorData.stepperSpeed;  // 스테핑 모터 속도
  doc["stepper_running"] = sensorData.stepperRunning;  // 스테핑 모터 실행 여부
  doc["timestamp"] = sensorData.timestamp;  // 데이터 수집 시간
  
  // JSON 전송
  serializeJson(doc, Serial);  // JSON 전송
  Serial.println();  // 줄 바꿈
}

// 상태 정보 전송
void sendStatus() {  // 상태 정보 전송
  doc.clear();  // JSON 문서 초기화
  doc["type"] = "status";  // 상태 타입
  doc["system_name"] = SYSTEM_NAME;
  doc["system_version"] = SYSTEM_VERSION;
  doc["uptime"] = systemStatus.system_uptime;  // 실행 시간
  doc["free_memory"] = freeMemory();  // 사용 가능한 메모리
  doc["arduino_ready"] = true;  // Arduino 준비 상태 
  doc["dht11_connected"] = (sensorData.temperature != -999 && sensorData.humidity != -999);  // DHT11 센서 연결 상태
  doc["step_position"] = sensorData.stepPosition;  // 스텝 위치
  doc["stepper_speed"] = sensorData.stepperSpeed;  // 스테핑 모터 속도
  doc["stepper_running"] = sensorData.stepperRunning;  // 스테핑 모터 실행 여부
  
  // 새장 청소 시스템 상태
  doc["emergency_stop"] = systemStatus.emergency_stop;
  doc["cleaning_servo_active"] = systemStatus.cleaning_servo_active;
  doc["cleaning_cycles"] = systemStatus.cleaning_cycles;
  doc["last_cleaning"] = systemStatus.last_cleaning;
  doc["max_cleaning_cycles"] = MAX_CLEANING_CYCLES;
  
  serializeJson(doc, Serial);  // JSON 전송
  Serial.println();  // 줄 바꿈
}

// LED 제어 (핀 13 사용)
void setLED(int state) {  // LED 제어
  pinMode(13, OUTPUT);  // 핀 13 설정
  digitalWrite(13, state);  // 핀 13 상태 설정
}

// ULN2003 스테핑 모터 이동
void moveStepper(int steps, int speed) {  // 스테핑 모터 이동
  if (speed > 0) {  // 속도가 0보다 크면
    setStepperSpeed(speed);  // 속도 설정
  }
  
  sensorData.stepperRunning = true;  // 실행 상태 설정
  
  // 28BYJ-48 + ULN2003 조합에 맞는 스텝 실행
  stepper.step(steps);  // 스텝 이동
  
  sensorData.stepPosition += steps;  // 현재 위치 업데이트
  sensorData.stepperRunning = false;  // 실행 상태 해제
  
  // 이동 완료 후 전력 절약을 위해 핀 비활성화
  disableStepperPins();  // 핀 비활성화
}

// ULN2003 스테핑 모터 정지
void stopStepper() {  // 스테핑 모터 정지
  sensorData.stepperRunning = false;  // 실행 상태 해제
  disableStepperPins();  // 핀 비활성화로 전력 절약
}

// ULN2003 스테핑 모터 속도 설정
void setStepperSpeed(int speed) {  // 스테핑 모터 속도 설정
  // 28BYJ-48 + ULN2003에 적합한 속도 범위 (5-15 RPM 권장)
  speed = constrain(speed, 5, 20);  // 5-20 RPM 범위로 제한
  stepper.setSpeed(speed);  // 속도 설정
  sensorData.stepperSpeed = speed;  // 속도 저장
}

// 스테핑 모터 위치 초기화
void resetStepperPosition() {  // 스테핑 모터 위치 초기화
  sensorData.stepPosition = 0;  // 위치 초기화
}

// ULN2003 스테핑 모터 핀 비활성화 (전력 절약)
void disableStepperPins() {  // 스테핑 모터 핀 비활성화
  digitalWrite(STEPPER_PIN1, LOW);  // IN1 핀 비활성화
  digitalWrite(STEPPER_PIN2, LOW);  // IN2 핀 비활성화
  digitalWrite(STEPPER_PIN3, LOW);  // IN3 핀 비활성화
  digitalWrite(STEPPER_PIN4, LOW);  // IN4 핀 비활성화
}

// 새장 화장실 청소 수행
void performCageCleaning() {
  // 청소 횟수 확인
  if (systemStatus.cleaning_cycles >= MAX_CLEANING_CYCLES) {
    Serial.println("{\"alert\": \"MAX_CLEANING_CYCLES_REACHED\", \"message\": \"최대 청소 횟수에 도달했습니다.\"}");
    return;
  }
  
  Serial.println("{\"info\": \"Bird cage toilet cleaning started\"}");
  
  // 상태 LED 켜기
  digitalWrite(STATUS_LED_PIN, HIGH);
  
  // 1단계: 모래 밀어내기 (청소 서보 작동)
  Serial.println("{\"info\": \"Step 1: Pushing sand with servo\"}");
  activateCleaningServo();
  
  // 2단계: 스테핑 모터로 똥 치우기 (앞으로 이동)
  Serial.println("{\"info\": \"Step 2: Moving stepper to clean poop\"}");
  int cleaningSteps = STEPS_PER_REVOLUTION * 3;  // 3바퀴 회전
  moveStepper(cleaningSteps, 12);
  delay(1000);
  
  // 3단계: 원위치 복귀
  Serial.println("{\"info\": \"Step 3: Returning to original position\"}");
  moveStepper(-cleaningSteps, 12);
  
  // 4단계: 추가 모래 정리
  Serial.println("{\"info\": \"Step 4: Final sand cleanup\"}");
  activateCleaningServo();
  
  // 청소 완료 처리
  systemStatus.cleaning_cycles++;
  systemStatus.last_cleaning = millis();
  
  // 상태 LED 끄기
  digitalWrite(STATUS_LED_PIN, LOW);
  
  // 완료 알림
  playBuzzer(1200, 300);
  
  Serial.println("{\"info\": \"Bird cage toilet cleaning completed\", \"total_cycles\": " + String(systemStatus.cleaning_cycles) + "}");
}

// 청소 서보 작동 (모래 밀어내기)
void activateCleaningServo() {
  systemStatus.cleaning_servo_active = true;
  
  // 서보 모터 PWM 신호 생성 (간단한 구현)
  Serial.println("{\"info\": \"Cleaning servo activated for sand pushing\"}");
  
  // 서보 모터 90도 회전 (모래 밀어내기)
  for (int i = 0; i < 20; i++) {  // 약 2초간 PWM 신호 전송
    digitalWrite(CLEANING_SERVO_PIN, HIGH);
    delayMicroseconds(1500);  // 90도 위치 PWM 신호
    digitalWrite(CLEANING_SERVO_PIN, LOW);
    delay(18);
  }
  
  delay(1000);  // 1초 대기
  
  // 서보 모터 0도 복귀
  for (int i = 0; i < 20; i++) {  // 약 2초간 PWM 신호 전송
    digitalWrite(CLEANING_SERVO_PIN, HIGH);
    delayMicroseconds(1000);  // 0도 위치 PWM 신호
    digitalWrite(CLEANING_SERVO_PIN, LOW);
    delay(18);
  }
  
  systemStatus.cleaning_servo_active = false;
  Serial.println("{\"info\": \"Cleaning servo deactivated\"}");
}

// 긴급 정지 처리 (인터럽트 함수)
void handleEmergencyStop() {
  systemStatus.emergency_stop = true;
  
  // 모든 출력 즉시 정지
  digitalWrite(CLEANING_SERVO_PIN, LOW);
  disableStepperPins();
  
  // 긴급 정지 알림
  digitalWrite(STATUS_LED_PIN, HIGH);  // 상태 LED 켜기
  
  systemStatus.cleaning_servo_active = false;
  sensorData.stepperRunning = false;
  
  Serial.println("{\"alert\": \"EMERGENCY_STOP_TRIGGERED\", \"message\": \"긴급 정지가 작동되었습니다.\"}");
}

// 부저 소리
void playBuzzer(int frequency, int duration) {
  tone(BUZZER_PIN, frequency, duration);
  delay(duration);
  noTone(BUZZER_PIN);
}

// 상태 LED 깜빡임
void blinkStatusLED(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(STATUS_LED_PIN, HIGH);
    delay(200);
    digitalWrite(STATUS_LED_PIN, LOW);
    delay(200);
  }
}

// 사용 가능한 메모리 반환
int freeMemory() {  // 사용 가능한 메모리 반환
  extern int __heap_start, *__brkval;  // 메모리 시작 주소와 브레이크 값
  int v;  // 임시 변수
  return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);  // 사용 가능한 메모리 반환
}