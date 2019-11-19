import pprint

from dohjsonclient.client import DohJsonClient

TestTLD = 'puffballdesigns.com'

client = DohJsonClient()

#result = client.resolve({'name': TestTLD, 'type': 'A'})

print('-----\nby Google public dns\n------\n')
result_google = client.resolve_google({'name': TestTLD, 'type': 'A'})
pprint.pprint(result_google)
print('\n\n')

print('-----\nby Cloudflare public dns\n-----\n')
result_cloudflare = client.resolve_cloudflare({'name': TestTLD, 'type': 'A'})
pprint.pprint(result_cloudflare)
print('\n\n')
