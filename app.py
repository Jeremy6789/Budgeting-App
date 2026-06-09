import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'moneymaster_secure_key' # 務必設定金鑰

# --- 資料庫設定 ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 資料模型 ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    transactions = db.relationship('Transaction', backref='owner', lazy=True)
    settings = db.relationship('Settings', backref='owner', lazy=True, uselist=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    icon = db.Column(db.String(50))
    is_need = db.Column(db.Boolean, default=True)
    date = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    budget = db.Column(db.Float, default=10000.0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

with app.app_context():
    db.create_all()

# --- 路由 ---
@app.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    return render_template('index.html')

@app.route('/history')
def history():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    return render_template('history.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

# --- 認證 API ---
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()
    if user and check_password_hash(user.password, data.get('password')):
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "帳號或密碼錯誤"}), 401

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    if User.query.filter_by(username=username).first():
        return jsonify({"status": "error", "message": "帳號已存在"}), 400
    
    new_user = User(username=username, password=generate_password_hash(data.get('password')))
    db.session.add(new_user)
    db.session.commit()
    # 建立該用戶的初始預算
    db.session.add(Settings(budget=10000.0, user_id=new_user.id))
    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/api/auth/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# --- 資料 API ---
@app.route('/api/data')
def get_data():
    u_id = session.get('user_id')
    if not u_id: return jsonify({"status": "error"}), 401
    
    # 確保每個用戶都有 Settings，沒有就補一個 (防呆)
    set_obj = Settings.query.filter_by(user_id=u_id).first()
    if not set_obj:
        set_obj = Settings(budget=10000.0, user_id=u_id)
        db.session.add(set_obj)
        db.session.commit()

    transactions = Transaction.query.filter_by(user_id=u_id).order_by(Transaction.date.desc()).all()
    return jsonify({
        "budget": set_obj.budget,
        "transactions": [{"id":t.id,"title":t.title,"amount":t.amount,"category":t.category,"icon":t.icon,"isNeed":t.is_need,"date":t.date} for t in transactions]
    })

@app.route('/api/transaction', methods=['POST'])
def add_transaction():
    u_id = session.get('user_id')
    if not u_id: return jsonify({"status": "error"}), 401
    data = request.json
    new_tx = Transaction(
        title=data['title'], amount=data['amount'], category=data['category'],
        icon=data['icon'], is_need=data['isNeed'], date=data['date'], user_id=u_id
    )
    db.session.add(new_tx)
    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/api/transaction/<int:tx_id>', methods=['DELETE', 'PUT'])
def handle_tx(tx_id):
    u_id = session.get('user_id')
    tx = Transaction.query.filter_by(id=tx_id, user_id=u_id).first_or_404()
    if request.method == 'DELETE':
        db.session.delete(tx)
    else:
        data = request.json
        tx.title, tx.amount, tx.date = data['title'], data['amount'], data['date']
        tx.category, tx.icon, tx.is_need = data['category'], data['icon'], data['isNeed']
    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/api/budget', methods=['POST'])
def update_budget():
    u_id = session.get('user_id')
    if not u_id: return jsonify({"status": "error"}), 401
    set_obj = Settings.query.filter_by(user_id=u_id).first()
    set_obj.budget = float(request.json.get('budget'))
    db.session.commit()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)