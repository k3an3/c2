from flask import Flask

app = Flask(__name__)


@app.route("/")
def update():
    return render_template('camo.html')


if __name__ == "__main__":
    app.run()
