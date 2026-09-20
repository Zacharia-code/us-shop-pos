from flask import Flask, render_template, request, redirect
import json, os

app = Flask(__name__)
DATA_FILE = 'data.json'

# Load data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE) as f:
        data = json.load(f)
        products = data.get('products', [{"name":"coca cola","barcode":"123","cost":1,"price":2.5,"qty":18}])
        debts = data.get('debts', [])
        sales = data.get('sales', [{"price":2.5,"cost":1,"qty":1}])
else:
    products = [{"name":"coca cola","barcode":"123","cost":1,"price":2.5,"qty":18}]
    debts = []
    sales = [{"price":2.5,"cost":1,"qty":1}]

def save():
    with open(DATA_FILE, 'w') as f:
        json.dump({"products":products,"debts":debts,"sales":sales}, f)

@app.route('/')
def index():
    currency = request.args.get('currency', 'GHS')
    symbol = "GH₵" if currency == 'GHS' else "$"
    today_total = sum(s['price']*s['qty'] for s in sales)
    profit = sum((s['price']-s['cost'])*s['qty'] for s in sales)
    return render_template('index.html', products=products, debts=debts, today_total=today_total, profit=profit, currency=currency, symbol=symbol)

@app.route('/add_product', methods=['POST'])
def add_product():
    products.append({"name":request.form['name'],"barcode":request.form.get('barcode',''),"cost":float(request.form['cost']),"price":float(request.form['price']),"qty":int(request.form['qty'])})
    save()
    return redirect("/?currency=GHS")

@app.route('/sell', methods=['POST'])
def sell():
    name = request.form['product']
    qty = int(request.form['qty'])
    for p in products:
        if p['name']==name and p['qty']>=qty:
            p['qty']-=qty
            sales.append({"price":p['price'],"cost":p['cost'],"qty":qty})
    save()
    return redirect("/?currency=GHS")

@app.route('/add_debt', methods=['POST'])
def add_debt():
    debts.append({"customer":request.form['customer'],"amount":float(request.form['amount'])})
    save()
    return redirect("/?currency=GHS")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
