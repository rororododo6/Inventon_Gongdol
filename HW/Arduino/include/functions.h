#ifndef FUNCTIONS_H
#define FUNCTIONS_H

// 함수 선언
void readSensorData();
void sendSensorData();
void sendStatus();
void processCommand(const char* command);
void setLED(int state);
void setMotor(int speed, int direction);
void stopMotor();
int freeMemory();

#endif 