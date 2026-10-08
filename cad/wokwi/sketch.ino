#include <DHT.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>

// =====================================================
// VIGIL-X - WOKWI + MQTT TLS
// =====================================================

// =====================================================
// CERTIFICAT CA MOSQUITTO
// =====================================================

const char MOSQUITTO_CA_CERT[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
MIIEAzCCAuugAwIBAgIUBY1hlCGvdj4NhBXkZ/uLUZNILAwwDQYJKoZIhvcNAQEL
BQAwgZAxCzAJBgNVBAYTAkdCMRcwFQYDVQQIDA5Vbml0ZWQgS2luZ2RvbTEOMAwG
A1UEBwwFRGVyYnkxEjAQBgNVBAoMCU1vc3F1aXR0bzELMAkGA1UECwwCQ0ExFjAU
BgNVBAMMDW1vc3F1aXR0by5vcmcxHzAdBgkqhkiG9w0BCQEWEHJvZ2VyQGF0Y2hv
by5vcmcwHhcNMjAwNjA5MTEwNjM5WhcNMzAwNjA3MTEwNjM5WjCBkDELMAkGA1UE
BhMCR0IxFzAVBgNVBAgMDlVuaXRlZCBLaW5nZG9tMQ4wDAYDVQQHDAVEZXJieTES
MBAGA1UECgwJTW9zcXVpdHRvMQswCQYDVQQLDAJDQTEWMBQGA1UEAwwNbW9zcXVp
dHRvLm9yZzEfMB0GCSqGSIb3DQEJARYQcm9nZXJAYXRjaG9vLm9yZzCCASIwDQYJ
KoZIhvcNAQEBBQADggEPADCCAQoCggEBAME0HKmIzfTOwkKLT3THHe+ObdizamPg
UZmD64Tf3zJdNeYGYn4CEXbyP6fy3tWc8S2boW6dzrH8SdFf9uo320GJA9B7U1FW
Te3xda/Lm3JFfaHjkWw7jBwcauQZjpGINHapHRlpiCZsquAthOgxW9SgDgYlGzEA
s06pkEFiMw+qDfLo/sxFKB6vQlFekMeCymjLCbNwPJyqyhFmPWwio/PDMruBTzPH
3cioBnrJWKXc3OjXdLGFJOfj7pP0j/dr2LH72eSvv3PQQFl90CZPFhrCUcRHSSxo
E6yjGOdnz7f6PveLIB574kQORwt8ePn0yidrTC1ictikED3nHYhMUOUCAwEAAaNT
MFEwHQYDVR0OBBYEFPVV6xBUFPiGKDyo5V3+Hbh4N9YSMB8GA1UdIwQYMBaAFPVV
6xBUFPiGKDyo5V3+Hbh4N9YSMA8GA1UdEwEB/wQFMAMBAf8wDQYJKoZIhvcNAQEL
BQADggEBAGa9kS21N70ThM6/Hj9D7mbVxKLBjVWe2TPsGfbl3rEDfZ+OKRZ2j6AC
6r7jb4TZO3dzF2p6dgbrlU71Y/4K0TdzIjRj3cQ3KSm41JvUQ0hZ/c04iGDg/xWf
+pp58nfPAYwuerruPNWmlStWAXf0UTqRtg4hQDWBuUFDJTuWuuBvEXudz74eh/wK
sMwfu1HFvjy5Z0iMDU8PUDepjVolOCue9ashlS4EB5IECdSR2TItnAIiIwimx839
LdUdRudafMu5T5Xma182OC0/u/xRlEm+tvKGGmfFcN0piqVl8OrSPBgIlb+1IKJE
m/XriWr/Cq4h/JfB7NTsezVslgkBaoU=
-----END CERTIFICATE-----
)EOF";

// ===============================
// BROCHES
// ===============================

#define PIN_DHT 15
#define PIN_PIR 13
#define PIN_MQ2 34
#define PIN_CAM 14

#define PIN_BUZZER 12

#define LED_GREEN 25
#define LED_ORANGE 26
#define LED_RED 27

// ===============================
// DHT22
// ===============================

#define DHTTYPE DHT22

DHT dht(PIN_DHT, DHTTYPE);

// ===============================
// WIFI WOKWI
// ===============================

const char *WIFI_SSID = "Wokwi-GUEST";
const char *WIFI_PASSWORD = "";

// ===============================
// MQTT TLS
// ===============================

const char *MQTT_SERVER = "test.mosquitto.org";
const int MQTT_PORT = 8883;

const char *MQTT_CLIENT_ID =
    "vigil-x-g5-esp32-wokwi-2026-a7f3";

const char *MQTT_TOPIC =
    "sentinel-x-g5-2026/sensors";

// ===============================
// CLIENT TLS
// ===============================

WiFiClientSecure secureClient;
PubSubClient mqttClient(secureClient);

// ===============================
// SEUILS TEMPERATURE
// ===============================

const float TEMP_WARNING_LOW = 18.0;
const float TEMP_WARNING_HIGH = 28.0;

const float TEMP_CRITICAL_LOW = 10.0;
const float TEMP_CRITICAL_HIGH = 40.0;

// ===============================
// SEUILS HUMIDITE
// ===============================

const float HUM_WARNING_LOW = 30.0;
const float HUM_WARNING_HIGH = 70.0;

const float HUM_CRITICAL_LOW = 20.0;
const float HUM_CRITICAL_HIGH = 85.0;

// ===============================
// SEUILS GAZ
// ===============================

const int GAS_DELTA_WARNING = 400;
const int GAS_DELTA_CRITICAL = 800;

const int GAS_ABSOLUTE_WARNING = 3000;
const int GAS_ABSOLUTE_CRITICAL = 3500;

// ===============================
// TEMPS
// ===============================

const unsigned long CALIBRATION_TIME = 5000;
const unsigned long READ_INTERVAL = 1000;

// ===============================
// VARIABLES
// ===============================

unsigned long startTime = 0;
unsigned long lastRead = 0;

long gasCalibrationSum = 0;
int gasCalibrationCount = 0;

int gasBaseline = 0;

bool calibrationFinished = false;

int threatLevel = 0;
int previousThreatLevel = -1;

// =====================================================
// WIFI
// =====================================================

void connectWiFi()
{
    if (WiFi.status() == WL_CONNECTED)
    {
        return;
    }

    Serial.print("Connexion WiFi");

    WiFi.mode(WIFI_STA);

    WiFi.begin(
        WIFI_SSID,
        WIFI_PASSWORD,
        6);

    while (WiFi.status() != WL_CONNECTED)
    {
        delay(250);
        Serial.print(".");
    }

    Serial.println();
    Serial.println("WiFi connecte.");

    Serial.print("Adresse IP ESP32 : ");
    Serial.println(WiFi.localIP());

    Serial.println();
}

// =====================================================
// TLS
// =====================================================

void configureTLS()
{
    Serial.println("Configuration TLS...");

    secureClient.setCACert(
        MOSQUITTO_CA_CERT);

    Serial.println(
        "Certificat CA Mosquitto charge.");

    Serial.println();
}

// =====================================================
// MQTT
// =====================================================

void connectMQTT()
{
    while (!mqttClient.connected())
    {
        Serial.print(
            "Connexion MQTT TLS... ");

        if (
            mqttClient.connect(
                MQTT_CLIENT_ID))
        {
            Serial.println("OK");

            Serial.print("Broker TLS : ");
            Serial.print(MQTT_SERVER);
            Serial.print(":");
            Serial.println(MQTT_PORT);

            Serial.print("Topic : ");
            Serial.println(MQTT_TOPIC);

            Serial.println(
                "Transport : MQTTS / TLS");

            Serial.println();
        }
        else
        {
            Serial.print(
                "ECHEC MQTT - code : ");

            Serial.println(
                mqttClient.state());

            Serial.println(
                "Nouvelle tentative dans 2 secondes...");

            delay(2000);
        }
    }
}

// =====================================================
// SORTIES
// =====================================================

void applyOutputs()
{
    if (threatLevel == 0)
    {
        digitalWrite(LED_GREEN, HIGH);
        digitalWrite(LED_ORANGE, LOW);
        digitalWrite(LED_RED, LOW);

        noTone(PIN_BUZZER);
    }
    else if (threatLevel == 1)
    {
        digitalWrite(LED_GREEN, LOW);
        digitalWrite(LED_ORANGE, HIGH);
        digitalWrite(LED_RED, LOW);

        noTone(PIN_BUZZER);
    }
    else
    {
        digitalWrite(LED_GREEN, LOW);
        digitalWrite(LED_ORANGE, LOW);
        digitalWrite(LED_RED, HIGH);

        tone(PIN_BUZZER, 1000);
    }
}

// =====================================================
// CALCUL NIVEAU DE MENACE
// =====================================================

int calculateThreatLevel(
    float temperature,
    float humidity,
    int gasValue,
    int pir,
    int camera)
{
    // ==========================================
    // NIVEAU 2 : CRITIQUE
    // ==========================================

    if (pir == HIGH && camera == 1)
    {
        return 2;
    }

    if (gasValue >= GAS_ABSOLUTE_CRITICAL)
    {
        return 2;
    }

    if (
        calibrationFinished &&
        gasValue >= gasBaseline + GAS_DELTA_CRITICAL)
    {
        return 2;
    }

    if (!isnan(temperature))
    {
        if (
            temperature < TEMP_CRITICAL_LOW ||
            temperature > TEMP_CRITICAL_HIGH)
        {
            return 2;
        }
    }

    if (!isnan(humidity))
    {
        if (
            humidity < HUM_CRITICAL_LOW ||
            humidity > HUM_CRITICAL_HIGH)
        {
            return 2;
        }
    }

    // ==========================================
    // NIVEAU 1 : WARNING
    // ==========================================

    if (pir == HIGH)
    {
        return 1;
    }

    if (camera == 1)
    {
        return 1;
    }

    if (gasValue >= GAS_ABSOLUTE_WARNING)
    {
        return 1;
    }

    if (
        calibrationFinished &&
        gasValue >= gasBaseline + GAS_DELTA_WARNING)
    {
        return 1;
    }

    if (!isnan(temperature))
    {
        if (
            temperature < TEMP_WARNING_LOW ||
            temperature > TEMP_WARNING_HIGH)
        {
            return 1;
        }
    }

    if (!isnan(humidity))
    {
        if (
            humidity < HUM_WARNING_LOW ||
            humidity > HUM_WARNING_HIGH)
        {
            return 1;
        }
    }

    return 0;
}

// =====================================================
// MESSAGE CHANGEMENT DE NIVEAU
// =====================================================

void printThreatMessage()
{
    if (threatLevel == previousThreatLevel)
    {
        return;
    }

    Serial.println();

    if (threatLevel == 0)
    {
        Serial.println("==============================");
        Serial.println("            VIGIL-X");
        Serial.println("ETAT : NORMAL");
        Serial.println("NIVEAU : 0");
        Serial.println("LED VERTE");
        Serial.println("BUZZER OFF");
        Serial.println("==============================");
    }
    else if (threatLevel == 1)
    {
        Serial.println("==============================");
        Serial.println("            VIGIL-X");
        Serial.println("ETAT : ANOMALIE");
        Serial.println("NIVEAU : 1");
        Serial.println("LED ORANGE");
        Serial.println("BUZZER OFF");
        Serial.println("==============================");
    }
    else
    {
        Serial.println("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!");
        Serial.println("            VIGIL-X");
        Serial.println("ETAT : ALERTE CRITIQUE");
        Serial.println("NIVEAU : 2");
        Serial.println("LED ROUGE");
        Serial.println("BUZZER ON");
        Serial.println("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!");
    }

    Serial.println();

    previousThreatLevel = threatLevel;
}

// =====================================================
// PUBLICATION MQTT TLS
// =====================================================

void publishSensorData(
    float temperature,
    float humidity,
    int gasValue,
    int pir,
    int camera)
{
    char payload[256];

    snprintf(
        payload,
        sizeof(payload),

        "{\"device_id\":\"esp32-wokwi\","
        "\"temp\":%.1f,"
        "\"hum\":%.1f,"
        "\"gaz\":%d,"
        "\"gaz_base\":%d,"
        "\"pir\":%d,"
        "\"cam\":%d,"
        "\"level\":%d}",

        temperature,
        humidity,
        gasValue,
        gasBaseline,
        pir,
        camera,
        threatLevel);

    bool published =
        mqttClient.publish(
            MQTT_TOPIC,
            payload);

    if (published)
    {
        Serial.print("MQTTS PUB -> ");
        Serial.print(MQTT_TOPIC);
        Serial.print(" : ");
        Serial.println(payload);
    }
    else
    {
        Serial.println(
            "ERREUR : publication MQTT TLS impossible");
    }
}

// =====================================================
// SETUP
// =====================================================

void setup()
{
    Serial.begin(115200);

    delay(500);

    // ===============================
    // ENTREES
    // ===============================

    pinMode(PIN_PIR, INPUT);
    pinMode(PIN_CAM, INPUT_PULLUP);
    pinMode(PIN_MQ2, INPUT);

    // ===============================
    // SORTIES
    // ===============================

    pinMode(PIN_BUZZER, OUTPUT);

    pinMode(LED_GREEN, OUTPUT);
    pinMode(LED_ORANGE, OUTPUT);
    pinMode(LED_RED, OUTPUT);

    // ===============================
    // DHT
    // ===============================

    dht.begin();

    // ===============================
    // ETAT INITIAL
    // ===============================

    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(LED_ORANGE, LOW);
    digitalWrite(LED_RED, LOW);

    noTone(PIN_BUZZER);

    Serial.println();
    Serial.println("==============================");
    Serial.println("            VIGIL-X");
    Serial.println("==============================");
    Serial.println();

    // ===============================
    // WIFI
    // ===============================

    connectWiFi();

    // ===============================
    // TLS
    // ===============================

    configureTLS();

    // ===============================
    // MQTT
    // ===============================

    mqttClient.setServer(
        MQTT_SERVER,
        MQTT_PORT);

    connectMQTT();

    // ===============================
    // CALIBRATION
    // ===============================

    startTime = millis();

    Serial.println(
        "Calibration du capteur MQ-2...");

    Serial.println(
        "Patientez 5 secondes.");

    Serial.println();
}

// =====================================================
// LOOP
// =====================================================

void loop()
{
    // ===================================================
    // MAINTIEN WIFI
    // ===================================================

    if (WiFi.status() != WL_CONNECTED)
    {
        connectWiFi();
    }

    // ===================================================
    // MAINTIEN MQTT
    // ===================================================

    if (!mqttClient.connected())
    {
        connectMQTT();
    }

    mqttClient.loop();

    // ===================================================
    // CALIBRATION MQ-2
    // ===================================================

    if (!calibrationFinished)
    {
        int gasValue =
            analogRead(PIN_MQ2);

        gasCalibrationSum += gasValue;
        gasCalibrationCount++;

        if (
            millis() - startTime <
            CALIBRATION_TIME)
        {
            delay(100);
            return;
        }

        if (gasCalibrationCount > 0)
        {
            gasBaseline =
                gasCalibrationSum /
                gasCalibrationCount;
        }

        calibrationFinished = true;

        Serial.println();
        Serial.println("==============================");
        Serial.println("CALIBRATION MQ-2 TERMINEE");
        Serial.println("==============================");

        Serial.print("Baseline gaz : ");
        Serial.println(gasBaseline);

        Serial.print("Warning relatif : ");
        Serial.println(
            gasBaseline +
            GAS_DELTA_WARNING);

        Serial.print("Critique relatif : ");
        Serial.println(
            gasBaseline +
            GAS_DELTA_CRITICAL);

        Serial.print("Warning absolu : ");
        Serial.println(
            GAS_ABSOLUTE_WARNING);

        Serial.print("Critique absolu : ");
        Serial.println(
            GAS_ABSOLUTE_CRITICAL);

        Serial.println();
        Serial.println(
            "VIGIL-X operationnel.");
        Serial.println();

        previousThreatLevel = -1;

        return;
    }

    // ===================================================
    // LECTURE CHAQUE SECONDE
    // ===================================================

    if (
        millis() - lastRead <
        READ_INTERVAL)
    {
        return;
    }

    lastRead = millis();

    // ===================================================
    // LECTURE CAPTEURS
    // ===================================================

    float temperature =
        dht.readTemperature();

    float humidity =
        dht.readHumidity();

    int gasValue =
        analogRead(PIN_MQ2);

    int pir =
        digitalRead(PIN_PIR);

    int camera =
        digitalRead(PIN_CAM) == LOW;

    // ===================================================
    // CALCUL MENACE
    // ===================================================

    threatLevel =
        calculateThreatLevel(
            temperature,
            humidity,
            gasValue,
            pir,
            camera);

    // ===================================================
    // LEDS + BUZZER
    // ===================================================

    applyOutputs();

    printThreatMessage();

    // ===================================================
    // AFFICHAGE LOCAL
    // ===================================================

    Serial.println(
        "------- CAPTEURS -------");

    Serial.print("Temperature : ");
    Serial.print(temperature, 1);
    Serial.println(" C");

    Serial.print("Humidite    : ");
    Serial.print(humidity, 1);
    Serial.println(" %");

    Serial.print("Gaz         : ");
    Serial.println(gasValue);

    Serial.print("Gaz baseline: ");
    Serial.println(gasBaseline);

    Serial.print("PIR         : ");
    Serial.println(pir);

    Serial.print("Camera      : ");
    Serial.println(camera);

    Serial.print("Niveau      : ");
    Serial.println(threatLevel);

    // ===================================================
    // PUBLICATION MQTT TLS
    // ===================================================

    publishSensorData(
        temperature,
        humidity,
        gasValue,
        pir,
        camera);

    Serial.println(
        "-------------------------");

    Serial.println();
}