# Expense Tracker Web Application

A secure, full-stack Expense Tracker web application built using Flask and SQLite.  
This application allows users to track daily expenses, analyze spending patterns, and export data.

---

## Features

- User authentication (Register / Login / Logout)
- Secure password hashing using Werkzeug
- Add, view, and delete expenses
- Dashboard with:
  - Total expenses
  - Category-wise spending (Pie Chart)
  - Monthly expense summary
- Filter expenses by category
- Export expenses to CSV
- User-specific data isolation

---

## Tech Stack

- Frontend: HTML, CSS, Jinja2, Chart.js  
- Backend: Python, Flask  
- Database: SQLite  
- Security: Werkzeug password hashing  

---

## Project Structure

expensetracker/
│
├── app.py
├── database.db
├── requirements.txt
├── README.md
│
├── templates/
│ ├── base.html
│ ├── index.html
│ ├── login.html
│ ├── register.html
│ ├── dashboard.html
│ ├── add_expense.html
│ └── expenses.html
│
└── venv/


---

## How to Run the Project

1. Clone the repository
2. Create virtual environment
3. Install dependencies
4. Run the application

```bash
python -m venv venv
venv\Scripts\activate
pip install Flask Werkzeug
python app.py

http://127.0.0.1:5000/

Future Enhancements

Monthly charts using bar graphs

Edit expense feature

Online deployment

Author

Ritik Sharma
BSc IT Student | Python & Flask Developer