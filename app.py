import os
from flask import Flask, render_template, request, redirect, session, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
from datetime import datetime
import csv
import io

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "europe-pos-final-kofi-2026-secure-49eur")

def get_db():
    conn = sqlite3.connect('pos.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT,
        password TEXT NOT NULL,
        vat_number TEXT,
        created_at TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL,
        cost REAL DEFAULT 0,
        vat_rate REAL DEFAULT 20
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER,
        product_name TEXT,
        qty INTEGER,
        total REAL NOT NULL,
        profit REAL NOT NULL,
        vat_amount REAL DEFAULT 0,
        payment_method TEXT DEFAULT 'Card',
        date TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

init_db()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        vat = request.form.get('vat','').strip()
        pwd = generate_password_hash(request.form['password'])
        try:
            conn = get_db()
            conn.execute("INSERT INTO users (username,email,password,vat_number,created_at) VALUES (?,?,?,?,?)",
                         (username, email, pwd, vat, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except Exception as e:
            return f"Shop name taken or error: {e}"
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        pwd_input = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], pwd_input):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            return redirect(url_for('dashboard'))
        return "Wrong login"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    products = conn.execute("SELECT * FROM products WHERE user_id=?", (session['user_id'],)).fetchall()
    sales = conn.execute("SELECT * FROM sales WHERE user_id=? ORDER BY date DESC", (session['user_id'],)).fetchall()
    
    total_sales = sum(s['total'] for s in sales) if sales else 0
    total_profit = sum(s['profit'] for s in sales) if sales else 0
    total_vat = sum(s['vat_amount'] for s in sales) if sales else 0
    cash_total = sum(s['total'] for s in sales if s['payment_method']=='Cash') if sales else 0
    card_total = sum(s['total'] for s in sales if s['payment_method']=='Card') if sales else 0

    conn.close()
    low_stock = [p for p in products if p['stock'] <= 5]
    return render_template('dashboard.html', products=products, sales=sales, total_sales=total_sales, total_profit=total_profit, total_vat=total_vat, cash_total=cash_total, card_total=card_total, low_stock=low_stock, shop_name=session['username'])

@app.route('/add', methods=['POST'])
@login_required
def add_product():
    name = request.form['name']
    price = float(request.form['price'])
    stock = int(request.form['stock'])
    cost = float(request.form.get('cost',0))
    vat_rate = float(request.form.get('vat_rate',20))
    conn = get_db()
    conn.execute("INSERT INTO products (user_id,name,price,stock,cost,vat_rate) VALUES (?,?,?,?,?,?)",
                 (session['user_id'], name, price, stock, cost, vat_rate))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/sell/<int:pid>', methods=['POST'])
@login_required
def sell(pid):
    qty = int(request.form.get('qty',1))
    payment_method = request.form.get('payment_method','Card')
    conn = get_db()
    p = conn.execute("SELECT * FROM products WHERE id=? AND user_id=?", (pid, session['user_id'])).fetchone()
    if p and p['stock'] >= qty:
        new_stock = p['stock'] - qty
        profit = (p['price'] - p['cost']) * qty
        # VAT calculation for Europe
        vat_amount = (p['price'] * p['vat_rate']/100) * qty
        total = p['price'] * qty
        conn.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, pid))
        conn.execute("INSERT INTO sales (user_id,product_id,product_name,qty,total,profit,vat_amount,payment_method,date) VALUES (?,?,?,?,?,?,?,?,?)",
                     (session['user_id'], pid, p['name'], qty, total, profit, vat_amount, payment_method, datetime.now().isoformat()))
        conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/export')
@login_required
def export_csv():
    # Europe shops need CSV for accountant - killer feature
    conn = get_db()
    sales = conn.execute("SELECT * FROM sales WHERE user_id=?", (session['user_id'],)).fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date','Product','Qty','Total','VAT','Profit','Payment'])
    for s in sales:
        writer.writerow([s['date'], s['product_name'], s['qty'], s['total'], s['vat_amount'], s['profit'], s['payment_method']])
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name=f'sales_{session["username"]}.csv')

if __name__ == '__main__':
    app.run(debug=True)