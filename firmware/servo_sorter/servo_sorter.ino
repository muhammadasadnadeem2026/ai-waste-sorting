#include <Servo.h>
Servo servo1;  // on pin 9
Servo servo2;  // on pin 10
Servo servo3;  // on pin 11
//─── servo1 ("p" command) state machine ───────────────────────────────────────
enum PState { P_IDLE, P_HOLDING, P_RETURNING } pState = P_IDLE;
uint32_t pStartTime = 0, pLastStep = 0;
uint8_t  pAngle     = 0;
const uint32_t P_HOLD_MS = 5000UL;  // hold at 120° for 5 s
const uint32_t P_STEP_MS = 20UL;    // return step interval
//─── servo2 ("m" command) state machine ───────────────────────────────────────
enum MState { M_IDLE, M_DELAY_START, M_HOLD_100, M_SLOW_UP } mState = M_IDLE;
uint32_t mStartTime = 0, mLastStep = 0;
uint8_t  mAngle     = 0;
const uint32_t M_DELAY_MS     = 2000UL; // wait 2 s before moving
const uint32_t M_HOLD100_MS   = 4000UL; // hold at 100° for 4 s
const uint32_t M_SLOW_STEP_MS = 20UL;   // 100→180 step interval
//─── servo3 ("c" command) state machine ───────────────────────────────────────
enum CState { C_IDLE, C_DELAY_START, C_HOLDING, C_RETURNING } cState = C_IDLE;
uint32_t cStartTime = 0, cLastStep = 0;
uint8_t  cAngle     = 0;
const uint32_t C_DELAY_MS = 3000UL;    // wait 3 s before moving
const uint32_t C_HOLD_MS  = 10000UL;    // hold at 120° for 6 s
const uint32_t C_STEP_MS  = 20UL;      // return step interval
void setup() {
  Serial.begin(9600);
  servo1.attach(9);
  servo2.attach(10);
  servo3.attach(11);
  servo1.write(0);
  servo2.write(0);
  servo3.write(0);
}
void loop() {
  // 1) Serial command handling
  if (Serial.available()) {
    char cmd = Serial.read();
    // servo1: 'p' or 'P'
    if ((cmd == 'p' || cmd == 'P') && pState == P_IDLE) {
      pAngle     = 120;
      servo1.write(pAngle);
      pStartTime = millis();
      pState     = P_HOLDING;
    }
    // servo2: 'm' or 'M'
    else if ((cmd == 'm' || cmd == 'M') && mState == M_IDLE) {
      mStartTime = millis();
      mState     = M_DELAY_START;
    }
    // servo3: 'c' or 'C'
    else if ((cmd == 'c' || cmd == 'C') && cState == C_IDLE) {
      cStartTime = millis();
      cState     = C_DELAY_START;
    }
  }
  // 2) Drive servo1 state machine
  switch (pState) {
    case P_HOLDING:
      if (millis() - pStartTime >= P_HOLD_MS) {
        pLastStep = millis();
        pState    = P_RETURNING;
      }
      break;
    case P_RETURNING:
      if (millis() - pLastStep >= P_STEP_MS) {
        pLastStep = millis();
        if (pAngle > 0) {
          --pAngle;
          servo1.write(pAngle);
        } else {
          pState = P_IDLE;
        }
      }
      break;
    default: break;
  }
  // 3) Drive servo2 state machine
  switch (mState) {
    case M_DELAY_START:
      if (millis() - mStartTime >= M_DELAY_MS) {
        mAngle     = 100;
        servo2.write(mAngle);
        mStartTime = millis();
        mState     = M_HOLD_100;
      }
      break;
    case M_HOLD_100:
      if (millis() - mStartTime >= M_HOLD100_MS) {
        mLastStep = millis();
        mState    = M_SLOW_UP;
      }
      break;
    case M_SLOW_UP:
      if (millis() - mLastStep >= M_SLOW_STEP_MS) {
        mLastStep = millis();
        if (mAngle < 180) {
          ++mAngle;
          servo2.write(mAngle);
        } else {
          servo2.write(0);
          mState = M_IDLE;
        }
      }
      break;
    default: break;
  }
  // 4) Drive servo3 state machine
  switch (cState) {
    case C_DELAY_START:
      if (millis() - cStartTime >= C_DELAY_MS) {
        cAngle     = 120;
        servo3.write(cAngle);
        cStartTime = millis();
        cState     = C_HOLDING;
      }
      break;
    case C_HOLDING:
      if (millis() - cStartTime >= C_HOLD_MS) {
        cLastStep = millis();
        cState    = C_RETURNING;
      }
      break;
    case C_RETURNING:
      if (millis() - cLastStep >= C_STEP_MS) {
        cLastStep = millis();
        if (cAngle > 0) {
          --cAngle;
          servo3.write(cAngle);
        } else {
          cState = C_IDLE;
        }
      }
      break;
    default: break;
  }
  // 5) Other non-blocking tasks
}
