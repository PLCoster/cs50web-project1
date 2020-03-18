import os

from flask import Flask, session, flash, jsonify, redirect, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user into site"""

    # Clear any current user ID:
    session.clear()

    # If User reaches Route via GET (e.g. clicking login link):
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user for the website"""

    # Clear any current user ID:
    session.clear()

    # If User reaches Route via GET (e.g. clicking login link):
    return render_template("register.html")

@app.route("/api/<isbn>")
def book_api(isbn):
    """Get a book from the database using its ISBN"""
    print("accessing API")
    print(isbn)
    # Check book exists in database:
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn":isbn}).fetchall()
    print(book)

    return book[0][2]
