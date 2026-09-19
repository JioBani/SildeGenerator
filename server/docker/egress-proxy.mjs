import http from 'node:http';
import net from 'node:net';
import { resolve4 } from 'node:dns/promises';
import { chmodSync, existsSync, unlinkSync } from 'node:fs';
const socket = '/proxy/egress.sock';
const domains = (process.env.EGRESS_ALLOW_HOSTS || 'chatgpt.com,*.chatgpt.com,openai.com,*.openai.com').split(',').map(x => x.trim().toLowerCase()).filter(Boolean);
if (!domains.length || domains.some(x => !/^(\*\.)?[a-z0-9][a-z0-9.-]+\.[a-z]{2,}$/.test(x))) throw Error('invalid egress allowlist');
export function publicIPv4(ip) {
  if (!net.isIPv4(ip)) return false;
  const [a,b] = ip.split('.').map(Number);
  return !(a===0 || a===10 || a===127 || a>=224 || (a===100 && b>=64 && b<=127) ||
    (a===169 && b===254) || (a===172 && b>=16 && b<=31) || (a===192 && (b===168 || b===0 || b===2)) ||
    (a===198 && (b===18 || b===19 || b===51)) || (a===203 && b===0));
}
const server = http.createServer((_req,res) => { res.writeHead(405); res.end(); });
server.maxConnections = 64;
server.headersTimeout = 10000;
server.on('connect', async (req, client, head) => {
  client.on('error', () => {});
  try {
    const m = /^([a-zA-Z0-9.-]+):443$/.exec(req.url || '');
    if (!m) throw Error('destination');
    const host = m[1].toLowerCase();
    if (!domains.some(d => d.startsWith('*.') ? host.endsWith(d.slice(1)) && host !== d.slice(2) : host===d)) throw Error('allowlist');
    const ips = await resolve4(host);
    if (!ips.length || ips.some(ip => !publicIPv4(ip))) throw Error('private address');
    // Connect to the validated address, never resolve the hostname a second time.
    const upstream = net.connect({host:ips[0],port:443});
    upstream.setTimeout(120000, () => upstream.destroy());
    client.setTimeout(120000, () => client.destroy());
    upstream.on('error', () => client.destroy());
    client.on('close', () => upstream.destroy());
    upstream.on('connect', () => {
      client.write('HTTP/1.1 200 Connection Established\r\n\r\n');
      if (head.length) upstream.write(head);
      upstream.pipe(client); client.pipe(upstream);
      console.log(JSON.stringify({event:'connect',host}));
    });
  } catch { client.end('HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n'); }
});
if (existsSync(socket)) unlinkSync(socket);
server.listen(socket, () => chmodSync(socket,0o666));
