# lambda_function.py
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_question')
def add_question():
    return render_template('add_question.html')

@app.route('/view_cache')
def view_cache():
    return render_template('view_cache.html')

# Add other routes as needed

# For serverless deployment
def handler(event, context):
    return app(event, context)
