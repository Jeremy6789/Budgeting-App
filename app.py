from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)

DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"budget": 10000, "transactions": []}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(load_data())

@app.route('/api/transaction', methods=['POST'])
def add_transaction():
    new_tx = request.json
    data = load_data()
    data['transactions'].insert(0, new_tx) # 新的在前
    save_data(data)
    return jsonify({"status": "success"})

@app.route('/api/transaction/<int:index>', methods=['DELETE'])
def delete_transaction(index):
    data = load_data()
    if 0 <= index < len(data['transactions']):
        data['transactions'].pop(index)
        save_data(data)
    return jsonify({"status": "success"})

@app.route('/api/budget', methods=['POST'])
def update_budget():
    new_budget = request.json.get('budget')
    data = load_data()
    data['budget'] = float(new_budget)
    save_data(data)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)