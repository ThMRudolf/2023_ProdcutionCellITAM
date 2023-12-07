const int HS_PIN1 = A0;
const int HS_PIN2 = A1;
const int HS_PIN3 = A2;

void setup() {
    Serial.begin(9600);
}

void loop() {
    int arr[3] = {HS_PIN1,HS_PIN2,HS_PIN3};
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