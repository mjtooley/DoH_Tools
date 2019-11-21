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
from utils.utils import (
    create_http_wire_response,
    create_http_json_response,
)


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
        print(e)


def get_question(dnsq):
    question = str(dnsq.question[0])
    question = question.split()
    question = question[0].rstrip('.')
    return question

def resolve(dnsq):
    question = get_question(dnsq)
    #question = str(dnsq.question[0])
    #question = question.split()
    #question = question[0].rstrip('.')
    dns_resolver = DNSResolverClient(name_server='internal')
    dnsr = dns_resolver.resolve((dnsq))
    # print("resolve:", dnsr)
    return dnsr



TV_EVERYWHERE_HOSTS = {'www.nbc.com', 'www.cbs.com', 'www.espn.com'}
TV_EVERYWHERE_AUTH = 'sp.auth.adobe.com'

tv_everywhere_hosts = {} # init the outer dict
for tvh in TV_EVERYWHERE_HOSTS:
    tv_everywhere_hosts[tvh] = {} # Init the inner list
last_tve = {}

def tv_everywhere_host(qname):
    for tvh in TV_EVERYWHERE_HOSTS:
        if tvh in qname:
            return tvh
    return None

def check_tve(client_ip, dnsq):
    q = get_question(dnsq)
    tvh = tv_everywhere_host(q)
    if tvh != None:
        # add a tuple for the entry
        # TO-DO Need to fix the code log the number of unique IPs per TVH
        if client_ip in tv_everywhere_hosts[h]:
        if tv_everywhere_hosts[tvh][client_ip]
        tv_everywhere_hosts[tvh][client_ip] = 0  # Append the client_ip tuple as seen chatting with the TVH
        last_tve[client_ip] = tvh # Store the last TVH seen for the IP
    # Now check if it is a TV_EVERYWHERE_AUTH
    if TV_EVERYWHERE_AUTH in q:
        for h in TV_EVERYWHERE_HOSTS:
            if client_ip in tv_everywhere_hosts[h]:
                if tv_everywhere_hosts[h][client_ip] == 0:
                    tv_everywhere_hosts[h][client_ip] = 3600
                    print("added {} to tv_everywhere_client[{}]".format(h, client_ip))
                elif tv_everywhere_hosts[h][client_ip] > 0:
                    print('--- Multiple Logins Detected for {} to {} -------\n'.format(client_ip, last_tve[client_ip]))



def add_tve_client(client_ip, dnsr):
    # extract the TTL from the dns response
    print("Add TVE client {}".format(client_ip))
    ttl = 3600
    if client_ip in tv_everywhere_clients:
        print("we already learned this client")
    else:
        tv_everywhere_clients[client_ip] = ttl
        print("added {} to tv_everywhere list".format(client_ip))

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        global tv_everywhere_clients
        # print('do_GET')
        url_path = self.path
        print(url_path)
        params: Dict[url_path, List]
        params = parse_qs(urlparse(url_path).query)

        headers = self.headers
        ua = self.headers['User-Agent']
        accept = self.headers['Accept']
        ct = self.headers['Content-Type']
        #content_length = int(self.headers['Content-Length'])
        client_ip = self.client_address[0]
        if 'referer' in self.headers:
            referrer = self.headers['referer']
        # Send DoH Request to upstream DoH Resolver or DNS Resolver
        client = DohJsonClient()
        try:
            print(params['name'], params['type'])
            if 'name' in params:
                qname = params['name'][0]
                dnsq = dns.message.make_query(qname, dns.rdatatype.ANY)
                dnsr = resolve(dnsq)
                result = client.resolve_cloudflare({'name': params['name'][0], 'type': params['type'][0]})
                check_tve(client_ip,dnsq)
                self.send_response(200)
                #self.send_header('content-type', 'application/dns-message')
                #self.send_header('server', 'ncta-doh')
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
        client_ip = self.client_address[0]
        #print("UA:", ua)
        #print("Client:", client_ip)
        if 'referer' in self.headers:
            referrer = self.headers['referer']
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        url_path = self.path
        # print("URL_Path:", url_path)
        params: Dict[url_path, List]
        params = parse_qs(urlparse(url_path).query)

        try:
            dnsq =dns_query_from_body(body)
            dnsr = resolve(dnsq)
            check_tve(client_ip,dnsq)
            #print("dnsr:", dnsr.answer)
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

ADDRESS = '172.25.12.45'
PORT = 4443
httpd = HTTPServer((ADDRESS, PORT), SimpleHTTPRequestHandler)

try:
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile='mypemfile.pem', server_side=True)
except Exception as e:
    print (e)

print("Starting DoH Server on {}:{}".format(ADDRESS,PORT))
httpd.serve_forever()
