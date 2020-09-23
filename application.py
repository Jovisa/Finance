import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # list to represent a table
    portfolio = []
    total_shares = 0

    # fetching user's cash from database
    cash = float(db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["cash"])
    cash = round(cash, 2)

    # fetching shares user ownes from database
    holdings = db.execute("SELECT symbol, SUM(shares) FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING SUM(shares) > 0",
                            user_id=session["user_id"])

    for holding in holdings:

        symbol = holding["symbol"]
        shares = holding["SUM(shares)"]
        name = lookup(symbol)["name"]
        price = lookup(symbol)["price"]
        total = round(shares * price, 2)

        total_shares += total

        # dictonary to represent row in table
        row = {}
        row["symbol"] = symbol
        row["shares"] = shares
        row["name"] = name
        row["price"] = "{:,}".format(price)
        row["total"] = "{:,}".format(total)

        portfolio.append(row)

    grand_total = "{:,}".format(round(total_shares + cash, 2))

    return render_template("index.html",portfolio=portfolio, cash=cash, grand_total=grand_total)




@app.route("/add-cash", methods=["GET", "POST"])
@login_required
def add_cash():

    """Add additional cash to account"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # select cash on user's account from database
        cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["cash"]

        cash_added = float(request.form.get("cash"))

        # ensure amount of cash is submitted
        if not cash_added:
            return apology("Must provide amount od cash", 403)

        # Ensure cash in positive number
        elif cash_added < 1:
            return apology("cash must be a positive number", 403)

        new_cash = cash + cash_added

        # update cash in users table in database
        db.execute("UPDATE users SET cash = :new_cash WHERE id = :user_id", new_cash=new_cash, user_id=session["user_id"])

        # Redirecting user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("add-cash.html")



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():

    """Buy shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        # Ensure symbol was submitted
        if not symbol:
            return apology("must provide a symbol", 403)

        # Ensure symbol is correct
        elif not lookup(symbol):
            return apology("Symbol does not exist", 403)

        # Ensure number of shares was submitted
        elif not shares:
            return apology("must provide number of shares", 403)

        # Ensure shares is positive integer
        elif shares < 1:
            return apology("must provide positive number of shares", 403)

        # ensure that user can afford to by shares
        cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["cash"]
        price = lookup(symbol)["price"]

        if cash < (price * shares):
            return apology("You don't have enough money", 403)

        # user has enough money, and can boy shares
        else:

            # update users table
            cash_updated = cash - (price * shares)
            db.execute("UPDATE users SET cash = :cash_updated WHERE id = :user_id", cash_updated=cash_updated, user_id=session["user_id"])

            # insert transaction data into transactions table
            db.execute("INSERT INTO transactions (user_id, symbol, shares, price, transacted) VALUES (:user_id, :symbol, :shares, :price, datetime('now'))",
                user_id=session["user_id"], symbol=symbol, shares=shares, price=price,)

            # redirect user to index page
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")



@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # fetching data from transactions table
    transactions = db.execute("SELECT symbol, shares, price, transacted FROM transactions WHERE user_id = :user_id",
                    user_id=session["user_id"])


    return render_template("history.html", transactions=transactions)

@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change Password"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for password hash
        old_password_hash = db.execute("SELECT hash FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["hash"]

        # Handle data user submited via form
        password = request.form.get("password")
        new_password = request.form.get("new-password")
        confirmation = request.form.get("confirmation")

        # Ensure password was submitted
        if not password:
            return apology("must provide a password", 403)

        # Ensure password is correct
        elif not check_password_hash(old_password_hash, password):
            return apology("password incorect", 403)

        # Ensure new password was submitted
        elif not new_password:
            return apology("must provide new password", 403)

        # Ensure new password is confirmed
        elif not confirmation or confirmation != new_password:
            return apology("must confirm new password",403)

        # Generate hash from new password
        password_hash = generate_password_hash(new_password)

        # Update password in users table
        db.execute("UPDATE users SET hash = :password_hash WHERE id = :user_id", password_hash=password_hash, user_id=session["user_id"])

        # Redirect user to login page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("change-password.html")






@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():

    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure symbol was submitted
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("Must provide a symbol", 403)

        # Ensure symbol is correct
        response = lookup(symbol)
        if not response:
            return  apology("Stock don't exist!")

        # handle response data
        name = response["name"]
        price = response["price"]
        company_symbol = response["symbol"]

        # show response data to the user
        return render_template("quoted.html", name=name, price=price, symbol=company_symbol)

    else:
        # User reached route via GET (as by clicking a link or via redirect)
        return render_template("quote.html")






@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Query database for username
        elif db.execute("SELECT username FROM users WHERE username = :username ", username=username):
            return apology("username already exists!", 403)

        # Ensure password was conformed and submitted
        elif not password:
            return apology("must provide a password", 403)
        elif not confirmation or confirmation != password:
            return apology("must confirm password", 403)


        # Hashing a password
        password_hash = generate_password_hash(password)

        # Isert username and hashed password into database
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :password_hash)", username=username, password_hash=password_hash)

        # Redirect user to login page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # fetching transictions data from database
    data = db.execute("SELECT symbol, SUM(shares) FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING SUM(shares) > 0",
                            user_id=session["user_id"])

    # converting data to dictonary
    holdings = {}
    for row in data:
        symbol = row["symbol"]
        shares = row["SUM(shares)"]
        holdings[symbol] = int(shares)

    if request.method == "POST":
        symbol =  request.form.get("symbol")
        shares_sold = int(request.form.get("shares"))
        shares_owned = int(holdings[symbol])

        # Ensure stock symbol was submitted
        if not symbol:
            return apology("must select stock symbol", 403)

        # Ensure number of shaers to be sold was submitted
        elif not shares_sold:
            return apology("must provide number of shares to sell", 403)

        # Ensure shares is positive integer
        elif shares_sold < 1:
            return apology("shares must be a positive integer", 403)

        # check if users owns enough shares
        elif shares_sold > shares_owned:
            return apology("You don't own enough shares", 403)

        price = lookup(symbol)["price"]
        cash = db.execute("SELECT cash from users WHERE id = :user_id", user_id=session["user_id"])[0]["cash"]
        cash = cash + round(shares_sold * price, 2)

        # Insert new trasaction into transactions table
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, transacted) VALUES (:user_id, :symbol, :shares_sold, :price, datetime('now'))",
                user_id=session["user_id"], symbol=symbol, shares_sold=-shares_sold, price=price,)

        # update user's cash in users table
        db.execute("UPDATE users SET cash = :cash WHERE id = :user_id", cash=cash, user_id=session["user_id"])

        # redirect user to index page
        return redirect("/")

    else:
        return render_template("sell.html", holdings=holdings)



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
