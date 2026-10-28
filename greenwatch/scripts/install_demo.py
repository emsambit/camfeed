import os
import binascii
import shutil
import subprocess
from pathlib import Path

assert os.geteuid() == 0
base = Path('/etc/greenwatch')
base.mkdir(mode=0o700, exist_ok=True)
backup = base / 'backup'
backup.mkdir(exist_ok=True)
for name in ['/etc/dhcpcd.conf','/etc/hostapd/hostapd.conf','/etc/dnsmasq.conf']:
    p=Path(name)
    target=backup/p.name
    if p.exists() and not target.exists():shutil.copy2(str(p),str(target))

password_file=base/'wifi-password'
if password_file.exists():password=password_file.read_text().strip()
else:
    password='GW-'+binascii.hexlify(os.urandom(6)).decode()
    password_file.write_text(password+'\n')
    password_file.chmod(0o600)

(base/'hostapd.conf').write_text('''interface=wlan0
driver=nl80211
ssid=Greenwatch-Demo
hw_mode=g
channel=6
wmm_enabled=1
ieee80211n=1
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase='''+password+'\n')
(base/'hostapd.conf').chmod(0o600)
(base/'dnsmasq.conf').write_text('''port=0
interface=wlan0
bind-interfaces
dhcp-range=192.168.4.10,192.168.4.60,255.255.255.0,12h
dhcp-option=3
dhcp-option=6
dhcp-authoritative
''')

script=Path('/usr/local/sbin/greenwatch-network')
script.write_text('''#!/bin/sh
set -eu
case "$1" in
start)
  systemctl stop dnsmasq hostapd || true
  systemctl stop dhcpcd wpa_supplicant
  /sbin/wpa_cli -i wlan0 terminate >/dev/null 2>&1 || true
  /sbin/ip link set wlan0 up
  /sbin/ip addr flush dev wlan0
  /sbin/ip addr add 192.168.4.1/24 dev wlan0
  /sbin/iw dev wlan0 set power_save off || true
  /usr/sbin/hostapd -B -P /run/greenwatch-hostapd.pid /etc/greenwatch/hostapd.conf
  /usr/sbin/dnsmasq --conf-file=/etc/greenwatch/dnsmasq.conf --pid-file=/run/greenwatch-dnsmasq.pid
  ;;
stop)
  for f in /run/greenwatch-dnsmasq.pid /run/greenwatch-hostapd.pid; do
    if [ -f "$f" ]; then kill "$(cat "$f")" || true; rm -f "$f"; fi
  done
  /sbin/ip addr flush dev wlan0
  systemctl start wpa_supplicant dhcpcd
  ;;
*) exit 2;;
esac
''')
script.chmod(0o755)

Path('/etc/systemd/system/greenwatch-ap.service').write_text('''[Unit]
Description=Greenwatch standalone demo Wi-Fi
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/greenwatch-network start
ExecStop=/usr/local/sbin/greenwatch-network stop
TimeoutStartSec=45

[Install]
WantedBy=multi-user.target
''')

Path('/usr/local/sbin/greenwatch-mode').write_text('''#!/bin/sh
set -eu
case "${1:-}" in
demo) systemctl enable greenwatch-ap.service; systemctl start greenwatch-ap.service;;
home) systemctl disable --now greenwatch-ap.service; systemctl restart dhcpcd;;
*) echo "Usage: sudo greenwatch-mode demo|home"; exit 2;;
esac
''')
Path('/usr/local/sbin/greenwatch-mode').chmod(0o755)

Path('/etc/systemd/system/greenwatch-camera.service').write_text('''[Unit]
Description=Greenwatch offline camera dashboard
After=network.target

[Service]
User=pi
Group=pi
WorkingDirectory=/home/pi/greenwatch
ExecStart=/usr/bin/python3 -u /home/pi/greenwatch/camera_server.py --backend legacy
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
''')

desktop=Path('/home/pi/Desktop')
for title,mode in [('Start Demo WiFi','demo'),('Restore Home WiFi','home')]:
    file=desktop/(title+'.desktop')
    file.write_text('[Desktop Entry]\nType=Application\nName='+title+'\nExec=sudo /usr/local/sbin/greenwatch-mode '+mode+'\nTerminal=true\nIcon=network-wireless\n')
    file.chmod(0o755)
    shutil.chown(str(file),user='pi',group='pi')

subprocess.check_call(['systemctl','daemon-reload'])
subprocess.check_call(['systemctl','disable','hostapd','dnsmasq'])
subprocess.check_call(['/usr/sbin/dnsmasq','--test','--conf-file=/etc/greenwatch/dnsmasq.conf'])
subprocess.check_call(['systemctl','enable','greenwatch-camera.service'])
print('Demo configuration installed; hotspot not activated yet.')
print('SSID: Greenwatch-Demo')
print('PASSWORD: '+password)
print('Page: http://192.168.4.1:8000')
