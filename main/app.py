'''Flask core imports: flask, render_template, request, session, 
url_for, redirect and flash provide web framework foundation for routing,
templating, HTTP requests, user sessions, URL generation, page redirection,
and displaying messages'''

'''Flask-SQLAlchemy provides ORM capabilities for database interactions,
allowing us to define database models as Python classes and perform CRUD operationseasily. FLask-Login manages
 user authentication, session management, and access control, while Flask-Bcrypt is used for securely hashing passwords.'''

'''Flask datetime and random are used for handling OTP generation and expiration. The functools wraps is used to
 create custom decorators for role-based access control.'''
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
    'mysql+pymysql://root:password@localhost/auth_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'
'''The SQLALCHEMY_DATABASE_URI configures the connection to the MySQL database using the PyMySQL driver.
 The SQLALCHEMY_TRACK_MODIFICATIONS is set to False to disable unnecessary overhead, and SECRET_KEY'''
# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect to login page if not authenticated
'''The database URI is set to connect to a MySQL database named auth_db with the username root and password Likhi123. 
The login_manager is initialized and configured to redirect unauthenticated users to the login page.'''
# User model with role-based access control
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(250), nullable=False)
    username = db.Column(db.String(250), unique=True, nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    role = db.Column(db.String(50), default="user", nullable=False)
''' The Users class defines the database model for user accounts, including fields for full name, 
username, email, phone number, password (hashed), role (user or admin), MFA status, and account 
creation timestamp. It inherits from UserMixin to integrate with Flask-Login's user management features.'''

    
''' this code block initializes the database and creates the necessary tables based on the defined models. 
It ensures that the database is set up and ready to store user information when the application starts.'''
# Initialize database
with app.app_context():
    db.create_all()

# User loader - required by Flask-Login
@login_manager.user_loader #decorator tells Flask-Login how to reload a user from the session
def load_user(user_id): #Function that receives the user’s ID stored in the session
    return Users.query.get(int(user_id)) #keeps the user logged in across requests
'''The load_user function is a user loader callback required by Flask-Login. 
It takes a user ID as input and queries the database to retrieve the corresponding user object. 
This function is essential for maintaining user sessions and allowing users to stay logged in across different requests.'''
# Routes

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


#Logout route
@app.route('/logout') #triggered when the user clicks logout
@login_required #Ensures only logged-in users can access this route
def logout():
    logout_user()
    return redirect(url_for("index"))


# Protected home route

@app.route('/home') # will be the home page.
@login_required # Only logged-in users can access. This decorator ensures the protected view. 
def home():
    return render_template("home.html")

#unprotected home page for non-logged in users.
@app.route('/')
def index():
    return render_template("index.html")


if __name__ == '__main__':
    app.run(debug=True)
    



