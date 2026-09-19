#!/usr/bin/env python3
"""Trusted host-only broker. No caller-controlled Docker arguments, mounts or commands."""
import base64, datetime, http.server, json, os, pathlib, re, selectors, socketserver, sqlite3, subprocess, tempfile, threading, time, uuid
ROOT = pathlib.Path(__file__).resolve().parents[1]
PRIVATE = ROOT / 'private'
SOCKET_DIR = PRIVATE / 'broker'
CONFIG = json.loads((PRIVATE / 'broker.json').read_text())
MODE = CONFIG.get('runner', 'mock')
if MODE not in ('mock', 'codex'): raise RuntimeError('invalid runner')
LIMIT = min(5, max(1, int(CONFIG.get('concurrency', 5))))
DAILY = min(100, max(1, int(CONFIG.get('daily_jobs', 30))))
TIMEOUT = min(3600, max(30, int(CONFIG.get('timeout_seconds', 900))))
SLOTS = threading.BoundedSemaphore(LIMIT)
AUTH_LOCK = threading.Lock()
AUTH_FILE = PRIVATE / 'codex-auth.json'
DB = PRIVATE / 'broker-usage.sqlite'
MAX_RESPONSE = 46 * 1024 * 1024
IMAGE_REF = re.compile(r'sha256:[0-9a-f]{64}|[a-z0-9][a-z0-9._/-]*(:[A-Za-z0-9._-]+)?(@sha256:[0-9a-f]{64})?')

def current_image():
    # Read per job: registering a new video-generator image applies to new jobs without restarting the broker.
    image = json.loads((PRIVATE / 'broker.json').read_text()).get('image')
    if not isinstance(image, str) or not IMAGE_REF.fullmatch(image): raise RuntimeError('video-generator image not registered')
    return image

def valid_auth(auth):
    # Only authentication state survives a job. Never accept config, scripts or arbitrary files.
    if not isinstance(auth, dict): return None
    result = {k:v for k,v in auth.items() if k in ('auth_mode','OPENAI_API_KEY','tokens','last_refresh')}
    if len(json.dumps(result)) > 32768: return None
    tokens = result.get('tokens')
    if tokens is not None:
        if not isinstance(tokens, dict): return None
        if any(k not in ('id_token','access_token','refresh_token','account_id') or not isinstance(v,str) or len(v)>20000 for k,v in tokens.items()): return None
    if any(not isinstance(result.get(k),(str,type(None))) for k in ('auth_mode','OPENAI_API_KEY','last_refresh')): return None
    return result

def charge():
    with sqlite3.connect(DB, timeout=10) as db:
        db.execute('CREATE TABLE IF NOT EXISTS usage (day TEXT PRIMARY KEY, n INTEGER NOT NULL)')
        db.execute('BEGIN IMMEDIATE')
        day = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
        n = db.execute('SELECT n FROM usage WHERE day=?',(day,)).fetchone()
        if n and n[0] >= DAILY: return False
        db.execute('INSERT INTO usage VALUES (?,1) ON CONFLICT(day) DO UPDATE SET n=n+1',(day,))
        return True

def render(scenario):
    auth = None
    if MODE == 'codex':
        with AUTH_LOCK: auth = valid_auth(json.loads(AUTH_FILE.read_text()))
        if not auth: raise RuntimeError('authentication missing')
    name = 'slidegen-job-' + uuid.uuid4().hex
    args = ['docker','run','--rm','--name',name,'--label','slidegen.ephemeral=true',
        '--network','none','--read-only','--user','1000:1000','--cap-drop','ALL',
        '--security-opt','no-new-privileges:true','--pids-limit','128','--memory','768m',
        '--memory-swap','768m','--cpus','0.7','--ulimit','nofile=256:256',
        '--tmpfs','/tmp:rw,noexec,nosuid,nodev,size=64m,uid=1000,gid=1000,mode=700',
        '--tmpfs','/work:rw,nosuid,nodev,size=384m,uid=1000,gid=1000,mode=700',
        '--mount','type=volume,src=slidegen-server_proxy-socket,dst=/proxy,readonly',
        '--env','RUNNER='+MODE,'--log-driver','none','-i',current_image()]
    # Input is JSON through stdin, never a shell command. No caller-supplied paths or options.
    payload = json.dumps({'scenario':scenario,'auth':auth}).encode()
    with tempfile.TemporaryFile() as incoming:
        incoming.write(payload); incoming.seek(0)
        proc = subprocess.Popen(args,stdin=incoming,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        try:
            output=bytearray(); deadline=time.monotonic()+TIMEOUT
            with selectors.DefaultSelector() as selector:
                selector.register(proc.stdout,selectors.EVENT_READ)
                while True:
                    if time.monotonic()>=deadline: raise TimeoutError('render timeout')
                    if not selector.select(timeout=1): continue
                    chunk=os.read(proc.stdout.fileno(),65536)
                    if not chunk: break
                    if len(output)+len(chunk)>MAX_RESPONSE: raise RuntimeError('output too large')
                    output.extend(chunk)
            if proc.wait(timeout=10): raise RuntimeError('render failed')
            result=json.loads(output)
        finally:
            # Always terminate the entire container, including background grandchildren.
            subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30)
            if proc.poll() is None: proc.kill(); proc.wait()
            proc.stdout.close()
    refreshed = valid_auth(result.get('auth'))
    if MODE == 'codex' and refreshed and refreshed != auth:
        identity=lambda a: (a.get('auth_mode'),a.get('OPENAI_API_KEY'),(a.get('tokens') or {}).get('account_id'))
        with AUTH_LOCK:
            current=valid_auth(json.loads(AUTH_FILE.read_text()))
            if current and identity(refreshed)==identity(current) and (refreshed.get('last_refresh') or '')>(current.get('last_refresh') or ''):
                tmp = AUTH_FILE.with_suffix('.tmp')
                tmp.write_text(json.dumps(refreshed)); tmp.chmod(0o600); tmp.replace(AUTH_FILE)
    video = base64.b64decode(result['video'],validate=True)
    if len(video)>32*1024*1024 or video[4:8]!=b'ftyp': raise RuntimeError('invalid video')
    return video

class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version='HTTP/1.0'
    def setup(self):
        super().setup(); self.connection.settimeout(15)
    def log_message(self,*args): pass
    def do_POST(self):
        if self.path!='/render' or self.headers.get('Transfer-Encoding'):
            self.send_error(400); return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=100000: raise ValueError()
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict) or set(data)!={'scenario'}: raise ValueError()
            scenario=data['scenario']
            if not isinstance(scenario,str) or not 1<=len(scenario.strip())<=20000: raise ValueError()
        except Exception: self.send_error(400); return
        if not SLOTS.acquire(blocking=False): self.send_error(429); return
        try:
            if not charge(): self.send_error(429); return
            video=render(scenario)
            self.send_response(200); self.send_header('Content-Type','video/mp4')
            self.send_header('Content-Length',str(len(video))); self.end_headers(); self.wfile.write(video)
        except Exception:
            self.send_error(502,'isolated render failed')
        finally: SLOTS.release()

class Server(socketserver.ThreadingMixIn,socketserver.UnixStreamServer):
    daemon_threads=True
    request_queue_size=8
    # Bound pre-auth threads too; a compromised worker cannot create unlimited threads.
    slots=threading.BoundedSemaphore(12)
    def process_request(self,request,address):
        if not self.slots.acquire(blocking=False): request.close(); return
        try: super().process_request(request,address)
        except Exception: self.slots.release(); raise
    def process_request_thread(self,request,address):
        try: super().process_request_thread(request,address)
        finally: self.slots.release()

if __name__=='__main__':
    os.umask(0o077)
    SOCKET_DIR.mkdir(parents=True,exist_ok=True)
    socket_path=SOCKET_DIR/'broker.sock'
    if socket_path.exists(): socket_path.unlink()
    # Recover one-shot jobs left behind by a broker/host crash before accepting new jobs.
    stale=subprocess.check_output(['docker','ps','-aq','--filter','label=slidegen.ephemeral=true'],text=True).split()
    if stale: subprocess.run(['docker','rm','-f',*stale],check=True,stdout=subprocess.DEVNULL)
    with Server(str(socket_path),Handler) as server:
        socket_path.chmod(0o660)
        print('broker ready',flush=True)
        server.serve_forever()
