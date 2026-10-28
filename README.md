# Camfeed / Greenwatch

Raspberry Pi ribbon-camera streaming with a green HUD, browser-based object detection and offline Bengaluru/India maps. The Pi captures video; a laptop browser performs detection. The original single-file viewer remains in `pi_camera_stream.py`.

## Features

- Continuous MJPEG video, green corner boxes, image-position tracking trails and PNG snapshots.
- COCO-SSD detection for people, cars, buses, trucks, motorcycles, bicycles and dogs. Detection is a trained AI model; this version does not use YOLO.
- Bundled TensorFlow.js and model weights: no internet/CDN is needed at demo time.
- Offline Bengaluru roads, lakes and locality labels, plus an India overview with generalized boundaries and city labels.
- Optional manual camera pin and a 50 m reference circle. GPS hardware integration is not implemented.
- Optional camera boot service and standalone Wi-Fi hotspot configuration for an existing legacy Pi installation.

## Requirements

- Pi with a connected CSI ribbon camera and a working camera stack.
- Tested camera backend: original Raspberry Pi Zero W, Raspbian Stretch, Python 3.5 and legacy `picamera`.
- A recent Chrome/Edge browser on a laptop. The laptop runs the detector and must remain connected to the Pi.
- The modern Picamera2 backend is included but has not been hardware-tested here. Stretch is obsolete; these scripts support the existing device rather than recommending it for new installations.

## Quick start

Clone/download this repository and copy the **entire** `greenwatch/` directory to `/home/pi/greenwatch` on the Pi. Keep the assets subdirectories intact. Close any other program using the camera.

```sh
cd /home/pi/greenwatch
python3 -c "import picamera"
python3 camera_server.py --backend legacy
```

Run `hostname -I` on the Pi, then open `http://PI_IP_ADDRESS:8000/` on the laptop. Click **Enable detection**. The first model load transfers roughly 20 MB over the local connection; load it before presenting. It does not need internet.

For a current Pi OS with Picamera2 already installed:

```sh
python3 camera_server.py --backend modern
```

Do not install both camera stacks or upgrade an old OS merely to run this program. For a camera-free interface preview on any computer with Python 3:

```sh
cd greenwatch
python3 camera_server.py --preview-only
```

Open `http://localhost:8000/`. The preview correctly reports CAMERA OFFLINE while the maps and local detector can load.

## Video settings

The legacy backend defaults to **480 x 360, 12 FPS, JPEG quality 45, 500,000 bits/s**. A bitrate cap matters on the Zero W: changing JPEG quality alone can leave the encoder's default bitrate too high for Wi-Fi.

```sh
python3 camera_server.py --backend legacy --width 320 --height 240 --fps 10 --quality 35 --bitrate 350000
```

The browser reads one continuous stream. The server sends the latest frame to each viewer rather than queuing a video history. Detection runs independently about twice per second. The displayed AI processing time is not the video frame rate. `--bitrate` and `--quality` currently configure the legacy backend; the modern backend uses its encoder defaults.

Endpoints: `/` (dashboard), `/video.mjpg` (MJPEG), `/snapshot.jpg` (latest JPEG), `/status.json` (capture health), `/assets/` (bundled local files). Video is not recorded continuously. Stop a foreground server with Ctrl+C.

## Offline map coverage

Use **Bengaluru** or **India overview** beside the video. Pan and zoom work without internet.

- Bengaluru extract: 12.80-13.20 N, 77.40-77.82 E; about 22,000 road/water/locality features. Residential lanes and areas outside the extract are not complete.
- India overview: country outlines and city labels, not street-level coverage of every place in India. Natural Earth boundaries are generalized and are not authoritative boundary records.
- Data sources: OpenStreetMap contributors (ODbL) and Natural Earth (public domain). Attribution is displayed in the map and included with the data. This is a schematic vector map, not Google Maps or satellite imagery.
- A manual pin is user-entered. No detections are placed on the map automatically, and GPS coordinates, speed, bearing and object distance are not fabricated.

## Standalone demo Wi-Fi and boot startup

See [DEMO-WIFI.md](greenwatch/DEMO-WIFI.md) before running the optional network scripts. They target **Raspbian Stretch with dhcpcd, user `pi`, and `/home/pi/greenwatch`**; they are not NetworkManager setup scripts.

The setup uses `hostapd` and `dnsmasq`, generates a unique WPA2 password on the Pi, and provides a home-Wi-Fi recovery command. No Wi-Fi passwords, SSH keys or camera images are committed to this repository.

**Current verification limit:** configuration files, package installation and camera service startup were checked. The temporary concurrent-AP hardware test interrupted the device's home connection. A full reboot/fallback/hotspot-client test has not yet passed. The unsafe concurrent test helper is not shipped. Treat hotspot setup as experimental until tested on the actual device with console access.

## Troubleshooting

- **No objects tracked:** no supported object passed the confidence threshold. Point the camera upright at a well-lit subject. Compression, low resolution and low confidence thresholds can cause missed or false labels. A person detection does not establish that someone is a burglar.
- **No fresh camera frames:** the health request failed, or capture stopped advancing. This can be a Wi-Fi stall rather than a permanent camera fault. Check power, Wi-Fi, other camera processes and `/status.json`; the current health check is intentionally simple.
- **Video lags:** reduce bitrate/resolution, improve Wi-Fi reception and close duplicate viewers. MJPEG consumes more bandwidth than H.264. The 12 FPS configuration is a target, not a guarantee.
- **Camera busy:** stop the older viewer or any camera application before starting Greenwatch. Only one program should own the camera.
- **Missing local model/map:** copy all of `greenwatch/assets/`; do not copy only the Python/HTML files.

## Limits and validation

The 50 m circle is a reference overlay, not a measured detection boundary. One fixed camera only covers its field of view. Tracking IDs are short-lived image-space associations, not identities. Activity is in browser memory and clears on refresh.

This prototype has no HTTP authentication or TLS. Keep it on a trusted LAN or the password-protected local demo network; do not forward its port to the internet.

Camera streaming, valid JPEGs and advancing capture status were verified on the legacy Pi. A Wi-Fi test delivered about 9 FPS with the dashboard open; a short first-frame test was about 0.33 seconds. These are observations, not guaranteed end-to-end latency. Offline maps and local model loading were verified in a browser. Modern camera hardware, GPS, complete offline hotspot operation and outdoor 50 m recognition remain unverified.

## Layout

```text
pi_camera_stream.py          Original minimal legacy viewer
greenwatch/camera_server.py  Camera and HTTP server
greenwatch/index.html        HUD and map layout
greenwatch/app.js            Local detection and overlay
greenwatch/assets/           Bundled model, libraries and offline maps
greenwatch/scripts/          Optional legacy-device startup/hotspot setup
docs/LEGACY-VIEWER.md        Original viewer instructions
```

Third-party licences and source links are in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The repository does not assign a new licence to pre-existing project code.
