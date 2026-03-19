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
    full_name = db.Column(db.String(250), nullable=False)
    username = db.Column(db.String(250), unique=True, nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    role = db.Column(db.String(50), default="user", nullable=False)

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
            return redirect(url_for("admin_dashboard" if user.role == "admin" else "home"))
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
    



