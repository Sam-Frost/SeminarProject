# Imports for Flask Application
from flask import Flask, flash, render_template, request, redirect, session, send_file, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.utils import secure_filename
from functools import wraps
import os

# Imports for SQL Queries
from cs50 import SQL

# Imports for VGG19
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.vgg19 import preprocess_input

# Custom Functions

def analysis(img_name):
    # Load the trained model
    model = load_model('/Users/sam/Desktop/SeminarProject/static/vgg_19/vgg19_model.h5')

    # Load and preprocess a new chest X-ray image
    img_path = '/Users/sam/Desktop/SeminarProject/uploads/' + img_name
    img = load_img(img_path, target_size=(224, 224))
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_preprocessed = preprocess_input(img_array)

    # Make a prediction on the new image
    prediction = model.predict(img_preprocessed)

    # Interpret the prediction
    if prediction[0][0] < 0.5:
        print('The new image is predicted to be COVID-19 negative.')
        return False
    else:
        print('The new image is predicted to be COVID-19 positive.')
        return True


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

#Configuring Flask Application
app = Flask(__name__)


UPLOAD_FOLDER = '/Users/sam/Desktop/SeminarProject/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///database.db")

#Landing onto homepage of the web application
#index route
@app.route("/")
def index():
    return render_template("index.html")

#Register route for registering user and creating user course and certificates table!
@app.route("/register", methods=["GET", "POST"])
def register():

    #Opens up html form for registering user
    if request.method == "GET":
        return render_template("register.html")

    #Processing User Input and registering user
    else:

        #Getting data from the Form
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        #Report Error If Password and Confirmation Message don't match
        if not password == confirmation:
            return apology("Password don't match")

        #Check If User Already Exists
        user_exist = db.execute("SELECT * FROM users WHERE username = ? ", username)
        if user_exist :
            return apology("User Already Exists!")

        #Hash funciton
        hashcode = generate_password_hash(password, method='plain', salt_length="2")

        #Insertion of new user into user table in database
        db.execute("INSERT into users (username, hash) VALUES (?, ?)", username, hashcode)

        # Create table for storings users courses
        table_name = username + "_courses"
        db.execute("CREATE TABLE ? (id INTEGER, coursename varchar(15) NOT NULL, no_of_videos INTEGER NOT NULL, course_status INTEGER NOT NULL, primary key(id))", table_name)

        #User is registered and redirected for being loged in
        return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    #Opens up html form for logging user in
    if request.method == "GET":
        return render_template("login.html")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("error.html", data = "invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/analyse", methods=["GET", "POST"])
@login_required
def analyse():

    if request.method == "GET":
        return render_template("analyse.html")

    else :
        # check if the post request has the file part
        if 'file' not in request.files:
            print('No file part')
            return render_template("error.html", data="File not send from the phone")

        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.

        if file.filename == '':
            print('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flag = analysis(filename)
            print(flag)
            return render_template("result.html", data=flag)
            # return redirect(url_for('download_file', name=filename))



@app.route("/prerecord", methods=["GET", "POST"])
@login_required
def prerecord():
    if request.method == "GET":
        return render_template("prerecord.html")

