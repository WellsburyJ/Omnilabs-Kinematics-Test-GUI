# ESP32 BLE Command Issue - Root Cause and Fix

## Problem

Pump control commands work over serial but not over BLE. Commands like `set outputs O0O0O0O0O0\n` (23 bytes) are being sent successfully from the Python side, but the ESP32 isn't processing them.

## Root Cause

The ESP32's BLE handler in `mBle.h` has a critical limitation:

```cpp
class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      String rxValue = pCharacteristic->getValue().c_str();  // Only gets LAST write!
      Serial.println("BLE << " + rxValue);
      // Parse the received command
      byte buffer[100];
      int length = rxValue.length();
      for (int i = 0; i < length && i < 100; i++) {
        buffer[i] = (byte)rxValue.charAt(i);
      }
      parse(buffer, length);
    }
};
```

**The problem:** `getValue()` only returns the value from the **last write**. If a command is sent in chunks (e.g., 20 bytes + 3 bytes), the ESP32 will only see the last chunk (3 bytes: `"O0\n"`), not the full command.

**Why it works over serial:** Serial communication buffers data automatically, so the ESP32 receives the complete command even if sent in multiple writes.

**Why it doesn't work over BLE:** BLE has a 20-byte MTU limit. Commands like `"set outputs O0O0O0O0O0\n"` are 23 bytes, so they must be chunked. The ESP32 doesn't buffer between BLE writes, so it only processes the last chunk.

## Solution

Modify the ESP32 firmware to buffer incoming BLE data until a complete line (ending with `\n`) is received.

### Required Changes to `mBle.h`

Add a buffer to accumulate BLE data:

```cpp
// Add this global variable at the top of mBle.h (after line 20)
String bleRxBuffer = "";  // Buffer for accumulating BLE data

// Modify the MyCallbacks class (replace lines 36-48):
class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      String rxValue = pCharacteristic->getValue().c_str();
      Serial.print("BLE << (chunk): ");
      Serial.println(rxValue);
      
      // Append to buffer
      bleRxBuffer += rxValue;
      
      // Check if we have a complete line (ends with \n or \r\n)
      int newlinePos = bleRxBuffer.indexOf('\n');
      if (newlinePos >= 0) {
        // Extract complete command (up to and including newline)
        String completeCommand = bleRxBuffer.substring(0, newlinePos + 1);
        bleRxBuffer = bleRxBuffer.substring(newlinePos + 1);  // Remove processed part
        
        Serial.print("BLE << (complete): ");
        Serial.println(completeCommand);
        
        // Parse the complete command
        byte buffer[100];
        int length = completeCommand.length();
        for (int i = 0; i < length && i < 100; i++) {
          buffer[i] = (byte)completeCommand.charAt(i);
        }
        parse(buffer, length);
      }
      // If no newline yet, wait for more data (buffer will accumulate)
    }
};
```

### Alternative: Negotiate Higher MTU

If your ESP32 BLE library supports MTU negotiation, you could negotiate a higher MTU (e.g., 23+ bytes) to send commands in one write. However, this requires changes to both the ESP32 firmware and the Python code, and may not be supported on all platforms.

## Testing

After modifying the ESP32 firmware:

1. Upload the modified firmware to the ESP32
2. Connect to the ESP32 via Serial Monitor (115200 baud) to see debug output
3. Try sending a pump command from the Python application
4. You should see in Serial Monitor:
   - `BLE << (chunk): set outputs O0O0O0O0` (first chunk)
   - `BLE << (chunk): O0\n` (second chunk)
   - `BLE << (complete): set outputs O0O0O0O0O0\n` (complete command)
   - `>: set outputs O0O0O0O0O0` (parsed command)

## Current Workaround

Until the ESP32 firmware is fixed, commands will not work over BLE. The Python code is correctly sending the commands, but the ESP32 is only receiving partial data.

## Files to Modify

- `references/ah-rc-03_29012025/mBle.h` - Add buffering logic to `MyCallbacks::onWrite()`


