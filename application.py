import os
import requests
import json

from flask import Flask, session, flash, jsonify, redirect, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variables
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

if not os.getenv("API_KEY"):
    raise RuntimeError("API_KEY is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def add_star_img(sql_list):
    """
    Helper function to append correct star rating imgs to each book or review.
    The book or review rating is the last entry in each tuple.
    """

    new_list = []

    for item in sql_list:
        new_item = list(item)

        rating = item[-1]

        if rating == 0:
            new_item.append('no_rating.png')
        else:
            new_item.append(str(round(rating)) + '_star.png')
        new_list.append(new_item)

    return new_list


@app.route("/")
def index():

    # Top Rated Books - select 6 highest rated books:
    top = db.execute("SELECT * FROM books WHERE average_rating >= 4.5 ORDER BY RANDOM() LIMIT 6").fetchall()

    top = add_star_img(top)

    # Lucky Dip Section - select 6 random books:
    lucky = db.execute("SELECT * FROM books ORDER BY RANDOM() LIMIT 6").fetchall()

    lucky = add_star_img(lucky)

    # Author Explore Section - select up to 6 books from an author:
    author = db.execute("SELECT * FROM books WHERE author in (SELECT author FROM books GROUP BY author ORDER BY RANDOM() LIMIT 1) LIMIT 6").fetchall()

    author = add_star_img(author)

    return render_template("home.html", top=top, lucky=lucky, author=author)


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
    """Display all books by a given author"""

    # Lucky Dip Section - select 4 random books:
    lucky = db.execute("SELECT * FROM books ORDER BY RANDOM() LIMIT 6").fetchall()

    lucky = add_star_img(lucky)

    # Author Explore Section - select up to 4 books from an author:
    author = db.execute("SELECT * FROM books WHERE author=:author", {"author":name}).fetchall()

    author = add_star_img(author)

    return render_template("author_details.html", author=author, lucky=author)


@app.route("/book_details/<book_id>")
def book_details(book_id):
    """Display a single book's details and its review page"""

    # Get Book Details:
    book = db.execute("SELECT * FROM books WHERE id=:id", {"id": book_id}).fetchall()

    book = add_star_img(book)

    # Get All Reviews and reviewer details for the Book:
    reviews = db.execute("SELECT users.id, users.username, reviews.text, reviews.date, reviews.rating FROM users INNER JOIN reviews ON users.id=reviews.user_id WHERE reviews.book_id=:book_id ORDER BY reviews.date DESC", {"book_id": book_id}).fetchall()

    reviews = add_star_img(reviews)

    # Get Additional Reviews and ratings from GoodReads API:
    gr_res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": os.getenv("API_KEY"), "isbns": book[0][1]}).json()['books'][0]

    good_reads = (gr_res['average_rating'], gr_res['work_ratings_count'])

    #GR Result Format: {'books': [{'id': 29207858, 'isbn': '1632168146', 'isbn13': '9781632168146', 'ratings_count': 0, 'reviews_count': 2, 'text_reviews_count': 0, 'work_ratings_count': 27, 'work_reviews_count': 123, 'work_text_reviews_count': 9, 'average_rating': '4.11'}]}

    return render_template("book_details.html", book=book, reviews=reviews, good_reads=good_reads)


@app.route("/user_details/<user_id>")
def user_details(user_id):
    """Display all the reviews written by a single user"""

    # Get all reviews by the user reviewer details for the Book:
    reviews = db.execute("SELECT users.username, books.id, books.isbn, books.title, books.author, reviews.text, reviews.date, reviews.rating FROM users INNER JOIN reviews ON users.id=reviews.user_id INNER JOIN books ON reviews.book_id = books.id WHERE users.id=:user_id ORDER BY reviews.date DESC", {"user_id": user_id}).fetchall()

    reviews = add_star_img(reviews)

    return render_template("user_details.html", reviews=reviews)


@app.route("/search", methods=["POST"])
def search():
    """ Get results for a title, author or ISBN search """

    # Get input from search bar
    search_type = request.form.get("search-type")
    search = request.form.get("search-text")
    search_text = '%' + search + '%'

    # If a search parameter is missing, render homepage with an apology
    if not search_type or not search_text:
        flash('Please select search type and enter a search value to search for books!')
        return redirect("/")

    # Otherwise check the search term and generate a query result:
    author = None
    title_isbn = None

    if search_type == 'author':
        author = []
        # Get 10 authors:
        author_names = db.execute("SELECT author FROM books WHERE author ILIKE :search_text GROUP BY author LIMIT 10", {"search_text" : search_text}).fetchall()

        # For each author in list, get 6 books:
        for name in author_names:
            author_books = db.execute("SELECT * FROM books WHERE author = :author LIMIT 6", {"author" : name[0]}).fetchall()

            author_books = add_star_img(author_books)

            author.append(author_books)

    else:
        # Get similar books by isbn or book title
        title_isbn = db.execute(f"SELECT * FROM books WHERE {search_type} ILIKE :search_text LIMIT 30", {"search_text" : search_text}).fetchall()

        title_isbn = add_star_img(title_isbn)

    return render_template("/search_results.html", search_type=search_type, search_text=search, author=author, title_isbn=title_isbn)


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
