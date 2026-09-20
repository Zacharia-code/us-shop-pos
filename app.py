from flask import Flask, render_template, request, redirect
import json, os

app = Flask(__name__)

# SAFE defaults - never crashes
products = [{"name":"coca cola","barcode":"123","cost":1,"price":2.5,"qty":18}]
debts = []
sales = [{"price":2.5,"cost":1,"qty":1}]

# Try load data.json but don't crash if bad
try:
    if os.path.exists('data.json'):
        with open('data.json') as f:
            data = json.load(f)
            if isinstance(data, dict):
                products = data.get('products', products)
                debts = data.get('debts', debts)
                sales = data.get('sales', sales)
except:
    pass

def save():
    try:
        with open('data.json', 'w') as f:
            json.dump({"products":products,"debts":debts,"sales":sales}, f)
    except:
        pass

@app.route('/')
def index():
    try:
        currency = request.args.get('currency', 'GHS')
        symbol = "GH₵" if currency == 'GHS' else "$"
        today_total = 0
        profit = 0
        for s in sales:
            try:
                p = float(s.get('price',0))
                c = float(s.get('cost',0))
                q = int(s.get('qty',0))
                today_total += p * q
                profit += (p-c)*q
            except:
                pass
        return render_template('index.html', products=products, debts=debts, today_total=today_total, profit=profit, currency=currency, symbol=symbol)
    except Exception as e:
        return f"Fixing... {e} - Please reload", 500

@app.route('/add_product', methods=['POST'])
def add_product():
    try:
        products.append({"name":request.form['name'],"barcode":request.form.get('barcode',''),"cost":float(request.form['cost']),"price":float(request.form['price']),"qty":int(request.form['qty'])})
        save()
    except: pass
    return redirect("/?currency=GHS")

@app.route('/sell', methods=['POST'])
def sell():
    try:
        name = request.form['product']
        qty = int(request.form['qty'])
        for p in products:
            if p['name']==name and p['qty']>=qty:
                p['qty']-=qty
                sales.append({"price":p['price'],"cost":p['cost'],"qty":qty})
        save()
    except: pass
    return redirect("/?currency=GHS")

@app.route('/add_debt', methods=['POST'])
def add_debt():
    try:
        debts.append({"customer":request.form['customer'],"amount":float(request.form['amount'])})
        save()
    except: pass
    return redirect("/?currency=GHS")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
