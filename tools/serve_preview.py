"""Serve this project locally on an available port. Ctrl-C stops the server."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(root)))
url=f'http://127.0.0.1:{s.server_port}/preview/'
(root/'preview/server-url.txt').write_text(url+'\n')
print(url,flush=True)
s.serve_forever()
