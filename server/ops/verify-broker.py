#!/usr/bin/env python3
import http.client,json,pathlib,socket
ROOT=pathlib.Path(__file__).resolve().parents[1]
class UnixHTTP(http.client.HTTPConnection):
    def connect(self):
        self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.sock.settimeout(5);self.sock.connect(str(ROOT/'private/broker/broker.sock'))
for payload in [{'scenario':'test','command':'id'},{'scenario':'test','image':'alpine'},{'scenario':'test','runner':'codex'},{'scenario':'x'*20001},{'scenario':[]}]:
    c=UnixHTTP('localhost');c.request('POST','/render',json.dumps(payload),{'Content-Type':'application/json'});r=c.getresponse();assert r.status==400;r.read();c.close()
print('PASS broker rejects command/image/mode overrides and invalid inputs (5 cases)')
