import os
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from services.database import (
    init_db,
    get_transactions,
    add_transaction,
    update_transaction,
    delete_transaction,
    get_categories,
    get_next_transaction_id
)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "personal-finance-secret-key-2026")

# Initialize SQLite database schema and seed default categories & sample data
init_db()

# Indonesian Month Abbreviations
MONTHS_ID = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

# =========================
# JINJA CUSTOM FILTERS
# =========================

@app.template_filter('category_icon')
def category_icon_filter(category):
    cat_lower = str(category).lower()
    if any(k in cat_lower for k in ['jajan', 'snack', 'camilan', 'boba', 'es krim', 'jajanan']):
        return '🧋'
    elif any(k in cat_lower for k in ['makan', 'minum', 'kuliner', 'restoran', 'kopi', 'food', 'makanan']):
        return '🍔'
    elif any(k in cat_lower for k in ['uang kaget', 'kaget', 'hadiah', 'giveaway', 'rezeki', 'doorprize', 'thr', 'temuan']):
        return '🎁'
    elif any(k in cat_lower for k in ['transport', 'bensin', 'ojek', 'grab', 'gojek', 'parkir', 'tol', 'kendaraan']):
        return '🚗'
    elif any(k in cat_lower for k in ['gaji', 'salary', 'income', 'payroll', 'bonus', 'freelance', 'upah']):
        return '💼'
    elif any(k in cat_lower for k in ['belanja', 'shopping', 'groceries', 'pasar', 'supermarket', 'mall']):
        return '🛒'
    elif any(k in cat_lower for k in ['tagihan', 'listrik', 'air', 'internet', 'wifi', 'pulsa', 'token', 'langganan']):
        return '💡'
    elif any(k in cat_lower for k in ['hiburan', 'nonton', 'game', 'liburan', 'travel', 'bioskop', 'rekreasi']):
        return '🎬'
    elif any(k in cat_lower for k in ['kesehatan', 'obat', 'dokter', 'rumahsakit', 'gym', 'fitness', 'sehat']):
        return '🏥'
    elif any(k in cat_lower for k in ['pendidikan', 'buku', 'kursus', 'kuliah', 'sekolah', 'edukasi']):
        return '📚'
    elif any(k in cat_lower for k in ['investasi', 'tabungan', 'saham', 'reksa', 'crypto', 'deposito']):
        return '📈'
    return '💳'


def helper_process_categories(raw_categories):
    processed = []
    has_jajan = False
    has_uang_kaget = False
    for cat in raw_categories:
        c_name = cat.get("Category", "")
        c_type = cat.get("Type", "")
        if c_name == "Makanan":
            c_name = "Makanan & Minuman"
        if c_name.lower() == "jajan":
            has_jajan = True
        if c_name.lower() == "uang kaget":
            has_uang_kaget = True
        processed.append({"Category": c_name, "Type": c_type})
    
    if not has_jajan:
        processed.append({"Category": "Jajan", "Type": "Pengeluaran"})
    if not has_uang_kaget:
        processed.append({"Category": "Uang kaget", "Type": "Pemasukan"})
    
    return processed


def helper_process_transactions(raw_transactions):
    processed = []
    for trx in raw_transactions:
        item = dict(trx)
        if item.get("Category") == "Makanan":
            item["Category"] = "Makanan & Minuman"
        processed.append(item)
    return processed


@app.template_filter('pretty_date')
def pretty_date_filter(date_str):
    if not date_str:
        return ''
    try:
        dt = datetime.strptime(str(date_str).strip(), "%Y-%m-%d")
        today = datetime.now().date()
        if dt.date() == today:
            return "Hari ini"
        elif (today - dt.date()).days == 1:
            return "Kemarin"
        else:
            return f"{dt.day} {MONTHS_ID[dt.month - 1]} {dt.year}"
    except Exception:
        return str(date_str)


# =========================
# DASHBOARD
# =========================

@app.route("/")
def dashboard():

    transactions = helper_process_transactions(get_transactions())

    total_income = sum(
        float(transaction["Amount"])
        for transaction in transactions
        if transaction["Type"] == "Pemasukan"
    )

    total_expense = sum(
        float(transaction["Amount"])
        for transaction in transactions
        if transaction["Type"] == "Pengeluaran"
    )

    balance = total_income - total_expense

    # Calculate Expense Breakdown by Category
    category_expenses = {}
    for t in transactions:
        if t.get("Type") == "Pengeluaran":
            cat = t.get("Category", "Lainnya")
            amt = float(t.get("Amount", 0))
            category_expenses[cat] = category_expenses.get(cat, 0) + amt

    expense_breakdown = []
    if total_expense > 0:
        for cat, amt in sorted(category_expenses.items(), key=lambda x: x[1], reverse=True):
            percentage = round((amt / total_expense) * 100, 1)
            expense_breakdown.append({
                "category": cat,
                "amount": amt,
                "percentage": percentage
            })

    return render_template(
        "dashboard.html",
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        expense_breakdown=expense_breakdown
    )


# =========================
# TRANSACTIONS
# =========================

@app.route("/transactions")
def transactions():

    data = helper_process_transactions(get_transactions())

    total_income = sum(
        float(transaction["Amount"])
        for transaction in data
        if transaction["Type"] == "Pemasukan"
    )

    total_expense = sum(
        float(transaction["Amount"])
        for transaction in data
        if transaction["Type"] == "Pengeluaran"
    )

    balance = total_income - total_expense

    return render_template(
        "transactions.html",
        transactions=data,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance
    )


# =========================
# ADD TRANSACTION
# =========================

@app.route("/transactions/add", methods=["GET", "POST"])
def add_transaction_page():

    categories = helper_process_categories(get_categories())

    if request.method == "POST":

        transaction_id = get_next_transaction_id()

        transaction = {
            "id": transaction_id,
            "date": request.form["date"],
            "type": request.form["type"],
            "category": request.form["category"],
            "amount": request.form["amount"],
            "description": request.form.get("description", "")
        }

        add_transaction(transaction)

        return redirect(url_for("transactions"))

    return render_template(
        "add_transaction.html",
        categories=categories
    )


# =========================
# EDIT TRANSACTION
# =========================

@app.route("/transactions/edit/<transaction_id>", methods=["GET", "POST"])
def edit_transaction(transaction_id):

    transactions = helper_process_transactions(get_transactions())
    categories = helper_process_categories(get_categories())

    # Search transaction by ID
    transaction = next((t for t in transactions if t["ID"] == transaction_id), None)
    if not transaction:
        return redirect(url_for("transactions"))

    if request.method == "POST":

        updated_transaction = {
            "id": transaction_id,
            "date": request.form["date"],
            "type": request.form["type"],
            "category": request.form["category"],
            "amount": request.form["amount"],
            "description": request.form.get("description", "")
        }

        update_transaction(
            transaction_id,
            updated_transaction
        )

        return redirect(url_for("transactions"))

    return render_template(
        "edit_transaction.html",
        transaction=transaction,
        categories=categories
    )


# =========================
# DELETE TRANSACTION
# =========================

@app.route("/transactions/delete/<transaction_id>")
def delete_transaction_page(transaction_id):

    delete_transaction(transaction_id)

    return redirect(url_for("transactions"))


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() in ["true", "1"]
    app.run(host=host, port=port, debug=debug_mode)