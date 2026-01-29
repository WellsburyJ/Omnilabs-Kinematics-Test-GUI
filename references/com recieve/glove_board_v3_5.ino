// Modified firmware for ATtiny1616 to read 5 Bend Labs One-Axis ADS sensors over I2C
// Compatible with ESP32 ah-rc-03 protocol - sends binary frames over Serial
// Based on the ads.h HAL library protocol - command-based I2C communication

#define PRODUCT_CODE            5681

// I2C sensor addresses
#define NUM_SENSORS             5
const uint8_t sensor_addresses[NUM_SENSORS] = {0x09, 0x0C, 0x0F, 0x12, 0x15};

// Serial communication settings
#define SERIAL_BAUD             115200

// Reading interval (milliseconds)
#define READING_INTERVAL_MS     10

// Debug mode: Set to 1 to enable human-readable output in Serial Monitor
// When enabled, sends both binary frames (for ESP32) and ASCII text (for debugging)
#define DEBUG_SERIAL            0

// ADS Protocol Constants (from ads_util.h)
#define ADS_TRANSFER_SIZE       3
#define ADS_POLLED_MODE         5
#define ADS_SAMPLE              0
#define ADS_STRETCH_SAMPLE      3

// ESP32 Protocol Constants (from com.h)
#define SOH                     0x02
#define EOT                     0x04
#define FLEXIONVALUES           'F'
#define DATA_LENGTH             10  // 5 fingers × 2 bytes each
#define MPU6050_VALUES          'M'  // MPU6050 data type
#define MPU6050_DATA_LENGTH     12   // 3 accel + 3 gyro × 2 bytes each

// MPU6050 I2C address
#define MPU6050_ADDR            0x68

// MPU6050 Register addresses
#define MPU6050_REG_PWR_MGMT_1  0x6B
#define MPU6050_REG_ACCEL_XOUT_H 0x3B
#define MPU6050_REG_GYRO_XOUT_H  0x43

#include <Wire.h>

static uint8_t frameNumber = 0;
static uint8_t mpuFrameNumber = 0;

// Encode 16-bit signed integer to little-endian bytes
void encode_int16(int16_t value, uint8_t *buffer)
{
    buffer[0] = (uint8_t)(value & 0xFF);
    buffer[1] = (uint8_t)((value >> 8) & 0xFF);
}

// Calculate CRC (XOR checksum) for frame
uint8_t calculateCRC(uint8_t frameNum, uint8_t type, uint8_t length, uint8_t *data)
{
    uint8_t crc = 0;
    crc ^= frameNum;
    crc ^= type;
    crc ^= length;
    for (uint8_t i = 0; i < length; i++) {
        crc ^= data[i];
    }
    return crc;
}

// Send flexion values as binary frame to ESP32
void sendFlexionFrame(int16_t values[5])
{
    uint8_t frame[16];  // SOH + Frame# + Type + Length + Data(10) + CRC + EOT
    
    frame[0] = SOH;
    frame[1] = frameNumber++;
    frame[2] = FLEXIONVALUES;
    frame[3] = DATA_LENGTH;
    
    // Pack 5 finger values as little-endian 16-bit integers
    for (uint8_t i = 0; i < 5; i++) {
        encode_int16(values[i], &frame[4 + (i * 2)]);
    }
    
    // Calculate CRC
    frame[14] = calculateCRC(frame[1], frame[2], frame[3], &frame[4]);
    
    // EOT
    frame[15] = EOT;
    
    // Send entire frame (binary for ESP32)
    Serial.write(frame, 16);
    
    // Debug output: Human-readable format for Serial Monitor
    #if DEBUG_SERIAL
    Serial.print("DEBUG: Frame #");
    Serial.print(frame[1]);
    Serial.print(" | Flex: ");
    for (uint8_t i = 0; i < 5; i++) {
        Serial.print(values[i]);
        if (i < 4) Serial.print(" ");
    }
    Serial.print(" | CRC: 0x");
    if (frame[14] < 16) Serial.print("0");
    Serial.print(frame[14], HEX);
    Serial.print(" | Hex: ");
    for (uint8_t i = 0; i < 16; i++) {
        if (frame[i] < 16) Serial.print("0");
        Serial.print(frame[i], HEX);
        if (i < 15) Serial.print(" ");
    }
    Serial.println();
    #endif
}

// Send MPU6050 data as binary frame to ESP32
void sendMPU6050Frame(int16_t accel[3], int16_t gyro[3])
{
    uint8_t frame[18];  // SOH + Frame# + Type + Length + Data(12) + CRC + EOT
    
    frame[0] = SOH;
    frame[1] = mpuFrameNumber++;
    frame[2] = MPU6050_VALUES;
    frame[3] = MPU6050_DATA_LENGTH;
    
    // Pack 3 accelerometer values (bytes 4-9)
    for (uint8_t i = 0; i < 3; i++) {
        encode_int16(accel[i], &frame[4 + (i * 2)]);
    }
    
    // Pack 3 gyroscope values (bytes 10-15)
    for (uint8_t i = 0; i < 3; i++) {
        encode_int16(gyro[i], &frame[10 + (i * 2)]);
    }
    
    // Calculate CRC
    frame[16] = calculateCRC(frame[1], frame[2], frame[3], &frame[4]);
    
    // EOT
    frame[17] = EOT;
    
    // Send entire frame (binary for ESP32)
    Serial.write(frame, 18);
    
    // Debug output: Human-readable format for Serial Monitor
    #if DEBUG_SERIAL
    Serial.print("DEBUG: MPU Frame #");
    Serial.print(frame[1]);
    Serial.print(" | Accel: ");
    for (uint8_t i = 0; i < 3; i++) {
        Serial.print(accel[i]);
        if (i < 2) Serial.print(" ");
    }
    Serial.print(" | Gyro: ");
    for (uint8_t i = 0; i < 3; i++) {
        Serial.print(gyro[i]);
        if (i < 2) Serial.print(" ");
    }
    Serial.print(" | CRC: 0x");
    if (frame[16] < 16) Serial.print("0");
    Serial.print(frame[16], HEX);
    Serial.println();
    #endif
}

// Decode 16-bit signed integer from little-endian bytes (from ads_util.h)
int16_t ads_int16_decode(const uint8_t * p_encoded_data)
{
    return ( (((uint16_t)(p_encoded_data)[0])) |
             (((int16_t)(p_encoded_data)[1]) << 8 ));
}

// Write command to specific sensor address
bool ads_write_command_at_address(uint8_t addr, uint8_t command, uint8_t param1, uint8_t param2)
{
    Wire.beginTransmission(addr);
    Wire.write(command);
    Wire.write(param1);
    Wire.write(param2);
    return (Wire.endTransmission() == 0);
}

// Read data packet from specific sensor address
bool ads_read_packet_at_address(uint8_t addr, uint8_t *buffer)
{
    uint8_t bytesRead = Wire.requestFrom(addr, (uint8_t)ADS_TRANSFER_SIZE);
    
    if (bytesRead != ADS_TRANSFER_SIZE) {
        return false;
    }
    
    for (uint8_t i = 0; i < ADS_TRANSFER_SIZE; i++) {
        buffer[i] = Wire.read();
    }
    
    return true;
}

// Enable polled mode on specific sensor
bool ads_enable_polled_mode_at_address(uint8_t addr, bool enable)
{
    return ads_write_command_at_address(addr, ADS_POLLED_MODE, enable ? 1 : 0, 0);
}

// Read sensor data from specific address and convert to integer value
// Returns raw 16-bit integer value (not degrees)
int16_t readSensorAtAddress(uint8_t addr)
{
    uint8_t buffer[ADS_TRANSFER_SIZE];
    
    // Read data packet from sensor
    if (!ads_read_packet_at_address(addr, buffer)) {
        return 0;  // Return 0 on error
    }
    
    // Check if this is a bend sample packet
    if (buffer[0] == ADS_SAMPLE) {
        // Decode 16-bit value from bytes 1-2 (little-endian)
        // This is the raw sensor value - ESP32 will handle calibration
        int16_t raw = ads_int16_decode(&buffer[1]);
        return raw;
    }
    else if (buffer[0] == ADS_STRETCH_SAMPLE) {
        // This is stretch data, not bend data
        return 0;
    }
    
    return 0;
}

// Scan I2C bus and print all detected addresses
void scanI2CBus()
{
    Serial.println("Scanning I2C bus for devices...");
    Serial.println();
    
    uint8_t found = 0;
    uint8_t found_addresses[127];
    
    for (uint8_t address = 1; address < 127; address++) {
        Wire.beginTransmission(address);
        uint8_t error = Wire.endTransmission();
        
        if (error == 0) {
            found_addresses[found] = address;
            found++;
        }
    }
    
    if (found == 0) {
        Serial.println("No I2C devices found!");
    } else {
        Serial.print("Found ");
        Serial.print(found);
        Serial.println(" device(s):");
        
        for (uint8_t i = 0; i < found; i++) {
            Serial.print("  - 0x");
            if (found_addresses[i] < 16) Serial.print("0");
            Serial.println(found_addresses[i], HEX);
        }
    }
    
    Serial.println();
}

// Initialize MPU6050
bool mpu6050_init()
{
    // Wake up the MPU6050 (clear sleep bit in power management register)
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(MPU6050_REG_PWR_MGMT_1);
    Wire.write(0x00);  // Clear sleep bit
    if (Wire.endTransmission() != 0) {
        return false;
    }
    delay(100);  // Wait for MPU6050 to wake up
    return true;
}

// Read MPU6050 accelerometer and gyroscope data
bool mpu6050_read(int16_t *accel, int16_t *gyro)
{
    // Read accelerometer data (6 bytes starting at 0x3B)
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(MPU6050_REG_ACCEL_XOUT_H);
    if (Wire.endTransmission() != 0) {
        return false;
    }
    
    uint8_t bytesRead = Wire.requestFrom(MPU6050_ADDR, (uint8_t)14);  // Read accel (6) + temp (2) + gyro (6)
    if (bytesRead != 14) {
        return false;
    }
    
    // Read accelerometer data (X, Y, Z) - each is 16-bit signed, big-endian
    for (uint8_t i = 0; i < 3; i++) {
        uint8_t high = Wire.read();
        uint8_t low = Wire.read();
        accel[i] = (int16_t)((high << 8) | low);
    }
    
    // Skip temperature data (2 bytes)
    Wire.read();
    Wire.read();
    
    // Read gyroscope data (X, Y, Z) - each is 16-bit signed, big-endian
    for (uint8_t i = 0; i < 3; i++) {
        uint8_t high = Wire.read();
        uint8_t low = Wire.read();
        gyro[i] = (int16_t)((high << 8) | low);
    }
    
    return true;
}

void setup() {
    // Initial delay
    delay(2000);
    
    // Initialize Serial communication
    Serial.begin(SERIAL_BAUD);
    delay(500);
    
    // Wait for Serial to be ready
    while (!Serial && millis() < 3000) {
        ; // Wait up to 3 seconds
    }
    
    Serial.println("========================================");
    Serial.println("ATtiny1616 Multi-Sensor Reader");
    Serial.print("Reading ");
    Serial.print(NUM_SENSORS);
    Serial.println(" sensors");
    Serial.println("ESP32 Compatible Binary Protocol");
    Serial.println("========================================");
    Serial.println();
    
    // Initialize I2C bus as master
    Wire.begin();
    Wire.setClock(100000);  // 100kHz - more reliable for ATtiny1616
    delay(100);
    
    // Scan I2C bus and print all detected addresses
    scanI2CBus();
    
    // Initialize MPU6050
    Serial.println("Initializing MPU6050...");
    Serial.print("  MPU6050 (0x");
    if (MPU6050_ADDR < 16) Serial.print("0");
    Serial.print(MPU6050_ADDR, HEX);
    Serial.print("): ");
    
    // Check if MPU6050 responds
    Wire.beginTransmission(MPU6050_ADDR);
    uint8_t error = Wire.endTransmission();
    
    if (error == 0) {
        if (mpu6050_init()) {
            Serial.println("OK");
        } else {
            Serial.println("Failed to initialize");
        }
    } else {
        Serial.print("Not responding (error ");
        Serial.print(error);
        Serial.println(")");
    }
    Serial.println();
    
    // Initialize all sensors
    Serial.println("Initializing sensors...");
    uint8_t sensors_initialized = 0;
    
    for (uint8_t i = 0; i < NUM_SENSORS; i++) {
        uint8_t addr = sensor_addresses[i];
        Serial.print("  Sensor ");
        Serial.print(i + 1);
        Serial.print(" (0x");
        if (addr < 16) Serial.print("0");
        Serial.print(addr, HEX);
        Serial.print("): ");
        
        // Check if sensor responds
        Wire.beginTransmission(addr);
        uint8_t error = Wire.endTransmission();
        
        if (error == 0) {
            // Enable polled mode
            if (ads_enable_polled_mode_at_address(addr, true)) {
                Serial.println("OK");
                sensors_initialized++;
            } else {
                Serial.println("Failed to enable polled mode");
            }
        } else {
            Serial.print("Not responding (error ");
            Serial.print(error);
            Serial.println(")");
        }
        
        delay(50); // Small delay between sensors
    }
    
    Serial.println();
    Serial.print("Initialized ");
    Serial.print(sensors_initialized);
    Serial.print(" of ");
    Serial.print(NUM_SENSORS);
    Serial.println(" sensors");
    Serial.println();
    
    if (sensors_initialized > 0) {
        Serial.println("Starting readings...");
        Serial.println("Sending binary frames to ESP32");
        Serial.println("Flex Format: [SOH][Frame#][Type='F'][Length=10][5×2 bytes][CRC][EOT]");
        Serial.println("MPU Format:  [SOH][Frame#][Type='M'][Length=12][3 accel×2 + 3 gyro×2][CRC][EOT]");
        #if DEBUG_SERIAL
        Serial.println("DEBUG MODE: ASCII output enabled for Serial Monitor");
        Serial.println("Each frame will show: Frame# | Values | CRC");
        #endif
        Serial.println("---");
        delay(500);
    } else {
        Serial.println("ERROR: No sensors initialized!");
        Serial.println("Check wiring and I2C addresses.");
    }
}

void loop() {
    // Read all flex sensors
    int16_t flexValues[5];
    bool any_data = false;
    
    for (uint8_t i = 0; i < NUM_SENSORS; i++) {
        int16_t raw = readSensorAtAddress(sensor_addresses[i]);
        flexValues[i] = raw;
        if (raw != 0) {
            any_data = true;
        }
    }
    
    // Send binary frame to ESP32 if we have any flex data
    if (any_data) {
        sendFlexionFrame(flexValues);
    }
    
    // Read MPU6050 data
    int16_t accel[3] = {0, 0, 0};
    int16_t gyro[3] = {0, 0, 0};
    if (mpu6050_read(accel, gyro)) {
        // Send MPU6050 frame on separate line
        sendMPU6050Frame(accel, gyro);
    }
    
    delay(READING_INTERVAL_MS);
}

