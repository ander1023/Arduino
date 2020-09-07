#include <ESP8266HTTPClient.h>
#include <ESP8266WiFi.h>

#define ssid "id"
#define psd "password"
#define api "https://v1.hitokoto.cn/?encode=text"
void setup() {
  // put your setup code here, to run once:
  //初始化串口设置
  Serial.begin(9600);


  //开始连接wifi
  WiFi.begin(ssid, psd);

  //等待WiFi连接,连接成功打印IP
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println(WiFi.localIP());

}

void loop() {
  // put your main code here, to run repeatedly:
  Serial.println(http_post());
  delay(5000);
}

String  http_post() {

  //创建 WiFiClient 实例化对象
  WiFiClient client;

  //创建http对象
  HTTPClient http;

  //配置请求地址
  http.begin(api); //HTTP请求
  Serial.print("[HTTP] begin...\n");

  //启动连接并发送HTTP报头和报文
  int httpCode = http.POST(" ");
  Serial.print("[HTTP] POST...\n");

  //连接失败时 httpCode时为负
  if (httpCode > 0) {

    //将服务器响应头打印到串口
    Serial.printf("[HTTP] POST... code: %d\n", httpCode);
    //返回string
    if (httpCode == HTTP_CODE_OK) {
      return http.getString();
      
    }
  } else {
    Serial.printf("[HTTP] POST... failed, error: %s\n", http.errorToString(httpCode).c_str());
  }
  //关闭http连接
  http.end();
}
