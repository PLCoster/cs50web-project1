# Seeds User Database with Users and then posts 10-20 random reviews per user
import os
import csv
import random
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

namelist = []

# Load Names from Two CSV Files into namelist:
f = open("names1.csv")
reader = csv.reader(f)
for line in reader:
  namelist.append(line[2])
f.close()

f = open("names2.csv")
reader = csv.reader(f)
for line in reader:
  namelist.append(line[2])
f.close()


one_star = ["Hated it!", "Worst book I've read in a while!", "Did not enjoy this book at all.", "Had to return the book as I found it completely unreadable.", "Would not recommend this book to anyone."]

two_star = ["Didn't really like the book.", "Not the right book for me", "Fans of the genre might like it but I did not enjoy it.", "Not my favorite read.", "Below Average!"]

three_star = ["Book was okay for me, I think fans of the genre would really enjoy it!", "I enjoyed the book although some aspects could be better!", "Pretty average but enjoyable!", "Not a bad read at all", "Quite enjoyable, would recommend to pick up if on sale."]

four_star = ["Really enjoyed this book", "A great read, looking forward to reading again in the future", "Great book that might interest those who don't normally enjoy this genre.", "Very well written book on the subject!", "One of the better books I have read this year!"]

five_star = ["Fantastic - already reading again!", "Enjoyed this book so much, I would recommend to all my friends and family", "If you read one book this year, read this one!", "An absolute masterpiece - full marks.", "Can't wait to read the next book by this author!"]

review_map = {1 : one_star, 2 : two_star, 3 : three_star, 4 : four_star, 5: five_star}

# Create 10-20 random reviews for a random book for each user:
for name in namelist:

  # Get user_id and review_count:
  user = db.execute("SELECT * FROM users WHERE username = :username", {"username": name}).fetchall()

  user_id = user[0][0]
  user_reviews = user[0][3]

  for rev_num in range(random.randint(10, 20)):
    user_reviews += 1

    # Generate random review rating
    rev_rating = random.randint(1, 5)

    rev_text = review_map[rev_rating][random.randint(0, 4)]

    # Get a random book ID and review count:
    book = db.execute("SELECT * FROM books ORDER BY RANDOM() LIMIT 1").fetchall()

    book_id = book[0][0]

    now = datetime.now()
    date = now.date()
    print(date)
    time = now.strftime("%H:%M:%S")

    # Generate a semi-random review date


    print(name, user_id, user_reviews, rev_rating, rev_text)





