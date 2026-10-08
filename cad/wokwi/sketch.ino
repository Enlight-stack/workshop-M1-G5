#include <DHT.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>

#include <time.h>
#include "mbedtls/md.h"

// =====================================================
// VIGIL-X
// MQTT TLS + HMAC-SHA256 + NTP
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

// =====================================================
// SECRET HMAC
// =====================================================
//
// Mets exactement la même clé que HMAC_SECRET
// dans ton fichier .env.
// Ne commit pas la vraie clé sur GitHub.
//

const char *HMAC_SECRET =
    "126994ddffbe6a14bf4b3d27387d7b4e3da3675162d3a676287b5e5749ec606f";

// =====================================================
// BROCHES
// =====================================================

#define PIN_DHT 15
#define PIN_PIR 13
#define PIN_MQ2 34
#define PIN_CAM 14

#define PIN_BUZZER 12

#define LED_GREEN 25
#define LED_ORANGE 26
#define LED_RED 27

// =====================================================
// DHT22
// =====================================================

#define DHTTYPE DHT22

DHT dht(
    PIN_DHT,
    DHTTYPE);

// =====================================================
// WIFI
// =====================================================

const char *WIFI_SSID =
    "Wokwi-GUEST";

const char *WIFI_PASSWORD =
    "";

// =====================================================
// MQTT TLS
// =====================================================

const char *MQTT_SERVER =
    "test.mosquitto.org";

const int MQTT_PORT =
    8883;

const char *MQTT_CLIENT_ID =
    "vigil-x-g5-esp32-wokwi-2026-a7f3";

const char *MQTT_TOPIC =
    "sentinel-x-g5-2026/sensors";

const char *DEVICE_ID =
    "esp32-wokwi";

WiFiClientSecure secureClient;

PubSubClient mqttClient(
    secureClient);

// =====================================================
// SEUILS TEMPERATURE
// =====================================================

const float TEMP_WARNING_LOW = 18.0;
const float TEMP_WARNING_HIGH = 28.0;

const float TEMP_CRITICAL_LOW = 10.0;
const float TEMP_CRITICAL_HIGH = 40.0;

// =====================================================
// SEUILS HUMIDITE
// =====================================================

const float HUM_WARNING_LOW = 30.0;
const float HUM_WARNING_HIGH = 70.0;

const float HUM_CRITICAL_LOW = 20.0;
const float HUM_CRITICAL_HIGH = 85.0;

// =====================================================
// SEUILS GAZ
// =====================================================

const int GAS_DELTA_WARNING = 400;
const int GAS_DELTA_CRITICAL = 800;

const int GAS_ABSOLUTE_WARNING = 3000;
const int GAS_ABSOLUTE_CRITICAL = 3500;

// =====================================================
// TIMERS
// =====================================================

const unsigned long CALIBRATION_TIME = 5000;

const unsigned long READ_INTERVAL = 1000;

// Resynchronisation NTP toutes les 60 secondes
const unsigned long NTP_RESYNC_INTERVAL = 60000;

// =====================================================
// VARIABLES
// =====================================================

unsigned long startTime = 0;

unsigned long lastRead = 0;

unsigned long lastNtpSync = 0;

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
    if (
        WiFi.status() ==
        WL_CONNECTED)
    {
        return;
    }

    Serial.print(
        "Connexion WiFi");

    WiFi.mode(
        WIFI_STA);

    WiFi.begin(
        WIFI_SSID,
        WIFI_PASSWORD,
        6);

    while (
        WiFi.status() !=
        WL_CONNECTED)
    {
        delay(
            250);

        Serial.print(
            ".");
    }

    Serial.println();

    Serial.println(
        "WiFi connecte.");

    Serial.print(
        "Adresse IP ESP32 : ");

    Serial.println(
        WiFi.localIP());

    Serial.println();
}

// =====================================================
// SYNCHRONISATION NTP
// =====================================================

void synchronizeTime(
    bool verbose = true)
{
    if (
        WiFi.status() !=
        WL_CONNECTED)
    {
        return;
    }

    if (
        verbose)
    {
        Serial.print(
            "Synchronisation NTP");
    }

    configTime(
        0,
        0,
        "pool.ntp.org",
        "time.google.com",
        "time.nist.gov");

    time_t now =
        time(
            nullptr);

    int attempts = 0;

    while (
        now <
            1700000000 &&
        attempts <
            20)
    {
        delay(
            250);

        if (
            verbose)
        {
            Serial.print(
                ".");
        }

        now =
            time(
                nullptr);

        attempts++;
    }

    lastNtpSync =
        millis();

    if (
        verbose)
    {
        Serial.println();

        if (
            now >=
            1700000000)
        {
            Serial.println(
                "Heure synchronisee.");

            Serial.print(
                "Timestamp UNIX : ");

            Serial.println(
                (long long)
                    now);
        }

        else
        {
            Serial.println(
                "ATTENTION : synchronisation NTP incomplete.");
        }

        Serial.println();
    }
}

// =====================================================
// RESYNCHRONISATION NTP PERIODIQUE
// =====================================================

void checkNtpResync()
{
    if (
        millis() -
            lastNtpSync <
        NTP_RESYNC_INTERVAL)
    {
        return;
    }

    Serial.println();

    Serial.println(
        "[NTP] Resynchronisation periodique...");

    synchronizeTime(
        false);

    time_t now =
        time(
            nullptr);

    Serial.print(
        "[NTP] Timestamp actuel : ");

    Serial.println(
        (long long)
            now);

    Serial.println(
        "[NTP] Synchronisation terminee.");

    Serial.println();
}

// =====================================================
// CONFIGURATION TLS
// =====================================================

void configureTLS()
{
    Serial.println(
        "Configuration TLS...");

    secureClient.setCACert(
        MOSQUITTO_CA_CERT);

    Serial.println(
        "Certificat CA Mosquitto charge.");

    Serial.println();
}

// =====================================================
// HMAC SHA-256
// =====================================================

String calculateHMAC(
    const String &message)
{
    unsigned char result[32];

    const mbedtls_md_info_t *mdInfo =
        mbedtls_md_info_from_type(
            MBEDTLS_MD_SHA256);

    if (
        mdInfo ==
        nullptr)
    {
        return "";
    }

    int resultCode =
        mbedtls_md_hmac(
            mdInfo,

            (
                const unsigned char *)
                HMAC_SECRET,

            strlen(
                HMAC_SECRET),

            (
                const unsigned char *)
                message.c_str(),

            message.length(),

            result);

    if (
        resultCode !=
        0)
    {
        Serial.print(
            "[HMAC] Erreur calcul : ");

        Serial.println(
            resultCode);

        return "";
    }

    char hexResult[65];

    for (
        int i = 0;
        i < 32;
        i++)
    {
        sprintf(
            &hexResult[i * 2],

            "%02x",

            result[i]);
    }

    hexResult[64] =
        '\0';

    return String(
        hexResult);
}

// =====================================================
// CONNEXION MQTT
// =====================================================

void connectMQTT()
{
    while (
        !mqttClient.connected())
    {
        Serial.print(
            "Connexion MQTT TLS... ");

        if (
            mqttClient.connect(
                MQTT_CLIENT_ID))
        {
            Serial.println(
                "OK");

            Serial.print(
                "Broker TLS : ");

            Serial.print(
                MQTT_SERVER);

            Serial.print(
                ":");

            Serial.println(
                MQTT_PORT);

            Serial.print(
                "Topic : ");

            Serial.println(
                MQTT_TOPIC);

            Serial.println(
                "Transport : MQTTS / TLS");

            Serial.println(
                "Authentification : HMAC-SHA256");

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

            delay(
                2000);
        }
    }
}

// =====================================================
// SORTIES
// =====================================================

void applyOutputs()
{
    if (
        threatLevel ==
        0)
    {
        digitalWrite(
            LED_GREEN,
            HIGH);

        digitalWrite(
            LED_ORANGE,
            LOW);

        digitalWrite(
            LED_RED,
            LOW);

        noTone(
            PIN_BUZZER);
    }

    else if (
        threatLevel ==
        1)
    {
        digitalWrite(
            LED_GREEN,
            LOW);

        digitalWrite(
            LED_ORANGE,
            HIGH);

        digitalWrite(
            LED_RED,
            LOW);

        noTone(
            PIN_BUZZER);
    }

    else
    {
        digitalWrite(
            LED_GREEN,
            LOW);

        digitalWrite(
            LED_ORANGE,
            LOW);

        digitalWrite(
            LED_RED,
            HIGH);

        tone(
            PIN_BUZZER,
            1000);
    }
}

// =====================================================
// CALCUL DU NIVEAU DE MENACE
// =====================================================

int calculateThreatLevel(
    float temperature,
    float humidity,
    int gasValue,
    int pir,
    int camera)
{
    // =================================================
    // NIVEAU 2 : CRITIQUE
    // =================================================

    if (
        pir ==
            HIGH &&
        camera ==
            1)
    {
        return 2;
    }

    if (
        gasValue >=
        GAS_ABSOLUTE_CRITICAL)
    {
        return 2;
    }

    if (
        calibrationFinished &&
        gasValue >=
            gasBaseline +
                GAS_DELTA_CRITICAL)
    {
        return 2;
    }

    if (
        !isnan(
            temperature))
    {
        if (
            temperature <
                TEMP_CRITICAL_LOW ||
            temperature >
                TEMP_CRITICAL_HIGH)
        {
            return 2;
        }
    }

    if (
        !isnan(
            humidity))
    {
        if (
            humidity <
                HUM_CRITICAL_LOW ||
            humidity >
                HUM_CRITICAL_HIGH)
        {
            return 2;
        }
    }

    // =================================================
    // NIVEAU 1 : WARNING
    // =================================================

    if (
        pir ==
        HIGH)
    {
        return 1;
    }

    if (
        camera ==
        1)
    {
        return 1;
    }

    if (
        gasValue >=
        GAS_ABSOLUTE_WARNING)
    {
        return 1;
    }

    if (
        calibrationFinished &&
        gasValue >=
            gasBaseline +
                GAS_DELTA_WARNING)
    {
        return 1;
    }

    if (
        !isnan(
            temperature))
    {
        if (
            temperature <
                TEMP_WARNING_LOW ||
            temperature >
                TEMP_WARNING_HIGH)
        {
            return 1;
        }
    }

    if (
        !isnan(
            humidity))
    {
        if (
            humidity <
                HUM_WARNING_LOW ||
            humidity >
                HUM_WARNING_HIGH)
        {
            return 1;
        }
    }

    return 0;
}

// =====================================================
// AFFICHAGE DU NIVEAU
// =====================================================

void printThreatMessage()
{
    if (
        threatLevel ==
        previousThreatLevel)
    {
        return;
    }

    Serial.println();

    if (
        threatLevel ==
        0)
    {
        Serial.println(
            "==============================");

        Serial.println(
            "            VIGIL-X");

        Serial.println(
            "ETAT : NORMAL");

        Serial.println(
            "NIVEAU : 0");

        Serial.println(
            "LED VERTE");

        Serial.println(
            "BUZZER OFF");

        Serial.println(
            "==============================");
    }

    else if (
        threatLevel ==
        1)
    {
        Serial.println(
            "==============================");

        Serial.println(
            "            VIGIL-X");

        Serial.println(
            "ETAT : ANOMALIE");

        Serial.println(
            "NIVEAU : 1");

        Serial.println(
            "LED ORANGE");

        Serial.println(
            "BUZZER OFF");

        Serial.println(
            "==============================");
    }

    else
    {
        Serial.println(
            "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!");

        Serial.println(
            "            VIGIL-X");

        Serial.println(
            "ETAT : ALERTE CRITIQUE");

        Serial.println(
            "NIVEAU : 2");

        Serial.println(
            "LED ROUGE");

        Serial.println(
            "BUZZER ON");

        Serial.println(
            "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!");
    }

    Serial.println();

    previousThreatLevel =
        threatLevel;
}

// =====================================================
// PUBLICATION MQTT TLS + HMAC
// =====================================================

void publishSensorData(
    float temperature,
    float humidity,
    int gasValue,
    int pir,
    int camera)
{
    // =================================================
    // VERIFICATION TIMESTAMP
    // =================================================

    time_t timestamp =
        time(
            nullptr);

    if (
        timestamp <
        1700000000)
    {
        Serial.println(
            "[SECURITY] Timestamp invalide.");

        Serial.println(
            "[SECURITY] Publication annulee.");

        return;
    }

    // =================================================
    // CHAINE CANONIQUE A SIGNER
    // =================================================
    //
    // IMPORTANT :
    // doit rester identique au backend Python.
    //
    // device_id|temp|hum|gaz|gaz_base|pir|cam|level|timestamp
    // =================================================

    char signingBuffer[256];

    snprintf(
        signingBuffer,

        sizeof(
            signingBuffer),

        "%s|%.1f|%.1f|%d|%d|%d|%d|%d|%lld",

        DEVICE_ID,

        temperature,

        humidity,

        gasValue,

        gasBaseline,

        pir,

        camera,

        threatLevel,

        (long long)
            timestamp);

    String signingString =
        String(
            signingBuffer);

    // =================================================
    // SIGNATURE HMAC
    // =================================================

    String signature =
        calculateHMAC(
            signingString);

    if (
        signature.length() !=
        64)
    {
        Serial.println(
            "[SECURITY] Signature HMAC invalide.");

        return;
    }

    // =================================================
    // JSON FINAL
    // =================================================

    char payload[512];

    snprintf(
        payload,

        sizeof(
            payload),

        "{"
        "\"device_id\":\"%s\","
        "\"temp\":%.1f,"
        "\"hum\":%.1f,"
        "\"gaz\":%d,"
        "\"gaz_base\":%d,"
        "\"pir\":%d,"
        "\"cam\":%d,"
        "\"level\":%d,"
        "\"timestamp\":%lld,"
        "\"signature\":\"%s\""
        "}",

        DEVICE_ID,

        temperature,

        humidity,

        gasValue,

        gasBaseline,

        pir,

        camera,

        threatLevel,

        (long long)
            timestamp,

        signature.c_str());

    // =================================================
    // PUBLICATION
    // =================================================

    bool published =
        mqttClient.publish(
            MQTT_TOPIC,
            payload);

    if (
        published)
    {
        Serial.print(
            "MQTTS + HMAC PUB -> ");

        Serial.println(
            payload);
    }

    else
    {
        Serial.println(
            "ERREUR publication MQTT.");
    }
}

// =====================================================
// SETUP
// =====================================================

void setup()
{
    Serial.begin(
        115200);

    delay(
        500);

    // =================================================
    // ENTREES
    // =================================================

    pinMode(
        PIN_PIR,
        INPUT);

    pinMode(
        PIN_CAM,
        INPUT_PULLUP);

    pinMode(
        PIN_MQ2,
        INPUT);

    // =================================================
    // SORTIES
    // =================================================

    pinMode(
        PIN_BUZZER,
        OUTPUT);

    pinMode(
        LED_GREEN,
        OUTPUT);

    pinMode(
        LED_ORANGE,
        OUTPUT);

    pinMode(
        LED_RED,
        OUTPUT);

    dht.begin();

    digitalWrite(
        LED_GREEN,
        HIGH);

    digitalWrite(
        LED_ORANGE,
        LOW);

    digitalWrite(
        LED_RED,
        LOW);

    noTone(
        PIN_BUZZER);

    Serial.println();

    Serial.println(
        "==============================");

    Serial.println(
        "            VIGIL-X");

    Serial.println(
        "==============================");

    Serial.println();

    // =================================================
    // WIFI
    // =================================================

    connectWiFi();

    // =================================================
    // NTP
    // =================================================

    synchronizeTime(
        true);

    // =================================================
    // TLS
    // =================================================

    configureTLS();

    // =================================================
    // MQTT
    // =================================================

    mqttClient.setServer(
        MQTT_SERVER,
        MQTT_PORT);

    connectMQTT();

    // =================================================
    // CALIBRATION MQ-2
    // =================================================

    startTime =
        millis();

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
    // =================================================
    // WIFI
    // =================================================

    if (
        WiFi.status() !=
        WL_CONNECTED)
    {
        connectWiFi();

        synchronizeTime(
            true);
    }

    // =================================================
    // NTP PERIODIQUE
    // =================================================

    checkNtpResync();

    // =================================================
    // MQTT
    // =================================================

    if (
        !mqttClient.connected())
    {
        connectMQTT();
    }

    mqttClient.loop();

    // =================================================
    // CALIBRATION MQ-2
    // =================================================

    if (
        !calibrationFinished)
    {
        int gasValue =
            analogRead(
                PIN_MQ2);

        gasCalibrationSum +=
            gasValue;

        gasCalibrationCount++;

        if (
            millis() -
                startTime <
            CALIBRATION_TIME)
        {
            delay(
                100);

            return;
        }

        if (
            gasCalibrationCount >
            0)
        {
            gasBaseline =
                gasCalibrationSum /
                gasCalibrationCount;
        }

        calibrationFinished =
            true;

        Serial.println();

        Serial.println(
            "==============================");

        Serial.println(
            "CALIBRATION MQ-2 TERMINEE");

        Serial.println(
            "==============================");

        Serial.print(
            "Baseline gaz : ");

        Serial.println(
            gasBaseline);

        Serial.println();

        Serial.println(
            "VIGIL-X operationnel.");

        Serial.println();

        previousThreatLevel =
            -1;

        return;
    }

    // =================================================
    // LECTURE CAPTEURS
    // =================================================

    if (
        millis() -
            lastRead <
        READ_INTERVAL)
    {
        return;
    }

    lastRead =
        millis();

    float temperature =
        dht.readTemperature();

    float humidity =
        dht.readHumidity();

    int gasValue =
        analogRead(
            PIN_MQ2);

    int pir =
        digitalRead(
            PIN_PIR);

    int camera =
        digitalRead(
            PIN_CAM) ==
        LOW;

    // =================================================
    // CALCUL MENACE
    // =================================================

    threatLevel =
        calculateThreatLevel(
            temperature,
            humidity,
            gasValue,
            pir,
            camera);

    // =================================================
    // SORTIES
    // =================================================

    applyOutputs();

    printThreatMessage();

    // =================================================
    // AFFICHAGE
    // =================================================

    Serial.println(
        "------- CAPTEURS -------");

    Serial.print(
        "Temperature : ");

    Serial.print(
        temperature,
        1);

    Serial.println(
        " C");

    Serial.print(
        "Humidite    : ");

    Serial.print(
        humidity,
        1);

    Serial.println(
        " %");

    Serial.print(
        "Gaz         : ");

    Serial.println(
        gasValue);

    Serial.print(
        "Gaz baseline: ");

    Serial.println(
        gasBaseline);

    Serial.print(
        "PIR         : ");

    Serial.println(
        pir);

    Serial.print(
        "Camera      : ");

    Serial.println(
        camera);

    Serial.print(
        "Niveau      : ");

    Serial.println(
        threatLevel);

    // =================================================
    // MQTT TLS + HMAC
    // =================================================

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