#include <DHT.h>

// =====================================================
// SENTINEL-X - VERSION FINALE WOKWI
// =====================================================

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
// SEUILS TEMPERATURE
// ===============================

// Normal : 18°C à 28°C

const float TEMP_WARNING_LOW = 18.0;
const float TEMP_WARNING_HIGH = 28.0;

// Critique : < 10°C ou > 40°C

const float TEMP_CRITICAL_LOW = 10.0;
const float TEMP_CRITICAL_HIGH = 40.0;

// ===============================
// SEUILS HUMIDITE
// ===============================

// Normal : 30% à 70%

const float HUM_WARNING_LOW = 30.0;
const float HUM_WARNING_HIGH = 70.0;

// Critique : < 20% ou > 85%

const float HUM_CRITICAL_LOW = 20.0;
const float HUM_CRITICAL_HIGH = 85.0;

// ===============================
// SEUILS GAZ
// ===============================

// Variation par rapport à la baseline

const int GAS_DELTA_WARNING = 400;
const int GAS_DELTA_CRITICAL = 800;

// Seuils absolus de sécurité
// Même si la baseline est déjà élevée,
// ces valeurs déclenchent une alerte.

const int GAS_ABSOLUTE_WARNING = 3000;
const int GAS_ABSOLUTE_CRITICAL = 3500;

// ===============================
// TEMPS
// ===============================

// Calibration gaz pendant 5 secondes

const unsigned long CALIBRATION_TIME = 5000;

// Lecture chaque seconde

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
// SORTIES
// =====================================================

void applyOutputs()
{

    // Niveau 0

    if (threatLevel == 0)
    {

        digitalWrite(LED_GREEN, HIGH);
        digitalWrite(LED_ORANGE, LOW);
        digitalWrite(LED_RED, LOW);

        noTone(PIN_BUZZER);
    }

    // Niveau 1

    else if (threatLevel == 1)
    {

        digitalWrite(LED_GREEN, LOW);
        digitalWrite(LED_ORANGE, HIGH);
        digitalWrite(LED_RED, LOW);

        noTone(PIN_BUZZER);
    }

    // Niveau 2

    else
    {

        digitalWrite(LED_GREEN, LOW);
        digitalWrite(LED_ORANGE, LOW);
        digitalWrite(LED_RED, HIGH);

        tone(PIN_BUZZER, 1000);
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

    // ===================================================
    // NIVEAU 2 : CRITIQUE
    // ===================================================

    // Intrusion confirmée : PIR + caméra

    if (pir == HIGH && camera == 1)
    {
        return 2;
    }

    // Gaz critique absolu

    if (gasValue >= GAS_ABSOLUTE_CRITICAL)
    {
        return 2;
    }

    // Gaz critique relatif à la baseline

    if (
        calibrationFinished &&
        gasValue >= gasBaseline + GAS_DELTA_CRITICAL)
    {
        return 2;
    }

    // Température critique

    if (!isnan(temperature))
    {

        if (
            temperature < TEMP_CRITICAL_LOW ||
            temperature > TEMP_CRITICAL_HIGH)
        {
            return 2;
        }
    }

    // Humidité critique

    if (!isnan(humidity))
    {

        if (
            humidity < HUM_CRITICAL_LOW ||
            humidity > HUM_CRITICAL_HIGH)
        {
            return 2;
        }
    }

    // ===================================================
    // NIVEAU 1 : ANOMALIE
    // ===================================================

    // PIR seul

    if (pir == HIGH)
    {
        return 1;
    }

    // Gaz warning absolu

    if (gasValue >= GAS_ABSOLUTE_WARNING)
    {
        return 1;
    }

    // Gaz warning relatif à la baseline

    if (
        calibrationFinished &&
        gasValue >= gasBaseline + GAS_DELTA_WARNING)
    {
        return 1;
    }

    // Température hors plage normale

    if (!isnan(temperature))
    {

        if (
            temperature < TEMP_WARNING_LOW ||
            temperature > TEMP_WARNING_HIGH)
        {
            return 1;
        }
    }

    // Humidité hors plage normale

    if (!isnan(humidity))
    {

        if (
            humidity < HUM_WARNING_LOW ||
            humidity > HUM_WARNING_HIGH)
        {
            return 1;
        }
    }

    // ===================================================
    // NIVEAU 0
    // ===================================================

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

        Serial.println("================================");
        Serial.println("          SENTINEL-X");
        Serial.println("--------------------------------");
        Serial.println("ETAT : NORMAL");
        Serial.println("NIVEAU : 0");
        Serial.println("LED : VERTE");
        Serial.println("BUZZER : OFF");
        Serial.println("================================");
    }

    else if (threatLevel == 1)
    {

        Serial.println("================================");
        Serial.println("          SENTINEL-X");
        Serial.println("--------------------------------");
        Serial.println("ETAT : ANOMALIE");
        Serial.println("NIVEAU : 1");
        Serial.println("LED : ORANGE");
        Serial.println("BUZZER : OFF");
        Serial.println("================================");
    }

    else
    {

        Serial.println("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!");
        Serial.println("          SENTINEL-X");
        Serial.println("--------------------------------");
        Serial.println("ETAT : ALERTE CRITIQUE");
        Serial.println("NIVEAU : 2");
        Serial.println("LED : ROUGE");
        Serial.println("BUZZER : ON");
        Serial.println("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!");
    }

    Serial.println();

    previousThreatLevel = threatLevel;
}

// =====================================================
// SETUP
// =====================================================

void setup()
{

    Serial.begin(115200);

    delay(500);

    // Entrées

    pinMode(PIN_PIR, INPUT);
    pinMode(PIN_CAM, INPUT_PULLUP);
    pinMode(PIN_MQ2, INPUT);

    // Sorties

    pinMode(PIN_BUZZER, OUTPUT);

    pinMode(LED_GREEN, OUTPUT);
    pinMode(LED_ORANGE, OUTPUT);
    pinMode(LED_RED, OUTPUT);

    // DHT

    dht.begin();

    // Etat initial

    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(LED_ORANGE, LOW);
    digitalWrite(LED_RED, LOW);

    noTone(PIN_BUZZER);

    startTime = millis();

    Serial.println();
    Serial.println("================================");
    Serial.println("          SENTINEL-X");
    Serial.println("================================");

    Serial.println();

    Serial.println("Demarrage du systeme...");
    Serial.println("Calibration du capteur MQ-2...");
    Serial.println("Patientez 5 secondes.");

    Serial.println();
}

// =====================================================
// LOOP
// =====================================================

void loop()
{

    // ===================================================
    // CALIBRATION GAZ
    // ===================================================

    if (!calibrationFinished)
    {

        int gasValue = analogRead(PIN_MQ2);

        gasCalibrationSum += gasValue;

        gasCalibrationCount++;

        if (millis() - startTime < CALIBRATION_TIME)
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
        Serial.println("================================");
        Serial.println("CALIBRATION MQ-2 TERMINEE");
        Serial.println("================================");

        Serial.print("Gaz baseline           : ");
        Serial.println(gasBaseline);

        Serial.print("Warning relatif        : ");
        Serial.println(
            gasBaseline + GAS_DELTA_WARNING);

        Serial.print("Critique relatif       : ");
        Serial.println(
            gasBaseline + GAS_DELTA_CRITICAL);

        Serial.print("Warning absolu         : ");
        Serial.println(GAS_ABSOLUTE_WARNING);

        Serial.print("Critique absolu        : ");
        Serial.println(GAS_ABSOLUTE_CRITICAL);

        Serial.println();
        Serial.println("Sentinel-X operationnel.");
        Serial.println();

        previousThreatLevel = -1;

        return;
    }

    // ===================================================
    // ATTENDRE 1 SECONDE
    // ===================================================

    if (millis() - lastRead < READ_INTERVAL)
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

    // ===================================================
    // MESSAGE DE CHANGEMENT
    // ===================================================

    printThreatMessage();

    // ===================================================
    // AFFICHAGE CAPTEURS
    // ===================================================

    Serial.println("------- CAPTEURS -------");

    // Température

    Serial.print("Temperature : ");

    if (isnan(temperature))
    {

        Serial.println("ERREUR");
    }
    else
    {

        Serial.print(temperature, 1);
        Serial.println(" C");
    }

    // Humidité

    Serial.print("Humidite    : ");

    if (isnan(humidity))
    {

        Serial.println("ERREUR");
    }
    else
    {

        Serial.print(humidity, 1);
        Serial.println(" %");
    }

    // Gaz

    Serial.print("Gaz         : ");
    Serial.println(gasValue);

    Serial.print("Gaz baseline: ");
    Serial.println(gasBaseline);

    // PIR

    Serial.print("PIR         : ");

    if (pir == HIGH)
    {

        Serial.println("PRESENCE");
    }
    else
    {

        Serial.println("Aucune presence");
    }

    // Caméra

    Serial.print("Camera      : ");

    if (camera == 1)
    {

        Serial.println("PERSONNE DETECTEE");
    }
    else
    {

        Serial.println("Aucune detection");
    }

    // Niveau

    Serial.print("Niveau      : ");
    Serial.println(threatLevel);

    // ===================================================
    // JSON
    // ===================================================

    Serial.print("JSON : ");

    Serial.printf(
        "{\"temp\":%.1f,\"hum\":%.1f,\"gaz\":%d,\"gaz_base\":%d,\"pir\":%d,\"cam\":%d,\"level\":%d}\n",
        temperature,
        humidity,
        gasValue,
        gasBaseline,
        pir,
        camera,
        threatLevel);

    Serial.println("-------------------------");
    Serial.println();
}