from flask import Flask, render_template, request, redirect
from datetime import datetime
app = Flask(__name__)

products = [{"name":"coca cola","cost":1.5,"price":2.5,"qty":19},{"name":"T-shirt","cost":15,"price":25,"qty":10}]
sales = []
last_sale = None
counter = 1

@app.route('/')
def index():
    cur = request.args.get('currency','USD')
    sym = "GH₵" if cur=="GHS" else "$"
    today = sum(s['total'] for s in sales)
    prof = sum(s['profit'] for s in sales)
    return render_template('index.html', products=products, currency=cur, symbol=sym, today_total=today, profit=prof)

@app.route('/add_product', methods=['POST'])
def add():
    cur = request.form.get('currency','USD')
    products.append({"name":request.form['name'],"cost":float(request.form['cost']),"price":float(request.form['price']),"qty":int(request.form['qty'])})
    return redirect(f"/?currency={cur}")

@app.route('/sell', methods=['POST'])
def sell():
    global last_sale, counter
    cur = request.form.get('currency','USD')
    name = request.form.get('product')
    qty = int(request.form.get('qty',1))
    for p in products:
        if p['name']==name and p['qty']>=qty:
            p['qty']-=qty
            total = p['price']*qty
            profit = (p['price']-p['cost'])*qty
            last_sale={"id":counter,"product":name,"qty":qty,"total":total,"profit":profit,"price":p['price']}
            sales.append(last_sale)
            counter+=1
            break
    return redirect(f"/?currency={cur}&sold={last_sale['id'] if last_sale else 1}")

@app.route('/receipt/<int:rid>')
def receipt(rid):
    cur = request.args.get('currency','USD')
    sym = "GH₵" if cur=="GHS" else "$"
    s = next((x for x in sales if x['id']==rid), last_sale)
    return f"<div style='text-align:center;padding:20px;font-family:Arial'><h2>Receipt #{rid}</h2><p>{s['product']} x {s['qty']} = {sym}{s['total']}</p><p>Profit: {sym}{s['profit']}</p><a href='/?currency={cur}'>Back</a></div>" if s else "No sale"
