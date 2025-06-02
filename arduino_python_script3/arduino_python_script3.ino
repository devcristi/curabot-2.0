#include <Servo.h>
#include <Braccio.h>

#define INPUT_BUFFER_SIZE 50

// Home position constants
#define ZERO_BASE   90  // servo 1
#define ZERO_SHOUL  85  // servo 2
#define ZERO_ELBOW  85  // servo 3
#define ZERO_WRSTV 103  // servo 4
#define ZERO_WRSTR  20  // servo 5
#define ZERO_GRIP   73  // servo 6

static char inputBuffer[INPUT_BUFFER_SIZE];
Braccio::Position armPosition;   // note: Position lives in the Braccio namespace

void setup() {
  Serial.begin(115200);
  Braccio.begin();               // instead of BraccioRobot.init()
}

void loop() {
  if (Serial.available()) {
    byte len = Serial.readBytesUntil('\n', inputBuffer, INPUT_BUFFER_SIZE - 1);
    inputBuffer[len] = '\0';
    interpretCommand(inputBuffer);
  }
}

void interpretCommand(const char* buf) {
  switch (buf[0]) {
    case 'P':
      positionArm(buf);
      break;
    case 'H':
      homePositionArm();
      break;
    case '0':
      Braccio.powerOff();
      Serial.println("OK");
      break;
    case '1':
      Braccio.powerOn();
      Serial.println("OK");
      break;
    default:
      Serial.println("E0");
      break;
  }
  Serial.flush();
}

void positionArm(const char *in) {
  int speed = armPosition.setFromString(in);
  if (speed > 0) {
    Braccio.moveToPosition(armPosition, speed);
    Serial.println("OK");
  } else {
    Serial.println("E1");
  }
}

void homePositionArm() {
  armPosition.set(ZERO_BASE, ZERO_SHOUL, ZERO_ELBOW,
                  ZERO_WRSTV, ZERO_WRSTR, ZERO_GRIP);
  uint16_t defaultSpeed = 150;
  Braccio.moveToPosition(armPosition, defaultSpeed);
  Serial.println("OK");
}
