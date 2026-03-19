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
bcrypt = Bcrypt(app)# Initialize Bcrypt for password hashing

#Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'mysql+pymysql://root:Likhi123@localhost/auth_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'
'''The SQLALCHEMY_DATABASE_URI configures the connection to the MySQL database using the PyMySQL driver.
 The SQLALCHEMY_TRACK_MODIFICATIONS is set to False to disable unnecessary overhead, and SECRET_KEY'''
# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect to login page if not authenticated

# User model with role-based access control
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

# User loader - required by Flask-Login
@login_manager.user_loader #decorator tells Flask-Login how to reload a user from the session
def load_user(user_id): #Function that receives the user’s ID stored in the session
    return Users.query.get(int(user_id)) #keeps the user logged in across requests




# Routes

#default route
@app.route('/')
def index():
    return render_template("index.html") #Renders the index page template when accessed via the root URL.

@app.route('/register', methods=["GET", "POST"]) #GET: shows sign-up page, POST: processes form submission
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not full_name or not username or not email or not password:
            flash("Please fill out all fields.", "danger")
            return render_template("register.html")

        # check for existing username or email
        existing_user = Users.query.filter_by(username=username).first()
        existing_email = Users.query.filter_by(email=email).first()
        if existing_user or existing_email:
            flash("Username or email already exists. Try a different one.", "danger")
            return render_template("register.html")

        # hash the password and create user
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = Users(full_name=full_name, username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html") #Renders the registration page template when accessed via GET request.


#Login route
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST": #Checks if the user submitted the form
        user = Users.query.filter_by( 
            username=request.form.get("username")).first() #Queries the database for a matching user

        if user and bcrypt.check_password_hash(user.password, request.form.get("password")):
            login_user(user) # this checks if the user exists and password matches the hashed password
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password. Try again.", "danger") #If user doesn’t exist OR password is wrong
    return render_template("login.html") #If GET request OR login fails, reload login page


#protected page
@app.route('/home') # will be the home page.
@login_required # Only logged-in users can access. This decorator ensures the protected view. 
def home():
    return render_template("home.html")


#Logout route
@app.route('/logout') #triggered when the user clicks logout
@login_required #Ensures only logged-in users can access this route
def logout():
    logout_user()
    return redirect(url_for("index"))

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
    return render_template('transaction.html')


@app.route('/buy-sell')
@login_required
def buy_sell():
    return render_template('buy_sell.html')


@app.route('/withdraw-deposit')
@login_required
def withdraw_deposit():
    return render_template('withdraw_deposit.html')


if __name__ == '__main__':
    app.run(debug=True)
    



