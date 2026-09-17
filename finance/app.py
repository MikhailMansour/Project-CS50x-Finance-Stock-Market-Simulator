import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash


from helpers import apology, login_required, lookup, usd

# Configure application

app = Flask(__name__)

app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response



@app.route("/")
@login_required
def index():
    """Show portfolio of stocks."""

    user_id = session["user_id"]

    # Get user's cash safely
    rows = db.execute(
        "SELECT cash FROM users WHERE id = ?",
        user_id
    )

    if len(rows) != 1:
        return apology("user not found", 403)

    cash = rows[0]["cash"]

    # Get all transactions for this user
    transactions = db.execute(
        """
        SELECT symbol, SUM(shares) AS total_shares
        FROM transactions
        WHERE user_id = ?
        GROUP BY symbol
        """,
        user_id
    )

    portfolio = []
    total = cash

    # Calculate current value of owned stocks
    for transaction in transactions:

        shares = transaction["total_shares"]

        # Ignore stocks with zero or negative shares
        if shares <= 0:
            continue

        symbol = transaction["symbol"]

        stock = lookup(symbol)

        if stock is None:
            continue

        price = stock["price"]
        stock_total = price * shares

        portfolio.append(
            {
                "symbol": symbol,
                "name": stock["name"],
                "shares": shares,
                "price": price,
                "total": stock_total,
            }
        )

        total += stock_total

    return render_template(
        "index.html",
        stocks=portfolio,
        cash=cash,
        total=total
    )
@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        symbol = request.form.get("symbol")

        if not symbol:
            return apology("must provide symbol", 400)

        stock = lookup(symbol)

        if stock is None:
            return apology("invalid symbol", 400)

        return render_template("quoted.html", stock=stock)

    return render_template("quote.html")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""

    if request.method == "POST":

        symbol = request.form.get("symbol")
        shares_input = request.form.get("shares")

        # Ensure symbol was submitted
        if not symbol:
            return apology("must provide symbol", 400)

        # Ensure shares was submitted
        if not shares_input:
            return apology("must provide shares", 400)

        # Validate number of shares
        try:
            shares = int(shares_input)
        except (ValueError, TypeError):
            return apology("shares must be a positive integer", 400)

        if shares <= 0:
            return apology("shares must be a positive integer", 400)

        # Look up stock
        symbol = symbol.upper()
        stock = lookup(symbol)

        if stock is None:
            return apology("invalid symbol", 400)

        price = stock["price"]
        total_cost = price * shares

        # Get user's current cash
        rows = db.execute(
            "SELECT cash FROM users WHERE id = ?",
            session["user_id"]
        )

        cash = rows[0]["cash"]

        # Ensure user can afford purchase
        if total_cost > cash:
            return apology("can't afford", 400)

        # Update user's cash
        db.execute(
            "UPDATE users SET cash = cash - ? WHERE id = ?",
            total_cost,
            session["user_id"]
        )

        # Record transaction
        db.execute(
            """
            INSERT INTO transactions (user_id, symbol, shares, price)
            VALUES (?, ?, ?, ?)
            """,
            session["user_id"],
            symbol,
            shares,
            price
        )

        flash("Bought!")

        return redirect("/")

    return render_template("buy.html")



@app.route("/history")
@login_required
def history():
    """Show history of transactions."""

    transactions = db.execute(
        """
        SELECT symbol, shares, price, timestamp
        FROM transactions
        WHERE user_id = ?
       ORDER BY timestamp DESC
        """,
        session["user_id"]
    )

    return render_template(
        "history.html",
        transactions=transactions
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # Forget any previous user
    session.clear()

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        if not password:
            return apology("must provide password", 403)

        # Look up user
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?",
            username
        )

        # Check username and password
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"],
            password
        ):
            return apology(
                "invalid username and/or password",
                403
            )

        # Remember logged-in user
        session["user_id"] = rows[0]["id"]

        return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out."""

    session.clear()

    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""

    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("must provide username", 400)

        if not password:
            return apology("must provide password", 400)

        if not confirmation:
            return apology("must confirm password", 400)

        if password != confirmation:
            return apology("passwords do not match", 400)

        # Check if username already exists
        existing_user = db.execute(
            "SELECT id FROM users WHERE username = ?",
            username
        )

        if existing_user:
            return apology("username already exists", 400)

        hash_password = generate_password_hash(password)

        new_user_id = db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            username,
            hash_password
        )

        session["user_id"] = new_user_id

        flash("Registered!")
        return redirect("/")

    return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""

    user_id = session["user_id"]

    if request.method == "POST":

        symbol = request.form.get("symbol")
        shares_input = request.form.get("shares")

        # Ensure symbol was submitted
        if not symbol:
            return apology("must provide symbol", 400)

        # Ensure shares was submitted
        if not shares_input:
            return apology("must provide shares", 400)

        # Validate number of shares
        try:
            shares = int(shares_input)
        except (ValueError, TypeError):
            return apology("shares must be a positive integer", 400)

        if shares <= 0:
            return apology("shares must be a positive integer", 400)

        symbol = symbol.upper()

        # Check how many shares the user owns
        rows = db.execute(
            """
            SELECT SUM(shares) AS total_shares
            FROM transactions
            WHERE user_id = ? AND symbol = ?
            """,
            user_id,
            symbol
        )

        owned_shares = rows[0]["total_shares"]

        if owned_shares is None:
            owned_shares = 0

        if shares > owned_shares:
            return apology("not enough shares", 400)

        # Look up current stock price
        stock = lookup(symbol)

        if stock is None:
            return apology("invalid symbol", 400)

        price = stock["price"]
        total_sale = price * shares

        # Add sale amount to user's cash
        db.execute(
            "UPDATE users SET cash = cash + ? WHERE id = ?",
            total_sale,
            user_id
        )

        # Record sale as negative shares
        db.execute(
            """
            INSERT INTO transactions (user_id, symbol, shares, price)
            VALUES (?, ?, ?, ?)
            """,
            user_id,
            symbol,
            -shares,
            price
        )

        flash("Sold!")

        return redirect("/")

    # Get stocks owned by user
    stocks = db.execute(
        """
        SELECT symbol, SUM(shares) AS total_shares
        FROM transactions
        WHERE user_id = ?
        GROUP BY symbol
        """,
        user_id
    )

    symbols = []

    for stock in stocks:
        if stock["total_shares"] > 0:
            symbols.append(stock["symbol"])

    return render_template(
        "sell.html",
        symbols=symbols
    )

