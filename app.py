from flask import Flask, render_template, request, redirect
import os, json
from datetime import datetime
app = Flask(__name__)
DATA="data.json"
def load():
    if not os.path.exists(DATA): return {"products":[],"sales":[],"debts":[]}
    try: return json.load(open(DATA))
    except: return {"products":[],"sales":[],"debts":[]}
def save(d): json.dump(d, open(DATA,"w"), indent=2)
@app.route("/")
def home():
    d=load()
    profit=sum(s['profit'] for s in d['sales'])
    today=datetime.now().strftime("%Y-%m-%d")
    today_sales=sum(s['total'] for s in d['sales'] if s['date'].startswith(today))
    return render_template("index.html", products=d['products'], sales=d['sales'], debts=d['debts'], currency="$", profit=profit, today_sales=today_sales)
@app.route("/add_product", methods=["POST"])  
def add_p():
    d=load()
    d['products'].append({"name":request.form['name'],"cost":float(request.form['cost']),"price":float(request.form['price']),"qty":int(request.form['qty']),"barcode":request.form.get('barcode','')})
    save(d); return redirect("/")
@app.route("/sell", methods=["POST"])
def sell():
    d=load(); name=request.form['product']; qty=int(request.form['qty'])
    for p in d['products']:
        if p['name']==name and p['qty']>=qty:
            p['qty']-=qty; d['sales'].append({"product":name,"qty":qty,"total":p['price']*qty,"profit":(p['price']-p['cost'])*qty,"date":datetime.now().isoformat()})
    save(d); return redirect("/")
@app.route("/add_debt", methods=["POST"])
def add_d():
    d=load(); d['debts'].append({"customer":request.form['customer'],"amount":float(request.form['amount']),"date":datetime.now().isoformat()}); save(d); return redirect("/")
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))