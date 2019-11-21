import pprint

from dohjsonclient.client import DohJsonClient

TestTLD = 'www.nbc.com'
TestTVE = 'sp.auth.adobe.com'
TestTLD2 = 'www.cbs.com'

client = DohJsonClient()

print('-----\n Local NCTA DOH Resolver \n ------\n')
print("Trying {}".format(TestTLD2))
result = client.resolve({'name': TestTLD2, 'type': 'A'})
#pprint.pprint(result)
print("Trying {}".format(TestTVE))
result = client.resolve({'name': TestTVE, 'type': 'A'})
#pprint.pprint(result)
print("Trying {}".format(TestTLD))
result = client.resolve({'name': TestTLD, 'type': 'A'})
#pprint.pprint(result)
print("Trying {}".format(TestTVE))
result = client.resolve({'name': TestTVE, 'type': 'A'})
#pprint.pprint(result)

print("attempting second login to NBC")
print("Trying {}".format(TestTVE))
result = client.resolve({'name': TestTVE, 'type': 'A'})
#pprint.pprint(result)


