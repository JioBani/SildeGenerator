#!/usr/bin/env python3
"""Run on mini. Creates and revokes test keys; keeps test job/audit data. Never prints keys."""
import concurrent.futures, json, pathlib, subprocess, time, urllib.request, urllib.error, uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
PREFIX='verify_'+uuid.uuid4().hex[:8]
USERS=[]
RESULTS=[]
def command(args): return subprocess.check_output(args,cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
def key(user):
    user=PREFIX+'_'+user; USERS.append(user)
    return user,command(['docker','compose','run','--rm','-T','keyctl','issue',user])
def http(method,path,token=None,body=None,extra=None):
    headers={'Content-Type':'application/json',**(extra or {})}
    if token: headers['Authorization']='Bearer '+token
    req=urllib.request.Request('http://127.0.0.1:3000/api/'+path,data=json.dumps(body).encode() if body is not None else None,headers=headers,method=method)
    try:
        with urllib.request.urlopen(req,timeout=20) as res: return res.status,res.read()
    except urllib.error.HTTPError as e: return e.code,e.read()
def check(name,actual,expected):
    ok=actual==expected; RESULTS.append({'test':name,'actual':actual,'expected':expected,'ok':ok});print(('PASS ' if ok else 'FAIL ')+name+': '+str(actual),flush=True)
    if not ok: raise AssertionError(name)
def redis(op,*args):
    # Credentials stay in the container; argv contains only test counters and identifiers.
    code="const R=require('ioredis'); const c=require('./dist/config/app-config'); const r=new R(c.redisConnection()); r.call(...JSON.parse(process.argv[1])).then(x=>{console.log(JSON.stringify(x));r.disconnect()}).catch(()=>process.exit(1))"
    return json.loads(command(['docker','compose','exec','-T','api','node','-e',code,json.dumps([op,*args])]))
def wait_job(token,jid):
    for _ in range(90):
        status,body=http('GET','jobs/'+jid,token)
        if status==200:
            state=json.loads(body)['status']
            if state=='completed': return
            if state=='failed': raise AssertionError('mock render failed')
        time.sleep(1)
    raise TimeoutError('mock job')
try:
    user,a=key('a'); _,b=key('b')
    check('missing key',http('POST','jobs',body={'scenario':'test'})[0],401)
    check('invalid key',http('POST','jobs','sg_'+'x'*43,{'scenario':'test'})[0],401)
    check('unknown field',http('POST','jobs',a,{'scenario':'test','command':'id'})[0],400)
    check('blank scenario',http('POST','jobs',a,{'scenario':'  '})[0],400)
    check('body size limit',http('POST','jobs',a,{'scenario':'x'*90000})[0],413)
    check('CORS denied',http('POST','jobs',a,{'scenario':'test'},{'Origin':'https://untrusted.invalid'})[0],403)
    check('management route absent',http('POST','keys',a,{})[0],404)
    check('test endpoint without key',http('GET','test')[0],401)
    code,data=http('GET','test',a)
    check('test endpoint with key',(code,json.loads(data).get('message')),(200,'slidegen authenticated test response'))
    code,data=http('POST','jobs',a,{'scenario':'security mock verification'})
    check('mock create',code,202);jid=json.loads(data)['id']
    check('other user status',http('GET','jobs/'+jid,b)[0],404)
    check('other user video',http('GET','jobs/'+jid+'/video',b)[0],404)
    wait_job(a,jid)
    code,data=http('GET','jobs/'+jid+'/video',a)
    check('mock download',code,200);check('mp4 magic',data[4:8].decode(),'ftyp')
    # Simulate a compromised worker placing a symlink in the shared output directory.
    flip="const f=require('fs');const p='/data/jobs/'+process.argv[1]+'/output/video.mp4';f.renameSync(p,p+'.original');f.symlinkSync('/keys/keys.json',p)"
    restore="const f=require('fs');const p='/data/jobs/'+process.argv[1]+'/output/video.mp4';f.unlinkSync(p);f.renameSync(p+'.original',p)"
    command(['docker','compose','exec','-T','worker','node','-e',flip,jid])
    try: check('worker symlink cannot expose API keys',http('GET','jobs/'+jid+'/video',a)[0],410)
    finally: command(['docker','compose','exec','-T','worker','node','-e',restore,jid])
    # Counters are seeded only for a freshly-created test identity.
    config=json.loads(command(['docker','compose','exec','-T','api','node','-e',"const {config:c}=require('./dist/config/app-config');console.log(JSON.stringify({daily:c.dailyJobs,pending:c.userPending,global:c.globalPending,rate:c.requestsPerMinute}))"]))
    day=time.strftime('%Y-%m-%d',time.gmtime())
    redis('SET','limits:daily:'+user+':'+day,str(config['daily']),'EX','120')
    check('daily limit',http('POST','jobs',a,{'scenario':'test'})[0],429)
    redis('DEL','limits:daily:'+user+':'+day)
    sentinels=['verify-'+uuid.uuid4().hex for _ in range(config['pending'])]
    redis('SADD','limits:pending:'+user,*sentinels)
    check('user pending limit',http('POST','jobs',a,{'scenario':'test'})[0],429)
    redis('SREM','limits:pending:'+user,*sentinels)
    sentinels=['verify-'+uuid.uuid4().hex for _ in range(config['global'])]
    try:
        redis('SADD','limits:pending:global',*sentinels)
        check('global queue limit',http('POST','jobs',a,{'scenario':'test'})[0],429)
    finally: redis('SREM','limits:pending:global',*sentinels)
    redis('SET','limits:rate:'+user,str(config['rate']),'EX','60')
    check('request rate limit',http('GET','jobs/'+jid,a)[0],429)
    command(['docker','compose','run','--rm','-T','keyctl','revoke',user])
    check('revoked key',http('GET','jobs/'+jid,a)[0],401)
    # Five separate users exercise five simultaneous per-job containers.
    tokens=[key('parallel'+str(i))[1] for i in range(5)]
    def start(token):
        code,data=http('POST','jobs',token,{'scenario':'parallel isolated mock'});check('parallel create',code,202)
        return token,json.loads(data)['id']
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool: jobs=list(pool.map(start,tokens))
    max_active=0
    for _ in range(90):
        active=command(['docker','ps','-q','--filter','label=slidegen.ephemeral=true']).split()
        max_active=max(max_active,len(active))
        states=[json.loads(http('GET','jobs/'+jid,t)[1])['status'] for t,jid in jobs]
        if all(s=='completed' for s in states): break
        if 'failed' in states: raise AssertionError('parallel job failed')
        time.sleep(0.5)
    check('five jobs completed',sum(s=='completed' for s in states),5)
    print('Peak simultaneous one-shot containers:',max_active,flush=True)
finally:
    for user in USERS: command(['docker','compose','run','--rm','-T','keyctl','revoke',user])
    (ROOT/'private'/'api-verification.json').write_text(json.dumps(RESULTS,indent=2))
