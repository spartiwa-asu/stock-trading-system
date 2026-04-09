from flask import Flask, render_template, request, session, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, 
    UserMixin, 
    login_user, 
    logout_user, \
login_required, current_user)
from flask_bcrypt import Bcrypt
from functools import wraps
from datetime import date, datetime, timedelta, time
import random
from flask import flash

app = Flask(__name__)
bcrypt = Bcrypt(app)

#Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'mysql+pymysql://root:Likhi123@localhost/auth_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

# User model 
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(25), nullable=False)
    username = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(25), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(50), default="user", nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    def get_id(self):
        return f"user:{self.id}"



class Portfolio(db.Model):
    portfolioId = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    financialTransactionId = db.Column(db.Integer, db.ForeignKey('financial_transaction.financialTransactionId'), nullable=False)
    stockName = db.Column(db.String(25), nullable=False)
    stockTicker = db.Column(db.String(25), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    currentMarketPrice = db.Column(db.Float, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)



class Stock(db.Model):
    stockId = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False, unique=True)
    ticker = db.Column(db.String(25), nullable=False, unique=True)
    initStockPrice = db.Column(db.Float, nullable=False)
    currentMarketPrice = db.Column(db.Float, nullable=False)
    volume = db.Column(db.Integer, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)


class FinancialTransaction(db.Model):
    financialTransactionId = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'), unique=False, nullable=False)
    stockId = db.Column(db.Integer, db.ForeignKey('stock.stockId'), nullable=True)
    stockTicker = db.Column(db.String(25), nullable=True)
    administratorId = db.Column(db.Integer, db.ForeignKey('administrator.id'), nullable=True)
    type = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(25), nullable=False)
    quantity = db.Column(db.Float, nullable=True)
    price = db.Column(db.Float, nullable=True)
    amount = db.Column(db.Float, nullable=False)
    balance = db.Column(db.Float, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)


class Administrator(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(25), nullable=False)
    username = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(25), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="admin", nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    def get_id(self):
        return f"admin:{self.id}"


class MarketSchedule(db.Model):
    scheduleId = db.Column(db.Integer, primary_key=True)
    dayOfWeek = db.Column(db.String(25), nullable=False)
    holidayDate = db.Column(db.Date, nullable=True)
    startTime = db.Column(db.Time, nullable=False)
    endTime = db.Column(db.Time, nullable=False)
    reason = db.Column(db.String(255), nullable=False)




#market logic
def market_check():
    x = datetime.now()
    today = x.date()
    current_time = x.time()
    day = x.strftime("%A")

    holiday = MarketSchedule.query.filter(MarketSchedule.holidayDate == today).first()
    if holiday:
        return False

    market_schedule = MarketSchedule.query.filter_by(dayOfWeek=day).first()
    if not market_schedule:
        return False
    
    return market_schedule.startTime <= current_time <= market_schedule.endTime





# Initialize database
with app.app_context():
    db.create_all()

    existing_admin = Administrator.query.filter_by(username="admin").first()
    if not existing_admin:
        hashed_pw = bcrypt.generate_password_hash("admin123").decode("utf-8")
        admin = Administrator(
            full_name="Admin User",
            username="admin",
            email="admin@example.com",
            password=hashed_pw,
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin created: username=admin, password=admin123")


#market schedule:
    if not MarketSchedule.query.first():
        initial_schedule = []
        
        #dayofWeek, starttime, endtime, reason
        strings = [("Monday", time(9, 0), time(17, 0), "Market is open"), 
                   ("Tuesday", time(9, 0), time(17, 0), "Market is open"),
                   ("Wednesday", time(9, 0), time(17, 0), "Market is open"),
                   ("Thursday", time(9, 0), time(17, 0), "Market is open"),
                   ("Friday", time(9, 0), time(17, 0), "Market is open"),
                   ("Saturday", time(0, 0), time(0, 0), "Market is closed"),
                   ("Sunday", time(0, 0), time(0, 0), "Market is closed")]
           
        for day, start, end, reason in strings:
            initial_schedule.append(MarketSchedule(
                dayOfWeek=day,
                startTime=start,
                endTime=end,
                holidayDate=None,
                reason=reason
            ))


        holidayDate= [(date(2026, 1, 1), "New Year's Day"), 
                      (date(2026, 1, 19), "Martin Luther King Jr. Day"),
                      (date(2026, 2, 16), "Presidents' Day"),
                      (date(2026, 5, 25), "Memorial Day"),
                      (date(2026, 6, 19), "Juneteenth"),
                      (date(2026, 7, 3), "Independence Day"),
                      (date(2026, 9, 7), "Labor Day"),
                      (date(2026, 10, 12), "Columbus Day"),
                      (date(2026, 11, 11), "Veterans Day"),
                      (date(2026, 11, 26), "Thanksgiving Day"),
                      (date(2026, 12, 25), "Christmas Day")]

        for hdate, hname in holidayDate:
            initial_schedule.append(MarketSchedule(
                dayOfWeek="Holiday",
                startTime=time(0, 0),
                endTime=time(0, 0),
                holidayDate=hdate,
                reason=hname
            ))

        db.session.add_all(initial_schedule)
        db.session.commit()



# User loader 
@login_manager.user_loader
def load_user(user_id):
    if not user_id:
        return None

    if ":" not in user_id:
        try:
            return Users.query.get(int(user_id))
        except (ValueError, TypeError):
            return None

    try:
        role, actual_id = user_id.split(":", 1)
        actual_id = int(actual_id)
    except (ValueError, TypeError):
        return None

    if role == "admin":
        return Administrator.query.get(actual_id)
    elif role == "user":
        return Users.query.get(actual_id)

    return None



#default route
@app.route('/')
def index():
    return render_template("index.html") 

@app.route('/register', methods=["GET", "POST"]) 
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not full_name or not username or not email or not password:
            flash("Please fill out all fields.", "danger")
            return render_template("register.html")

        # checks if the user already exists
        existing_user = Users.query.filter_by(username=username).first()
        existing_email = Users.query.filter_by(email=email).first()
        if existing_user or existing_email:
            flash("Username or email already exists. Try a different one.", "danger")
            return render_template("register.html")

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = Users(full_name=full_name, username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html") 


#Login route
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST": 
        user = Users.query.filter_by(username=request.form.get("username")).first()
        if user and bcrypt.check_password_hash(user.password, request.form.get("password")):
            login_user(user)  # log the user in
            # Redirect admins to admin dashboard, normal users to home
            return redirect(url_for( "home"))
        
        admin = Administrator.query.filter_by(username=request.form.get("username")).first()
        if admin and bcrypt.check_password_hash(admin.password, request.form.get("password")):
            login_user(admin)
            return redirect(url_for("admin_dashboard"))

        else:
            flash("Invalid username or password. Try again.", "danger")
    return render_template("login.html")


#protected page
@app.route('/home') 
@login_required 
def home():
    return render_template("home.html")


#Logout route
@app.route('/logout') 
@login_required 
def logout():
    logout_user()
    return redirect(url_for("index"))


#protected pages
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user




@app.route('/portfolio', methods=['GET', 'POST'])
@login_required
def portfolio():
    stocks = Stock.query.all()

    if request.method == 'POST':
        action = request.form.get("action")
        quantity = request.form.get("quantity", type=float)

        if action == "cancel":
            transaction_id = request.form.get("transaction_id", type=int)
            transaction = db.session.get(FinancialTransaction, transaction_id)

            if not transaction or transaction.userId != current_user.id or transaction.status != "pending":
                flash("Invalid transaction to cancel.", "danger")
                return redirect(url_for('portfolio'))

            transaction.status = "cancelled"

            if transaction.type == "buy":
                flash(f"Your buy order for {transaction.quantity} share(s) of {db.session.get(Stock, transaction.stockId).name} has been cancelled.", "danger")
                

            elif transaction.type == "sell":
                flash(f"Your sell order for {transaction.quantity} share(s) of {db.session.get(Stock, transaction.stockId).name} has been cancelled.", "danger")

            db.session.commit()
            return redirect(url_for('portfolio'))

        if not action or quantity is None or quantity <= 0:
            flash("Please enter valid order details.", "danger")
            return redirect(url_for('portfolio'))

        if action == "buy":
            stock_id = request.form.get("stock_id", type=int)

            if not stock_id:
                flash("Please choose a stock to buy.", "danger")
                return redirect(url_for('portfolio'))

            stock = db.session.get(Stock, stock_id)
            if not stock:
                flash("Stock not found.", "danger")
                return redirect(url_for('portfolio'))

            price = stock.currentMarketPrice
            shares_cost = price * quantity

            if current_user.balance < shares_cost:
                flash("Not enough cash!", "danger")
                return redirect(url_for('portfolio'))


            if not market_check():
                transaction = FinancialTransaction(
                    stockId=stock.stockId,
                    userId=current_user.id,
                    stockTicker=stock.ticker,
                    administratorId=1,
                    type="buy",
                    status="pending",
                    quantity=quantity,
                    price=price,
                    amount=shares_cost,
                    balance=current_user.balance
                )
                db.session.add(transaction)
                db.session.commit()
                flash(f"Market is closed. Your order to buy {quantity} share(s) of {stock.name} has been placed as pending. It will be executed when the market opens.", "warning")
                return redirect(url_for('portfolio'))


            current_user.balance -= shares_cost

            transaction = FinancialTransaction(
                stockId=stock.stockId,
                userId=current_user.id,
                stockTicker=stock.ticker,
                administratorId=1,
                type="buy",
                status="completed",
                quantity=quantity,
                price=price,
                amount=shares_cost,
                balance=current_user.balance
            )
            db.session.add(transaction)
            db.session.flush()

            portfolio_entry = Portfolio.query.filter_by(
                userId=current_user.id,
                stockTicker=stock.ticker
            ).first()

            if portfolio_entry:
                portfolio_entry.quantity += quantity
                portfolio_entry.currentMarketPrice = price
                portfolio_entry.updatedAt = datetime.utcnow()
                portfolio_entry.financialTransactionId = transaction.financialTransactionId
            else:
                portfolio_entry = Portfolio(
                    userId=current_user.id,
                    financialTransactionId=transaction.financialTransactionId,
                    stockName=stock.name,
                    stockTicker=stock.ticker,
                    quantity=quantity,
                    currentMarketPrice=price,
                    updatedAt=datetime.utcnow()
                )
                db.session.add(portfolio_entry)

            flash(f"Bought {quantity} share(s) of {stock.name} for ${shares_cost:.2f}", "success")

        elif action == "sell":
            stock_ticker = request.form.get("stock_ticker")

            if not stock_ticker:
                flash("Please choose a stock to sell.", "danger")
                return redirect(url_for('portfolio'))

            stock = Stock.query.filter_by(ticker=stock_ticker).first()
            if not stock:
                flash("Stock not found.", "danger")
                return redirect(url_for('portfolio'))

            portfolio_entry = Portfolio.query.filter_by(
                userId=current_user.id,
                stockTicker=stock_ticker
            ).first()

            if not portfolio_entry or portfolio_entry.quantity < quantity:
                flash("Not enough shares to sell!", "danger")
                return redirect(url_for('portfolio'))

            price = stock.currentMarketPrice
            shares_cost = price * quantity

            if not market_check():
                transaction = FinancialTransaction(
                    stockId=stock.stockId,
                    userId=current_user.id,
                    stockTicker=stock.ticker,
                    administratorId=1,
                    type="sell",
                    status="pending",
                    quantity=quantity,
                    price=price,
                    amount=shares_cost,
                    balance=current_user.balance
                )
                db.session.add(transaction)
                db.session.commit()
                flash(f"Market is closed. Your order to sell {quantity} share(s) of {stock.name} has been placed as pending. It will be executed when the market opens.", "warning")
                return redirect(url_for('portfolio'))

            current_user.balance += shares_cost

            transaction = FinancialTransaction(
                stockId=stock.stockId,
                userId=current_user.id,
                stockTicker=stock.ticker,
                administratorId=1,
                type="sell",
                status="completed",
                quantity=quantity,
                price=price,
                amount=shares_cost,
                balance=current_user.balance
            )
            db.session.add(transaction)
            db.session.flush()

            portfolio_entry.quantity -= quantity
            portfolio_entry.currentMarketPrice = price
            portfolio_entry.updatedAt = datetime.utcnow()
            portfolio_entry.financialTransactionId = transaction.financialTransactionId

            if portfolio_entry.quantity == 0:
                db.session.delete(portfolio_entry)

            flash(f"Sold {quantity} share(s) of {stock.name} for ${shares_cost:.2f}", "success")

        else:
            flash("Invalid action.", "danger")
            return redirect(url_for('portfolio'))

        db.session.commit()
        return redirect(url_for('portfolio'))

    portfolio_items = Portfolio.query.filter_by(userId=current_user.id).all()
    pending_orders= FinancialTransaction.query.filter_by(userId=current_user.id, status="pending").all()
    for order in pending_orders:
        stock = db.session.get(Stock, order.stockId)
        order.stock_name = stock.name if stock else "Unknown Stock"

    portfolio_total_value = sum(
        item.quantity * item.currentMarketPrice for item in portfolio_items
    )

    total_account_value = current_user.balance + portfolio_total_value

    return render_template(
        'portfolio.html',
        stocks=stocks,
        portfolio_items=portfolio_items,
        pending_orders=pending_orders,
        current_user=current_user,
        portfolio_total_value=portfolio_total_value,
        total_account_value=total_account_value
    )

import time
import threading
import random

def update_stock_prices():
    with app.app_context():
        while True:
            #for pending orders
            if market_check(): 
                pending_orders = FinancialTransaction.query.filter_by(status="pending").all()

                for order in pending_orders:
                    stock= db.session.get(Stock, order.stockId)
                    user= db.session.get(Users, order.userId)

                    if order.type == "buy":
                        user.balance -= stock.currentMarketPrice * order.quantity
                        existing = Portfolio.query.filter_by(userId=user.id, stockTicker=stock.ticker).first()
                        if existing:
                                existing.quantity += order.quantity
                        else:
                                db.session.add(Portfolio(
                                    userId=order.userId,
                                    financialTransactionId=order.financialTransactionId,
                                    stockName=stock.name,
                                    stockTicker=stock.ticker,
                                    quantity=order.quantity,
                                    currentMarketPrice=stock.currentMarketPrice,
                                ))
 
                    elif order.type == "sell":
                        existing = Portfolio.query.filter_by(userId=user.id, stockTicker=stock.ticker).first()
                        existing.quantity -= order.quantity
                        user.balance += stock.currentMarketPrice * order.quantity
                        if existing.quantity <= 0:
                            db.session.delete(existing)
                       
                    order.status = "completed"

                db.session.commit()

           #pricegen 
            stocks = Stock.query.all()

            for stock in stocks:
                base_price = stock.initStockPrice
                percent_change = random.uniform(-0.2, 0.2)
                new_price = base_price * (1 + percent_change)
                stock.currentMarketPrice = round(max(1, new_price), 2)

                portfolios= Portfolio.query.filter_by(stockTicker=stock.ticker).all()
                for portfolio in portfolios:
                    portfolio.currentMarketPrice = stock.currentMarketPrice
                    portfolio.updatedAt = datetime.utcnow()

            db.session.commit()
            print("Stock prices updated")

            time.sleep(15)



@app.route('/market_info')
@login_required
def market_info():
    market_schedule = MarketSchedule.query.filter(MarketSchedule.holidayDate == None).all()
    holiday = MarketSchedule.query.filter(MarketSchedule.holidayDate != None).all()
    return render_template('market_info.html', market_schedule=market_schedule, holiday=holiday)


@app.route('/transactions')
@login_required
def transactions():
    results = (
        db.session.query(FinancialTransaction, Stock)
        .outerjoin(Stock, FinancialTransaction.stockId == Stock.stockId)
        .filter(FinancialTransaction.userId == current_user.id)
        .filter(FinancialTransaction.status.in_(["completed", "cancelled", "pending"]))
        .order_by(FinancialTransaction.createdAt.desc())
        .all()
    )

    transactions = []

    for ft, stock in results:
        transactions.append({
            "createdAt": ft.createdAt,
            "type": ft.type,
            "status": ft.status,
            "quantity": ft.quantity,
            "price": ft.price,
            "amount": ft.amount,
            "ticker": stock.ticker if stock else None,
            "stock_name": stock.name if stock else None
        })

    return render_template("transactions.html", transactions=transactions)


@app.route('/withdraw-deposit', methods=["GET", "POST"])
@login_required
def withdraw_deposit():
    if current_user.role == "admin":
        flash("Admins cannot deposit or withdraw here.", "danger")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        action = request.form.get("action")
        amount = request.form.get("amount", type=float)

        if amount is None or amount <= 0:
            flash("Enter a valid amount.", "danger")
            return redirect(url_for("withdraw_deposit"))

        if action == "withdraw":
            if current_user.balance < amount:
                flash("Insufficient balance.", "danger")
                return redirect(url_for("withdraw_deposit"))

            current_user.balance -= amount

            transaction = FinancialTransaction(
                userId=current_user.id,
                stockId=None,
                administratorId=None,
                stockTicker=None,
                type="withdraw",
                status="completed",
                quantity=None,
                price=None,
                amount=amount,
                balance=current_user.balance
            )
            db.session.add(transaction)
            flash("Withdraw successful.", "success")

        elif action == "deposit":
            current_user.balance += amount

            transaction = FinancialTransaction(
                userId=current_user.id,
                stockId=None,
                stockTicker=None,
                administratorId=None,
                type="deposit",
                status="completed",
                quantity=None,
                price=None,
                amount=amount,
                balance=current_user.balance
            )
            db.session.add(transaction)
            flash("Deposit successful.", "success")

        else:
            flash("Invalid action.", "danger")
            return redirect(url_for("withdraw_deposit"))

        db.session.commit()
        return redirect(url_for("withdraw_deposit"))

    return render_template("withdraw_deposit.html", balance=current_user.balance)

@app.route("/admin-dashboard", methods=["GET", "POST"])
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return redirect(url_for("home"))

    if request.method == "POST":
        action = request.form.get("action")
        if action == "edit_market_schedule":
            schedule_id = request.form.get("schedule_id", type=int)
            start_time_str = request.form.get("start_time")
            end_time_str = request.form.get("end_time")
            schedule = db.session.get(MarketSchedule, schedule_id)
            schedule.startTime = datetime.strptime(start_time_str, "%H:%M").time()
            schedule.endTime = datetime.strptime(end_time_str, "%H:%M").time()
            db.session.commit()
            flash("Schedule updated successfully.", "success")
            return redirect(url_for("admin_dashboard")) 
        
        if action == "edit_holiday":
            schedule_id = request.form.get("schedule_id", type=int)
            reason = request.form.get("reason")
            holiday_date= request.form.get("holiday_date")

            schedule= db.session.get(MarketSchedule, schedule_id)
            schedule.reason = reason
            schedule.holidayDate = datetime.strptime(holiday_date, "%Y-%m-%d").date()
            db.session.commit()
            flash("Holiday updated successfully.", "success")
            return redirect(url_for("admin_dashboard")) 

        name = request.form.get("name")
        ticker = request.form.get("ticker")
        init_stock_price = request.form.get("init_stock_price", type=float)
        volume = request.form.get("volume", type=int)

        if not name or not ticker or init_stock_price is None or volume is None:
            flash("Please fill all fields.", "danger")
            return redirect(url_for("admin_dashboard"))

        volume = max(0, volume)

        if volume == 0:
            flash("Volume must be greater than 0.", "danger")
            return redirect(url_for("admin_dashboard"))

        existing_stock = Stock.query.filter(
            (Stock.name == name) | (Stock.ticker == ticker)
        ).first()

        if existing_stock:
            flash("Stock already exists.", "danger")
            return redirect(url_for("admin_dashboard"))

        new_stock = Stock(
            name=name,
            ticker=ticker,
            initStockPrice=init_stock_price,
            currentMarketPrice=init_stock_price,
            volume=volume
        )

        db.session.add(new_stock)
        db.session.commit()
        flash("Stock created successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    stocks = Stock.query.order_by(Stock.stockId.desc()).all()
    market_schedule = MarketSchedule.query.filter(MarketSchedule.holidayDate == None).all()
    holiday = MarketSchedule.query.filter(MarketSchedule.holidayDate != None).all()
    return render_template("admin_dashboard.html", stocks=stocks, market_schedule=market_schedule, holiday=holiday)

if __name__ == '__main__':
    price_thread = threading.Thread(target=update_stock_prices)
    price_thread.daemon = True
    price_thread.start()

    app.run(debug=True)
