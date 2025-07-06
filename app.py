from flask import Flask, render_template, request, redirect, session, url_for
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
app.secret_key = "tualekshop_secret"

# เชื่อม Google Sheet
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)
sheet = client.open("TualekPhoneDB").worksheet("Sheet1")

# ---------------- Login ----------------
users = {
    "0001": "branch1",
    "0003": "branch2",
    "admin01": "admin"
}

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        if user in users:
            session["user"] = user
            session["role"] = users[user]
            return redirect("/menu")
        else:
            return "รหัสไม่ถูกต้อง"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- Menu ----------------
@app.route("/menu")
def menu():
    if "user" not in session:
        return redirect("/")
    return render_template("menu.html", role=session["role"])

# ---------------- ซื้อเข้า ----------------
@app.route("/buy", methods=["GET", "POST"])
def buy():
    if "user" not in session:
        return redirect("/")
    
    # ดึงรายการที่เคยซื้อเข้าแล้วมาแสดงใน dropdown
    records = sheet.get_all_records()
    brands = list(set([r["ยี่ห้อ"] for r in records if r["ยี่ห้อ"]]))
    models = list(set([r["รุ่น"] for r in records if r["รุ่น"]]))
    storages = list(set([r["ความจุ"] for r in records if r["ความจุ"]]))

    if request.method == "POST":
        data = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            request.form["imei"],
            request.form["brand"],
            request.form["model"],
            request.form["storage"],
            request.form["condition"],
            request.form["defect"],
            request.form["buy_price"],
            request.form["seller"],
            "", "", "", "", "", "", session["user"]  # ช่องว่างสำหรับข้อมูลขาย
        ]
        sheet.append_row(data)
        return redirect("/menu")

    return render_template("buy.html", brands=brands, models=models, storages=storages)

# ---------------- ขายออก ----------------
@app.route("/sell", methods=["GET", "POST"])
def sell():
    if "user" not in session:
        return redirect("/")

    records = sheet.get_all_records()
    imeis = [r["IMEI"] for r in records if r["ราคาขาย"] == ""]
    buyers = list(set([r["ผู้ซื้อ"] for r in records if r["ผู้ซื้อ"]]))

    if request.method == "POST":
        search_imei = request.form["imei"]
        found = None
        for i, r in enumerate(records):
            if search_imei in r["IMEI"] and r["ราคาขาย"] == "":
                found = (i + 2)  # บรรทัดจริงใน Google Sheet
                break
        if found:
            sheet.update_cell(found, 10, request.form["sell_price"])  # ราคาขาย
            sheet.update_cell(found, 11, request.form["buyer"])      # ผู้ซื้อ
            sheet.update_cell(found, 12, request.form["profit"])     # กำไร
            sheet.update_cell(found, 13, request.form["commission"]) # ค่าคอม
            sheet.update_cell(found, 14, request.form["sell_date"])  # วันที่ขาย
            sheet.update_cell(found, 15, request.form["note"])       # หมายเหตุ
            sheet.update_cell(found, 16, session["user"])            # ผู้บันทึก (สาขา)
            return redirect("/menu")

    return render_template("sell.html", imeis=imeis, buyers=buyers)

# ---------------- Dashboard ----------------
@app.route("/dashboard")
def dashboard():
    if session.get("role") != "admin":
        return "เฉพาะเจ้าของร้านเท่านั้น"

    records = sheet.get_all_records()
    branch = request.args.get("branch")
    date = request.args.get("date")  # optional filter

    if branch:
        records = [r for r in records if r["ผู้บันทึก"] == branch]
    if date:
        records = [r for r in records if r["วันที่ขาย"] == date]

    total_sell = sum([float(r["ราคาขาย"]) if r["ราคาขาย"] else 0 for r in records])
    total_profit = sum([float(r["กำไร"]) if r["กำไร"] else 0 for r in records])

    return render_template("dashboard.html", records=records, total_sell=total_sell, total_profit=total_profit)

if __name__ == "__main__":
    app.run(debug=True)
