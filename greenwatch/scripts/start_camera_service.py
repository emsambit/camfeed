import os
import signal
import subprocess
import time
subprocess.call(['systemctl','stop','greenwatch-camera.service'])
for name in os.listdir('/proc'):
    if not name.isdigit():continue
    try:
        with open('/proc/'+name+'/cmdline','rb') as f:args=f.read().split(b'\0')
        if b'/home/pi/greenwatch/camera_server.py' in args or b'/home/pi/pi_camera_stream.py' in args:
            os.kill(int(name),signal.SIGTERM)
    except (IOError,OSError):pass
time.sleep(2)
subprocess.check_call(['systemctl','start','greenwatch-camera.service'])
print(subprocess.check_output(['systemctl','is-active','greenwatch-camera.service']).decode())
