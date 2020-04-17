/**
 * Author: Caspar Treijtel
 *
 * This little Arduino program listen's to the Serial port
 * where it awaits instructions for resetting a Raspberry Pi.
 *
 * The Pi will have its RUN pin connected to pin 13 of the
 * Arduino. If the RUN pin is pulled down, then the Raspberry
 * Pi will reset.
 *
 * If an 'r' is sent to the Arduino (yes, 'r' from reset),
 * the Arduino does the thing.
 */
void setup() {
  // put your setup code here, to run once:
  pinMode(13,OUTPUT);
  digitalWrite(13,HIGH);
  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  if(Serial.available() > 0) {
    if(Serial.read() == 'r') {
      // Pull down pin 13, this will make the raspberry pi reset,
      // because it is connected to the RUN pin on the pi.
      digitalWrite(13,LOW);
      delay(500);
    }
  } else {
    // Do nothing, just keep pin 13 high so raspberry pi RUN pin
    // is not touched.
    digitalWrite(13,HIGH);
  }
}
