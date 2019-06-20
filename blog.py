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
            flash("You must be logged in to view this page.", "danger")
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


####### Article Form

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

@app.route("/articles")
def articles():
    
    cursor = mysql.connection.cursor()
    inquiry = "SELECT * FROM articles"
    result = cursor.execute(inquiry)

    if result > 0:

        articles = cursor.fetchall()


        return render_template("articles.html", articles = articles)

    else:
        return render_template("articles.html")

@app.route("/dashboard")
@login_required
def dashboard():

    cursor = mysql.connection.cursor()
    inquiry = "SELECT * FROM articles WHERE author = %s"
    result = cursor.execute(inquiry,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles = articles)

    else:
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


### DETAIL PAGE
@app.route("/article/<string:id>")
def article(id):

    cursor = mysql.connection.cursor()
    inquiry = "SELECT * FROM articles WHERE id = %s"
    result = cursor.execute(inquiry,(id,))

    if result > 0:
        
        article = cursor.fetchone()
        return render_template("article.html", article = article)
    
    else:

        return render_template("article.html")

### ADD ARTICLE

@app.route("/addarticle", methods = ["GET", "POST"])
def add_article():

    form = Article(request.form)
    if request.method == "POST" and form.validate():

        title = form.title.data
        content = form.content.data
        
        cursor = mysql.connection.cursor()
        inquiry = "INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(inquiry,(title, session["username"], content))

        mysql.connection.commit()
        cursor.close()

        flash("Article added successfuly.","success")
        return redirect(url_for("dashboard"))
    
    return render_template("addarticle.html", form = form)


### DELETE ARTICLE

@app.route("/delete/<string:id>")
@login_required
def delete(id):

    cursor = mysql.connection.cursor()
    inquiry = "SELECT * FROM articles WHERE author = %s AND id = %s"
    result = cursor.execute(inquiry,(session["username"],id))

    if result > 0:
        
        inquiry_2 = "DELETE FROM articles WHERE id = %s"
        result = cursor.execute(inquiry_2, (id,))
        MySQL.connection.commit()

        return redirect(url_for("dashboard"))

    else:
        
        flash("There is no article by that ID or you do not have permission.", "danger")
        return redirect(url_for("index"))

### EDIT ARTICLE

@app.route("/edit/<string:id>", methods = ["GET", "POST"])
@login_required
def update(id):

    if request.method == "GET":
        
        cursor = mysql.connection.cursor()
        inquiry = "SELECT * FROM articles WHERE id = %s AND author = %s"
        result = cursor.execute(inquiry,(id,session["username"]))

        if result == 0:
            flash("There is no article by that ID or you do not have permission.", "danger")
            return redirect(url_for("index"))
        
        else:
            article = cursor.fetchone()
            form = Article()
            form.title.data = article["title"]
            form.content.data = article["content"] 
            return render_template("update.html", form = form)

    else: # POST REQUEST #
        
        form = Article(request.form)

        new_Title = form.title.data
        new_Content = form.content.data

        update_inquiry = "UPDATE articles SET title = %s AND content = %s WHERE id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(update_inquiry,(new_Title, new_Content, id))

        mysql.connection.commit()
        
        flash("Article updated successfully.")
        return redirect(url_for("dashboard"))


### SEARCH URL

@app.route("/search", methods = ["GET", "POST"])
def search():
    
    if request.method == "GET":

        return redirect(url_for("index"))

    else:

        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        inquiry = "SELECT * FROM articles WHERE title LIKE '%" + keyword + "%' "
        result = cursor.execute(inquiry)

        if result == 0:
            flash("No articles found by that name.", "warning")
            return redirect(url_for("articles"))
        
        else:
            articles = cursor.fetchall()
            return render_template("articles.html", articles = articles)
            
    
######################### DEBUG ##############################

if __name__ == "__main__":

    app.run(debug=True)


