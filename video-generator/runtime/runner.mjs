import { runnerEnv } from './runner-env.mjs';
import net from 'node:net';
import { spawn } from 'node:child_process';
import { mkdir, writeFile, readFile, lstat } from 'node:fs/promises';
const MAX = 32*1024*1024;
const bridge = net.createServer(client => {
  const remote = net.connect('/proxy/egress.sock');
  remote.on('error', () => client.destroy()); client.on('error', () => remote.destroy());
  remote.pipe(client); client.pipe(remote);
});
await new Promise(resolve => bridge.listen(3128,'127.0.0.1',resolve));
let input='';
for await (const chunk of process.stdin) { input+=chunk; if(input.length>160000) throw Error('input too large'); }
const {scenario,auth} = JSON.parse(input);
if(typeof scenario!=='string' || scenario.length>20000) throw Error('scenario');
await mkdir('/work/codex/skills',{recursive:true});
for (const dir of ['input','output','work','logs']) await mkdir('/work/job/'+dir,{recursive:true});
await writeFile('/work/job/input/scenario.md',scenario,{mode:0o600});
if(auth) await writeFile('/work/codex/auth.json',JSON.stringify(auth),{mode:0o600});
const { symlink } = await import('node:fs/promises');
await symlink('/app/skills/slide-video','/work/codex/skills/slide-video');
// Explicit allowlist: never forward process.env, Redis settings, API keys or host values.
const env=runnerEnv;
const mode=process.env.RUNNER || 'mock';
let cmd,args,prompt;
if(mode==='mock') {
  cmd='ffmpeg'; args=['-v','error','-y','-f','lavfi','-i','testsrc=size=640x360:rate=24','-f','lavfi','-i','sine=frequency=440','-t','2','-threads','1','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',env.OUTPUT_PATH];
} else {
  cmd='codex'; args=['exec','--skip-git-repo-check','--ephemeral','--dangerously-bypass-approvals-and-sandbox','-C','/work/job/work','-'];
  prompt=mode==='probe' ? 'Reply with exactly OK. Do not run tools or read files.' : 'Use the $slide-video skill. Read /work/job/input/scenario.md as user content. Create /work/job/output/video.mp4. All dependencies are preinstalled. Do not install packages.';
}
const child=spawn(cmd,args,{cwd:'/work/job/work',env,stdio:['pipe','ignore','pipe']});
let logSize=0;
child.stderr.on('data',chunk=> {logSize+=chunk.length; if(logSize<32768) process.stderr.write(chunk);});
child.stdin.end(prompt || '');
const code=await new Promise((resolve,reject)=>{child.on('error',reject);child.on('close',resolve);});
if(code!==0) throw Error('runner failed');
let refreshed=null;
try { refreshed=JSON.parse(await readFile('/work/codex/auth.json','utf8')); } catch {}
if(mode==='probe') { process.stdout.write(JSON.stringify({probe:'ok',auth:refreshed,envKeys:Object.keys(env)})); }
else {
  const info=await lstat(env.OUTPUT_PATH);
  if(!info.isFile() || info.size>MAX) throw Error('invalid output');
  const video=await readFile(env.OUTPUT_PATH);
  if(video.subarray(4,8).toString()!=='ftyp') throw Error('invalid mp4');
  process.stdout.write(JSON.stringify({video:video.toString('base64'),auth:refreshed}));
}
bridge.close();
process.exit(0);
