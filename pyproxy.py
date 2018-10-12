#!/usr/bin/env python
'''
Extremely basic, simple Python 3 based proxy that proxies a single specified remote site.
Sometimes, we will not have access to the web services from compute nodes.
SSH tunnels are an option here but may have timeout concerns and may have SSL issues.
If installing and using heavy weight proxies (Squid/Apache/npm/node etc) are not worth the effort....
Many caveats
--> No security checks
--> Not copying headers across; if needed, this can be added.
--> Redirection should be handled by urllib.
--> Only GET's are supported for now.
'''

import os
import sys
import logging
import argparse
import shutil

from SocketServer import TCPServer, ForkingTCPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from urllib import urlopen

logger = logging.getLogger(__name__)

class ProxyHandler(SimpleHTTPRequestHandler):
    def __init__(self, request, client_address, server, remote_url):
        self.remote_url = remote_url
        SimpleHTTPRequestHandler.__init__(self, request, client_address, server)
    def do_GET(self):
        logger.debug("Path:" + self.path)
        shutil.copyfileobj(urlopen(self.remote_url + self.path), self.wfile)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='An extremely simplistic HTTP proxy.')
    parser.add_argument('-v', '--verbose', action="store_true")
    parser.add_argument('--interface', default="0.0.0.0", help="The IP address/interface to listen on. For security reasons, listen on an internal IP. This defaults to listening on all interfaces. Hostnames should be acceptable.")
    parser.add_argument('--port', default=7557, help="The port to listen on.")
    parser.add_argument('remote_url', help="All requests are proxied to this URL. That is, the path of the request is appended to this parameter and used to generate the remote URL from which we will fetch contents.")
    args = parser.parse_args()

    root = logging.getLogger()
    ch = logging.StreamHandler(sys.stdout)

    if args.verbose:
        root.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
    else:
        root.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

    server_address = (args.interface, args.port)
    def createHandler(request, client_address, server):
        return ProxyHandler(request, client_address, server, args.remote_url)
    httpd = ForkingTCPServer(server_address, createHandler)
    logger.info("Proxying requests to http://{1}:{2}/ to remote URL {0}".format(args.remote_url, args.interface, args.port))
    httpd.serve_forever()
