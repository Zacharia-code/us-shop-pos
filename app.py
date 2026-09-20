from flask import Flask, render_template, request, redirect
import json, os
from datetime import datetime

app = Flask(__name__)

products = [{"name":"coca cola","barcode":"123","cost":1,"price":2.5,"qty":18}]
debts = []
sales = []
last_sale = {"product":"coca cola","qty":1,"price":2.5,"total":2.5}

try:
    if os.path.exists('data.json'):
        with open('data.json') as f:
            data = json.load(f)
            if isinstance(data, dict):
                products = data.get('products', products)
                debts = data.get('debts', debts)
                sales = data.get('sales', sales)
                last_sale = data.get('last_sale', last_sale)
except:
    pass

def save():
    try:
        with open('data.json', 'w') as f:
            json.dump({"products":products,"debts":debts,"sales":sales,"last_sale":last_sale}, f)
    except:
        pass

@app.route('/')
def index():
    try:
        currency = request.args.get('currency', 'GHS')
        symbol = "GH₵" if currency == 'GHS' else "$"
        today_total = sum(float(s.get('price',0))*int(s.get('qty',0)) for s in sales)
        profit = sum((float(s.get('price',0))-float(s.get('cost',0)))*int(s.get('qty',0)) for s in sales)
        return render_template('index.html', products=products, debts=debts, today_total=today_total, profit=profit, currency=currency, symbol=symbol)
    except Exception as e:
        return f"Reload... {e}", 500

@app.route('/add_product', methods=['POST'])
def add_product():
    try:
        products.append({"name":request.form['name'],"barcode":request.form.get('barcode',''),"cost":float(request.form['cost']),"price":float(request.form['price']),"qty":int(request.form['qty'])})
        save()
    except: pass
    return redirect("/?currency=GHS")

@app.route('/sell', methods=['POST'])
def sell():
    global last_sale
    try:
        name = request.form['product']
        qty = int(request.form['qty'])
        for p in products:
            if p['name']==name and p['qty']>=qty:
                p['qty']-=qty
                total = p['price']*qty
                sales.append({"price":p['price'],"cost":p['cost'],"qty":qty})
                last_sale = {"product":name,"qty":qty,"price":p['price'],"total":total}
        save()
    except: pass
    return redirect('/receipt')

@app.route('/receipt')
def receipt():
    date = datetime.now().strftime("%d/%m/%Y %H:%M")
    return render_template('receipt.html', sale=last_sale, date=date)

@app.route('/add_debt', methods=['POST'])
def add_debt():
    try:
        debts.append({"customer":request.form['customer'],"amount":float(request.form['amount'])})
        save()
    except: pass
    return redirect("/?currency=GHS")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
