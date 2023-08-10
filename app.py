from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    title = 'My Flask Website'
    website_name = 'Awesome Flask Site'
    return render_template('index.html', title=title, website_name=website_name)
