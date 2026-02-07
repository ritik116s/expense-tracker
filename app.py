from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import send_file
import csv
import io


import sqlite3

app = Flask(__name__)
app.secret_key = "mysecretkey"   # later we will make it secure

DATABASE = "database.db"


# ---------- DB INIT ----------
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # EXPENSES TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()



# ---------- ROUTES ----------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # convert normal password into hashed password
        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )
            conn.commit()
            conn.close()

            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Username already exists! Try another.", "danger")

    return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            user_id = user[0]
            db_username = user[1]
            db_password_hash = user[2]

            # check password with hash
            if check_password_hash(db_password_hash, password):
                session["user_id"] = user_id
                session["username"] = db_username

                flash("Login successful!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid password!", "danger")
        else:
            flash("User not found!", "danger")

    return render_template("login.html")



@app.route("/dashboard", methods=["GET"])
def dashboard():
    selected_category = request.args.get("category")

    if "user_id" not in session:
        flash("Please login first!", "danger")
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Total spent
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id=?
    """, (session["user_id"],))
    total_spent = cursor.fetchone()[0]

    # Total number of expenses
    cursor.execute("""
        SELECT COUNT(*)
        FROM expenses
        WHERE user_id=?
    """, (session["user_id"],))
    total_entries = cursor.fetchone()[0]

    # Category wise total
    cursor.execute("""
        SELECT category, COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id=?
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """, (session["user_id"],))
    category_data = cursor.fetchall()

    # Monthly summary
    cursor.execute("""
        SELECT substr(date, 1, 7) AS month, SUM(amount)
        FROM expenses
        WHERE user_id=?
        GROUP BY month
        ORDER BY month DESC
    """, (session["user_id"],))
    monthly_data = cursor.fetchall()

    # Latest 5 expenses (with filter)
    if selected_category:
        cursor.execute("""
            SELECT date, amount, category, note
            FROM expenses
            WHERE user_id=? AND category=?
            ORDER BY id DESC
            LIMIT 5
        """, (session["user_id"], selected_category))
    else:
        cursor.execute("""
            SELECT date, amount, category, note
            FROM expenses
            WHERE user_id=?
            ORDER BY id DESC
            LIMIT 5
        """, (session["user_id"],))

    latest_expenses = cursor.fetchall()
    conn.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        total_spent=total_spent,
        total_entries=total_entries,
        category_data=category_data,
        monthly_data=monthly_data,
        latest_expenses=latest_expenses,
        selected_category=selected_category
    )




@app.route("/add-expense", methods=["GET", "POST"])
def add_expense():
    if "user_id" not in session:
        flash("Please login first!", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        amount = request.form["amount"]
        category = request.form["category"]
        note = request.form["note"]

        date = datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO expenses (user_id, date, amount, category, note)
            VALUES (?, ?, ?, ?, ?)
        """, (session["user_id"], date, amount, category, note))
        conn.commit()
        conn.close()

        flash("Expense added successfully!", "success")
        return redirect(url_for("expenses"))

    return render_template("add_expense.html")


@app.route("/expenses")
def expenses():
    if "user_id" not in session:
        flash("Please login first!", "danger")
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, date, amount, category, note
        FROM expenses
        WHERE user_id=?
        ORDER BY id DESC
    """, (session["user_id"],))
    all_expenses = cursor.fetchall()
    conn.close()

    return render_template("expenses.html", expenses=all_expenses)


@app.route("/delete-expense/<int:expense_id>")
def delete_expense(expense_id):
    if "user_id" not in session:
        flash("Please login first!", "danger")
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id=? AND user_id=?", (expense_id, session["user_id"]))
    conn.commit()
    conn.close()

    flash("Expense deleted successfully!", "success")
    return redirect(url_for("expenses"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("home"))

@app.route('/export')
def export_csv():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, amount, category, note
        FROM expenses
        WHERE user_id = ?
    """, (session['user_id'],))

    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['Date', 'Amount', 'Category', 'Note'])
    writer.writerows(rows)

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='expenses.csv'
    )




if __name__ == "__main__":
    init_db()
    app.run(debug=True)
