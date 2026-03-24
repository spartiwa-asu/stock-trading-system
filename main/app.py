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
    'mysql+pymysql://root:password@localhost/auth_db'
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
    availableFunds = db.Column(db.Float, default=0.0, nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(50), default="user", nullable=False)
    userAccountNumber = db.Column(db.String(25), unique=True, nullable=False, index=True)
    portfolio = db.relationship('Portfolio', backref='user', uselist=False)
    order_history = db.relationship('OrderHistory', backref='user', lazy=True)


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
    companyId= db.Column(db.Integer, db.ForeignKey('company.companyId'), nullable=False)
    administratorId = db.Column(db.Integer, db.ForeignKey('administrator.id'), nullable=False)
    name = db.Column(db.String(25), nullable=False, unique=True)
    ticker = db.Column(db.String(25), nullable=False, unique=True)
    initStockPrice = db.Column(db.Float, nullable=False)
    currentMarketPrice = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.BigInteger, nullable=False)
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
    companyName = db.Column(db.String(25), nullable=False)
    ticker = db.Column(db.String(25), nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)


class FinancialTransaction(db.Model):
    financialTransactionId = db.Column(db.Integer, primary_key=True)
    userAccountNumber = db.Column(db.String(25), db.ForeignKey('users.userAccountNumber'), nullable=False)
    companyId = db.Column(db.Integer, db.ForeignKey('company.companyId'), nullable=False)
    orderId = db.Column(db.Integer, db.ForeignKey('order_history.orderId'), nullable=False)
    type = db.Column(db.String(25), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)


class Company(db.Model):
    companyId = db.Column(db.Integer, primary_key=True)
    companyName = db.Column(db.String(25), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    stockTotalQuantity = db.Column(db.BigInteger, nullable=False)
    ticker = db.Column(db.String(25), nullable=False, unique=True)
    currentMarketPrice = db.Column(db.Float, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)


class Administrator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(25), nullable=False)
    username = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(25), unique=True, nullable=False)
    password = db.Column(db.String(25), nullable=False)
    role = db.Column(db.String(50), default="admin", nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    updatedAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)


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

# User loader 
@login_manager.user_loader #
def load_user(user_id):
    return Users.query.get(int(user_id)) 


# Routes

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
        account_number = str(random.randint(100000, 999999))
        new_user = Users(full_name=full_name, username=username, email=email, password=hashed_pw, userAccountNumber=account_number)
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
@app.route('/portfolio')
@login_required
def portfolio():
    return render_template("portfolio.html")

@app.route('/market_info')
@login_required
def market_info():
    return render_template('market_info.html')

@app.route('/transactions')
@login_required
def transactions():
    return render_template('transactions.html')

@app.route('/withdraw-deposit')
@login_required
def withdraw_deposit():
    return render_template('withdraw_deposit.html')

@app.route("/admin-dashboard")
@login_required
def admin_dashboard():
    if current_user.role != "admin": 
        return redirect(url_for("home"))
    return render_template("admin_dashboard.html")

if __name__ == '__main__':
    app.run(debug=True)