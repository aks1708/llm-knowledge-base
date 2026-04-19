#!/usr/bin/env python3
"""Simple quiz application with dark theme."""

import json
import os
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

def get_quiz_file():
    """Load the test_questions.json file."""
    quiz_dir = os.path.dirname(__file__)
    return os.path.join(quiz_dir, 'test_questions.json')

QUIZ_FILE = get_quiz_file()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/quiz')
def get_quiz():
    with open(QUIZ_FILE, 'r') as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/api/quiz', methods=['POST'])
def save_quiz():
    data = request.get_json()
    with open(QUIZ_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
