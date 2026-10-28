#!/usr/bin/env python3
"""LAN camera + dashboard. Supports legacy picamera and current Picamera2."""
import argparse
import io
import json
import mimetypes
import os
import threading
import time
from http import server
from socketserver import ThreadingMixIn

ROOT = os.path.dirname(os.path.abspath(__file__))


class Frames(io.BufferedIOBase):
    def __init__(self):
        super().__init__()
        self.pending = bytearray()
        self.frame = None
        self.updated = 0
        self.sequence = 0
        self.condition = threading.Condition()

    def writable(self):
        return True

    def write(self, data):
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
                self.updated = time.time()
                self.sequence += 1
                self.condition.notify_all()
        return len(data)


frames = Frames()


class Handler(server.BaseHTTPRequestHandler):
    # Python 3.5's unbuffered socket writer can perform short writes, truncating
    # large JPEGs. BufferedWriter guarantees complete writes; flush each frame.
    wbufsize = 65536

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path.startswith('/assets/'):
            base = os.path.realpath(os.path.join(ROOT, 'assets'))
            target = os.path.realpath(os.path.join(ROOT, path.lstrip('/')))
            if not target.startswith(base + os.sep) or not os.path.isfile(target):
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', mimetypes.guess_type(target)[0] or 'application/octet-stream')
            self.send_header('Content-Length', str(os.path.getsize(target)))
            self.send_header('Cache-Control', 'public, max-age=86400')
            self.end_headers()
            with open(target, 'rb') as source:
                while True:
                    chunk = source.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        elif path in ('/', '/index.html', '/app.js'):
            name = 'index.html' if path != '/app.js' else 'app.js'
            with open(os.path.join(ROOT, name), 'rb') as source:
                body = source.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8' if name.endswith('html') else 'text/javascript; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)
        elif path == '/status.json':
            body = json.dumps({'camera': bool(frames.frame) and time.time() - frames.updated < 4,
                               'last_frame': frames.updated, 'sequence': frames.sequence,
                               'gps': None}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == '/snapshot.jpg':
            with frames.condition:
                frame = frames.frame
            if frame is None:
                self.send_error(503, 'Camera warming up')
                return
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(frame)))
            self.end_headers()
            self.wfile.write(frame)
        elif path == '/video.mjpg':
            self.connection.settimeout(10)
            self.send_response(200)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            previous = -1
            try:
                while True:
                    with frames.condition:
                        frames.condition.wait_for(lambda: frames.sequence != previous, timeout=5)
                        if frames.frame is None or frames.sequence == previous:
                            continue
                        frame, previous = frames.frame, frames.sequence
                    self.wfile.write(b'--FRAME\r\nContent-Type: image/jpeg\r\nContent-Length: ' +
                                     str(len(frame)).encode() + b'\r\n\r\n' + frame + b'\r\n')
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
        else:
            self.send_error(404)


class CameraServer(ThreadingMixIn, server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', choices=['auto', 'legacy', 'modern'], default='auto')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--width', type=int, default=480)
    parser.add_argument('--height', type=int, default=360)
    parser.add_argument('--fps', type=int, default=12)
    parser.add_argument('--quality', type=int, default=45)
    parser.add_argument('--bitrate', type=int, default=500000)
    parser.add_argument('--preview-only', action='store_true', help='Serve UI without a camera; honestly reports offline')
    args = parser.parse_args()
    if not (160 <= args.width <= 1920 and 120 <= args.height <= 1080 and
            1 <= args.fps <= 30 and 10 <= args.quality <= 95 and 100000 <= args.bitrate <= 5000000):
        parser.error('Invalid dimensions, fps or JPEG quality')
    camera = None
    if not args.preview_only:
        backend = args.backend
        if backend == 'auto':
            try:
                import picamera2
                backend = 'modern'
            except ImportError:
                backend = 'legacy'
        if backend == 'modern':
            from picamera2 import Picamera2
            from picamera2.encoders import MJPEGEncoder
            from picamera2.outputs import FileOutput
            camera = Picamera2()
            camera.configure(camera.create_video_configuration(main={'size': (args.width, args.height)}, controls={'FrameRate': args.fps}))
            camera.start_recording(MJPEGEncoder(), FileOutput(frames))
        else:
            import picamera
            camera = picamera.PiCamera(resolution=(args.width, args.height), framerate=args.fps)
            camera.start_recording(frames, format='mjpeg', quality=args.quality, bitrate=args.bitrate)
    try:
        print('Greenwatch: open http://PI_IP_ADDRESS:%s on your laptop (localhost for preview). Ctrl+C stops it.' % args.port, flush=True)
        CameraServer(('0.0.0.0', args.port), Handler).serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if camera:
            camera.stop_recording()
            camera.close()


if __name__ == '__main__':
    main()
