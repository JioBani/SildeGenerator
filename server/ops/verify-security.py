#!/usr/bin/env python3
"""Read-only network/security checks; no sudo and no firewall mutation."""
import json, pathlib, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
def run(args): return subprocess.check_output(args,cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
results={}
for service in ['api','worker','redis','egress-proxy']:
    cid=run(['docker','compose','ps','-q',service]); item=json.loads(run(['docker','inspect',cid]))[0]
    results[service]={'uid':item['Config']['User'],'readOnly':item['HostConfig']['ReadonlyRootfs'],'capDrop':item['HostConfig']['CapDrop'],
      'securityOpt':item['HostConfig']['SecurityOpt'],'memory':item['HostConfig']['Memory'],'pids':item['HostConfig']['PidsLimit'],
      'dockerSocketMounted':any(m['Destination']=='/var/run/docker.sock' for m in item['Mounts'])}
    assert results[service]['uid']=='1000:1000' and results[service]['readOnly'] and not results[service]['dockerSocketMounted']
script=r"""
const net=require('node:net');
(async()=>{const out={uid:process.getuid(),targets:{}};
for(const [host,port] of [['192.168.0.1',80],['10.0.0.1',80],['100.100.100.100',80],['169.254.169.254',80],['172.30.70.1',22],['1.1.1.1',443]]) {
 out.targets[host+':'+port]=await new Promise(resolve=>{const s=net.connect({host,port});s.setTimeout(1000);s.on('connect',()=>{s.destroy();resolve('CONNECTED')});s.on('error',e=>resolve(e.code));s.on('timeout',()=>{s.destroy();resolve('TIMEOUT')})});
} console.log(JSON.stringify(out));})();
"""
results['workerNetwork']=json.loads(run(['docker','compose','exec','-T','worker','node','-e',script]))
args=['docker','run','--rm','--network','none','--read-only','--user','1000:1000','--cap-drop','ALL','--security-opt','no-new-privileges:true','--pids-limit','64','--memory','128m','--cpus','0.3','--mount','type=volume,src=slidegen-server_proxy-socket,dst=/proxy,readonly',json.loads((ROOT/'private'/'broker.json').read_text())['image'],'node','-e']
env_script=r"""
import {spawnSync} from 'node:child_process';import {runnerEnv} from './runner-env.mjs';
const child=spawnSync('node',['-e','console.log(JSON.stringify(Object.keys(process.env)))'],{env:runnerEnv,encoding:'utf8'});
const keys=JSON.parse(child.stdout);
if(keys.some(k=>k.includes('REDIS')||k.includes('TOKEN')||k==='OPENAI_API_KEY')) process.exit(1);
const codex=spawnSync('codex',['--version'],{env:runnerEnv,encoding:'utf8'});
if(codex.status!==0)process.exit(1);
console.log(JSON.stringify({childEnvKeys:keys,codexVersion:codex.stdout.trim()}));
"""
env_args=args[:-2]+['node','--input-type=module','-e',env_script]
# Pass deliberate parent sentinel values; they must not reach the actual child environment.
env_args[env_args.index(json.loads((ROOT/'private'/'broker.json').read_text())['image']):env_args.index(json.loads((ROOT/'private'/'broker.json').read_text())['image'])]=['-e','REDIS_PASSWORD=sentinel','-e','APP_ACCESS_TOKEN=sentinel']
results['childEnvironment']=json.loads(run(env_args))
results['runnerNetwork']=json.loads(run(args+[script]))
proxy_script=r"""
const net=require('node:net');(async()=>{const out={};
for(const host of ['192.168.0.1','10.0.0.1','100.100.100.100','169.254.169.254','172.30.70.1','example.com','chatgpt.com','auth.openai.com']) {
 out[host]=await new Promise(resolve=>{const s=net.connect('/proxy/egress.sock');s.setTimeout(8000);s.on('connect',()=>s.write('CONNECT '+host+':443 HTTP/1.1\r\nHost: '+host+':443\r\n\r\n'));s.once('data',b=>{s.destroy();resolve(b.toString().split('\r\n')[0])});s.on('error',e=>resolve(e.code));s.on('timeout',()=>{s.destroy();resolve('TIMEOUT')});});
} console.log(JSON.stringify(out));})();
"""
results['proxyDestinations']=json.loads(run(args+[proxy_script]))
for host,result in results['runnerNetwork']['targets'].items(): assert result!='CONNECTED',host
for host,result in results['proxyDestinations'].items():
    assert ('200' if host in ['chatgpt.com','auth.openai.com'] else '403') in result,(host,result)
results['hostFirewallPending']=results['workerNetwork']['targets']['172.30.70.1:22']not in ['ENETUNREACH','EHOSTUNREACH','TIMEOUT']
print(json.dumps(results,indent=2))
(ROOT/'private'/'isolation-verification.json').write_text(json.dumps(results,indent=2))
if results['hostFirewallPending']: print('PENDING: worker can initiate host gateway SSH. Apply ops/apply-firewall.sh before external publication.')

if results['hostFirewallPending']: sys.exit(2)
