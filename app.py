from flask import Flask, render_template, request, redirect
from datetime import datetime
import json, os

app = Flask(__name__)

DATA_FILE = "/tmp/data.json"
products = []
sales = []
debts = []
last_sale = None

def load():
    global products, sales, debts, last_sale
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE,'r') as f:
                d = json.load(f)
                products = d.get('products',[])
                sales = d.get('sales',[])
                debts = d.get('debts',[])
                last_sale = d.get('last_sale')
        except:
            pass

def save():
    try:
        with open(DATA_FILE,'w') as f:
            json.dump({'products':products,'sales':sales,'debts':debts,'last_sale':last_sale}, f)
    except:
        pass

load()

@app.route('/')
def index():
    currency = request.args.get('currency','GHS')
    symbol = "GH₵" if currency == "GHS" else "$"
    today_total = sum(s['price']*s['qty'] for s in sales)
    profit = sum((s['price']-s['cost'])*s['qty'] for s in sales)
    return render_template('index.html', products=products, sales=sales, currency=currency, symbol=symbol, today_total=today_total, profit=profit)

@app.route('/add_product', methods=['POST'])
def add_product():
    global products
    try:
        currency = request.form.get('currency','GHS')
        products.append({
            "name": request.form['name'],
            "barcode": request.form.get('barcode',''),
            "cost": float(request.form['cost']),
            "price": float(request.form['price']),
            "qty": int(request.form['qty'])
        })
        save()
        return redirect(f"/?currency={currency}")
    except:
        pass
    return redirect("/?currency=GHS")

@app.route('/sell', methods=['POST'])
def sell():
    global last_sale
    currency = request.form.get('currency','GHS')
    try:
        name = request.form.get('product') or request.form.get('product_id')
        qty = int(request.form['qty'])
        for p in products:
            if p['name'] == name and p['qty'] >= qty:
                p['qty'] -= qty
                total = p['price'] * qty
                sales.append({"price": p['price'], "cost": p['cost'], "qty": qty})
                last_sale = {"product": name, "qty": qty, "price": p['price'], "total": total}
                break
        save()
    except Exception as e:
        print(e)
    return redirect(f"/?currency={currency}&sold=1")

@app.route('/receipt')
def receipt():
    currency = request.args.get('currency','GHS')
    symbol = "GH₵" if currency == "GHS" else "$"
    date = datetime.now().strftime("%d/%m/%Y %H:%M")
    return render_template('receipt.html', sale=last_sale, date=date, currency=currency, symbol=symbol)

@app.route('/add_debt', methods=['POST'])
def add_debt():
    currency = request.form.get('currency','GHS')
    try:
        debts.append({"customer": request.form['customer'], "amount": float(request.form['amount'])})
        save()
    except:
        pass
    return redirect(f"/?currency={currency}")

if __name__ == '__main__':
    app.run()
