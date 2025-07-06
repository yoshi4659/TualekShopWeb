from flask import Flask, render_template, request, redirect, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'tualekshop-secret'

# Setup Google Sheet
SHEET_NAME = 'TualekPhoneDB'
SHEET_TAB = 'Sheet1'

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).worksheet(SHEET_TAB)

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        code = request.form["code"]
        if code in ["0001", "0002", "admin01"]:
            session["user"] = code
            return redirect("/menu")
        else:
            return render_template("login.html", error="รหัสไม่ถูกต้อง")
    return render_template("login.html")

# ---------------- MENU ----------------
@app.route("/menu")
def menu():
    if "user" not in session:
        return redirect("/")
    return render_template("menu.html", user=session["user"])

# ---------------- BUY ----------------
@app.route("/buy", methods=["GET", "POST"])
def buy():
    if "user" not in session:
        return redirect("/")
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
            "", "", "", "", "", "", session["user"]
        ]
        sheet.append_row(data)
        return redirect("/menu")
    return render_template("buy.html")

# ---------------- SELL ----------------
@app.route("/sell", methods=["GET", "POST"])
def sell():
    if "user" not in session:
        return redirect("/")
    found = []
    if request.method == "POST":
        if "search" in request.form:
            imei = request.form["search"]
            records = sheet.get_all_values()
            for i, row in enumerate(records):
                if imei in row[1]:
                    found.append((i + 1, row))  # (row number, data)
            return render_template("sell.html", found=found)
        elif "confirm" in request.form:
            index = int(request.form["index"])
            sheet.update_cell(index, 10, request.form["sell_price"])   # ราคาขาย
            sheet.update_cell(index, 11, request.form["buyer"])        # ผู้ซื้อ
            sheet.update_cell(index, 12, request.form["profit"])       # กำไร
            sheet.update_cell(index, 13, request.form["commission"])   # ค่าคอม
            sheet.update_cell(index, 14, datetime.now().strftime("%Y-%m-%d"))  # วันที่ขาย
            sheet.update_cell(index, 15, request.form["note"])         # หมายเหตุ
            return redirect("/menu")
    return render_template("sell.html", found=found)

# ---------------- DASHBOARD (admin01 only) ----------------
@app.route("/dashboard")
def dashboard():
    if session.get("user") != "admin01":
        return redirect("/")
    records = sheet.get_all_values()
    return render_template("dashboard.html", rows=records)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

if __name__ == "__main__":
    import os
port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port)

