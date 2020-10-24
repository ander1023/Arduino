#include <TM1637.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266WiFi.h>


#define ssid "Xiaomi_cmcc"
#define psd "xiaomi991212"

#define api "https://v1.hitokoto.cn/?encode=text"
#define api1 "http://quan.suning.com/getSysTime.do"
//tm1637
#define CLK 13 //d7
#define DIO 15 //d8

TM1637 tm1637(CLK,DIO);

void setup() {
  Serial.begin(9600);
  WiFi.begin(ssid, psd);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(WiFi.localIP());

  tm1637.init();
  tm1637.set(1);
}

void loop() {
  String getTime = http_post();
  int timeShi1 = getOther(getTime,54);
  int timeShi2 = getOther(getTime,55);
  int timeFen1 = getOther(getTime,56);
  int timeFen2 = getOther(getTime,57);

  tm1637.display(0,timeShi1);
  tm1637.display(1,timeShi2);
  tm1637.display(2,timeFen1);
  tm1637.display(3,timeFen2);
  Serial.print(timeShi1);
  Serial.print(timeShi2);
  Serial.print(timeFen1);
  Serial.println(timeFen2);
  delay(1000);
}

String  http_post() {
  WiFiClient client;
  HTTPClient http;
  http.begin(api1);
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
