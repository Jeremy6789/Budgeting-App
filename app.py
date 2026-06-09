import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# --- 資料庫設定 ---
# 使用絕對路徑確保在不同環境（如 Render 或本地）執行時資料庫位置正確
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- 資料模型 (Models) ---

class Transaction(db.Model):
    """帳目明細模型"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)   # 項目名稱
    amount = db.Column(db.Float, nullable=False)        # 金額
    category = db.Column(db.String(50))                 # 分類 (飲食, 交通...)
    icon = db.Column(db.String(50))                     # FontAwesome 圖標類名
    is_need = db.Column(db.Boolean, default=True)       # 是否為必要支出 (Need vs Want)
    date = db.Column(db.String(10), nullable=False)     # 日期 (格式: YYYY-MM-DD)

class Settings(db.Model):
    """全域設定模型 (儲存總預算)"""
    id = db.Column(db.Integer, primary_key=True)
    budget = db.Column(db.Float, default=10000.0)

# --- 初始化資料庫 ---
with app.app_context():
    db.create_all()
    # 如果是第一次執行，初始化預算設定
    if not Settings.query.first():
        db.session.add(Settings(budget=10000.0))
        db.session.commit()

# --- 頁面渲染路由 ---

@app.route('/')
def index():
    """主儀表板頁面"""
    return render_template('index.html')

@app.route('/history')
def history():
    """帳目明細歷史頁面"""
    return render_template('history.html')

# --- API 路由 (供前端 JS 呼叫) ---

@app.route('/api/data', methods=['GET'])
def get_data():
    """獲取初始資料：包含預算與所有交易紀錄"""
    settings = Settings.query.first()
    # 按日期降序排列，讓最新的顯示在前面
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
            "date": tx.date
        })
    
    return jsonify({
        "budget": settings.budget,
        "transactions": tx_list
    })

@app.route('/api/transaction', methods=['POST'])
def add_transaction():
    """新增一筆紀錄"""
    data = request.get_json()
    try:
        new_tx = Transaction(
            title=data['title'],
            amount=float(data['amount']),
            category=data.get('category', '其他'),
            icon=data.get('icon', 'fa-dollar-sign'),
            is_need=data.get('isNeed', True),
            date=data.get('date', datetime.now().strftime("%Y-%m-%d"))
        )
        db.session.add(new_tx)
        db.session.commit()
        return jsonify({"status": "success", "message": "已儲存紀錄"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/transaction/<int:tx_id>', methods=['PUT'])
def update_transaction(tx_id):
    """更新既有紀錄"""
    data = request.get_json()
    tx = Transaction.query.get_or_404(tx_id)
    try:
        tx.title = data['title']
        tx.amount = float(data['amount'])
        tx.category = data['category']
        tx.icon = data['icon']
        tx.is_need = data['isNeed']
        tx.date = data['date']
        db.session.commit()
        return jsonify({"status": "success", "message": "已更新紀錄"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/transaction/<int:tx_id>', methods=['DELETE'])
def delete_transaction(tx_id):
    """刪除筆紀錄"""
    tx = Transaction.query.get(tx_id)
    if tx:
        db.session.delete(tx)
        db.session.commit()
        return jsonify({"status": "success", "message": "已刪除紀錄"})
    return jsonify({"status": "error", "message": "找不到該紀錄"}), 404

@app.route('/api/budget', methods=['POST'])
def update_budget():
    """更新每月總預算"""
    data = request.get_json()
    new_budget = data.get('budget')
    if new_budget is not None:
        settings = Settings.query.first()
        settings.budget = float(new_budget)
        db.session.commit()
        return jsonify({"status": "success", "message": "預算已更新"})
    return jsonify({"status": "error", "message": "無效的預算數值"}), 400

# --- 啟動應用程式 ---

if __name__ == '__main__':
    # host='0.0.0.0' 允許外部網路連線（如 Render 部署需求）
    # port=5000 為 Flask 預設埠號
    app.run(debug=True, host='0.0.0.0', port=5000)