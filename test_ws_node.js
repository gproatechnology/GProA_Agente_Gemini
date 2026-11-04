const http = require('http');
const fs = require('fs');

const path = process.argv[2] || '/';
const out = [];

const opts = {
  hostname: '127.0.0.1',
  port: 18789,
  path,
  method: 'GET',
  headers: {
    'Upgrade': 'websocket',
    'Connection': 'Upgrade',
    'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
    'Sec-WebSocket-Version': '13',
    'Authorization': '7e5afe89ced49cea1145c87e98637a27726876fcdd2e488d'
  }
};

const req = http.request(opts, (res) => {
  out.push('STATUS: ' + res.statusCode);
  res.on('data', (d) => out.push(d.toString().slice(0, 500)));
  res.on('end', () => {
    fs.writeFileSync('/tmp/ws-result.txt', out.join('\n'));
    console.log('written');
  });
});

req.on('socket', (s) => {
  s.setTimeout(3000);
  s.on('timeout', () => {
    out.push('TIMEOUT');
    fs.writeFileSync('/tmp/ws-result.txt', out.join('\n'));
    req.destroy();
  });
});

req.on('error', (e) => {
  out.push('ERROR: ' + e.message);
  fs.writeFileSync('/tmp/ws-result.txt', out.join('\n'));
});

req.end();
setTimeout(() => {
  if (!fs.existsSync('/tmp/ws-result.txt') || fs.statSync('/tmp/ws-result.txt').size === 0) {
    fs.writeFileSync('/tmp/ws-result.txt', 'NO_OUTPUT');
  }
  process.exit(0);
}, 6000);
