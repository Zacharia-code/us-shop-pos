from flask import Flask, render_template, request, redirect
from datetime import datetime
import json, os

app = Flask(__name__)
DATA_FILE = "data.json"

# Load
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
            products = data.get('products', [])
            sales = data.get('sales', [])
            counter = data.get('counter', 1)
            # Fix old sales without date
            for s in sales:
                if 'date' not in s:
                    s['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    s['date_short'] = datetime.now().strftime("%Y-%m-%d")
    except:
        products = [{"name":"coca cola","cost":1.5,"price":2.5,"qty":19},{"name":"T-shirt","cost":15,"price":25,"qty":10}]
        sales = []; counter = 1
else:
    products = [{"name":"coca cola","cost":1.5,"price":2.5,"qty":19},{"name":"T-shirt","cost":15,"price":25,"qty":10}]
    sales = []; counter = 1

def save():
    with open(DATA_FILE,'w') as f:
        json.dump({"products":products,"sales":sales,"counter":counter}, f)

@app.route('/')
def index():
    cur = request.args.get('currency','USD')
    sym = "GH₵" if cur=="GHS" else "$"
    today_str = datetime.now().strftime("%Y-%m-%d")
    todays_sales = [s for s in sales if today_str in s.get('date','')]
    today_total = sum(s.get('total',0) for s in todays_sales)
    profit = sum(s.get('profit',0) for s in todays_sales)
    all_time = sum(s.get('total',0) for s in sales)
    return render_template('index.html', products=products, currency=cur, symbol=sym, today_total=today_total, profit=profit, all_time=all_time, sales=sales)

@app.route('/add_product', methods=['POST'])
def add():
    global products
    cur = request.form.get('currency','USD')
    products.append({"name":request.form['name'],"cost":float(request.form['cost']),"price":float(request.form['price']),"qty":int(request.form['qty'])})
    save()
    return redirect(f"/?currency={cur}")

@app.route('/sell', methods=['POST'])
def sell():
    global counter
    cur = request.form.get('currency','USD')
    name = request.form.get('product')
    qty = int(request.form.get('qty',1))
    now = datetime.now()
    for p in products:
        if p['name']==name and p['qty']>=qty:
            p['qty']-=qty
            total = p['price']*qty
            prof = (p['price']-p['cost'])*qty
            sale = {"id":counter,"product":name,"qty":qty,"price":p['price'],"total":total,"profit":prof,"date":now.strftime("%Y-%m-%d %H:%M:%S"),"date_short":now.strftime("%Y-%m-%d")}
            sales.append(sale)
            counter+=1
            save()
            return redirect(f"/receipt/{sale['id']}?currency={cur}")
    return redirect(f"/?currency={cur}")

@app.route('/receipt/<int:rid>')
def receipt(rid):
    cur = request.args.get('currency','USD')
    sym = "GH₵" if cur=="GHS" else "$"
    s = next((x for x in sales if x.get('id')==rid), None)
    if not s:
        return f"<h1>Receipt #{rid} not found</h1><p>Sales: {sales}</p><a href='/?currency={cur}'>Back</a>"
    return render_template('receipt.html', sale=s, symbol=sym, currency=cur, shop_name="My Shop POS", date=s.get('date',''))

@app.route('/reset_today')
def reset_today():
    global sales
    cur = request.args.get('currency','USD')
    today_str = datetime.now().strftime("%Y-%m-%d")
    sales = [s for s in sales if today_str not in s.get('date','')]
    save()
    return redirect(f"/?currency={cur}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
