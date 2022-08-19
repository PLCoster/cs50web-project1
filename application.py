import os
import requests
import json
import datetime


from flask import Flask, session, flash, jsonify, redirect, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError

from helpers import add_star_img, validate_pass, form_time, get_rating

app = Flask(__name__, static_folder='static')

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


@app.route("/")
def index():
    """ Home Page of the Application """

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

    # If user is already logged in, return to home:
    if session.get("user_id") != None:
        return redirect("/")

    # If reached via POST by submitting login form:
    if request.method == "POST":

        # Get input from login form:
        username = request.form.get("username")
        password = request.form.get("password")

        # Check that login has been filled out:
        if not username or not password:
            flash("Please enter username AND password to Log in!")
            return render_template("login.html")

        # Query database for username:
        user = db.execute("SELECT * FROM users WHERE username = :username", {"username" : username}).fetchone()

        # Check username exists and password is correct:
        if not user or not check_password_hash(user[2], password):
            flash("Invalid username and/or password! Please try again!")
            return render_template("login.html")

        # Otherwise log in user and redirect to homepage:
        session["user_id"] = user[0]
        session["username"] = user[1]

        flash('Log in Successful! Welcome back to READ-RATE!')
        return redirect("/")

    # If User reaches Route via GET (e.g. clicking login link):
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user for the website"""

    # If user is already logged in, return to home:
    if session.get("user_id") != None:
        return redirect("/")

    # If reached via POST by submitting form - try to register new user:
    if request.method == "POST":

        # Get input from registration form:
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")

        # If form is incomplete, return and flash apology:
        if not username or not password or not confirm:
            flash('Please fill in all three fields to register!')
            return render_template("register.html")

        # If password and confirmation do not match, return and flash apology:
        elif password != confirm:
            flash('Password and confirmation did not match! Please try again.')
            return render_template("register.html")

        # Ensure password meets password requirements:
        elif not validate_pass(password):
            flash('Password must be eight characters long with at least one number and one letter!')
            return render_template("register.html")

        # Otherwise information from registration is complete:
        else:
            # Check username does not already exist, if it does then ask for a different name:
            if db.execute("SELECT * FROM users WHERE username = :username", {"username" : username}).fetchone():
                flash('Sorry but that username is already in use, please pick a different username!')
                return render_template("register.html")

            # Otherwise add user to database using hashed password:
            hash_pass = generate_password_hash(password)

            # Add new user to users table:
            db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", {"username" : username, "hash" : hash_pass})

            db.commit()

            # Put unique user ID and username into session:

            user_info = db.execute("SELECT id, username FROM users WHERE username=:username", {"username" : username}).fetchall()

            session["user_id"] = user_info[0][0]
            session["username"] = user_info[0][1]

            # Return to home page, logged in:
            flash('Welcome to READ-RATE! You have been succesfully registered and logged in!')
            return redirect("/")

    # If User reaches Route via GET (e.g. clicking registration link):
    else:
        return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # If user not logged in return to home:
    if session.get("user_id") == None:
        return redirect("/")

    # Forget any user_id
    session.clear()

    # Redirect user to home page
    flash('You have been logged out. See you again soon!')
    return redirect("/")


@app.route("/author_details/<name>")
def author_details(name):
    """Display all books by a given author"""

    # Author Explore Section - select up to 4 books from an author:
    author = db.execute("SELECT * FROM books WHERE author=:author", {"author":name}).fetchall()

    # If author does not exist then return home with apology:
    if not author:
        flash("Sorry but that author could not be found in the READ-RATE database!")
        return redirect("/")

    author = add_star_img(author)

    return render_template("author_details.html", author=author, lucky=author)


@app.route("/book_details/<book_id>")
def book_details(book_id):
    """Display a single book's details and its review page"""

    user_review = None

    # Get Book Details:
    book = db.execute("SELECT * FROM books WHERE id=:id", {"id": book_id}).fetchall()

    # If book is not in database, return to homepage with apology:
    if not book:
        flash("Sorry, this book ID does not exist in the READ-RATE database!")
        return redirect("/")

    book = add_star_img(book)

    # Get All Reviews and reviewer details for the Book:
    reviews = db.execute("SELECT users.id, users.username, reviews.text, reviews.date, reviews.rating FROM users INNER JOIN reviews ON users.id=reviews.user_id WHERE reviews.book_id=:book_id ORDER BY reviews.date DESC", {"book_id": book_id}).fetchall()

    reviews = add_star_img(reviews)
    reviews = form_time(reviews)

    """
    # GoodReads API no longer available - Now switched to scraping the Goodreads website
    # Get Additional Reviews and ratings from GoodReads API:
    try:
      gr_res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": os.getenv("API_KEY"), "isbns": book[0][1]}).json()['books'][0]
    except json.decoder.JSONDecodeError:
      flash("Error with GoodReads API!")
      return redirect("/")

    good_reads = (gr_res['average_rating'], gr_res['work_ratings_count'])
    """
    print(book, book[0][1], type(book[0][1]))
    # Scrape GoodReads website for additional reviews/ratings:
    good_reads = get_rating(book[0][1])

    # If a user is logged in, check if they have left their own review:
    if session.get("user_id"):
        user_review = db.execute("SELECT id, user_id, text, date, rating FROM reviews WHERE user_id=:user_id AND book_id=:book_id", {"user_id": session["user_id"], "book_id": book_id}).fetchall()

        user_review = add_star_img(user_review)
        user_review = form_time(user_review)

    return render_template("book_details.html", book=book, reviews=reviews, good_reads=good_reads, user_review=user_review)


@app.route("/review/<book_id>", methods=["POST"])
def add_review(book_id):
    """ Adds a user's book review to the database """

    # If user not logged in return to book page:
    if session.get("user_id") == None:
        flash("You must be logged in to leave a review!")
        return redirect(f"/book_details/{book_id}")

    # Get review details and check they are valid:
    review_text = request.form.get("review_text")
    review_score = request.form.get("review_score")

    # If no review text or no review score return to book_details:
    if not review_text or not review_score:
        flash("Please provide review text and score to submit a review!")
        return redirect(f"/book_details/{book_id}")

    # Check that score is a valid int:
    try:
        review_score = int(review_score)
    except ValueError:
        flash("Please provide a valid review score in the range 1-5!")
        return redirect(f"/book_details/{book_id}")

    # Check the user has not already reviewed this book:
    if db.execute("SELECT * FROM reviews WHERE user_id=:user_id AND book_id=:book_id", {"user_id": session["user_id"], "book_id": book_id}).fetchone():
        flash("You have already reviewed this book - please edit your current review instead!")
        return redirect(f"/book_details/{book_id}")

    # Otherwise add the review to database, update the book's score and return to the book page:
    db.execute("INSERT INTO reviews (user_id, book_id, text, rating, date) VALUES(:user_id, :book_id, :text, :rating, CURRENT_TIMESTAMP(0))", {"user_id": session["user_id"], "book_id": book_id, "text": review_text, "rating": review_score})

    # Update books table with review count and avg review score:
    book_reviews = db.execute("SELECT COUNT(*), AVG(rating) FROM reviews WHERE book_id=:book_id", {"book_id": book_id}).fetchall()

    num_reviews = book_reviews[0][0]
    avg_review = round(float(book_reviews[0][1]),2)

    db.execute("UPDATE books SET review_count=:review_count, average_rating=:average_rating WHERE id=:book_id", {"review_count": num_reviews, "average_rating": avg_review, "book_id": book_id})

    # Update a user's number of reviews:
    db.execute("UPDATE users SET num_reviews = num_reviews + 1 WHERE id=:id", {"id": session["user_id"]})

    db.commit()

    # Return to book details page:
    flash("Thank you for your review! It has been added to the READ-RATE database.")
    return redirect(f"/book_details/{book_id}")


@app.route("/edit_review/<book_id>", methods=["POST"])
def edit_review(book_id):
    """ Edit a user's book review in the database """

    # If user not logged in return to book page:
    if session.get("user_id") == None:
        flash("You must be logged in to edit a review!")
        return redirect(f"/book_details/{book_id}")

    # Get review details and check they are valid:
    review_text = request.form.get("review_text")
    review_score = request.form.get("review_score")

    # If no review text or no review score return to book_details:
    if not review_text or not review_score:
        flash("Please provide review text and score to edit a review!")
        return redirect(f"/book_details/{book_id}")

    # Check that score is a valid int:
    try:
        review_score = int(review_score)
    except ValueError:
        flash("Please provide a valid review score in the range 1-5!")
        return redirect(f"/book_details/{book_id}")

    # Check the user has already reviewed this book:
    if not db.execute("SELECT * FROM reviews WHERE user_id=:user_id AND book_id=:book_id", {"user_id": session["user_id"], "book_id": book_id}).fetchone():
        flash("You not yet reviewed this book - please submit a review instead!")
        return redirect(f"/book_details/{book_id}")

    # Otherwise update the review in the database, update the book's score and return to the book page:
    db.execute("UPDATE reviews SET text=:text, rating=:rating, date=CURRENT_TIMESTAMP(0) WHERE user_id=:user_id AND book_id=:book_id", {"user_id": session["user_id"], "book_id": book_id, "text": review_text, "rating": review_score})

    # Update books table with review count and avg review score:
    book_reviews = db.execute("SELECT COUNT(*), AVG(rating) FROM reviews WHERE book_id=:book_id", {"book_id": book_id}).fetchall()

    num_reviews = book_reviews[0][0]
    avg_review = round(float(book_reviews[0][1]),2)

    db.execute("UPDATE books SET review_count=:review_count, average_rating=:average_rating WHERE id=:book_id", {"review_count": num_reviews, "average_rating": avg_review, "book_id": book_id})

    db.commit()

    # Return to book details page:
    flash("Your review has been updated!")
    return redirect(f"/book_details/{book_id}")


@app.route("/delete/<book_id>", methods=["POST"])
def delete_review(book_id):
    """ Delete a user's Review From the Database"""

    # If user not logged in return to book page:
    if session.get("user_id") == None:
        flash("You must be logged in to delete a review!")
        return redirect(f"/book_details/{book_id}")

    # Remove user's review for the book from the database:
    db.execute("DELETE FROM reviews WHERE user_id=:user_id AND book_id=:book_id" , {"user_id": session["user_id"], "book_id": book_id})

    # Update books table with review count and avg review score:
    book_reviews = db.execute("SELECT COUNT(*), AVG(rating) FROM reviews WHERE book_id=:book_id", {"book_id": book_id}).fetchall()

    num_reviews = book_reviews[0][0]
    avg_review = round(float(book_reviews[0][1]),2)

    db.execute("UPDATE books SET review_count=:review_count, average_rating=:average_rating WHERE id=:book_id", {"review_count": num_reviews, "average_rating": avg_review, "book_id": book_id})

    # Update a user's number of reviews:
    db.execute("UPDATE users SET num_reviews = num_reviews - 1 WHERE id=:id", {"id": session["user_id"]})

    db.commit()

    # Return to book details page:
    flash("Your review has been removed!")
    return redirect(f"/book_details/{book_id}")


@app.route("/user_details/<user_id>")
def user_details(user_id):
    """Display all the reviews written by a single user"""

    # Get the username of the user:
    username = db.execute("SELECT username FROM users WHERE id=:user_id", {"user_id": user_id}).fetchone()

    # If username does not exist return to homepage with apology:
    if not username:
        flash("Sorry but this user does not exist!")
        return redirect("/")

    # Get all reviews by the user reviewer details for the Book:
    reviews = db.execute("SELECT users.username, books.id, books.isbn, reviews.date, books.title, books.author, reviews.text, reviews.rating FROM users INNER JOIN reviews ON users.id=reviews.user_id INNER JOIN books ON reviews.book_id = books.id WHERE users.id=:user_id ORDER BY reviews.date DESC", {"user_id": user_id}).fetchall()

    reviews = add_star_img(reviews)
    reviews = form_time(reviews)

    return render_template("user_details.html", username=username, reviews=reviews)


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

@app.route("/recommended")
def recommended():
    """ Gets some simple book recommendations for a user based on their reviews """

    # If user not logged in return to home page:
    if session.get("user_id") == None:
        flash("You must be logged in to get book recommendations!")
        return redirect("/")

    author_rec = None
    books_rec = None

    # Pick a book that the user has reviewed 4-5 stars, and if the author has some other books, recommend up to 6 of them to the user:

    author_rec = db.execute("SELECT * FROM books WHERE author IN (SELECT books.author FROM books INNER JOIN reviews ON books.id=reviews.book_id WHERE reviews.user_id=:user_id AND reviews.rating >= 4 ORDER BY RANDOM() LIMIT 1) AND id NOT IN (SELECT book_id FROM reviews WHERE user_id=:user_id) ORDER BY RANDOM() LIMIT 6", {"user_id": session["user_id"]}).fetchall()

    author_rec = add_star_img(author_rec)

    # Pick a book that the user has reviewed highly, find users that also reviewed this book highly, and find other books they enjoyed:
    hr_book = db.execute("SELECT books.id, books.title, books.author FROM books INNER JOIN reviews ON books.id=reviews.book_id WHERE reviews.user_id=:user_id AND reviews.rating >= 4 ORDER BY RANDOM() LIMIT 1", {"user_id": session["user_id"]}).fetchone()

    if hr_book:
        books_rec = db.execute("SELECT * FROM books WHERE id IN (SELECT book_id FROM reviews WHERE user_id IN (SELECT user_id FROM reviews WHERE book_id=:book_id AND rating >=4 AND user_id!=:user_id) AND book_id!=:book_id GROUP BY book_id ORDER BY AVG(rating) DESC LIMIT 6)", {"book_id": hr_book[0], "user_id": session["user_id"]}).fetchall()

        books_rec = add_star_img(books_rec)

    return render_template("recommended.html", author_rec=author_rec, hr_book=hr_book, books_rec=books_rec)


@app.route("/account", methods=["GET", "POST"])
def account():
    """Let users change account password and delete their account"""

    # If user not logged in return to home page:
    if session.get("user_id") == None:
        flash("You must be logged in to access account settings!")
        return redirect("/")

    # User reached route via POST (by submitting password change form):
    if request.method == "POST":

        # Get input from form:
        curr_pass = request.form.get("curr-pass")
        new_pass = request.form.get("new-pass")
        confirm = request.form.get("check-pass")

        # Check input fields are correct:
        if not curr_pass or not new_pass or new_pass != confirm:
            flash("Please fill in all password fields!")
            return render_template("account.html")

        # Get current password hash to check it matches:
        logged_pass = db.execute("SELECT hash FROM users WHERE id=:id", {"id": session["user_id"]}).fetchone()[0]

        if not check_password_hash(logged_pass, curr_pass):
            flash("Incorrect current password entered, please try again!")
            return render_template("account.html")

        # Ensure password meets password requirements
        elif not validate_pass(new_pass):
            flash("New password does not meet requirements - must be at least eight chars long including one number and one letter!")
            return render_template("account.html")

        # Otherwise generate new password hash and update the password hash in DBfor this user:
        new_pass_hash = generate_password_hash(new_pass)
        db.execute("UPDATE users SET hash = :new_pass_hash WHERE id = :id", {"new_pass_hash": new_pass_hash, "id": session["user_id"]})

        db.commit()

        flash('Password successfully updated!')
        return redirect("/")

    # User reached route via GET (as by clicking acount link)
    else:
        return render_template("account.html")


@app.route("/delete_account", methods=["POST"])
def delete_account():
    """Deletes a users account and all their reviews from the database"""

    # If user not logged in return to home page:
    if session.get("user_id") == None:
        flash("You must be logged in to delete your account!")
        return redirect("/")

    # Check user has input their password correctly:
    del_pass = request.form.get("del-pass")

    logged_pass = db.execute("SELECT hash FROM users WHERE id=:id", {"id": session["user_id"]}).fetchone()[0]

    if not check_password_hash(logged_pass, del_pass):
        flash("Incorrect password entered for account deletion. Please try again.")
        return render_template("account.html")

    # Get all of a user's reviews from the database:
    book_ids = db.execute("SELECT book_id FROM reviews WHERE user_id=:user_id", {"user_id": session["user_id"]}).fetchall()

    # Delete all of the user's reviews:
    db.execute("DELETE FROM reviews WHERE user_id=:user_id", {"user_id": session["user_id"]})

    # Update all of the book avg scores in books table that have had reviews deleted:
    for book_id in book_ids:
        book_reviews = db.execute("SELECT COUNT(*), AVG(rating) FROM reviews WHERE book_id=:book_id", {"book_id": book_id[0]}).fetchall()

        num_reviews = book_reviews[0][0] or 0
        avg_review = round(float(book_reviews[0][1] or 0),2)

        db.execute("UPDATE books SET review_count=:review_count, average_rating=:average_rating WHERE id=:book_id", {"review_count": num_reviews, "average_rating": avg_review, "book_id": book_id[0]})

    # Remove the user from the user's table:
    db.execute("DELETE FROM users WHERE id=:user_id", {"user_id": session["user_id"]})
    db.commit()

    # Log out user and return to homepage:
    session.clear()
    flash("Your account has been deleted and you have been logged out. Thank you for using READ-RATE!")
    return redirect("/")

@app.route("/api/<isbn>")
def book_api(isbn):
    """Get a book from the database using its ISBN"""

    # Try and get book from the database:
    book = db.execute(('SELECT * '
                       'FROM books '
                       'WHERE isbn = :isbn'), {"isbn":isbn}).fetchall()

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
        return jsonify({"error": "Book ISBN is not in READ-RATE Database"}), 404

    return book[0][2]


# Error Handler:
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    flash(f"Internal Server Error! {e.name}, {e.code}")
    return redirect("/")


# Handle static files from root:
@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
