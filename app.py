from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# 設定 SQLite 資料庫
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 資料模型
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    icon = db.Column(db.String(50))
    is_need = db.Column(db.Boolean, default=True)
    date = db.Column(db.String(10), nullable=False) 

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    budget = db.Column(db.Float, default=10000.0)

# 初始化資料庫
with app.app_context():
    db.create_all()
    if not Settings.query.first():
        db.session.add(Settings(budget=10000.0))
        db.session.commit()

# --- 頁面路由 ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    return render_template('history.html')

# --- API 路由 ---
@app.route('/api/data', methods=['GET'])
def get_data():
    settings = Settings.query.first()
    # 確保抓資料時不會因為欄位不存在而報錯
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    
    tx_list = []
    for tx in transactions:
        tx_list.append({
            "id": tx.id,
            "title": tx.title,
            "amount": tx.amount,
            "category": tx.category,
            "icon": tx.icon,
            "isNeed": tx.is_need,
            "date": tx.date  # <--- 這裡修改：直接傳送字串，不要用 .strftime
        })
    
    return jsonify({
        "budget": settings.budget,
        "transactions": tx_list
    })

@app.route('/api/transaction', methods=['POST'])
def add_transaction():
    data = request.json
    new_tx = Transaction(
        title=data['title'],
        amount=data['amount'],
        category=data['category'],
        icon=data['icon'],
        is_need=data['isNeed'],
        date=data.get('date', datetime.now().strftime("%Y-%m-%d"))
    )
    db.session.add(new_tx)
    db.session.commit()
    return jsonify({"status": "success"})

# 編輯/更新 API
@app.route('/api/transaction/<int:tx_id>', methods=['PUT'])
def update_transaction(tx_id):
    data = request.json
    tx = Transaction.query.get_or_404(tx_id)
    tx.title = data['title']
    tx.amount = data['amount']
    tx.category = data['category']
    tx.icon = data['icon']
    tx.is_need = data['isNeed']
    tx.date = data['date']
    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/api/transaction/<int:tx_id>', methods=['DELETE'])
def delete_transaction(tx_id):
    tx = Transaction.query.get(tx_id)
    if tx:
        db.session.delete(tx)
        db.session.commit()
    return jsonify({"status": "success"})

@app.route('/api/budget', methods=['POST'])
def update_budget():
    new_budget = request.json.get('budget')
    settings = Settings.query.first()
    settings.budget = float(new_budget)
    db.session.commit()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)