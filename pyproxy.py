#!/usr/bin/env python
'''
Extremely basic, simple Python based proxy that proxies a single specified remote site.
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

import requests

from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.request import urlopen


logger = logging.getLogger(__name__)
remote_url = ""

class ProxyHandler(SimpleHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        SimpleHTTPRequestHandler.__init__(self, request, client_address, server)
    def do_GET(self):
        logger.debug("Path: %s, proxying to %s", self.path, remote_url + self.path)
        with urlopen(remote_url + self.path) as f:
            self.wfile.write(str.encode("HTTP/1.1 200 OK\n"))
            self.wfile.write(str.encode(f.headers.as_string()))
            shutil.copyfileobj(f, self.wfile)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='An extremely simplistic HTTP proxy.')
    parser.add_argument('-v', '--verbose', action="store_true")
    parser.add_argument('--interface', default="0.0.0.0", help="The IP address/interface to listen on. For security reasons, listen on an internal IP. This defaults to listening on all interfaces. Hostnames should be acceptable.")
    parser.add_argument('--port', default=7557, help="The port to listen on.", type=int)
    parser.add_argument('remote_url', help="All requests are proxied to this URL. That is, the path of the request is appended to this parameter and used to generate the remote URL from which we will fetch contents.")
    args = parser.parse_args()
    remote_url = args.remote_url

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
    httpd = ThreadingHTTPServer(server_address, ProxyHandler)
    logger.info("Proxying requests to http://{1}:{2}/ to remote URL {0}".format(args.remote_url, args.interface, args.port))
    httpd.serve_forever()
