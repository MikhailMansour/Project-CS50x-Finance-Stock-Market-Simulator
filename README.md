# 💰 CS50 Finance - 🏛️ Harvard #

A Flask-based stock trading web application that allows users to quote, buy, sell, and manage stocks using a virtual portfolio. 📈

## ✨ Features

- 🔐 Authentication — Register, Login & Logout
- 💵 Virtual Cash — $10,000 starting balance
- 🔎 Stock Quotes — Real-time stock lookup
- 📊 Portfolio — Track stocks, shares & balance
- 🛒 Buy — Purchase stocks
- 💸 Sell — Sell owned stocks
- 📜 History — Track transactions
- 🗄️ SQLite — Persistent data storage
- 🔒 Password Hashing — Secure credentials
- ✅ Validation — Input & transaction validation

## 🛠️ Technologies

- 🐍 Python
- 🌐 Flask
- 🗄️ SQLite
- 🧩 CS50 SQL
- 🎨 HTML / CSS / Bootstrap
- 📝 Jinja2
- 🔐 Werkzeug Security
- 📈 Stock Lookup API

- ## 📂 Project Structure

```text
finance/
├── app.py
├── helpers.py
├── finance.db
├── requirements.txt
├── static/
│   └── styles.css
└── templates/
    ├── apology.html
    ├── buy.html
    ├── history.html
    ├── index.html
    ├── layout.html
    ├── login.html
    ├── quote.html
    ├── quoted.html
    ├── register.html
    └── sell.html

