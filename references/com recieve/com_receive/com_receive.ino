/*
 * ESP32 Serial Data Receiver
 * Receives 18-byte frames with IMU data and prints to Serial Monitor
 * Frame format: [SOH][Frame#][Type='M'][Length=12][Data][CRC][EOT]
 * Data: 3 accel (X,Y,Z) + 3 gyro (X,Y,Z) as 16-bit signed little-endian
 */

#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define SOH 0x02  // Match sender's SOH value
#define EOT 0x04
#define FRAME_SIZE_FLEX 16  // Flex frames are 16 bytes
#define FRAME_SIZE_MPU 18   // MPU frames are 18 bytes
#define DATA_START 4
#define DATA_SIZE_FLEX 10
#define DATA_SIZE_MPU 12

// Serial port for receiving data (adjust pins as needed)
#define RX_PIN 16
#define TX_PIN 17
#define BAUD_RATE 115200

// MPU6050 conversion constants (default ±2g accel, ±250°/s gyro)
#define ACCEL_SENSITIVITY 16384.0f  // LSB/g for ±2g range

// Use Serial for USB connection, or Serial1 for hardware serial
// If connected via USB, change SerialData to Serial below
HardwareSerial SerialData(1); // Use Serial1 for data input

uint8_t frameBuffer[18];  // Max frame size (MPU is 18 bytes)
uint8_t frameIndex = 0;
bool frameStarted = false;
uint8_t expectedFrameSize = 0;

void setup() {
  // Initialize Serial Monitor
  Serial.begin(115200);
  delay(1000);
  
  // Initialize Serial1 for data reception
  SerialData.begin(BAUD_RATE, SERIAL_8N1, RX_PIN, TX_PIN);
  
  Serial.println("ESP32 Serial Data Receiver - Ready");
}

void loop() {
  // Check if data is available
  while (SerialData.available() > 0) {
    uint8_t byte = SerialData.read();
    
    // Look for SOH to start frame
    if (!frameStarted && byte == SOH) {
      frameBuffer[0] = byte;
      frameIndex = 1;
      frameStarted = true;
      expectedFrameSize = 0;  // Will determine from frame type
    }
    // If frame started, collect bytes
    else if (frameStarted) {
      // Store the byte first
      if (frameIndex < 18) {  // Prevent buffer overflow
        frameBuffer[frameIndex] = byte;
        frameIndex++;
      } else {
        // Buffer overflow, reset silently
        frameStarted = false;
        frameIndex = 0;
        expectedFrameSize = 0;
        continue;
      }
      
      // After storing 3rd byte (index 2), we know the frame type and can determine size
      if (frameIndex == 3 && expectedFrameSize == 0) {
        uint8_t frameType = frameBuffer[2];
        if (frameType == 'F') {
          expectedFrameSize = FRAME_SIZE_FLEX;
        } else if (frameType == 'M') {
          expectedFrameSize = FRAME_SIZE_MPU;
        } else {
          // Unknown frame type, reset silently
          frameStarted = false;
          frameIndex = 0;
          expectedFrameSize = 0;
          continue;
        }
      }
      
      // Check if we received complete frame
      if (expectedFrameSize > 0 && frameIndex == expectedFrameSize) {
        if (frameBuffer[expectedFrameSize - 1] == EOT) {
          // Complete frame received
          processFrame();
        }
        frameStarted = false;
        frameIndex = 0;
        expectedFrameSize = 0;
      } else if (expectedFrameSize > 0 && frameIndex > expectedFrameSize) {
        // Frame too long, reset silently
        frameStarted = false;
        frameIndex = 0;
        expectedFrameSize = 0;
      }
    }
  }
}

void processFrame() {
  // Verify frame structure
  if (frameBuffer[0] != SOH) {
    return;
  }
  
  uint8_t frameNumber = frameBuffer[1];
  uint8_t frameType = frameBuffer[2];
  uint8_t frameSize = (frameType == 'F') ? FRAME_SIZE_FLEX : FRAME_SIZE_MPU;
  
  if (frameBuffer[frameSize - 1] != EOT) {
    return;
  }
  
  // Process based on frame type
  if (frameType == 'F') {
    // Flex frame (16 bytes)
    // Extract 5 finger values (16-bit signed little-endian)
    int16_t flexValuesRaw[5];
    for (uint8_t i = 0; i < 5; i++) {
      flexValuesRaw[i] = (int16_t)(frameBuffer[DATA_START + (i * 2)] | 
                                    (frameBuffer[DATA_START + (i * 2) + 1] << 8));
    }
    
    // Convert raw values to bend angles in degrees
    // Formula: angle = raw / 64 (no sign inversion)
    String values = "values flex ";
    for (uint8_t i = 0; i < 5; i++) {
      float angle = flexValuesRaw[i] / 64.0f;
      values += String(angle, 2);  // Format with 2 decimal places
      values += ",";
    }
    values += "\n";
    Serial.print(values);
    
  } else if (frameType == 'M') {
    // MPU6050 frame (18 bytes)
    // Extract 16-bit signed integers (little-endian)
    int16_t accelX_raw = (int16_t)(frameBuffer[DATA_START] | (frameBuffer[DATA_START + 1] << 8));
    int16_t accelY_raw = (int16_t)(frameBuffer[DATA_START + 2] | (frameBuffer[DATA_START + 3] << 8));
    int16_t accelZ_raw = (int16_t)(frameBuffer[DATA_START + 4] | (frameBuffer[DATA_START + 5] << 8));
    
    // Convert to physical units
    float accelX_g = accelX_raw / ACCEL_SENSITIVITY;  // g
    float accelY_g = accelY_raw / ACCEL_SENSITIVITY;  // g
    float accelZ_g = accelZ_raw / ACCEL_SENSITIVITY;  // g
    
    // Calculate orientation angles from accelerometer (pitch and roll)
    // Pitch: rotation around Y axis (nose up/down)
    float pitch_float = atan2(accelX_g, sqrt(accelY_g * accelY_g + accelZ_g * accelZ_g)) * 180.0f / M_PI;
    
    // Roll: rotation around X axis (wing up/down)
    float roll_float = atan2(accelY_g, sqrt(accelX_g * accelX_g + accelZ_g * accelZ_g)) * 180.0f / M_PI;
    
    // Convert to integers (matching ah-rc-03 format)
    int yaw = 0;  // Yaw cannot be determined from accelerometer alone (would need magnetometer)
    int pitch = (int)round(pitch_float);
    int roll = (int)round(roll_float);
    
    // Print in ah-rc-03 format: values ypr yaw,pitch,roll,\n
    char buffer[50];
    sprintf(buffer, "%d,%d,%d", yaw, pitch, roll);
    String ypr = buffer;
    String values = "values ypr ";
    values += ypr;
    values += ",\n";
    Serial.print(values);
  }
}

