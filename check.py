"""Validate the built website using an automatically started static HTTP server."""
import functools
import http.server
import pathlib
import subprocess
import sys
import threading

ROOT=pathlib.Path(__file__).resolve().parent
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(ROOT)))
thread=threading.Thread(target=server.serve_forever,daemon=True)
thread.start()
try:
    subprocess.run([sys.executable,str(ROOT/'dev/tools/verify_pages.py'),str(ROOT),'--base',f'http://127.0.0.1:{server.server_port}'],cwd=ROOT,check=True)
finally:
    server.shutdown()
    server.server_close()
