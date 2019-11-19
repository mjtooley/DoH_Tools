import json
import urllib.parse
import urllib.request
import urllib.error
from urllib.error import HTTPError
import ssl
import requests
import dns.message

PUBLIC_DNS_SERVERS = {
    'default': 'https://172.25.12.45:443',
    'local': 'http://127.0.0.1:8080',
    'Google': 'https://dns.google/resolve',
    'Cloudflare': 'https://cloudflare-dns.com/dns-query'
}

#PUBLIC_DNS_SERVERS = {
#    'Google': 'https://dns.google/resolve',
#    'Cloudflare': 'https://cloudflare-dns.com/dns-query',
#}


class DohJsonClient:

    def __init__(self, *args, **kwargs):
        self.servers = kwargs.get('servers', PUBLIC_DNS_SERVERS)
        self.default_server = kwargs.get('default_server', PUBLIC_DNS_SERVERS['default'])

    def resolve(self, query: object, server: object = None) -> object:
        _server = server or self.default_server
        result = self._request(_server, query)
        result.update({'DOHServer': _server})
        return result

    def resolve_google(self, query):
        server = PUBLIC_DNS_SERVERS['Google']
        return self.resolve(query, server)

    def resolve_cloudflare(self, query):
        server = PUBLIC_DNS_SERVERS['Cloudflare']
        return self.resolve(query, server)

    def resolve_all(self, query):
        results = []
        for server in PUBLIC_DNS_SERVERS.values():
            results.append(self.resolve(query, server))
        return results

    def _request(self, base_url, data_dict={}):
        print ("_request: ", base_url)
        context = ssl._create_unverified_context()
        headers = {
            'Accept': 'application/dns-json'
        }
        data = urllib.parse.urlencode(data_dict)
        dnsq = dns.message.make_query(data_dict['name'],data_dict['type'])

        request = urllib.request.Request(
            base_url+'?'+data, headers=headers, method='GET')

        try:
            response = urllib.request.urlopen(request,context=context)  # nosec
        except HTTPError as error:
            response = error

        try:
            result = json.loads(response.read())
        except json.JSONDecodeError:
            raise
            result = {}
        return result
