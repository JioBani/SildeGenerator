#!/usr/bin/env python3
"""One real Codex probe; never prints tokens and never changes host ~/.codex settings."""
import json,pathlib,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
def record_failure(error):
    quota = b"hit your usage limit" in error.lower()
    summary = {'realCodex': 'blocked_usage_limit' if quota else 'failed',
               'network': 'none', 'proxy': 'unix socket -> allowlisted HTTPS',
               'upstreamReturnedUsageLimit': quota, 'fullExecutionCompleted': False}
    (ROOT/'private'/'codex-verification.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
    return 3 if quota else 1
if '--record-last-error' in sys.argv:
    sys.exit(record_failure((ROOT/'private'/'codex-probe-error.log').read_bytes()))
authfile=ROOT/'private'/'codex-auth.json'
if not authfile.exists():
    # Reuse the old API-only Codex volume, not the host Codex directory.
    raw=subprocess.check_output(['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--user','0:0','-v','slidegen-server_codex-home:/codex:ro','alpine:3.22','cat','/codex/auth.json'])
    auth=json.loads(raw);authfile.write_text(json.dumps(auth));authfile.chmod(0o600)
auth=json.loads(authfile.read_text())
name='slidegen-codex-probe'
args=['docker','run','--rm','--name',name,'--network','none','--read-only','--user','1000:1000','--cap-drop','ALL',
 '--security-opt','no-new-privileges:true','--pids-limit','128','--memory','768m','--memory-swap','768m','--cpus','0.7',
 '--tmpfs','/tmp:rw,noexec,nosuid,nodev,size=64m,uid=1000,gid=1000,mode=700',
 '--tmpfs','/work:rw,nosuid,nodev,size=384m,uid=1000,gid=1000,mode=700',
 '--mount','type=volume,src=slidegen-server_proxy-socket,dst=/proxy,readonly',
 '--env','RUNNER=probe','--log-driver','none','-i',json.loads((ROOT/'private'/'broker.json').read_text())['image']]
proc=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
    out,err=proc.communicate(json.dumps({'scenario':'connection probe','auth':auth}).encode(),timeout=180)
    if proc.returncode:
        # Save bounded diagnostic in the private operator directory, never print auth-bearing output.
        (ROOT/'private'/'codex-probe-error.log').write_bytes(err[-16000:])
        sys.exit(record_failure(err))
    result=json.loads(out)
    assert result['probe']=='ok'
    assert not any('REDIS' in key or 'TOKEN' in key or key in ['APP_ACCESS_TOKEN','OPENAI_API_KEY'] for key in result['envKeys'])
    if result.get('auth'): authfile.write_text(json.dumps(result['auth']));authfile.chmod(0o600)
    summary={'realCodex':'ok','network':'none','proxy':'unix socket -> allowlisted HTTPS','childEnvKeys':result['envKeys']}
    print(json.dumps(summary,indent=2));(ROOT/'private'/'codex-verification.json').write_text(json.dumps(summary,indent=2))
finally:
    subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if proc.poll() is None: proc.kill();proc.wait()
