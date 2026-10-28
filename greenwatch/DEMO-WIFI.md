# Optional standalone demo Wi-Fi

## Status and prerequisites

This configuration targets an existing Raspbian Stretch device using dhcpcd, user `pi`, and `/home/pi/greenwatch`. It is not suitable for blindly applying to newer NetworkManager-based systems. **Full hotspot-client verification is pending:** a temporary concurrent-AP test interrupted the home connection. Have physical console access before changing Wi-Fi. That test helper is not included.

Install the camera directory and confirm normal streaming first. Ensure `hostapd` and `dnsmasq` are installed from an appropriate trusted package source. Old Stretch mirrors may no longer contain every dependency; do not disable package verification or upgrade the OS blindly.

## Install startup configuration

The first command backs up existing network files under `/etc/greenwatch/backup`, writes dedicated AP settings and enables the camera service. It generates a random WPA2 password locally and prints it. It does not switch to hotspot mode.

```sh
cd /home/pi/greenwatch
sudo python3 scripts/install_demo.py
sudo python3 scripts/start_camera_service.py
```

The second command stops an older camera server and starts `greenwatch-camera.service`. It causes a brief camera interruption.

## Enable offline-demo fallback

```sh
sudo python3 scripts/configure_fallback.py
```

This enables a one-time check at 45 seconds after boot. If wlan0 has a saved Wi-Fi association and IPv4 address, it keeps that connection. Otherwise it starts the demo hotspot. It is a boot fallback, not a continuous network monitor. **When first enabled after the Pi has already been running for 45 seconds, the check may run immediately.**

## Connect at the demo

1. Power the Pi and allow at least 60 seconds for boot and Wi-Fi fallback.
2. Join **Greenwatch-Demo** from the laptop. Obtain the generated password on the Pi with `sudo cat /etc/greenwatch/wifi-password`.
3. Stay connected when the laptop reports no internet.
4. Open **http://192.168.4.1:8000** and click **Enable detection**.

Camera video, detector libraries/model weights and Bengaluru/India maps are all local. Initial model loading transfers roughly 20 MB from the Pi; open it before presenting. No Google Maps or internet is required.

To force demo mode at home, use the **Start Demo WiFi** Pi Desktop launcher or:

```sh
sudo greenwatch-mode demo
```

This replaces the current Wi-Fi connection, disconnects SSH/VNC at the home IP and enables hotspot mode for subsequent boots. The laptop must join the Pi's Wi-Fi and use the demo address.

## Return to home Wi-Fi

From the Pi console or the hotspot connection:

```sh
sudo greenwatch-mode home
```

The **Restore Home WiFi** Desktop launcher does the same. Reconnect the laptop to the home network and use the Pi's home IP. The optional boot fallback timer remains enabled.

For recovery from the earlier temporary uap0 test only:

```sh
sudo pkill hostapd
sudo /sbin/iw dev uap0 del
sudo greenwatch-mode home
```

An error that uap0 does not exist is harmless. A reboot clears that temporary virtual interface. Do not run the recovery sequence during a working demo unless you intend to disconnect it.

## Services and files

- `greenwatch-camera.service`: camera/dashboard startup.
- `greenwatch-ap.service`: dedicated hotspot mode.
- `greenwatch-auto-hotspot.timer`: one-time boot fallback.
- `/etc/greenwatch/`: dedicated settings and generated password; root-only access.
- `/etc/greenwatch/backup/`: original configuration copies.

No Wi-Fi passwords or private keys belong in Git. Backups on a real device can contain credentials; keep them on that device.
