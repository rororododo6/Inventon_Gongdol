#include <Arduino.h>
#include <DHT11.h> // 사용하시는 DHT11 라이브러리
#include <Servo.h>

// ================================================================================
// 핀 번호 정의 (기존 설정 유지)
// ================================================================================
#define DHT_PIN 2
#define SERVO_PIN 6
#define LED_PIN 7
#define BUZZER_PIN 5
#define EMERGENCY_STOP_PIN 3
#define TRASH_EMPTY_BUTTON_PIN 4

// ================================================================================
// 상수 정의 (기존 설정 유지)
// ================================================================================
namespace CleaningConfig {
  const unsigned long DURATION = 3000; // 청소 동작 시간 (3초)
}

// ================================================================================
// 전역 객체 및 변수
// ================================================================================
DHT11 dht11(DHT_PIN); // 라이브러리에 맞게 객체 생성
Servo cleaningServo;

// 시스템 상태 변수
bool isEmergencyStopped = false;
byte cleaningCycleCount = 0;

// ================================================================================
// 함수 프로토타입
// ================================================================================
void performCleaningSequence();
void sendSensorData();
void playBuzzer(int frequency, int duration);
void handleEmergencyStop();

// ================================================================================
// SETUP: 시스템 초기화
// ================================================================================
void setup() {
  // 시리얼 통신 시작 (안정적인 9600 보드레이트 사용)
  Serial.begin(115200);
  
  // 핀 모드 설정
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(EMERGENCY_STOP_PIN, INPUT_PULLUP);
  pinMode(TRASH_EMPTY_BUTTON_PIN, INPUT_PULLUP);
  
  // 서보모터 연결 및 초기화
  cleaningServo.attach(SERVO_PIN);
  cleaningServo.write(90); // 0도(원점)에서 시작
  
  // 긴급 정지 인터럽트 설정
  attachInterrupt(digitalPinToInterrupt(EMERGENCY_STOP_PIN), handleEmergencyStop, FALLING);
  
  // 시작 알림
  digitalWrite(LED_PIN, HIGH);
  tone(BUZZER_PIN, 1000, 200);
  delay(500);
  digitalWrite(LED_PIN, LOW);
  
  Serial.println("Arduino Ready. Simple Command Mode.");
}

// ================================================================================
// LOOP: 메인 루프
// ================================================================================
void loop() {
  // 긴급 정지 상태에서는 아무것도 하지 않음
  if (isEmergencyStopped) {
    // 2초 이상 길게 누르면 긴급 정지 해제
    if (digitalRead(EMERGENCY_STOP_PIN) == LOW) {
      delay(2000);
      if (digitalRead(EMERGENCY_STOP_PIN) == LOW) {
        isEmergencyStopped = false;
        digitalWrite(LED_PIN, LOW);
        Serial.println("OK: Emergency stop released.");
      }
    }
    return;
  }
  
  // 쓰레기통 비우기 버튼 감지
  if (digitalRead(TRASH_EMPTY_BUTTON_PIN) == LOW) {
      delay(100); // 디바운싱
      if (digitalRead(TRASH_EMPTY_BUTTON_PIN) == LOW) {
        cleaningCycleCount = 0;
        Serial.println("OK: Cleaning cycles reset.");
        playBuzzer(1500, 100);
        delay(1000); // 중복 리셋 방지
      }
  }

  // 라즈베리파이로부터 명령 수신 처리
  if (Serial.available() > 0) {
    char command = Serial.read();

    switch (command) {
      case '1': // LED 켜기
        digitalWrite(LED_PIN, HIGH);
        Serial.println("OK: LED ON");
        break;
        
      case '2': // LED 끄기
        digitalWrite(LED_PIN, LOW);
        Serial.println("OK: LED OFF");
        break;
        
      case '3': // 버저 울림
        playBuzzer(1200, 100);
        Serial.println("OK: BUZZER");
        break;
        
      case '4': // 전체 청소 시퀀스 실행
        performCleaningSequence();
        break;
        
      case '6': // 온습도 데이터 전송 요청
        sendSensorData();
        break;
    }
  }
}

// ================================================================================
// 핵심 기능 함수
// ================================================================================

/**
 * @brief 전체 청소 시퀀스를 수행합니다. (LED, 부저, 서보모터)
 */
void performCleaningSequence() {
  Serial.println("INFO: Cleaning sequence started.");
  digitalWrite(LED_PIN, HIGH);
  playBuzzer(1000, 150);

  // 1. 앞으로 이동
  cleaningServo.write(0);
  delay(CleaningConfig::DURATION);

  // 2. 뒤로 복귀
  cleaningServo.write(180);
  delay(CleaningConfig::DURATION);
  
  digitalWrite(LED_PIN, LOW);
  playBuzzer(1500, 150);
  cleaningServo.write(90);
  cleaningCycleCount++;
  Serial.print("OK: Cleaning complete. Count: ");
  Serial.println(cleaningCycleCount);
}

/**
 * @brief DHT11 센서 값을 읽어 시리얼로 전송합니다.
 * [수정 사항] 제공해주신 라이브러리 예제에 맞춰 수정
 */
void sendSensorData() {
  int temperature = 0;
  int humidity = 0;

  // 온습도 값을 읽어 변수에 저장하고, 결과 코드를 반환받음
  int result = dht11.readTemperatureHumidity(temperature, humidity);

  // 결과 코드가 0이면 성공
  if (result == 0) {
    Serial.print("DATA: Temp=");
    Serial.print(temperature);
    Serial.print("C, Hum=");
    Serial.print(humidity);
    Serial.println("%");
  } else {
    // 라이브러리의 에러 문자열 출력 함수 사용
    Serial.print("Error: ");
    Serial.println(DHT11::getErrorString(result));
  }
}

/**
 * @brief 특정 주파수와 시간으로 부저를 울립니다.
 */
void playBuzzer(int frequency, int duration) {
  tone(BUZZER_PIN, frequency, duration);
}

/**
 * @brief 긴급 정지 인터럽트 핸들러.
 */
void handleEmergencyStop() {
  // 모든 동작 즉시 중지
  cleaningServo.write(90); // 서보모터 원위치
  digitalWrite(LED_PIN, HIGH); // LED를 켜서 상태 표시
  noTone(BUZZER_PIN);
  
  isEmergencyStopped = true;
  // 인터럽트 안에서는 Serial.println 사용을 피하는 것이 좋음
}