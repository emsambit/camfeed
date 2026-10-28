import subprocess
from pathlib import Path

script=Path('/usr/local/sbin/greenwatch-auto-hotspot')
script.write_text('''#!/bin/sh
set -eu
if /sbin/iw dev wlan0 link | grep -q 'Connected to' && /sbin/ip -4 addr show dev wlan0 | grep -q 'inet '; then
  echo 'Saved Wi-Fi connected; keeping home mode.'
else
  echo 'No saved Wi-Fi connection; starting Greenwatch hotspot.'
  systemctl start greenwatch-ap.service
fi
''')
script.chmod(0o755)
Path('/etc/systemd/system/greenwatch-auto-hotspot.service').write_text('''[Unit]
Description=Start demo hotspot if saved Wi-Fi is unavailable
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/greenwatch-auto-hotspot
''')
Path('/etc/systemd/system/greenwatch-auto-hotspot.timer').write_text('''[Unit]
Description=Check Wi-Fi and start Greenwatch hotspot after boot

[Timer]
OnBootSec=45
Unit=greenwatch-auto-hotspot.service

[Install]
WantedBy=timers.target
''')
subprocess.check_call(['systemctl','daemon-reload'])
subprocess.check_call(['systemctl','disable','hostapd','dnsmasq'])
subprocess.check_call(['systemctl','stop','dnsmasq'])
subprocess.check_call(['systemctl','enable','--now','greenwatch-auto-hotspot.timer'])
print('Automatic offline demo hotspot fallback enabled for 45 seconds after boot.')
