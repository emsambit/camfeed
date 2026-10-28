#!/usr/bin/env python3
"""Browser camera stream for legacy Raspberry Pi OS (Stretch / picamera)."""
import argparse
import io
import logging
import socketserver
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

PAGE = b'''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pi Camera Live</title><style>
body{background:#101820;color:#eef5fa;font:18px system-ui;text-align:center;margin:24px}
img{width:100%;max-width:960px;background:#000;border-radius:12px}
button,a{padding:12px;margin:8px;color:inherit}button{background:#304758;border:0;border-radius:8px}
</style></head><body><h1>Pi Camera Live</h1><p>Live video over local Wi-Fi</p>
<img id="video" src="/stream.mjpg" alt="Live camera stream">
<p><button onclick="document.getElementById('video').src='/stream.mjpg?t='+Date.now()">Reconnect</button>
<button onclick="document.getElementById('video').src=''">Pause</button>
<a href="/snapshot.jpg" target="_blank">Snapshot</a></p>
<p>If the picture freezes, press Reconnect. GPS is not connected to this viewer yet.</p>
</body></html>'''


class Frames(io.BufferedIOBase):
    def __init__(self):
        self.pending = bytearray()
        self.frame = None
        self.sequence = 0
        self.condition = threading.Condition()

    def writable(self):
        return True

    def write(self, data):
        # Parse complete JPEGs, including markers split across camera writes.
        self.pending.extend(data)
        while True:
            start = self.pending.find(b'\xff\xd8')
            if start < 0:
                self.pending[:] = self.pending[-1:]
                break
            if start:
                del self.pending[:start]
            end = self.pending.find(b'\xff\xd9', 2)
            if end < 0:
                if len(self.pending) > 8 * 1024 * 1024:
                    self.pending.clear()
                break
            frame = bytes(self.pending[:end + 2])
            del self.pending[:end + 2]
            with self.condition:
                self.frame = frame
                self.sequence += 1
                self.condition.notify_all()
        return len(data)


class Handler(BaseHTTPRequestHandler):
    def reply(self, content, content_type):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        try:
            if path in ('/', '/index.html'):
                self.reply(PAGE, 'text/html; charset=utf-8')
            elif path == '/snapshot.jpg':
                with self.server.frames.condition:
                    frame = self.server.frames.frame
                if frame is None:
                    self.send_error(503, 'Camera warming up; retry shortly')
                else:
                    self.reply(frame, 'image/jpeg')
            elif path == '/stream.mjpg':
                self.connection.settimeout(10)
                self.send_response(200)
                self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                sequence = -1
                frames = self.server.frames
                while True:
                    with frames.condition:
                        ready = frames.condition.wait_for(
                            lambda: frames.frame is not None and frames.sequence != sequence,
                            timeout=15)
                        if not ready:
                            return
                        frame, sequence = frames.frame, frames.sequence
                    self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: '
                                     + str(len(frame)).encode('ascii') + b'\r\n\r\n'
                                     + frame + b'\r\n')
                    self.wfile.flush()
            else:
                self.send_error(404)
        except (OSError, IOError):
            pass  # Viewer disconnected or stopped reading.

    def log_message(self, fmt, *args):
        logging.info('%s %s', self.client_address[0], fmt % args)


class Server(socketserver.ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--width', type=int, default=640)
    parser.add_argument('--height', type=int, default=480)
    parser.add_argument('--fps', type=int, default=15)
    parser.add_argument('--quality', type=int, default=65)
    parser.add_argument('--rotation', type=int, choices=(0, 90, 180, 270), default=0)
    args = parser.parse_args()
    if not (1 <= args.port <= 65535 and 1 <= args.fps <= 30
            and 1 <= args.quality <= 100 and 16 <= args.width <= 1920
            and 16 <= args.height <= 1080):
        parser.error('Invalid port, frame rate, quality or dimensions')
    try:
        import picamera
    except ImportError:
        parser.exit(1, 'Missing Python 3 picamera module. This script needs Python 3\n'
                    'and the legacy picamera library. Share this error for setup help.\n')
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    frames = Frames()
    server = Server(('0.0.0.0', args.port), Handler)
    server.frames = frames
    try:
        with picamera.PiCamera(resolution=(args.width, args.height), framerate=args.fps) as camera:
            camera.rotation = args.rotation
            camera.start_recording(frames, format='mjpeg', quality=args.quality)
            try:
                print('Open http://raspberrypi.local:{}/ on your laptop.'.format(args.port))
                print('Press Ctrl+C to stop. Local network access has no password.')
                server.serve_forever()
            finally:
                camera.stop_recording()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
