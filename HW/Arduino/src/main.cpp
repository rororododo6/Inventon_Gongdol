#include <Arduino.h>  // Arduino 헤더 파일
#include <ArduinoJson.h>  // JSON 라이브러리
#include <DHT.h>  // DHT 센서 라이브러리
#include <Stepper.h>  // 스테핑 모터 라이브러리
#include "functions.h"  // 함수 헤더 파일

// 통신 관련 변수들
const long BAUD_RATE = 115200L;  // 통신 속도
const int BUFFER_SIZE = 256;  // 버퍼 크기
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

// 스테핑 모터 객체 생성 (ULN2003 핀 순서: IN1, IN3, IN2, IN4)
Stepper stepper(STEPS_PER_REVOLUTION, STEPPER_PIN1, STEPPER_PIN3, STEPPER_PIN2, STEPPER_PIN4);

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
int freeMemory();  // 사용 가능한 메모리 반환

void setup() {  // 설정
  // 시리얼 통신 초기화
  Serial.begin(BAUD_RATE);  // 통신 속도 설정
  
  // DHT22 센서 초기화
  dht.begin();  // DHT 센서 초기화
  
  // ULN2003 스테핑 모터 초기 속도 설정 (기본 10 RPM)
  stepper.setSpeed(10);  // 28BYJ-48에 적합한 속도
  
  // 초기 데이터 설정
  sensorData.temperature = 0.0;  // 온도 초기값
  sensorData.humidity = 0.0;  // 습도 초기값
  sensorData.stepPosition = 0;  // 스텝 위치 초기값
  sensorData.stepperSpeed = 10;  // 스테핑 모터 속도 초기값 (RPM)
  sensorData.stepperRunning = false;  // 스테핑 모터 실행 여부 초기값
  sensorData.timestamp = millis();  // 데이터 수집 시간 초기값
  
  Serial.println("Arduino Ready for Raspberry Pi Communication");  // 라즈베리파이 통신 준비 메시지
  Serial.println("DHT11 Sensor and ULN2003 Stepper Motor Control Available");  // DHT11 센서와 ULN2003 스테핑 모터 제어 가능 메시지
}

void loop() {  // 루프
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
  static unsigned long lastSendTime = 0;  // 마지막 전송 시간
  if (millis() - lastSendTime > 3000) {
    readSensorData();  // 센서 데이터 읽기
    sendSensorData();  // 센서 데이터 전송
    lastSendTime = millis();  // 마지막 전송 시간 업데이트
  }
  
  delay(100);  // 100ms 대기
}

// 라즈베리파이로부터 받은 명령 처리
void processCommand(const char* command) {  // 명령 처리
  // JSON 파싱
  DeserializationError error = deserializeJson(doc, command);
  
  if (error) {  // JSON 파싱 실패 시
    Serial.println("{\"error\": \"JSON parsing failed\"}");  // JSON 파싱 실패 메시지
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
    Serial.println("{\"response\": \"LED state changed\"}");  // LED 상태 변경 메시지
  }
  else if (strcmp(cmdType, "move_stepper") == 0) {  // 스테핑 모터 이동 명령
    int steps = doc["steps"];  // 이동할 스텝 수 (양수: 시계방향, 음수: 반시계방향)
    int speed = doc["speed"];  // 속도 (RPM)
    moveStepper(steps, speed);  // 스테핑 모터 이동
    Serial.println("{\"response\": \"Stepper moved\"}");  // 스테핑 모터 이동 메시지
  }
  else if (strcmp(cmdType, "set_stepper_speed") == 0) {  // 스테핑 모터 속도 설정 명령
    int speed = doc["speed"];  // 속도 (RPM)
    setStepperSpeed(speed);  // 스테핑 모터 속도 설정
    Serial.println("{\"response\": \"Stepper speed changed\"}");  // 스테핑 모터 속도 변경 메시지
  }
  else if (strcmp(cmdType, "stop_stepper") == 0) {  // 스테핑 모터 정지 명령
    stopStepper();  // 스테핑 모터 정지
    Serial.println("{\"response\": \"Stepper stopped\"}");  // 스테핑 모터 정지 메시지
  }
  else if (strcmp(cmdType, "reset_stepper_position") == 0) {  // 스테핑 모터 위치 초기화 명령
    resetStepperPosition();  // 스테핑 모터 위치 초기화
    Serial.println("{\"response\": \"Stepper position reset\"}");  // 스테핑 모터 위치 초기화 메시지
  }
  else if (strcmp(cmdType, "disable_stepper") == 0) {  // 스테핑 모터 핀 비활성화 명령
    disableStepperPins();  // 스테핑 모터 핀 비활성화
    Serial.println("{\"response\": \"Stepper pins disabled\"}");  // 스테핑 모터 핀 비활성화 메시지
  }
  else if (strcmp(cmdType, "get_status") == 0) {  // 상태 정보 요청 명령
    sendStatus();  // 상태 정보 전송
  }
  else {  // 알 수 없는 명령
    Serial.println("{\"error\": \"Unknown command\"}");  // 알 수 없는 명령 메시지
  }
}

// DHT22 센서에서 데이터 읽기
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
  doc["uptime"] = millis();  // 실행 시간
  doc["free_memory"] = freeMemory();  // 사용 가능한 메모리
  doc["arduino_ready"] = true;  // Arduino 준비 상태 
  doc["dht11_connected"] = (sensorData.temperature != -999 && sensorData.humidity != -999);  // DHT11 센서 연결 상태
  doc["step_position"] = sensorData.stepPosition;  // 스텝 위치
  doc["stepper_speed"] = sensorData.stepperSpeed;  // 스테핑 모터 속도
  doc["stepper_running"] = sensorData.stepperRunning;  // 스테핑 모터 실행 여부
  
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

// 사용 가능한 메모리 반환
int freeMemory() {  // 사용 가능한 메모리 반환
  extern int __heap_start, *__brkval;  // 메모리 시작 주소와 브레이크 값
  int v;  // 임시 변수
  return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);  // 사용 가능한 메모리 반환
}