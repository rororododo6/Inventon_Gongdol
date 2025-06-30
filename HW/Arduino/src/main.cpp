#include <Arduino.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include "functions.h"

// 통신 관련 변수들
const int BAUD_RATE = 115200;
const int BUFFER_SIZE = 256;
char inputBuffer[BUFFER_SIZE];
int bufferIndex = 0;

// DHT22 센서 설정
#define DHTPIN 2        // DHT22 센서 연결 핀
#define DHTTYPE DHT22   // DHT22 센서 타입
DHT dht(DHTPIN, DHTTYPE);

// DC모터 제어 핀 설정
#define MOTOR_PIN1 5    // DC모터 제어 핀 1
#define MOTOR_PIN2 6    // DC모터 제어 핀 2
#define MOTOR_ENABLE 9  // DC모터 PWM 속도 제어 핀

// 센서 데이터 구조체
struct SensorData {
  float temperature;
  float humidity;
  int motorSpeed;
  bool motorRunning;
  unsigned long timestamp;
};

SensorData sensorData;

// JSON 문서 생성
StaticJsonDocument<200> doc;

// 함수 선언
void readSensorData();
void sendSensorData();
void sendStatus();
void processCommand(const char* command);
void setLED(int state);
void setMotor(int speed, int direction);
void stopMotor();
int freeMemory();

void setup() {
  // 시리얼 통신 초기화
  Serial.begin(BAUD_RATE);
  
  // DHT22 센서 초기화
  dht.begin();
  
  // DC모터 핀 설정
  pinMode(MOTOR_PIN1, OUTPUT);
  pinMode(MOTOR_PIN2, OUTPUT);
  pinMode(MOTOR_ENABLE, OUTPUT);
  
  // 모터 정지
  stopMotor();
  
  // 초기 데이터 설정
  sensorData.temperature = 0.0;
  sensorData.humidity = 0.0;
  sensorData.motorSpeed = 0;
  sensorData.motorRunning = false;
  sensorData.timestamp = millis();
  
  Serial.println("Arduino Ready for Raspberry Pi Communication");
  Serial.println("DHT22 Sensor and DC Motor Control Available");
}

void loop() {
  // 라즈베리파이로부터 명령 수신
  if (Serial.available()) {
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
  
  // 주기적으로 센서 데이터 전송 (3초마다)
  static unsigned long lastSendTime = 0;
  if (millis() - lastSendTime > 3000) {
    readSensorData();
    sendSensorData();
    lastSendTime = millis();
  }
  
  delay(100);
}

// 라즈베리파이로부터 받은 명령 처리
void processCommand(const char* command) {
  // JSON 파싱
  DeserializationError error = deserializeJson(doc, command);
  
  if (error) {
    Serial.println("{\"error\": \"JSON parsing failed\"}");
    return;
  }
  
  // 명령 타입 확인
  const char* cmdType = doc["command"];
  
  if (strcmp(cmdType, "get_sensor_data") == 0) {
    readSensorData();
    sendSensorData();
  }
  else if (strcmp(cmdType, "set_led") == 0) {
    int ledState = doc["state"];
    setLED(ledState);
    Serial.println("{\"response\": \"LED state changed\"}");
  }
  else if (strcmp(cmdType, "set_motor") == 0) {
    int speed = doc["speed"];
    int direction = doc["direction"]; // 1: 정방향, -1: 역방향, 0: 정지
    setMotor(speed, direction);
    Serial.println("{\"response\": \"Motor state changed\"}");
  }
  else if (strcmp(cmdType, "stop_motor") == 0) {
    stopMotor();
    Serial.println("{\"response\": \"Motor stopped\"}");
  }
  else if (strcmp(cmdType, "get_status") == 0) {
    sendStatus();
  }
  else {
    Serial.println("{\"error\": \"Unknown command\"}");
  }
}

// DHT22 센서에서 데이터 읽기
void readSensorData() {
  // 온도 읽기
  float temp = dht.readTemperature();
  if (isnan(temp)) {
    sensorData.temperature = -999; // 에러 표시
  } else {
    sensorData.temperature = temp;
  }
  
  // 습도 읽기
  float hum = dht.readHumidity();
  if (isnan(hum)) {
    sensorData.humidity = -999; // 에러 표시
  } else {
    sensorData.humidity = hum;
  }
  
  sensorData.timestamp = millis();
}

// 센서 데이터 전송
void sendSensorData() {
  // JSON으로 데이터 포맷팅
  doc.clear();
  doc["type"] = "sensor_data";
  doc["temperature"] = sensorData.temperature;
  doc["humidity"] = sensorData.humidity;
  doc["motor_speed"] = sensorData.motorSpeed;
  doc["motor_running"] = sensorData.motorRunning;
  doc["timestamp"] = sensorData.timestamp;
  
  // JSON 전송
  serializeJson(doc, Serial);
  Serial.println();
}

// 상태 정보 전송
void sendStatus() {
  doc.clear();
  doc["type"] = "status";
  doc["uptime"] = millis();
  doc["free_memory"] = freeMemory();
  doc["arduino_ready"] = true;
  doc["dht22_connected"] = (sensorData.temperature != -999 && sensorData.humidity != -999);
  doc["motor_speed"] = sensorData.motorSpeed;
  doc["motor_running"] = sensorData.motorRunning;
  
  serializeJson(doc, Serial);
  Serial.println();
}

// LED 제어 (핀 13 사용)
void setLED(int state) {
  pinMode(13, OUTPUT);
  digitalWrite(13, state);
}

// DC모터 제어
void setMotor(int speed, int direction) {
  speed = constrain(speed, 0, 255); // 0-255 범위로 제한
  
  if (direction == 0) {
    stopMotor();
    return;
  }
  
  if (direction == 1) {
    // 정방향
    digitalWrite(MOTOR_PIN1, HIGH);
    digitalWrite(MOTOR_PIN2, LOW);
  } else {
    // 역방향
    digitalWrite(MOTOR_PIN1, LOW);
    digitalWrite(MOTOR_PIN2, HIGH);
  }
  
  analogWrite(MOTOR_ENABLE, speed);
  
  sensorData.motorSpeed = speed;
  sensorData.motorRunning = (speed > 0);
}

// DC모터 정지
void stopMotor() {
  digitalWrite(MOTOR_PIN1, LOW);
  digitalWrite(MOTOR_PIN2, LOW);
  analogWrite(MOTOR_ENABLE, 0);
  
  sensorData.motorSpeed = 0;
  sensorData.motorRunning = false;
}

// 사용 가능한 메모리 반환
int freeMemory() {
  extern int __heap_start, *__brkval;
  int v;
  return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
}