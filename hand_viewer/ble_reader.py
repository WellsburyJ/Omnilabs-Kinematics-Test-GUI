"""
Bluetooth Low Energy (BLE) reader for ESP32 communication.
Handles device discovery, connection, and line-by-line reading over BLE.
"""

import asyncio
from threading import Thread
from typing import Optional, Callable, List
from bleak import BleakScanner, BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice

try:
    from .data_reader import DataReader
except ImportError:
    from data_reader import DataReader

# Common BLE UART service UUIDs
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"  # Nordic UART Service
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  # RX (write)
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # TX (notify)

# Alternative common UART service UUIDs
ALT_UART_SERVICE_UUID = "0000FFE0-0000-1000-8000-00805F9B34FB"
ALT_UART_RX_CHAR_UUID = "0000FFE1-0000-1000-8000-00805F9B34FB"
ALT_UART_TX_CHAR_UUID = "0000FFE1-0000-1000-8000-00805F9B34FB"


class BLEReader(DataReader):
    """Thread-safe BLE reader."""
    
    def __init__(self, on_line_received: Callable[[str], None]):
        """
        Args:
            on_line_received: Callback function called with each received line
        """
        super().__init__(on_line_received)
        self.client: Optional[BleakClient] = None
        self.device_address: Optional[str] = None
        self.device_name_str: Optional[str] = None
        self.running = False
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        self.loop_thread: Optional[Thread] = None
        self.tx_characteristic: Optional[BleakGATTCharacteristic] = None
        self.rx_characteristic: Optional[BleakGATTCharacteristic] = None
        self.buffer = ""
        self._connection_lock = asyncio.Lock()
        self._last_error: Optional[str] = None
    
    @staticmethod
    def list_available_devices() -> List[str]:
        """List all available BLE devices (blocking)."""
        try:
            # Run scanner in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            devices = loop.run_until_complete(BLEReader._scan_devices())
            loop.close()
            return devices
        except Exception as e:
            print(f"BLE scan error: {e}")
            return []
    
    @staticmethod
    async def _scan_devices() -> List[str]:
        """Scan for BLE devices (async)."""
        devices = await BleakScanner.discover(timeout=5.0)
        result = []
        for device in devices:
            # Format: "Device Name (Address)"
            if device.name:
                result.append(f"{device.name} ({device.address})")
            else:
                result.append(device.address)
        return result
    
    def _start_event_loop(self):
        """Start the asyncio event loop in a separate thread."""
        def run_loop():
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            self.event_loop.run_forever()
        
        self.loop_thread = Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
        # Wait a bit for loop to start
        import time
        time.sleep(0.1)
    
    def _stop_event_loop(self):
        """Stop the asyncio event loop."""
        if self.event_loop and self.event_loop.is_running():
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)
        if self.loop_thread:
            self.loop_thread.join(timeout=2.0)
        self.event_loop = None
        self.loop_thread = None
    
    def connect(self, device: str, **kwargs) -> bool:
        """
        Connect to the specified BLE device.
        
        Args:
            device: Device identifier (can be address or "Name (Address)" format)
            **kwargs: Additional connection parameters (ignored for now)
            
        Returns:
            True if connection successful, False otherwise
        """
        if self.client and self.client.is_connected:
            self.disconnect()
        
        # Extract address from device string (handle "Name (Address)" format)
        address = device
        if "(" in device and ")" in device:
            address = device.split("(")[1].split(")")[0]
        
        try:
            # Start event loop if not running
            if not self.event_loop or not self.event_loop.is_running():
                self._start_event_loop()
            
            # Run connection in event loop
            future = asyncio.run_coroutine_threadsafe(
                self._connect_async(address), self.event_loop
            )
            success = future.result(timeout=15.0)  # Increased timeout
            
            if success:
                self.device_address = address
                self.device_name_str = device
                self.running = True
                return True
            else:
                print(f"BLE connection failed: Could not connect to {address}")
                return False
        except asyncio.TimeoutError:
            error_msg = f"BLE connection timeout: Device {address} did not respond within 15 seconds"
            print(error_msg)
            self._last_error = error_msg
            return False
        except Exception as e:
            error_msg = f"Failed to connect to BLE device {device}: {type(e).__name__}: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self._last_error = error_msg
            return False
    
    async def _connect_async(self, address: str) -> bool:
        """Async connection logic."""
        try:
            print(f"Attempting to connect to BLE device: {address}")
            self.client = BleakClient(address)
            await self.client.connect(timeout=10.0)
            
            if not self.client.is_connected:
                print(f"BLE connection failed: Client reports not connected")
                return False
            
            print(f"BLE device connected, discovering services...")
            # Discover services and characteristics
            # In newer versions of bleak (2.x), services is a property (BleakGATTServiceCollection)
            # Access it directly - it's automatically discovered on connect
            services = self.client.services
            # Convert to list for iteration and counting
            services_list = list(services)
            print(f"Found {len(services_list)} services")
            
            # Try to find UART service and characteristics
            for service in services_list:
                # Check for Nordic UART Service
                if service.uuid.lower() == UART_SERVICE_UUID.lower():
                    print(f"Found Nordic UART Service: {service.uuid}")
                    for char in service.characteristics:
                        if char.uuid.lower() == UART_TX_CHAR_UUID.lower():
                            self.tx_characteristic = char
                            print(f"Found TX characteristic: {char.uuid}")
                        elif char.uuid.lower() == UART_RX_CHAR_UUID.lower():
                            self.rx_characteristic = char
                            print(f"Found RX characteristic: {char.uuid}")
                
                # Check for alternative UART service
                elif service.uuid.lower() == ALT_UART_SERVICE_UUID.lower():
                    print(f"Found Alternative UART Service: {service.uuid}")
                    for char in service.characteristics:
                        if char.uuid.lower() == ALT_UART_TX_CHAR_UUID.lower():
                            if not self.tx_characteristic:
                                self.tx_characteristic = char
                                print(f"Found TX characteristic: {char.uuid}")
                            if not self.rx_characteristic:
                                self.rx_characteristic = char
                                print(f"Found RX characteristic: {char.uuid}")
                
                # Fallback: find any notify-enabled characteristic
                if not self.tx_characteristic:
                    for char in service.characteristics:
                        if "notify" in char.properties or "indicate" in char.properties:
                            self.tx_characteristic = char
                            print(f"Found notify characteristic (fallback): {char.uuid}")
                            break
                
                # Fallback: find any write-enabled characteristic
                if not self.rx_characteristic:
                    for char in service.characteristics:
                        if "write" in char.properties:
                            self.rx_characteristic = char
                            print(f"Found write characteristic (fallback): {char.uuid}")
                            break
            
            if not self.tx_characteristic:
                print("Warning: No notify characteristic found. Data reception may not work.")
                # List all characteristics for debugging
                print("Available characteristics:")
                for service in services_list:
                    for char in service.characteristics:
                        print(f"  Service {service.uuid}: {char.uuid} - Properties: {char.properties}")
            
            if not self.rx_characteristic:
                print("Warning: No write characteristic found. Command sending may not work.")
            
            # Enable notifications if we have a TX characteristic
            if self.tx_characteristic:
                await self.client.start_notify(
                    self.tx_characteristic.uuid,
                    self._notification_handler
                )
                print("BLE notifications enabled")
            
            print("BLE connection successful!")
            return True
        except Exception as e:
            error_msg = f"BLE connection error: {type(e).__name__}: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return False
    
    def _notification_handler(self, sender: BleakGATTCharacteristic, data: bytearray):
        """Handle BLE notification (called from asyncio thread)."""
        try:
            # Decode data
            text = data.decode('utf-8', errors='ignore')
            self.buffer += text
            
            # Process complete lines
            while '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
                line = line.strip()
                if line:
                    # Call callback (this should be thread-safe)
                    self.on_line_received(line)
        except Exception as e:
            print(f"BLE notification error: {e}")
    
    def disconnect(self):
        """Disconnect from BLE device."""
        self.running = False
        
        if self.event_loop and self.event_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                self._disconnect_async(), self.event_loop
            )
            try:
                future.result(timeout=5.0)
            except Exception as e:
                print(f"Error during BLE disconnect: {e}")
        
        self.client = None
        self.device_address = None
        self.device_name_str = None
        self.tx_characteristic = None
        self.rx_characteristic = None
        self.buffer = ""
    
    async def _disconnect_async(self):
        """Async disconnect logic."""
        if self.client and self.client.is_connected:
            if self.tx_characteristic:
                try:
                    await self.client.stop_notify(self.tx_characteristic.uuid)
                except Exception:
                    pass
            await self.client.disconnect()
    
    def is_connected(self) -> bool:
        """Check if currently connected."""
        if not self.client or not self.running:
            return False
        
        # Check connection status in event loop
        if self.event_loop and self.event_loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._check_connected_async(), self.event_loop
                )
                return future.result(timeout=1.0)
            except Exception:
                return False
        return False
    
    async def _check_connected_async(self) -> bool:
        """Check connection status (async)."""
        return self.client is not None and self.client.is_connected
    
    def write(self, command: str) -> bool:
        """
        Send a command string to the ESP32 via BLE.
        
        Args:
            command: Command string to send (should include newline if needed)
            
        Returns:
            True if command sent successfully, False otherwise
        """
        if not self.is_connected():
            print("BLE write failed: Not connected")
            return False
        
        if not self.rx_characteristic:
            print("BLE write failed: No RX characteristic found")
            return False
        
        try:
            # Ensure command ends with newline
            if not command.endswith('\n'):
                command += '\n'
            
            # Encode and write via BLE
            data = command.encode('utf-8')
            print(f"BLE writing command: {command.strip()}")
            
            if self.event_loop and self.event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self._write_async(data), self.event_loop
                )
                # For write-without-response, this should complete very quickly
                # But we'll use a reasonable timeout and handle it gracefully
                try:
                    future.result(timeout=2.0)
                    print(f"BLE command sent successfully: {command.strip()}")
                    return True
                except (asyncio.TimeoutError, TimeoutError):
                    # If timeout, check if future is done (might have completed just after timeout)
                    if future.done():
                        try:
                            # Future completed, check for exceptions
                            future.result()
                            print(f"BLE command sent successfully (completed after timeout check): {command.strip()}")
                            return True
                        except Exception as e:
                            # There was an actual error
                            print(f"BLE write completed but with error: {e}")
                            return False
                    else:
                        # Future not done - for write-without-response, this is often OK
                        # The write is fire-and-forget, so if it was submitted, consider it success
                        print(f"BLE command submitted (fire-and-forget, timeout on wait): {command.strip()}")
                        return True
            else:
                print("BLE write failed: Event loop not running")
                return False
        except Exception as e:
            error_msg = f"Failed to write BLE command: {type(e).__name__}: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return False
    
    async def _write_async(self, data: bytes):
        """Async write logic."""
        if not self.client or not self.client.is_connected:
            raise Exception("BLE client not connected")
        
        if not self.rx_characteristic:
            raise Exception("No RX characteristic available")
        
        try:
            char_props = self.rx_characteristic.properties
            print(f"BLE write: {len(data)} bytes, characteristic: {self.rx_characteristic.uuid}, properties: {char_props}")
            print(f"BLE write data (hex): {data.hex()}")
            print(f"BLE write data (text): {data.decode('utf-8', errors='replace')}")
            
            # Try to write the full command first - some ESP32 BLE implementations support longer writes
            # If that fails, fall back to chunking
            max_write_size = 20  # Standard BLE write-without-response MTU
            
            if len(data) > max_write_size:
                print(f"BLE data ({len(data)} bytes) exceeds standard MTU ({max_write_size})")
                # Try writing the full command first - ESP32 might support longer writes
                try:
                    print("Attempting to write full command (ESP32 may support extended MTU)...")
                    await self._write_chunk_async(data, char_props)
                    print("Full command write succeeded!")
                except Exception as e:
                    print(f"Full write failed ({e}), falling back to chunking...")
                    # Chunk the data if full write fails
                    chunks = []
                    for i in range(0, len(data), max_write_size):
                        chunk = data[i:i + max_write_size]
                        chunks.append(chunk)
                        print(f"BLE chunk {len(chunks)}: {len(chunk)} bytes")
                    
                    # Write each chunk sequentially with delay
                    for idx, chunk in enumerate(chunks):
                        print(f"Writing chunk {idx + 1}/{len(chunks)}...")
                        await self._write_chunk_async(chunk, char_props)
                        # Small delay between chunks to ensure they're processed in order
                        if idx < len(chunks) - 1:  # Don't delay after last chunk
                            await asyncio.sleep(0.02)  # 20ms delay between chunks
                    print(f"BLE finished writing {len(data)} bytes in {len(chunks)} chunks")
            else:
                await self._write_chunk_async(data, char_props)
                
        except Exception as e:
            error_msg = f"BLE write_gatt_char error: {type(e).__name__}: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            raise
    
    async def _write_chunk_async(self, chunk: bytes, char_props):
        """Write a single chunk of data."""
        # Check what write methods are supported
        has_write = "write" in char_props
        has_write_no_response = "write-without-response" in char_props or "write_no_response" in char_props
        
        if has_write_no_response:
            # Prefer write-without-response for UART services (faster, no response needed)
            await self.client.write_gatt_char(self.rx_characteristic.uuid, chunk, response=False)
            print(f"BLE wrote {len(chunk)} bytes (no response) to characteristic {self.rx_characteristic.uuid}")
        elif has_write:
            # Only write-with-response is available according to the characteristic
            # However, ESP32 BLE UART services often accept write-without-response even if not advertised
            # Since write-with-response is timing out, try write-without-response directly
            # This is the standard approach for UART BLE services
            print("Characteristic supports write-with-response, but trying write-without-response (standard for UART)...")
            try:
                await self.client.write_gatt_char(self.rx_characteristic.uuid, chunk, response=False)
                print(f"BLE wrote {len(chunk)} bytes (no response, UART mode) to characteristic {self.rx_characteristic.uuid}")
            except Exception as e:
                # If write-without-response fails, try write-with-response as fallback
                print(f"Write-without-response failed ({type(e).__name__}), trying write-with-response...")
                try:
                    await asyncio.wait_for(
                        self.client.write_gatt_char(self.rx_characteristic.uuid, chunk, response=True),
                        timeout=2.0
                    )
                    print(f"BLE wrote {len(chunk)} bytes (with response) to characteristic {self.rx_characteristic.uuid}")
                except asyncio.TimeoutError:
                    # Timeout on write-with-response - write might have still succeeded
                    print(f"Warning: Write-with-response timed out, but write may have succeeded")
                    print(f"BLE attempted to write {len(chunk)} bytes to characteristic {self.rx_characteristic.uuid}")
                    # Assume success since the write was sent
                except Exception as e2:
                    print(f"Write-with-response also failed: {e2}")
                    raise
        else:
            # No write properties found - try write-without-response as last resort
            try:
                await self.client.write_gatt_char(self.rx_characteristic.uuid, chunk, response=False)
                print(f"BLE wrote {len(chunk)} bytes (no response, fallback) to characteristic {self.rx_characteristic.uuid}")
            except Exception as e:
                print(f"BLE write failed: {e}")
                raise
    
    @property
    def device_name(self) -> Optional[str]:
        """Get the name/identifier of the currently connected device."""
        return self.device_name_str or self.device_address

