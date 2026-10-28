# Camfeed

A lightweight browser viewer for a Raspberry Pi ribbon camera using the legacy `picamera` library. Includes live MJPEG video, pause/reconnect controls, and JPEG snapshots.

## Requirements

- Raspberry Pi with a working CSI camera and legacy camera support enabled.
- Python 3 and the Python 3 `picamera` package (not Picamera2).
- Tested on an original Pi Zero W running Raspbian Stretch. This targets that existing legacy installation; Stretch is obsolete and is not recommended for a new installation.
- Laptop and Pi on the same trusted local network.

## Run

Copy `pi_camera_stream.py` to your Pi, then run in its terminal:

```bash
python3 -c "import picamera"
python3 ~/pi_camera_stream.py
```

Open `http://raspberrypi.local:8000/` on your laptop. If the hostname does not resolve to an IPv4 address, run `hostname -I` on the Pi and use `http://PI_IPV4_ADDRESS:8000/`. The server binds IPv4 only.

Stop with Ctrl+C. Close other camera applications before starting.

To keep running after closing the terminal:

```bash
nohup python3 ~/pi_camera_stream.py > ~/pi_camera_stream.log 2>&1 &
```

This does not configure automatic startup after reboot.

## Options

Defaults: 640x480, 15 fps, JPEG quality 65, port 8000.

```bash
# Reduce Wi-Fi bandwidth
python3 ~/pi_camera_stream.py --width 320 --height 240 --fps 10 --quality 50

# Rotate the image
python3 ~/pi_camera_stream.py --rotation 180
```

`/snapshot.jpg` returns the latest JPEG frame; `/stream.mjpg` returns the multipart MJPEG stream.

## Limits

There is no authentication or encryption. Do not expose this server to the Internet. This prototype provides video and snapshots only; it has no GPS integration, object detection, audio, or flight-control functionality. MJPEG uses more bandwidth than H.264; performance and latency depend on the network.

If Python 3 cannot import `picamera`, the required library is missing. Do not substitute Picamera2; it uses a different API. Old Stretch repositories may no longer support normal package installation.

## Validation

Frame parsing and HTTP response generation were checked locally. On the Pi, the Python 3 camera library loaded, the server started, and the snapshot endpoint returned HTTP 200 with image data. The viewer page also returned HTTP 200 from the laptop. These checks do not establish sustained frame rate, flight suitability, or guaranteed latency.

Reference: [PiCamera documentation](https://picamera.readthedocs.io/en/release-1.13/recipes2.html#web-streaming).
