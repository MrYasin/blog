"""

"""

from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

####### User Login Decorator

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "logged_in" in session:
            return f(*args, **kwargs)
    
        else:
            flash("You must be logged in to view this page", "danger")
            return redirect(url_for("login"))

    return decorated_function

####### Register Form

class Registration(Form):
    
    name = StringField("Name:", validators=[validators.Length(min=3, max=25)])
    username = StringField("Username:", validators=[validators.Length(min=4, max=35),])
    email = StringField("E-Mail:", validators=[validators.Email(message="E-Mail address not valid.")])

    password = PasswordField("Password:", validators=[

        validators.DataRequired(message="Invalid password."),
        validators.EqualTo(fieldname="confirm", message="Passwords do not match."),

    ])
    
    confirm = PasswordField("Confirm Password:")


####### Login Form

class Login(Form):

    username = StringField("Username:")
    password = PasswordField("Password:")


####### Login Form

class Article(Form):
    
    title = StringField("Title",validators=[validators.Length(min=5, max=100)])
    content = TextAreaField("Content", validators=[validators.Length(min=10)])


### MYSQL CONFIG

app = Flask(__name__)
app.secret_key = "ybblog"   # FOR FLASHES #

app.config["MYSQL_HOST"] = "127.0.0.1"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

###

@app.route("/")
def index():

    return render_template("index.html")

@app.route("/about")
def about():

    return render_template("about.html")


@app.route("/dashboard")
@login_required
def dashboard():
    
    return render_template("dashboard.html")

### REGISTER

@app.route("/register", methods = ["GET", "POST"])
def register():

    form = Registration(request.form)

    if request.method == "POST" and form.validate():

        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        
        cursor = mysql.connection.cursor()
        inquiry = "INSERT INTO users(name, email, username, password) VALUES(%s,%s,%s,%s)"
        
        cursor.execute(inquiry,(name, email, username, password))
        mysql.connection.commit()

        cursor.close()

    ########## FLASHING

        flash("Registered succesfully.","success")

        return redirect(url_for("login"))

    else:
        return render_template("register.html", form=form)


### LOGIN

@app.route("/login", methods = ["GET", "POST"])
def login():

    form = Login(request.form)

    if request.method == "POST":

        username = form.username.data
        pass_ent = form.password.data

        cursor = mysql.connection.cursor()
        inquiry = "SELECT * FROM users WHERE username = %s"

        result = cursor.execute(inquiry, (username,))
        
        if result > 0:

            data = cursor.fetchone()
            real_pass = data["password"]
            
            if sha256_crypt.verify(pass_ent, real_pass):
                
                flash("Logged in successfully.", "success")

                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index"))

            else:

                flash("Wrong username of password.", "danger")
                return redirect(url_for("login"))

        else:

            flash("No user by that username.","danger")
            return redirect(url_for("login"))


    return render_template("login.html", form = form)


### LOGOUT

@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for("index"))


### ADD ARTICLE

@app.route("/addarticle", methods = ["GET", "POST"])
def add_article():

    form = Article(request.form)
    if request.method == ["POST"] and form.validate():

        title = form.title.data
        content = form.content.data
        
        cursor = mysql.connection.cursor()
        inquiry = "INSERT INTO articles(title, author, content) VALUES(%s,%s,%s)"
        cursor.execute(inquiry,(title, session["username"], content))

        mysql.connection.commit()
        cursor.close()

        flash("Article added successfuly.","success")
        return redirect(url_for("dashboard"))

    return render_template("addarticle.html", form = form)


######################### DEBUG ##############################

if __name__ == "__main__":

    app.run(debug=True)
    

