var httpProxy = require('http-proxy');
httpProxy.createProxyServer({
  target: {
    protocol: 'https:',
    host: 'pswww.slac.stanford.edu',
    port: 443
  },
  changeOrigin: true,
}).listen(6749);
