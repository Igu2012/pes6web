#!/usr/bin/env python3
"""Serve the local PES6 web build on loopback, including byte-range requests."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import mimetypes
import os
import re

ROOT = Path(__file__).resolve().parent / "site"
HOST = "127.0.0.1"
PORT = int(os.environ.get("PES6_PORT", "8765"))
mimetypes.add_type("application/wasm", ".wasm")
mimetypes.add_type("application/octet-stream", ".gz")
mimetypes.add_type("application/octet-stream", ".pak")


class RangeHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def send_head(self):
        path = self.translate_path(self.path)
        try:
            resolved = Path(path).resolve(strict=True)
            resolved.relative_to(ROOT.resolve())
        except (FileNotFoundError, ValueError, OSError):
            self.send_error(404, "File not found")
            return None
        if resolved.is_dir():
            if not self.path.endswith("/"):
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            resolved = resolved / "index.html"
        if not resolved.is_file():
            self.send_error(404, "File not found")
            return None

        size = resolved.stat().st_size
        range_header = self.headers.get("Range")
        start, end = 0, size - 1
        partial = False
        if range_header:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
            if not match or size == 0:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                return None
            a, b = match.groups()
            if not a:
                suffix = int(b or "0")
                if suffix <= 0:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.send_header("Accept-Ranges", "bytes")
                    self.end_headers()
                    return None
                start = max(0, size - suffix)
            else:
                start = int(a)
                end = min(size - 1, int(b)) if b else size - 1
            if start >= size or end < start:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                return None
            partial = True

        file = resolved.open("rb")
        file.seek(start)
        self._range_remaining = end - start + 1
        self._range_active = partial
        self.send_response(206 if partial else 200)
        self.send_header("Content-Type", self.guess_type(str(resolved)))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(self._range_remaining))
        if partial:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Last-Modified", self.date_time_string(resolved.stat().st_mtime))
        self.end_headers()
        return file

    def copyfile(self, source, outputfile):
        remaining = getattr(self, "_range_remaining", None)
        if remaining is None:
            return super().copyfile(source, outputfile)
        try:
            while remaining:
                chunk = source.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args), flush=True)


if __name__ == "__main__":
    os.chdir(ROOT)
    server = ThreadingHTTPServer((HOST, PORT), RangeHandler)
    print(f"PES6 local server: http://{HOST}:{PORT}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
