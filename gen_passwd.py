import json
from hashlib import md5

with open('sites.json') as f:
    sites= json.load(f)

f=open('.passwd','a')

for s in sites:
    passwd=md5('HIDDEN'.encode()).hexdigest()
    f.write('{},{}\n'.format(s['id'],passwd[:6]))
    
f.close()

