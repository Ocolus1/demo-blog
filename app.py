from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import sha256_crypt
from sqlalchemy.exc import IntegrityError
from functools import wraps
from sqlalchemy.dialects.mysql import  TEXT
import os 



# initialising flaks app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(username='roots',
                                        password='root', hostname='localhost', databasename='mydb')
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.update(

    #Set the secret key to a sufficiently random value
    SECRET_KEY=os.urandom(24)
)



# initialise the cursor
db = SQLAlchemy(app)


# the users table
class User(db.Model):
    __tablename__ = "user"
    id = db.Column("id", db.Integer, primary_key=True, nullable=False)
    name = db.Column("name", db.String(100), nullable=False)
    email = db.Column("email", db.String(100), nullable=False)
    username = db.Column("username", db.String(100), nullable=False, unique=True)
    password = db.Column("password", db.String(100), nullable=False)
    register_date = db.Column('register_date', db.String(6), nullable=False)

    def __init__(self, name, email, username, password):
        self.name = name
        self.email = email
        self.username = username
        self.password = password


# the users table
class Article(db.Model):
    __tablename__ = "article"
    id = db.Column("id", db.Integer, primary_key=True, nullable=False)
    title = db.Column("title", db.String(255), nullable=False)
    author = db.Column("author", db.String(100), nullable=False)
    body = db.Column("body", TEXT, nullable=False)
    created_date = db.Column('created_date', db.String(6), nullable=False)

    def __init__(self, title, author, body):
        self.title = title
        self.author = author
        self.body = body



# Check if user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorised, Please Login", "danger")
            return redirect(url_for("login"))
    return wrapper


# the index page
@app.route("/")
def index():
    return render_template("index.htm")


# the homepage
@app.route("/dashboard", methods=["POST", "GET"])
@is_logged_in
def dashboard():
    results = db.engine.execute("SELECT * FROM article")
    arts = Article.query.all()
    if results:
        return render_template("dashboard.htm", arts=arts)
    else:
        msg = "No articles found"
        return render_template("dashboard.htm", msg=msg)


# the about page
@app.route("/about")
def about():
    return render_template("about.htm")


# the articles page
@app.route("/articles")
def articles():
    results = db.engine.execute("SELECT * FROM article")
    articles = Article.query.all()
    if results:
        return render_template("articles.htm", articles=articles)
    else:
        msg = "No articles found"
        return render_template("articles.htm", msg=msg)


# the article page
@app.route("/article/<string:id>/")
@is_logged_in
def article(id):
    # result = db.engine.execute("SELECT * FROM user WHERE id = %s", [id])
    article = Article.query.filter_by(id=id).first()
    return render_template("article.htm", article=article)


# the register page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form['confirm_password']
        if not name or not email or not username or not password or not confirm_password:
            flash("Enter all fields", "danger")
        else:
            try:
                # creating an instance of User
                users = User(name, email, username, sha256_crypt.encrypt(str(password)))
                if password == confirm_password:
                    # committing to the database
                    db.session.add(users)
                    db.session.commit()
                    flash("You have successfully registered", "success")
                    return redirect(url_for("login"))
                else:
                    error = "Password do not match"
                    return render_template("register.htm", error=error)
            except IntegrityError:
                db.session.rollback()
                flash("ERROR! There was an error in registering, try again later", "danger")
    return render_template("register.htm")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if not username or not password:
            flash("Enter all fields", "danger")
        else:
            results = User.query.filter_by(username=username).first()
            if results:
                result = results.password
                if sha256_crypt.verify(password, result):
                    # passed
                    session["logged_in"] = True
                    session["username"] = username
                    session["password"] = password
                    flash("You are now logged in.", "success")
                    return redirect(url_for("dashboard"))
                elif not sha256_crypt.verify(password, result):
                    flash("Invalid Password", "danger")
                    return render_template('login.htm')
            else:
                error = "This username does not exist"
                return render_template("login.htm", error=error)

    return render_template("login.htm")


@app.route("/add_article", methods=["POST","GET"])
@is_logged_in
def add_article():
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        if not body or not title:
            flash("Enter all fields", "danger")
        else:
            art = Article(title, session["username"], body)
            db.session.add(art)
            db.session.commit()
            flash("Article Created", "success")
            return redirect(url_for("dashboard"))

    return render_template("add_article.htm")


@app.route("/edit_article/<string:id>", methods=["POST", "GET"])
@is_logged_in
def edit_article(id):
    article = Article.query.filter_by(id=id).first()
    # populate the data
    article_title = article.title
    article_body = article.body
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        if not body or not title:
            flash("Enter all fields", "danger")
        else:
            article.title = title
            article.username = session["username"]
            article.body = body
            db.session.commit()
            flash("Article Updated", "success")
            return redirect(url_for("dashboard"))

    return render_template("edit_article.htm", article_title=article_title, article_body=article_body)


@app.route("/delete_article/<string:id>", methods=["POST"])
@is_logged_in
def delete_article(id):
    article = Article.query.filter_by(id=id).first()
    db.session.delete(article)
    db.session.commit()
    flash("Article Deleted", "success")
    return redirect(url_for("dashboard"))


@app.route("/logout", methods=["POST", "GET"])
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
