from flask import Flask, render_template, request, redirect
from datetime import datetime
import json, os

app = Flask(__name__)
DATA_FILE = "/tmp/data.json"
products, sales, debts, last_sale = [], [], [], None
receipt_counter = 1

def load():
    global products, sales, receipt_counter, last_sale
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE,'r') as f:
                d=json.load(f)
                products=d.get('products',[]); sales=d.get('sales',[]); last_sale=d.get('last_sale'); receipt_counter=d.get('counter',1)
        except: pass

def save():
    try:
        with open(DATA_FILE,'w') as f:
            json.dump({'products':products,'sales':sales,'last_sale':last_sale,'counter':receipt_counter}, f)
    except: pass

load()

@app.route('/')
def index():
    currency = request.args.get('currency','USD')
    symbol = "GH₵" if currency=="GHS" else "$"
    today_total = sum(s['total'] for s in sales)
    profit = sum(s['profit'] for s in sales)
    return render_template('index.html', products=products, currency=currency, symbol=symbol, today_total=today_total, profit=profit, last_sale=last_sale)

@app.route('/add_product', methods=['POST'])
def add_product():
    cur = request.form.get('currency','USD')
    products.append({
        "name": request.form['name'],
        "cost": float(request.form['cost']),
        "price": float(request.form['price']),
        "qty": int(request.form['qty'])
    })
    save()
    return redirect(f"/?currency={cur}")

@app.route('/sell', methods=['POST'])
def sell():
    global last_sale, receipt_counter
    cur = request.form.get('currency','USD')
    name = request.form.get('product')
    qty = int(request.form.get('qty',1))
    for p in products:
        if p['name']==name and p['qty']>=qty:
            p['qty']-=qty
            total = p['price']*qty
            prof = (p['price']-p['cost'])*qty
            sale = {"product":name,"qty":qty,"price":p['price'],"total":total,"profit":prof,"id":receipt_counter}
            sales.append(sale)
            last_sale = sale
            receipt_counter+=1
            break
    save()
    return redirect(f"/?currency={cur}&sold={last_sale['id'] if last_sale else 1}")

@app.route('/receipt/<int:rid>')
def receipt(rid):
    cur = request.args.get('currency','USD')
    symbol = "GH₵" if cur=="GHS" else "$"
    date = datetime.now().strftime("%d/%m/%Y %H:%M")
    sale = next((s for s in sales if s['id']==rid), last_sale)
    return render_template('receipt.html', sale=sale, date=date, symbol=symbol, currency=cur)

@app.route('/receipt')
def receipt_latest():
    cur = request.args.get('currency','USD')
    return redirect(f"/receipt/{last_sale['id']}?currency={cur}" if last_sale else f"/?currency={cur}")
