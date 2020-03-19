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

def add_star_img(book_list):
    """ Helper fuinction to add correct star rating imgs to each book"""

    new_book_list = []

    for book in book_list:
        new_book = list(book)
        rating = book[6]
        if rating == None:
            new_book.append('no_rating.png')
        else:
            new_book.append(str(round(rating)) + '_star.png')
        new_book_list.append(new_book)

    return new_book_list


@app.route("/")
def index():

    # Lucky Dip Section - select 4 random books:
    lucky = db.execute("SELECT * FROM books ORDER BY RANDOM() LIMIT 6").fetchall()

    lucky = add_star_img(lucky)

    # Author Explore Section - select up to 4 books from an author:
    author = db.execute("SELECT * FROM books WHERE author in (SELECT author FROM books GROUP BY author ORDER BY RANDOM() LIMIT 1) LIMIT 6").fetchall()

    author = add_star_img(author)

    return render_template("home.html", lucky=lucky, author=author)


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


@app.route("/author_details/<name>")
def author_details(name):

    # Lucky Dip Section - select 4 random books:
    lucky = db.execute("SELECT * FROM books ORDER BY RANDOM() LIMIT 6").fetchall()

    lucky = add_star_img(lucky)

    # Author Explore Section - select up to 4 books from an author:
    author = db.execute("SELECT * FROM books WHERE author=:author", {"author":name}).fetchall()

    author = add_star_img(author)

    return render_template("author_details.html", author=author, lucky=author)


@app.route("/api/<isbn>")
def book_api(isbn):
    """Get a book from the database using its ISBN"""
    print("accessing API")
    print(isbn)
    # Try and get book from the database:
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn":isbn}).fetchall()

    # If book exists, return JSON:
    if book:
        return jsonify({
            "title": book[0][2],
            "author": book[0][3],
            "year": book[0][4],
            "isbn": book[0][1],
            "review_count": book[0][5],
            "average_score": book[0][6]
        })
    # If book not in database, return error:
    else:
        return jsonify({"error": "Book ISBN is not in READ-RATE Database"}), 422


    print(book)

    return book[0][2]
