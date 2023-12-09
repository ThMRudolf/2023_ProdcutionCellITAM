# drive axis X
const int HS_PIN11 = A0;
const int HS_PIN12 = A1;
const int HS_PIN13 = A2;

# drive axis Y
const int HS_PIN21 = A3;
const int HS_PIN22 = A4;
const int HS_PIN23 = A5;

# drive axis Z
const int HS_PIN31 = A6;
const int HS_PIN32 = A7;
const int HS_PIN33 = A8;

# drive axis Spindle
const int HS_PIN41 = A9;
const int HS_PIN42 = A10;
const int HS_PIN43 = A11;


# Comunication to ??
void setup() {
    Serial.begin(9600);
}

void loop() {
    int arr[12] = {HS_PIN11,HS_PIN12,HS_PIN13,
                    HS_PIN21,HS_PIN22,HS_PIN23, 
                    HS_PIN31,HS_PIN32,HS_PIN33, 
                    HS_PIN41,HS_PIN42,HS_PIN43};
    readMultipleCurrents(arr);
}

void readMultipleCurrents(int sensors[]){
  const int n = sizeof(sensors);
  float currents[n];
  for(int i=0;i<n;i++){
    currents[i] = readCurrentFromPin(sensors[i]);
    Serial.print(currents[i]);
    Serial.print(" - ");
  }
  Serial.println("\n");

  //return currents;
}

float readCurrentFromPin(int pin){
  float valueA = analogRead(pin);
  //Serial.println(valueA);
  float m = 0.0631;
  float offset = 2.5197;
  float valueAAnalogue = valueA*5/1023;
  float current = (valueAAnalogue-offset)/m;
  return current;
}