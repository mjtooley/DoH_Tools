from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
import socket
from io import BytesIO
from urllib.parse import urlparse, parse_qs
from typing import Dict, List
import random
import requests
from dohjsonclient.client import DohJsonClient
import json
import dns.exception
import dns.message
from dns.message import Message
import dns.rcode
from dns import resolver, query, exception

class DNSResolverClient:
    def __init__(self, name_server: str = "internal"):
        self.name_server = name_server

    def resolve(self, message: Message) -> Message:
        maximum = 4
        timeout = 0.4
        response_message = 0
        if self.name_server == 'internal':
            self.name_server = resolver.get_default_resolver().nameservers[0]
        done = False
        tests = 0
        while not done and tests < maximum:
            try:
                response_message = query.udp(message, self.name_server, timeout=timeout)
                done = True
            except exception.Timeout:
                tests += 1
        return response_message

def dns_query_from_body(body: bytes):
    exc = b'Malformed DNS query'
    try:
        return dns.message.from_wire(body)
    except Exception as e:
        if debug:
            exc = str(e).encode('utf-8')
    raise server_protocol.DOHDNSException(exc)

def resolve(dnsq):
    question = str(dnsq.question[0])
    question = question.split()
    question = question[0].rstrip('.')
    dns_resolver = DNSResolverClient(name_server='internal')
    dnsr = dns_resolver.resolve((dnsq))
    print("resolve:", dnsr)
    return dnsr

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        print('do_GET')
        url_path = self.path
        print(url_path)
        params: Dict[url_path, List]
        params = parse_qs(urlparse(url_path).query)

        headers = self.headers
        ua = self.headers['User-Agent']
        accept = self.headers['Accept']
        ct = self.headers['Content-Type']
        #content_length = int(self.headers['Content-Length'])
        client = self.client_address[0]
        # Send DoH Request to upstream DoH Resolver or DNS Resolver
        client = DohJsonClient()
        try:
            print(params['name'], params['type'])
            if 'name' in params:
                result = client.resolve_cloudflare({'name': params['name'][0], 'type': params['type'][0]})
                print (result)
            self.send_response(200)
            self.end_headers()
            doh_resp = json.dumps(result)
            # Need to encode the serialized JSON data
            self.wfile.write(doh_resp.encode('utf-8'))
        except Exception as e:
            print(e)

    def do_POST(self):
        print("do_POST")
        headers = self.headers
        ua = self.headers['User-Agent']
        accept = self.headers['Accept']
        ct = self.headers['Content-Type']
        client = self.client_address[0]
        print("UA:", ua)
        print("Client:", client)
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        url_path = self.path
        # print("URL_Path:", url_path)
        params: Dict[url_path, List]
        params = parse_qs(urlparse(url_path).query)

        try:
            dnsq =dns_query_from_body(body)
            dnsr = resolve(dnsq)
            print("dnsr:", dnsr.answer)
        except Exception as e:
            print(e)


        if dnsr is None:
            dnsr = dns.message.make_response(dnsq)
            dnsr.set_rcode(dns.rcode.SERVFAIL)

        # response_headers.append(('content-length', str(len(body))))
        self.send_response(200)
        self.send_header('content-type', 'application/dns-message')
        self.send_header('server', 'ncta-doh')
        self.end_headers()

        body = dnsr.to_wire()
        response = BytesIO()
        response.write(body)
        self.wfile.write(response.getvalue())

httpd = HTTPServer(('172.25.12.45', 443), SimpleHTTPRequestHandler)

try:
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile='mypemfile.pem', server_side=True)
except Exception as e:
    print (e)

print("Starting DoH Server")
httpd.serve_forever()
