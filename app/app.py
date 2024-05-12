import os
from flask import Flask, render_template, request, Response

app = Flask(__name__)



@app.route('/')
def index():
    return render_template('index.html')


def generate(messages, model_type):
    return 'salve'


@app.route('/gpt4', methods=['POST'])
def gpt4():
    data = request.get_json()
    messages = data.get('messages', [])
    model_type = data.get('model_type')

    assistant_response = generate(messages, model_type)
    return Response(assistant_response, mimetype='text/event-stream')



if __name__ == '__main__':
    app.run(debug=True)
