#include <TM1637.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266WiFi.h>


#define ssid "Xiaomi_cmcc"
#define psd "xiaomi991212"

#define api "ander1023.github.io/Arduino_Text"


//TM1637 tm1637(CLK,DIO);

void setup() {
  Serial.begin(9600);
  WiFi.begin(ssid, psd);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(WiFi.localIP());
}

void loop() {
  String getTime = http_post();
  Serial.println(getTime);
  delay(5000);
}

String  http_post() {
  WiFiClient client;
  HTTPClient http;
  http.begin(api);
  int httpCode = http.POST(" ");
    if (httpCode == HTTP_CODE_OK) {
      return http.getString();
    }
  http.end();
}
  /*
    年：46——49
    月：50——51
    日：52  53
    时：54  55
    分：56  57
    秒：58  59
  */
int getOther(String b2,int index){
  return b2.charAt(index) - 48;
  }
