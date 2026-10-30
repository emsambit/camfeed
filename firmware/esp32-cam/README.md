# ESP32-CAM with GC2145

CameraWebServer for the classic ESP32-CAM / AI Thinker pin layout with a GC2145 sensor (observed PID `0x2145`). Adapted from Espressif's Arduino-ESP32 3.3.12 CameraWebServer example.

## Camera fix

The GC2145 does not provide the hardware JPEG output requested by the stock example. This sketch captures RGB565 at QVGA (320 x 240), uses one frame buffer, and keeps the existing server's software JPEG conversion for snapshots and MJPEG streaming. It zero-initializes the camera configuration, selects frame-buffer memory based on PSRAM availability, and prints the sensor PID after successful initialization.

## Build

1. Install **esp32 by Espressif Systems 3.3.12** in Arduino IDE. Board index: https://espressif.github.io/arduino-esp32/package_esp32_index.json
2. Open `CameraWebServer/CameraWebServer.ino`.
3. Replace the SSID/password placeholders locally with your 2.4 GHz Wi-Fi credentials. Do not commit real credentials.
4. Select **AI Thinker ESP32-CAM**, Huge APP (3 MB), flash frequency 40 MHz, and your USB serial port.

## Reliable flashing used during diagnosis

Normal uploading failed while using the flasher stub / higher baud rate. ROM flashing at 115200 baud with `--no-stub` succeeded and verified every image. This workaround does not establish the root cause of the normal upload failure.

Compile using Arduino CLI (adjust paths and your CLI configuration as needed):

```powershell
arduino-cli compile --fqbn esp32:esp32:esp32cam --build-path build CameraWebServer
```

Put GPIO0 at GND, reset the ESP32-CAM, and close Serial Monitor. From the build directory run your installed esptool executable:

```powershell
esptool --chip esp32 --port COM10 --baud 115200 --no-stub write-flash --flash-mode dio --flash-freq 40m --flash-size 4MB 0x1000 CameraWebServer.ino.bootloader.bin 0x8000 CameraWebServer.ino.partitions.bin 0xe000 boot_app0.bin 0x10000 CameraWebServer.ino.bin
```

COM10 was the tested port; replace it with your programmer's port. This command writes firmware to flash. Do not use the Arduino Debug button: a USB serial programmer is not a JTAG debugger.

After flashing, remove GPIO0 from GND and reset. Open Serial Monitor at 115200 baud, then browse to the printed camera URL on the same Wi-Fi network and click **Start Stream**. The MJPEG endpoint is normally `http://<camera-ip>:81/stream`.

## Verified status and remaining blocker

- Compiled with Arduino-ESP32 3.3.12 for AI Thinker ESP32-CAM.
- Firmware uploaded at 115200 baud without a stub; hashes verified.
- Camera initialization passed and logged `Camera sensor PID: 0x2145`.
- The subsequent startup repeatedly reported `Brownout detector was triggered`; Wi-Fi connection and live video were **not verified**.

Use a stable regulated 5V supply rated at least 1A at the camera board's 5V/GND inputs, with short wires. Keep serial-adapter ground common. If externally powering the camera, disconnect the adapter/Uno power wire to avoid tying supplies together. Do not power the camera from an Uno's 3.3V output. Keep brownout protection enabled and resolve the supply problem before expecting stable video.

## Attribution

The files in `CameraWebServer/` originate from the Espressif Arduino-ESP32 CameraWebServer example, with the modifications above. Upstream: https://github.com/espressif/arduino-esp32/tree/3.3.12/libraries/ESP32/examples/Camera/CameraWebServer . See upstream source notices and licensing; this addition does not relicense third-party source files.
