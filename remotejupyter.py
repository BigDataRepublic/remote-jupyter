
import threading
import http.server
import socketserver
import json
import queue
import sys
import traceback
from functools import partial

Handler = http.server.SimpleHTTPRequestHandler

def sendJson(self, status, bodyObject):
    self.send_response(status)
    self.send_header('access-control-allow-origin', '*')
    self.send_header('content-type', 'application/json; charset=UTF-8')
    self.send_header('cache-control', 'no-store')
    self.end_headers()
    self.wfile.write(json.dumps(bodyObject).encode("utf-8"))


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('content-type', 'plain/text; charset=UTF-8')
        self.send_header('access-control-allow-origin', '*')
        self.send_header('access-control-allow-headers', self.headers.get('Access-Control-Request-Headers'))
        self.send_header('access-control-allow-methods', self.headers.get('Access-Control-Request-Method'))
        self.end_headers()
        self.wfile.write("ok".encode("utf-8"))

    def do_POST(self):
        content_len = int(self.headers.get('content-length', 0))
        post_body = self.rfile.read(content_len)

        try:
            requestObject = json.loads(post_body)
        except Exception as e:
            sendJson(self, 400, {"error": str(e), "phase": "request parsing", "stack": traceback.format_exc()})
            return

        try:
            responseObject = self.server.getImplementation()(requestObject)
        except Exception as e:
            sendJson(self, 400, {"error": str(e), "phase": "calling implementation", "stack": traceback.format_exc()})
            return

        try:
            sendJson(self, 200, responseObject)
        except Exception as e:
            sendJson(self, 400, {"error": str(e), "phase": "response serialization and sending", "stack": traceback.format_exc()})
            return


    def do_GET(self):
        sendJson(self, 200, {"handler memory id": id(self.server.getImplementation())})


def getImplementation(q, state):
    try:
        newImpl = q.get(block = False)
        state[0] = newImpl
    except queue.Empty:
        pass
    return state[0]

def start(q):
    socketserver.TCPServer.allow_reuse_address = True
    sys.stderr.write('Starting server at port http://localhost:5000/\n')
    with socketserver.TCPServer(("", 5000), Handler) as httpd:
        httpd.getImplementation = partial(getImplementation, q, [lambda x: {"not implemented yet"}])
        httpd.serve_forever()


def startServer():
    q = queue.Queue()
    t = threading.Thread(target = start, args=(q,))
    t.start()
    return q

if __name__ == "__main__":
    q = startServer()
    import time
    import datetime
    while True:
        time.sleep(5)
        r = datetime.datetime.now().isoformat()
        q.put(lambda x: {"asdf": r})
