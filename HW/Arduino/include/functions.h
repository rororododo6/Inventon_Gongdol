#ifndef FUNCTIONS_H
#define FUNCTIONS_H

// 함수 선언
void readSensorData();
void sendSensorData();
void sendStatus();
void processCommand(const char* command);
void setLED(int state);
void moveStepper(int steps, int speed);
void stopStepper();
void setStepperSpeed(int speed);
void resetStepperPosition();
void disableStepperPins();
int freeMemory();

#endif 