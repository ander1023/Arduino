/*
    HTTP over TLS (HTTPS) example sketch

    This example demonstrates how to use
    WiFiClientSecure class to access HTTPS API.
    We fetch and display the status of
    esp8266/Arduino project continuous integration
    build.

    Limitations:
      only RSA certificates
      no support of Perfect Forward Secrecy (PFS)
      TLSv1.2 is supported since version 2.4.0-rc1

    Created by Ivan Grokhotkov, 2015.
    This example is in public domain.
*/

#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>

const char* ssid = "Xiaomi_cmcc";
const char* password = "xiaomi991212";

const char* host = "v1.hitokoto.cn";
const String url = "?encode=text";
//const String url = "";
const int httpsPort = 443;

// Use web browser to view and copy
// SHA1 fingerprint of the certificate
const char* fingerprint = "43 CA B2 41 71 ED 91 1D 7A A8 B8 0D 17 B6 34 10 F8 4F 30 AF";

void setup() {
  Serial.begin(9600);
  Serial.println();
  Serial.print("connecting to ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  // Use WiFiClientSecure class to create TLS connection
  WiFiClientSecure client;
  Serial.print("connecting to ");
  Serial.println(host);
  if (!client.connect(host, httpsPort)) {
    Serial.println("connection failed");
    return;
  }

  if (client.verify(fingerprint, host)) {
    Serial.println("certificate matches");
  } else {
    Serial.println("certificate doesn't match");
  }

  
  Serial.print("requesting URL: ");
  Serial.println(url);

//  client.print(String("GET ")  + url + " HTTP/1.1\r\n" +
//               "Host: " + host + "\r\n" +
//               "User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163\r\n" +
//               "Connection: close\r\n\r\n");
//  client.print(host);
    client.println("GET " + url + " HTTPS/1.1");
    client.print("Host: "); client.println(host);
    client.println("User-Agent: arduino/1.0");

  Serial.println("request sent");
  while (client.connected()) {
    String line = client.readString();
      Serial.println("headers received");
      Serial.println(line);
      break;
    }
  }
  


void loop() {
}
