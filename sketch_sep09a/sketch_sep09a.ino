#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <ESP8266WebServer.h>

#define ssid  "Xiaomi_cmcc"
#define psd   "xiaomi991212"

const String url = "v1.hitokoto.cn/?encode=text";
//const String host = "a"
const int   port = 80;

//const char finger[] PROGMEM = "43 CA B2 41 71 ED 91 1D 7A A8 B8 0D 17 B6 34 10 F8 4F 30 AF";
void initWiFi(){
  Serial.begin(9600);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid,psd);
  Serial.println("开始连接");
  while(WiFi.status() != WL_CONNECTED ){
      delay(500);
      Serial.print(".");
    }
  Serial.println("连接成功");
  }

void wifiTcp(){
  WiFiClient HC;
  if(HC.connect(url,80))
    Serial.println("连接成功");
  HC.print(String("GET ") + url + " HTTP/1.1\r\n" + "Connection: close\r\n\r\n");
  delay(100);
  String data = "";
  while (HC.available()) {
    String line = HC.readStringUntil('\r');
    data += line;
  }
  Serial.println(data);
  HC.stop();

//  HC.setFingerprint(finger);
//  HC.verify(finger,host);
//  HC.setTimeout(15000);
//  delay(1000);
//
//  int r = 0;
//  while((!HC.connect(host,httpsPort)) && (r < 30)){
//    delay(100);
//    Serial.print("..");
//    r++;
//    }
//  if(r == 30){
//    Serial.println("success");
//    }
//  String request =  String("GET /a/check") + " HTTP/1.1\r\n" +
//                        "Host: " + host + "\r\n" +
//                        "Connection: close\r\n" +
//                        "\r\n";
//  HC.print(request);
//  while(HC.connected()){
//     String line = HC.readStringUntil('\n');
//    if (line == "\r") {
//      Serial.println("服务器已响应");
//      break;
//      }
    }

//  while(HC.available()){
//    Serial.println(HC.readStringUntil('\n'));
//    
//    }
//  HC.stop();
//  Serial.println("关闭连接");
//  }
void setup() {
  // put your setup code here, to run once:
  initWiFi();
  wifiTcp();
}

void loop() {
  // put your main code here, to run repeatedly:

}
