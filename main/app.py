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
from datetime import datetime, timedelta
import random
from flask import flash

app = Flask(__name__)
bcrypt = Bcrypt(app)

#Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'mysql+pymysql://root:Heer3481%40ift401@localhost/auth_db'
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
    userId = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    orderId = db.Column(db.Integer, db.ForeignKey('order_history.orderId'), nullable=False)
    stockName = db.Column(db.String(25), nullable=False)
    stockTicker = db.Column(db.String(25), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    currentMarketPrice = db.Column(db.Float, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)



class Stock(db.Model):
    stockId = db.Column(db.Integer, primary_key=True)
    companyId= db.Column(db.Integer, nullable=False)
    administratorId = db.Column(db.Integer, db.ForeignKey('administrator.id'), nullable=False)
    name = db.Column(db.String(25), nullable=False, unique=True)
    ticker = db.Column(db.String(25), nullable=False, unique=True)
    initStockPrice = db.Column(db.Float, nullable=False)
    currentMarketPrice = db.Column(db.Float, nullable=False)
    totalShares = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    createdAt= db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)



class OrderHistory(db.Model):
    orderId = db.Column(db.Integer, primary_key=True)
    stockId = db.Column(db.Integer, db.ForeignKey('stock.stockId'), nullable=False)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    administratorId = db.Column(db.Integer, db.ForeignKey('administrator.id'), nullable=False)
    type = db.Column(db.String(25), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    totalValue = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(25), nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)



class FinancialTransaction(db.Model):
    financialTransactionId = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    orderId = db.Column(db.Integer, db.ForeignKey('order_history.orderId'), nullable=True)
    type = db.Column(db.String(25), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    availableFunds = db.Column(db.Float, default=0.0, nullable=False)



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



class Exception(db.Model):
    exceptionId = db.Column(db.Integer, primary_key=True)
    administratorId = db.Column(db.Integer, db.ForeignKey('administrator.id'), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    holidayDate = db.Column(db.Date, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)



class WorkingDay(db.Model):
    WorkingDayId = db.Column(db.Integer, primary_key=True)
    administratorId = db.Column(db.Integer, db.ForeignKey('administrator.id'), nullable=False)
    dayOfWeek = db.Column(db.String(25), nullable=False)
    startTime = db.Column(db.Time, nullable=False)
    endTime = db.Column(db.Time, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)



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


# User loader 
@login_manager.user_loader
def load_user(user_id):
    role, actual_id = user_id.split(":")
    if role == "user":
        return db.session.get(Users, int(actual_id))
    if role == "admin":
        return db.session.get(Administrator, int(actual_id))
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
        stock_id = request.form.get("stock_id", type=int)
        action = request.form.get("action")
        quantity = request.form.get("quantity", type=float)

        if not stock_id or not action or not quantity or quantity <= 0:
            flash("Please enter valid order details.", "danger")
            return redirect(url_for('portfolio'))

        stock = db.session.get(Stock, stock_id)
        if not stock:
            flash("Stock not found.", "danger")
            return redirect(url_for('portfolio'))

        price = stock.price
        shares_cost = price * quantity

        portfolio_entry = Portfolio.query.filter_by(
            customerId=current_user.id,
            stockName=stock.company_name
        ).first()

        if action == "buy":
            if current_user.balance < shares_cost:
                flash("Not enough cash!", "danger")
                return redirect(url_for('portfolio'))

            current_user.balance -= shares_cost

            if not portfolio_entry:
                portfolio_entry = Portfolio(
                    customerId=current_user.id,
                    stockId=stock.id,
                    stockName=stock.company_name,
                    stockTicker=stock.company_name[:4].upper(),
                    quantity=quantity,
                    currentMarketPrice=price,
                    updatedAt=datetime.utcnow()
                )
                db.session.add(portfolio_entry)
            else:
                portfolio_entry.quantity += quantity
                portfolio_entry.currentMarketPrice = price
                portfolio_entry.updatedAt = datetime.utcnow()

            flash(f"Bought {quantity} shares of {stock.company_name} for ${shares_cost:.2f}", "success")

        elif action == "sell":
            if not portfolio_entry or portfolio_entry.quantity < quantity:
                flash("Not enough shares to sell!", "danger")
                return redirect(url_for('portfolio'))

            current_user.balance += shares_cost
            portfolio_entry.quantity -= quantity
            portfolio_entry.currentMarketPrice = price
            portfolio_entry.updatedAt = datetime.utcnow()

            flash(f"Sold {quantity} shares of {stock.company_name} for ${shares_cost:.2f}", "success")

            if portfolio_entry.quantity == 0:
                db.session.delete(portfolio_entry)

        else:
            flash("Invalid action.", "danger")
            return redirect(url_for('portfolio'))

        order = OrderHistory(
            stockId=stock.id,
            userId=current_user.id,
            administratorId=1,  # replace with a real admin id or make nullable if needed
            type=action,
            quantity=quantity,
            price=price,
            totalValue=shares_cost,
            status="completed"
        )

        db.session.add(order)
        db.session.commit()

        return redirect(url_for('portfolio'))

    portfolio_items = Portfolio.query.filter_by(customerId=current_user.id).all()
    return render_template(
        'portfolio.html',
        stocks=stocks,
        portfolio_items=portfolio_items,
        current_user=current_user
    )



@app.route('/market_info')
@login_required
def market_info():
    return render_template('market_info.html')

@app.route('/transactions')
@login_required
def transactions():
    return render_template('transactions.html')

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
            flash("Withdraw successful.", "success")

        elif action == "deposit":
            current_user.balance += amount
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
        company_id = request.form.get("company_id", type=int)
        name = request.form.get("name")
        ticker = request.form.get("ticker")
        init_stock_price = request.form.get("init_stock_price", type=float)
        total_shares = request.form.get("total_shares", type=int)
        quantity = request.form.get("quantity", type=int)

        if not all([company_id, name, ticker, init_stock_price, total_shares, quantity]):
            flash("Please fill all fields.", "danger")
            return redirect(url_for("admin_dashboard"))

        existing_stock = Stock.query.filter(
            (Stock.name == name) | (Stock.ticker == ticker)
        ).first()

        if existing_stock:
            flash("Stock already exists.", "danger")
            return redirect(url_for("admin_dashboard"))

        new_stock = Stock(
            companyId=company_id,
            administratorId=current_user.id,
            name=name,
            ticker=ticker,
            initStockPrice=init_stock_price,
            currentMarketPrice=init_stock_price,
            totalShares=total_shares,
            quantity=quantity
        )

        db.session.add(new_stock)
        db.session.commit()
        flash("Stock created successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    stocks = Stock.query.order_by(Stock.stockId.desc()).all()
    return render_template("admin_dashboard.html", stocks=stocks)

if __name__ == '__main__':
    app.run(debug=True)