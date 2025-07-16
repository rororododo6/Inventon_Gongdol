#include <Arduino.h>  // Arduino 헤더 파일
#include <ArduinoJson.h>  // JSON 라이브러리
#include <DHT11.h>  // DHT11 센서 라이브러리
#include <Servo.h>  // 서보 모터 라이브러리
//#include "functions.h"  // 함수 헤더 파일

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

// 360도 서보모터 (MG996R)
#define CLEANING_SERVO_PIN 6  // 청소 서보 핀 (MG996R)

// 시스템 제어 핀
#define EMERGENCY_STOP_PIN 3  // 긴급 정지 핀
#define STATUS_LED_PIN 7  // 상태 LED 핀
#define BUZZER_PIN 5  // 부저 핀
#define TRASH_EMPTY_BUTTON_PIN 4  // 쓰레기통 비우기 버튼 핀

// ========== 시스템 상수 ==========
namespace SystemConfig {
  const byte MAX_CLEANING_CYCLES = 100; // 최대 청소 횟수
  const unsigned long SENSOR_UPDATE_INTERVAL = 3000;  // 3초
  const unsigned long EMERGENCY_REPORT_INTERVAL = 5000;  // 5초
  const unsigned int LOOP_DELAY = 100;  // 100ms
}

namespace ServoConfig {
  const int SERVO_STOP = 1500;           // 정지 위치 (1500us)
  const int SERVO_FORWARD = 1700;        // 앞으로 회전 (1700us)
  const int SERVO_BACKWARD = 1300;       // 뒤로 회전 (1300us)
  const unsigned long CLEANING_DURATION = 3000;  // 청소 시간 (3초)
  const int SERVO_CYCLE_TIME = 20;       // PWM 주기 (20ms)
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
DHT11 dht11(DHTPIN); // DHT11 센서 객체
Servo cleaningServo; // 360도 서보모터 객체
JsonDocument doc; // JSON 문서 객체

// ========== 데이터 구조체 ==========
struct SystemStatus {
  bool emergency_stop; // 긴급 정지 상태
  bool cleaning_servo_active; // 청소 서보 작동 상태
  byte cleaning_cycles; // 청소 횟수
  unsigned long last_cleaning; // 마지막 청소 시간
  bool trash_full; // 쓰레기통 가득 참 상태
  bool trash_empty_button_pressed; // 쓰레기통 비우기 버튼 눌림 상태
};

struct SensorData {
  float temperature; // 온도
  float humidity; // 습도
  bool servoRunning; // 서보 모터 실행 여부
  int servoDirection; // 서보 모터 방향 (0: 정지, 1: 앞으로, -1: 뒤로)
  bool trashFull; // 쓰레기통 가득 참 상태
  bool trashEmptyButtonPressed; // 쓰레기통 비우기 버튼 눌림 상태
  unsigned long timestamp; // 데이터 수집 시간
};

SystemStatus systemStatus; // 시스템 상태 구조체
SensorData sensorData; // 센서 데이터 구조체

// ========== PROGMEM 문자열 ==========
const char MSG_READY[] PROGMEM = "Arduino Ready for Raspberry Pi Communication"; // 준비 메시지
const char MSG_DHT_SERVO[] PROGMEM = "DHT11 Sensor and MG996R 360 Servo Motor Control Available"; // DHT11 센서와 360도 서보모터 제어 가능
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
void handleServoControl();  // 서보 모터 제어 처리
void handleServoStop();  // 서보 모터 정지
void handleCageCleaning();  // 새장 화장실 청소 처리
void handleEmergencyReset();  // 긴급 정지 초기화
void handleCleaningCyclesReset();  // 청소 횟수 초기화
void handleSystemTest();  // 시스템 테스트
void handleTrashEmptyButton();  // 쓰레기통 비우기 버튼 처리

// 하드웨어 제어
void setLED(bool state);  // LED 제어
void controlServo(int direction);  // 서보 모터 제어 (0: 정지, 1: 앞으로, -1: 뒤로)
void stopServo();  // 서보 모터 정지
void performCageCleaning();  // 새장 화장실 청소 처리
void playBuzzer(int frequency, int duration);  // 부저 작동 처리
void blinkStatusLED(byte times);  // 상태 LED 깜빡임

// 유틸리티
void handleEmergencyStop();  // 긴급 정지 처리
void checkEmergencyButtonHold();  // 긴급 정지 버튼 2초 길게 누르기 체크
int freeMemory();  // 메모리 사용량 체크
void copyProgmemToBuffer(const char* progmemStr, char* buffer, size_t maxLen);  // PROGMEM 문자열 복사
bool isCleaningLimitReached();  // 청소 횟수 제한 체크
void readTrashEmptyButton();  // 쓰레기통 비우기 버튼 읽기
bool isTrashFull();  // 쓰레기통 가득 참 상태 체크

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
    checkEmergencyButtonHold();  // 2초 길게 누르기 체크
    return;
  }
  
  // 쓰레기통 비우기 버튼 체크
  readTrashEmptyButton();
  
  // 명령어 수신 처리
  handleSerialInput();  // 시리얼 입력 처리
  
  // 주기적 센서 데이터 전송
  handlePeriodicSensorUpdate();  // 주기적 센서 데이터 전송
  
  delay(SystemConfig::LOOP_DELAY);
}

// ========== 초기화 함수들 ==========
void initializeSystem() {
  cleaningServo.attach(CLEANING_SERVO_PIN);
  cleaningServo.writeMicroseconds(ServoConfig::SERVO_STOP); // 초기 정지 상태
}

void initializePins() {
  pinMode(STATUS_LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(EMERGENCY_STOP_PIN, INPUT_PULLUP);
  pinMode(TRASH_EMPTY_BUTTON_PIN, INPUT_PULLUP);  // 쓰레기통 비우기 버튼 핀
  
  // 인터럽트 설정
  attachInterrupt(digitalPinToInterrupt(EMERGENCY_STOP_PIN), handleEmergencyStop, FALLING);
  
  // 초기 상태 설정
  digitalWrite(STATUS_LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);
}

void initializeData() {
  // 센서 데이터 초기화
  sensorData.temperature = 0.0;
  sensorData.humidity = 0.0;
  sensorData.servoRunning = false;
  sensorData.servoDirection = 0;
  sensorData.trashFull = false;
  sensorData.trashEmptyButtonPressed = false;
  sensorData.timestamp = millis();
  
  // 시스템 상태 초기화
  systemStatus.emergency_stop = false;
  systemStatus.cleaning_servo_active = false;
  systemStatus.cleaning_cycles = 0;
  systemStatus.last_cleaning = 0;
  systemStatus.trash_full = false;
  systemStatus.trash_empty_button_pressed = false;
}

void printSystemInfo() {
  Serial.print(F("=== "));
  Serial.print((__FlashStringHelper*)SYSTEM_NAME);
  Serial.print(F(" v"));
  Serial.print((__FlashStringHelper*)SYSTEM_VERSION);
  Serial.println(F(" ==="));
  
  Serial.println((__FlashStringHelper*)MSG_READY);
  Serial.println((__FlashStringHelper*)MSG_DHT_SERVO);
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
  } else if (strcmp_P(cmdType, PSTR("control_servo")) == 0) {
    handleServoControl();
  } else if (strcmp_P(cmdType, PSTR("stop_servo")) == 0) {
    handleServoStop();
  } else if (strcmp_P(cmdType, PSTR("cage_cleaning")) == 0) {
    handleCageCleaning();
  } else if (strcmp_P(cmdType, PSTR("reset_emergency_stop")) == 0) {
    handleEmergencyReset();
  } else if (strcmp_P(cmdType, PSTR("reset_cleaning_cycles")) == 0) {
    handleCleaningCyclesReset();
  } else if (strcmp_P(cmdType, PSTR("get_status")) == 0) {
    sendStatus();
  } else if (strcmp_P(cmdType, PSTR("system_test")) == 0) {
    handleSystemTest();
  } else if (strcmp_P(cmdType, PSTR("trash_empty_button")) == 0) {
    handleTrashEmptyButton();
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

// ========== 서보 모터 제어 처리 ==========
void handleServoControl() {
  int direction = doc["direction"]; // 0: 정지, 1: 앞으로, -1: 뒤로
  controlServo(direction);
  
  doc.clear();
  doc["response"] = "Servo control changed";
  doc["direction"] = direction;
  serializeJson(doc, Serial);
  Serial.println();
}

// ========== 서보 모터 정지 처리 ==========
void handleServoStop() {
  stopServo();
  sendResponse("Servo stopped");
}

// ========== 새장 화장실 청소 처리 ==========
void handleCageCleaning() {
  if (isTrashFull()) {
    Serial.println(F("{\"alert\":\"TRASH_FULL_EMPTY_REQUIRED\"}"));
    return;
  }
  
  if (isCleaningLimitReached()) {
    Serial.println(F("{\"alert\":\"MAX_CLEANING_CYCLES_REACHED\"}"));
    return;
  }
  
  performCageCleaning();
  sendResponse("Cage cleaning completed", systemStatus.cleaning_cycles);
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
  int temp = dht11.readTemperature();
  int hum = dht11.readHumidity();
  
  // 새 라이브러리는 에러 시 DHT11::ERROR_TIMEOUT(-1) 또는 DHT11::ERROR_CHECKSUM(-2) 반환
  sensorData.temperature = (temp < 0) ? -999 : temp;
  sensorData.humidity = (hum < 0) ? -999 : hum;
  sensorData.trashFull = systemStatus.trash_full;
  sensorData.trashEmptyButtonPressed = systemStatus.trash_empty_button_pressed;
  sensorData.timestamp = millis();
}

// ========== 센서 데이터 전송 ==========
void sendSensorData() {
  doc.clear();
  doc["type"] = "sensor_data";
  doc["temp"] = sensorData.temperature;
  doc["hum"] = sensorData.humidity;
  doc["servo_run"] = sensorData.servoRunning;
  doc["servo_dir"] = sensorData.servoDirection;
  doc["trash_full"] = sensorData.trashFull;
  doc["trash_empty_btn"] = sensorData.trashEmptyButtonPressed;
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
  doc["servo_run"] = sensorData.servoRunning;
  doc["servo_dir"] = sensorData.servoDirection;
  doc["estop"] = systemStatus.emergency_stop;
  doc["servo_active"] = systemStatus.cleaning_servo_active;
  doc["cycles"] = systemStatus.cleaning_cycles;
  doc["last"] = systemStatus.last_cleaning;
  doc["max"] = SystemConfig::MAX_CLEANING_CYCLES;
  doc["trash_full"] = systemStatus.trash_full;
  doc["trash_empty_btn"] = systemStatus.trash_empty_button_pressed;
  
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

// ========== 서보 모터 제어 ==========
void controlServo(int direction) {
  sensorData.servoDirection = direction;
  
  if (direction == 1) { // 앞으로
    cleaningServo.writeMicroseconds(ServoConfig::SERVO_FORWARD);
    sensorData.servoRunning = true;
  } else if (direction == -1) { // 뒤로
    cleaningServo.writeMicroseconds(ServoConfig::SERVO_BACKWARD);
    sensorData.servoRunning = true;
  } else { // 정지
    cleaningServo.writeMicroseconds(ServoConfig::SERVO_STOP);
    sensorData.servoRunning = false;
  }
}

// ========== 서보 모터 정지 ==========
void stopServo() {
  cleaningServo.writeMicroseconds(ServoConfig::SERVO_STOP);
  sensorData.servoRunning = false;
  sensorData.servoDirection = 0;
}

// ========== 새장 화장실 청소 처리 ==========
void performCageCleaning() {
  Serial.println(F("{\"info\":\"Cage cleaning started\"}"));
  
  setLED(true);
  systemStatus.cleaning_servo_active = true;
  
  // 1단계: 앞으로 3초 회전
  Serial.println(F("{\"info\":\"Cleaning forward rotation started\"}"));
  controlServo(1); // 앞으로
  delay(ServoConfig::CLEANING_DURATION); // 3초
  
  // 2단계: 뒤로 3초 회전
  Serial.println(F("{\"info\":\"Cleaning backward rotation started\"}"));
  controlServo(-1); // 뒤로
  delay(ServoConfig::CLEANING_DURATION); // 3초
  
  // 3단계: 정지
  Serial.println(F("{\"info\":\"Cleaning rotation stopped\"}"));
  stopServo();
  
  // 청소 완료 처리
  systemStatus.cleaning_cycles++;
  systemStatus.last_cleaning = millis();
  systemStatus.cleaning_servo_active = false;
  
  // 10번 청소 후 쓰레기통 가득 참 상태로 설정
  if (systemStatus.cleaning_cycles >= 10) {
    systemStatus.trash_full = true;
    Serial.println(F("{\"alert\":\"TRASH_FULL_AFTER_10_CLEANINGS\"}"));
  }
  
  setLED(false);
  playBuzzer(BuzzerConfig::COMPLETE_FREQ, BuzzerConfig::COMPLETE_DURATION);
  
  Serial.println(F("{\"info\":\"Cage cleaning completed\"}"));
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

// ========== 긴급 정지 처리 (활성화만) ==========
void handleEmergencyStop() {
  static unsigned long lastInterruptTime = 0;
  unsigned long interruptTime = millis();
  
  // 디바운싱: 200ms 이내의 중복 신호 무시
  if (interruptTime - lastInterruptTime < 200) {
    return;
  }
  lastInterruptTime = interruptTime;
  
  // 긴급 정지만 활성화 (해제는 2초 길게 누르기로만 가능)
  if (!systemStatus.emergency_stop) {
    systemStatus.emergency_stop = true;
    
    // 모든 출력 즉시 정지
    stopServo();
    setLED(true);
    systemStatus.cleaning_servo_active = false;
    Serial.println(F("{\"alert\":\"EMERGENCY_STOP_ACTIVATED\",\"message\":\"Hold button 2s to reset\"}"));
  }
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

// ========== 청소 횟수 제한 체크 ==========
bool isCleaningLimitReached() {
  return systemStatus.cleaning_cycles >= SystemConfig::MAX_CLEANING_CYCLES;
}

// ========== 쓰레기통 비우기 버튼 처리 ==========
void handleTrashEmptyButton() {
  if (systemStatus.trash_empty_button_pressed) {
    systemStatus.trash_full = false;
    systemStatus.trash_empty_button_pressed = false;
    sendResponse("Trash emptied", 1);
  } else {
    sendError("Trash empty button not pressed");
  }
}

// ========== 쓰레기통 비우기 버튼 읽기 ==========
void readTrashEmptyButton() {
  static bool lastButtonState = HIGH;
  static unsigned long lastDebounceTime = 0;
  const unsigned long debounceDelay = 50;
  
  bool currentButtonState = digitalRead(TRASH_EMPTY_BUTTON_PIN);
  
  if (currentButtonState != lastButtonState) {
    lastDebounceTime = millis();
  }
  
  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (currentButtonState == LOW && lastButtonState == HIGH) {
      // 버튼이 눌렸을 때
      systemStatus.trash_empty_button_pressed = true;
      Serial.println(F("{\"alert\":\"TRASH_EMPTY_BUTTON_PRESSED\"}"));
    }
  }
  
  lastButtonState = currentButtonState;
}

// ========== 쓰레기통 가득 참 상태 체크 ==========
bool isTrashFull() {
  return systemStatus.trash_full;
}

// ========== 긴급 정지 버튼 2초 길게 누르기 체크 ==========
void checkEmergencyButtonHold() {
  static bool buttonWasPressed = false;
  static unsigned long buttonPressStartTime = 0;
  static unsigned long lastBlinkTime = 0;
  static bool ledBlinkState = false;
  
  bool buttonCurrentlyPressed = (digitalRead(EMERGENCY_STOP_PIN) == LOW);
  
  if (buttonCurrentlyPressed) {
    if (!buttonWasPressed) {
      // 버튼이 새로 눌렸을 때
      buttonWasPressed = true;
      buttonPressStartTime = millis();
      Serial.println(F("{\"info\":\"Hold button to reset emergency stop...\"}"));
    }
    
    unsigned long holdTime = millis() - buttonPressStartTime;
    
    // 1초 후부터 LED 깜빡임으로 진행상황 표시
    if (holdTime >= 1000) {
      if (millis() - lastBlinkTime >= 100) {  // 100ms마다 깜빡임
        ledBlinkState = !ledBlinkState;
        setLED(ledBlinkState);
        lastBlinkTime = millis();
      }
    }
    
    // 2초 이상 눌렀을 때 긴급 정지 해제
    if (holdTime >= 2000) {
      systemStatus.emergency_stop = false;
      setLED(false);
      Serial.println(F("{\"info\":\"EMERGENCY_STOP_DEACTIVATED\",\"message\":\"System restored\"}"));
      
      // 상태 초기화
      buttonWasPressed = false;
      buttonPressStartTime = 0;
      ledBlinkState = false;
    }
  } else {
    if (buttonWasPressed) {
      // 버튼을 놓았을 때
      buttonWasPressed = false;
      setLED(true);  // 긴급 정지 상태로 LED 다시 켜기
      Serial.println(F("{\"info\":\"Button released - emergency stop still active\"}"));
    }
  }
}