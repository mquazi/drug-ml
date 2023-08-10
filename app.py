from flask import Flask, render_template, url_for

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/structure")
def structure():
    return render_template("structure.html")


@app.route("/batch")
def batch():
    return render_template("batch.html")


@app.route("/models")
def models():
    return render_template("models.html")


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
