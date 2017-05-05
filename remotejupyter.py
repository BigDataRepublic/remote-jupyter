
import threading
import http.server
import socketserver
import json
import queue
import sys

from functools import partial

Handler = http.server.SimpleHTTPRequestHandler

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    def do_POST(self):
        content_len = int(self.headers.get('content-length', 0))
        post_body = self.rfile.read(content_len)
        try:
            requestObject = json.loads(post_body)
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e), "phase": "request parsing"}).encode("utf-8"))
            return
        try:
            responseObject = self.server.getImplementation()(requestObject)
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e), "phase": "calling implementation"}).encode("utf-8"))
            return
        try:
            response = json.dumps(responseObject).encode("utf-8")
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e), "phase": "response serialization"}).encode("utf-8"))
            return

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(response)


    def do_GET(self):
        handlers = self.server.getImplementation()
        self.send_response(400)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(
            {"handler memory id": id(self.server.getImplementation())}
        ).encode("utf-8"))

def getImplementation(q, state):
    try:
        newImpl = q.get(block = False)
        state[0] = newImpl
    except queue.Empty:
        pass
    return state[0]

def start(q):
    socketserver.TCPServer.allow_reuse_address = True
    sys.stderr.write('Starting server at port 5000\n')
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
