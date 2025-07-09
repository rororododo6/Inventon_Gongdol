#include <Arduino.h>  // Arduino 헤더 파일
#include <ArduinoJson.h>  // JSON 라이브러리
#include <DHT.h>  // DHT 센서 라이브러리
#include <Stepper.h>  // 스테핑 모터 라이브러리
#include "functions.h"  // 함수 헤더 파일

// ========== 시스템 정보 ==========
const char SYSTEM_VERSION[] PROGMEM = "1.3.1";  // 클린코딩 버전
const char SYSTEM_NAME[] PROGMEM = "Bird Cage Toilet Cleaning System"; // 시스템 이름

// ========== 통신 설정 ==========
const unsigned long BAUD_RATE = 115200; // 통신 속도
const unsigned int BUFFER_SIZE = 512; // 버퍼 크기
char inputBuffer[BUFFER_SIZE]; // 입력 버퍼
unsigned int bufferIndex = 0; // 버퍼 인덱스

// ========== 하드웨어 핀 정의 ==========
// DHT11 센서
#define DHTPIN 2  // DHT11 센서 연결 핀
#define DHTTYPE DHT11  // DHT11 센서 타입

// 스테핑 모터 (ULN2003 + 28BYJ-48)
#define STEPS_PER_REVOLUTION 2048
#define STEPPER_PIN1 5    // IN1
#define STEPPER_PIN2 6    // IN2
#define STEPPER_PIN3 7    // IN3
#define STEPPER_PIN4 8    // IN4

// 청소 시스템 핀
#define CLEANING_SERVO_PIN 9  // 청소 서보 핀
#define EMERGENCY_STOP_PIN 3  // 긴급 정지 핀
#define STATUS_LED_PIN 13  // 상태 LED 핀
#define BUZZER_PIN 11  // 부저 핀

// ========== 시스템 상수 ==========
namespace SystemConfig {
  const byte MAX_CLEANING_CYCLES = 100; // 최대 청소 횟수
  const unsigned long SENSOR_UPDATE_INTERVAL = 3000;  // 3초
  const unsigned long EMERGENCY_REPORT_INTERVAL = 5000;  // 5초
  const unsigned int LOOP_DELAY = 100;  // 100ms
}

namespace ServoConfig {
  const int SERVO_90_PULSE = 1500;    // 90도 위치 PWM
  const int SERVO_0_PULSE = 1000;     // 0도 위치 PWM
  const int SERVO_CYCLE_TIME = 18;    // PWM 주기
  const byte SERVO_REPEAT_COUNT = 20;  // 반복 횟수
  const int SERVO_HOLD_TIME = 1000;   // 위치 유지 시간
}

namespace StepperConfig {
  const byte DEFAULT_SPEED = 10;      // 기본 속도 (RPM)
  const byte MIN_SPEED = 5;           // 최소 속도
  const byte MAX_SPEED = 20;          // 최대 속도
  const byte CLEANING_SPEED = 12;     // 청소 속도
  const int CLEANING_ROTATIONS = 3;   // 청소 시 회전 수
  const int CLEANING_STEPS = STEPS_PER_REVOLUTION * CLEANING_ROTATIONS; // 청소 스텝 수
  const int CLEANING_DELAY = 1000;    // 청소 단계 간 대기
}

namespace BuzzerConfig {
  const int STARTUP_FREQ = 1000;      // 시작 부저 주파수
  const int STARTUP_DURATION = 200;   // 시작 부저 지속시간
  const int COMPLETE_FREQ = 1200;     // 완료 부저 주파수
  const int COMPLETE_DURATION = 300;  // 완료 부저 지속시간
  const int TEST_FREQ1 = 800;         // 테스트 부저 1
  const int TEST_FREQ2 = 1200;        // 테스트 부저 2
  const int TEST_DURATION = 100;      // 테스트 부저 지속시간
}

namespace LEDConfig {
  const byte STARTUP_BLINKS = 3;      // 시작 시 깜빡임 횟수
  const byte TEST_BLINKS = 2;         // 테스트 시 깜빡임 횟수
  const int BLINK_DURATION = 200;     // 깜빡임 지속시간
}

// ========== 전역 객체 ==========
DHT dht(DHTPIN, DHTTYPE); // DHT 센서 객체
Stepper stepper(STEPS_PER_REVOLUTION, STEPPER_PIN1, STEPPER_PIN3, STEPPER_PIN2, STEPPER_PIN4); // 스테핑 모터 객체
JsonDocument doc; // JSON 문서 객체

// ========== 데이터 구조체 ==========
struct SystemStatus {
  bool emergency_stop; // 긴급 정지 상태
  bool cleaning_servo_active; // 청소 서보 작동 상태
  byte cleaning_cycles; // 청소 횟수
  unsigned long last_cleaning; // 마지막 청소 시간
};

struct SensorData {
  float temperature; // 온도
  float humidity; // 습도
  long stepPosition; // 스텝 위치
  byte stepperSpeed; // 스테핑 모터 속도
  bool stepperRunning; // 스테핑 모터 실행 여부
  unsigned long timestamp; // 데이터 수집 시간
};

SystemStatus systemStatus; // 시스템 상태 구조체
SensorData sensorData; // 센서 데이터 구조체

// ========== PROGMEM 문자열 ==========
const char MSG_READY[] PROGMEM = "Arduino Ready for Raspberry Pi Communication"; // 준비 메시지
const char MSG_DHT_STEPPER[] PROGMEM = "DHT11 Sensor and ULN2003 Stepper Motor Control Available"; // DHT11 센서와 스테핑 모터 제어 가능
const char MSG_CAGE_CLEANING[] PROGMEM = "Bird Cage Toilet Cleaning System Enabled"; // 새장 화장실 청소 시스템 활성화
const char MSG_EMERGENCY[] PROGMEM = "Emergency Stop System Active"; // 긴급 정지 시스템 활성화

// ========== 함수 선언 ==========
// 초기화 및 메인 루프
void initializeSystem();  // 시스템 초기화
void initializePins();  // 핀 초기화
void initializeData();  // 데이터 초기화
void printSystemInfo();  // 시스템 정보 출력

// 메인 루프 헬퍼 함수들
void handleEmergencyMode();  // 긴급 모드 처리
void handleSerialInput();  // 시리얼 입력 처리
void handlePeriodicSensorUpdate();  // 주기적 센서 데이터 전송

// 센서 및 데이터 처리
void readSensorData();  // 센서 데이터 읽기
void sendSensorData();  // 센서 데이터 전송
void sendStatus();  // 상태 정보 전송
void sendResponse(const char* message, int value = -1);  // 응답 전송
void sendError(const char* error);  // 에러 메시지 전송

// 명령어 처리
void processCommand(const char* command);  // 명령어 처리
bool validateCommand(const char* command);  // 명령어 유효성 검사
bool parseCommand(const char* command);  // 명령어 파싱
void executeCommand(const char* cmdType);  // 명령어 실행

// 개별 명령어 처리기
void handleSensorDataRequest();  // 센서 데이터 요청 처리
void handleLedControl();  // LED 제어 처리
void handleStepperMove();  // 스테핑 모터 이동 처리
void handleStepperSpeedSet();  // 스테핑 모터 속도 설정
void handleStepperStop();  // 스테핑 모터 정지
void handleStepperReset();  // 스테핑 모터 위치 초기화
void handleStepperDisable();  // 스테핑 모터 비활성화
void handleCageCleaning();  // 새장 화장실 청소 처리
void handleCleaningServo();  // 청소 서보 작동 처리
void handleEmergencyReset();  // 긴급 정지 초기화
void handleCleaningCyclesReset();  // 청소 횟수 초기화
void handleSystemTest();  // 시스템 테스트

// 하드웨어 제어
void setLED(bool state);  // LED 제어
void moveStepper(int steps, int speed = -1);  // 스테핑 모터 이동
void stopStepper();  // 스테핑 모터 정지
void setStepperSpeed(int speed);  // 스테핑 모터 속도 설정
void resetStepperPosition();  // 스테핑 모터 위치 초기화
void disableStepperPins();  // 스테핑 모터 핀 비활성화
void performCageCleaning();  // 새장 화장실 청소 처리
void activateCleaningServo();  // 청소 서보 작동 처리
void playBuzzer(int frequency, int duration);  // 부저 작동 처리
void blinkStatusLED(byte times);  // 상태 LED 깜빡임

// 유틸리티
void handleEmergencyStop();  // 긴급 정지 처리
int freeMemory();  // 메모리 사용량 체크
void copyProgmemToBuffer(const char* progmemStr, char* buffer, size_t maxLen);  // PROGMEM 문자열 복사
bool isValidSpeed(int speed);  // 속도 유효성 검사
bool isCleaningLimitReached();  // 청소 횟수 제한 체크

// ========== 메인 설정 ==========
void setup() {
  Serial.begin(BAUD_RATE);  // 시리얼 통신 시작
  
  initializeSystem();  // 시스템 초기화
  initializePins();  // 핀 초기화
  initializeData();  // 데이터 초기화
  
  // 시스템 시작 알림
  blinkStatusLED(LEDConfig::STARTUP_BLINKS);  // 상태 LED 깜빡임
  playBuzzer(BuzzerConfig::STARTUP_FREQ, BuzzerConfig::STARTUP_DURATION);  // 부저 작동
  
  printSystemInfo();  // 시스템 정보 출력
  readSensorData();  // 센서 데이터 읽기
}

// ========== 메인 루프 ==========
void loop() {
  // 긴급 정지 상태 확인
  if (systemStatus.emergency_stop) {
    handleEmergencyMode();  // 긴급 모드 처리
    return;
  }
  
  // 명령어 수신 처리
  handleSerialInput();  // 시리얼 입력 처리
  
  // 주기적 센서 데이터 전송
  handlePeriodicSensorUpdate();  // 주기적 센서 데이터 전송
  
  delay(SystemConfig::LOOP_DELAY);
}

// ========== 초기화 함수들 ==========
void initializeSystem() {
  dht.begin();
  stepper.setSpeed(StepperConfig::DEFAULT_SPEED);
}

void initializePins() {
  pinMode(CLEANING_SERVO_PIN, OUTPUT);
  pinMode(STATUS_LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(EMERGENCY_STOP_PIN, INPUT_PULLUP);
  
  // 인터럽트 설정
  attachInterrupt(digitalPinToInterrupt(EMERGENCY_STOP_PIN), handleEmergencyStop, FALLING);
  
  // 초기 상태 설정
  digitalWrite(CLEANING_SERVO_PIN, LOW);
  digitalWrite(STATUS_LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);
}

void initializeData() {
  // 센서 데이터 초기화
  sensorData.temperature = 0.0;
  sensorData.humidity = 0.0;
  sensorData.stepPosition = 0;
  sensorData.stepperSpeed = StepperConfig::DEFAULT_SPEED;
  sensorData.stepperRunning = false;
  sensorData.timestamp = millis();
  
  // 시스템 상태 초기화
  systemStatus.emergency_stop = false;
  systemStatus.cleaning_servo_active = false;
  systemStatus.cleaning_cycles = 0;
  systemStatus.last_cleaning = 0;
}

void printSystemInfo() {
  Serial.print(F("=== "));
  Serial.print((__FlashStringHelper*)SYSTEM_NAME);
  Serial.print(F(" v"));
  Serial.print((__FlashStringHelper*)SYSTEM_VERSION);
  Serial.println(F(" ==="));
  
  Serial.println((__FlashStringHelper*)MSG_READY);
  Serial.println((__FlashStringHelper*)MSG_DHT_STEPPER);
  Serial.println((__FlashStringHelper*)MSG_CAGE_CLEANING);
  Serial.println((__FlashStringHelper*)MSG_EMERGENCY);
}

// ========== 메인 루프 헬퍼 함수들 ==========
void handleEmergencyMode() {
  static unsigned long lastEmergencyReport = 0;
  if (millis() - lastEmergencyReport > SystemConfig::EMERGENCY_REPORT_INTERVAL) {
    Serial.println(F("{\"alert\":\"EMERGENCY_STOP_ACTIVE\",\"message\":\"Emergency stop active\"}"));
    lastEmergencyReport = millis();
  }
  delay(1000);
}

// ========== 시리얼 입력 처리 ==========
void handleSerialInput() {
  if (!Serial.available()) return;
  
  char incomingChar = Serial.read();
  
  if (incomingChar == '\n') {
    inputBuffer[bufferIndex] = '\0';
    processCommand(inputBuffer);
    bufferIndex = 0;
  } else if (bufferIndex < BUFFER_SIZE - 1) {
    inputBuffer[bufferIndex] = incomingChar;
    bufferIndex++;
  }
}

// ========== 주기적 센서 데이터 전송 ==========
void handlePeriodicSensorUpdate() {
  static unsigned long lastSendTime = 0;
  if (millis() - lastSendTime > SystemConfig::SENSOR_UPDATE_INTERVAL) {
    readSensorData();
    sendSensorData();
    lastSendTime = millis();
  }
}

// ========== 명령어 처리 ==========
void processCommand(const char* command) {
  if (!validateCommand(command)) return;
  if (!parseCommand(command)) return;
  
  const char* cmdType = doc["command"];
  executeCommand(cmdType);
}

// ========== 명령어 유효성 검사 ==========
bool validateCommand(const char* command) {
  if (systemStatus.emergency_stop && strstr_P(command, PSTR("reset_emergency_stop")) == NULL) {
    sendError("EMERGENCY_STOP_ACTIVE");
    return false;
  }
  return true;
}

// ========== 명령어 파싱 ==========
bool parseCommand(const char* command) {
  DeserializationError error = deserializeJson(doc, command);
  if (error) {
    sendError("JSON parsing failed");
    return false;
  }
  return true;
}

// ========== 명령어 실행 ==========
void executeCommand(const char* cmdType) {
  if (strcmp_P(cmdType, PSTR("get_sensor_data")) == 0) {
    handleSensorDataRequest();
  } else if (strcmp_P(cmdType, PSTR("set_led")) == 0) {
    handleLedControl();
  } else if (strcmp_P(cmdType, PSTR("move_stepper")) == 0) {
    handleStepperMove();
  } else if (strcmp_P(cmdType, PSTR("set_stepper_speed")) == 0) {
    handleStepperSpeedSet();
  } else if (strcmp_P(cmdType, PSTR("stop_stepper")) == 0) {
    handleStepperStop();
  } else if (strcmp_P(cmdType, PSTR("reset_stepper_position")) == 0) {
    handleStepperReset();
  } else if (strcmp_P(cmdType, PSTR("disable_stepper")) == 0) {
    handleStepperDisable();
  } else if (strcmp_P(cmdType, PSTR("cage_cleaning")) == 0) {
    handleCageCleaning();
  } else if (strcmp_P(cmdType, PSTR("activate_cleaning_servo")) == 0) {
    handleCleaningServo();
  } else if (strcmp_P(cmdType, PSTR("reset_emergency_stop")) == 0) {
    handleEmergencyReset();
  } else if (strcmp_P(cmdType, PSTR("reset_cleaning_cycles")) == 0) {
    handleCleaningCyclesReset();
  } else if (strcmp_P(cmdType, PSTR("get_status")) == 0) {
    sendStatus();
  } else if (strcmp_P(cmdType, PSTR("system_test")) == 0) {
    handleSystemTest();
  } else {
    sendError("Unknown command");
  }
}

// ========== 개별 명령어 처리기들 ==========
void handleSensorDataRequest() {
  readSensorData();
  sendSensorData();
}

// ========== LED 제어 처리 ==========
void handleLedControl() {
  bool ledState = doc["state"];
  setLED(ledState);
  sendResponse("LED state changed", ledState);
}

// ========== 스테핑 모터 이동 처리 ==========
void handleStepperMove() {
  int steps = doc["steps"];
  int speed = doc["speed"];
  moveStepper(steps, speed);
  
  doc.clear();
  doc["response"] = "Stepper moved";
  doc["steps"] = steps;
  doc["speed"] = speed;
  serializeJson(doc, Serial);
  Serial.println();
}

// ========== 스테핑 모터 속도 설정 처리 ==========
void handleStepperSpeedSet() {
  int speed = doc["speed"];
  if (isValidSpeed(speed)) {
    setStepperSpeed(speed);
    sendResponse("Stepper speed changed", speed);
  } else {
    sendError("Invalid speed range");
  }
}

// ========== 스테핑 모터 정지 처리 ==========
void handleStepperStop() {
  stopStepper();
  sendResponse("Stepper stopped");
}

// ========== 스테핑 모터 위치 초기화 처리 ==========
void handleStepperReset() {
  resetStepperPosition();
  sendResponse("Stepper position reset");
}

// ========== 스테핑 모터 핀 비활성화 처리 ==========
void handleStepperDisable() {
  disableStepperPins();
  sendResponse("Stepper pins disabled");
}

// ========== 새장 화장실 청소 처리 ==========
void handleCageCleaning() {
  if (isCleaningLimitReached()) {
    Serial.println(F("{\"alert\":\"MAX_CLEANING_CYCLES_REACHED\"}"));
    return;
  }
  
  performCageCleaning();
  sendResponse("Cage cleaning completed", systemStatus.cleaning_cycles);
}

// ========== 청소 서보 작동 처리 ==========
void handleCleaningServo() {
  activateCleaningServo();
  sendResponse("Cleaning servo activated");
}

// ========== 긴급 정지 초기화 처리 ==========
void handleEmergencyReset() {
  systemStatus.emergency_stop = false;
  setLED(false);
  sendResponse("Emergency stop reset");
}

// ========== 청소 횟수 초기화 처리 ==========
void handleCleaningCyclesReset() {
  systemStatus.cleaning_cycles = 0;
  sendResponse("Cleaning cycles reset");
}

// ========== 시스템 테스트 처리 ==========
void handleSystemTest() {
  sendResponse("System test started");
  blinkStatusLED(LEDConfig::TEST_BLINKS);
  playBuzzer(BuzzerConfig::TEST_FREQ1, BuzzerConfig::TEST_DURATION);
  delay(200);
  playBuzzer(BuzzerConfig::TEST_FREQ2, BuzzerConfig::TEST_DURATION);
  sendResponse("System test completed");
}

// ========== 센서 데이터 읽기 ==========
void readSensorData() {
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  
  sensorData.temperature = isnan(temp) ? -999 : temp;
  sensorData.humidity = isnan(hum) ? -999 : hum;
  sensorData.timestamp = millis();
}

// ========== 센서 데이터 전송 ==========
void sendSensorData() {
  doc.clear();
  doc["type"] = "sensor_data";
  doc["temp"] = sensorData.temperature;
  doc["hum"] = sensorData.humidity;
  doc["pos"] = sensorData.stepPosition;
  doc["spd"] = sensorData.stepperSpeed;
  doc["run"] = sensorData.stepperRunning;
  doc["time"] = sensorData.timestamp;
  
  serializeJson(doc, Serial);
  Serial.println();
}

// ========== 상태 정보 전송 ==========
void sendStatus() {
  char tempBuffer[32];
  
  doc.clear();
  doc["type"] = "status";
  
  copyProgmemToBuffer(SYSTEM_VERSION, tempBuffer, sizeof(tempBuffer));
  doc["ver"] = tempBuffer;
  
  doc["mem"] = freeMemory();
  doc["ready"] = true;
  doc["dht"] = (sensorData.temperature != -999 && sensorData.humidity != -999);
  doc["pos"] = sensorData.stepPosition;
  doc["spd"] = sensorData.stepperSpeed;
  doc["run"] = sensorData.stepperRunning;
  doc["estop"] = systemStatus.emergency_stop;
  doc["servo"] = systemStatus.cleaning_servo_active;
  doc["cycles"] = systemStatus.cleaning_cycles;
  doc["last"] = systemStatus.last_cleaning;
  doc["max"] = SystemConfig::MAX_CLEANING_CYCLES;
  
  serializeJson(doc, Serial);
  Serial.println();
}

// ========== 응답 전송 ==========
void sendResponse(const char* message, int value) {
  Serial.print(F("{\"response\":\""));
  Serial.print(message);
  if (value >= 0) {
    Serial.print(F("\",\"value\":"));
    Serial.print(value);
  }
  Serial.println(F("\"}"));
}

// ========== 에러 메시지 전송 ==========
void sendError(const char* error) {
  Serial.print(F("{\"error\":\""));
  Serial.print(error);
  Serial.println(F("\"}"));
}

// ========== 하드웨어 제어 ==========
void setLED(bool state) {
  digitalWrite(STATUS_LED_PIN, state ? HIGH : LOW);
}

// ========== 스테핑 모터 이동 ==========
void moveStepper(int steps, int speed) {
  if (speed > 0) {
    setStepperSpeed(speed);
  }
  
  sensorData.stepperRunning = true;
  stepper.step(steps);
  sensorData.stepPosition += steps;
  sensorData.stepperRunning = false;
  
  disableStepperPins();
}

// ========== 스테핑 모터 정지 ==========
void stopStepper() {
  sensorData.stepperRunning = false;
  disableStepperPins();
}

// ========== 스테핑 모터 속도 설정 ==========
void setStepperSpeed(int speed) {
  speed = constrain(speed, StepperConfig::MIN_SPEED, StepperConfig::MAX_SPEED);
  stepper.setSpeed(speed);
  sensorData.stepperSpeed = (byte)speed;
}

// ========== 스테핑 모터 위치 초기화 ==========
void resetStepperPosition() {
  sensorData.stepPosition = 0;
}

// ========== 스테핑 모터 핀 비활성화 ==========
void disableStepperPins() {
  digitalWrite(STEPPER_PIN1, LOW);
  digitalWrite(STEPPER_PIN2, LOW);
  digitalWrite(STEPPER_PIN3, LOW);
  digitalWrite(STEPPER_PIN4, LOW);
}

// ========== 새장 화장실 청소 처리 ==========
void performCageCleaning() {
  Serial.println(F("{\"info\":\"Cage cleaning started\"}"));
  
  setLED(true);
  
  // 1단계: 모래 밀어내기
  activateCleaningServo();
  
  // 2단계: 스테핑 모터로 똥 치우기
  moveStepper(StepperConfig::CLEANING_STEPS, StepperConfig::CLEANING_SPEED);
  delay(StepperConfig::CLEANING_DELAY);
  
  // 3단계: 원위치 복귀
  moveStepper(-StepperConfig::CLEANING_STEPS, StepperConfig::CLEANING_SPEED);
  
  // 4단계: 추가 모래 정리
  activateCleaningServo();
  
  // 청소 완료 처리
  systemStatus.cleaning_cycles++;
  systemStatus.last_cleaning = millis();
  
  setLED(false);
  playBuzzer(BuzzerConfig::COMPLETE_FREQ, BuzzerConfig::COMPLETE_DURATION);
  
  Serial.println(F("{\"info\":\"Cage cleaning completed\"}"));
}

// ========== 청소 서보 작동 처리 ==========
void activateCleaningServo() {
  systemStatus.cleaning_servo_active = true;
  
  // 서보 모터 90도 회전
  for (byte i = 0; i < ServoConfig::SERVO_REPEAT_COUNT; i++) {
    digitalWrite(CLEANING_SERVO_PIN, HIGH);
    delayMicroseconds(ServoConfig::SERVO_90_PULSE);
    digitalWrite(CLEANING_SERVO_PIN, LOW);
    delay(ServoConfig::SERVO_CYCLE_TIME);
  }
  
  delay(ServoConfig::SERVO_HOLD_TIME);
  
  // 서보 모터 0도 복귀
  for (byte i = 0; i < ServoConfig::SERVO_REPEAT_COUNT; i++) {
    digitalWrite(CLEANING_SERVO_PIN, HIGH);
    delayMicroseconds(ServoConfig::SERVO_0_PULSE);
    digitalWrite(CLEANING_SERVO_PIN, LOW);
    delay(ServoConfig::SERVO_CYCLE_TIME);
  }
  
  systemStatus.cleaning_servo_active = false;
}

// ========== 부저 작동 처리 ==========
void playBuzzer(int frequency, int duration) {
  tone(BUZZER_PIN, frequency, duration);
  delay(duration);
  noTone(BUZZER_PIN);
}

// ========== 상태 LED 깜빡임 ==========
void blinkStatusLED(byte times) {
  for (byte i = 0; i < times; i++) {
    setLED(true);
    delay(LEDConfig::BLINK_DURATION);
    setLED(false);
    delay(LEDConfig::BLINK_DURATION);
  }
}

// ========== 긴급 정지 처리 ==========
void handleEmergencyStop() {
  systemStatus.emergency_stop = true;
  
  // 모든 출력 즉시 정지
  digitalWrite(CLEANING_SERVO_PIN, LOW);
  disableStepperPins();
  setLED(true);
  
  systemStatus.cleaning_servo_active = false;
  sensorData.stepperRunning = false;
}

// ========== 메모리 사용량 체크 ==========
int freeMemory() {
  extern int __heap_start, *__brkval;
  int v;
  return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
}

// ========== PROGMEM 문자열 복사 ==========
void copyProgmemToBuffer(const char* progmemStr, char* buffer, size_t maxLen) {
  strncpy_P(buffer, progmemStr, maxLen - 1);
  buffer[maxLen - 1] = '\0';
}

// ========== 속도 유효성 검사 ==========
bool isValidSpeed(int speed) {
  return speed >= StepperConfig::MIN_SPEED && speed <= StepperConfig::MAX_SPEED;
}

// ========== 청소 횟수 제한 체크 ==========
bool isCleaningLimitReached() {
  return systemStatus.cleaning_cycles >= SystemConfig::MAX_CLEANING_CYCLES;
}