# Seeds User Database with Users and then posts 10-20 random reviews per user
import os
import csv
import random

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

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

review_map = {1: one_star, 2: two_star, 3: three_star, 4: four_star, 5: five_star}

review_dist = {1 : 1, 2 : 2, 3 : 2, 4 : 3, 5: 3, 6: 3, 7: 4, 8: 4, 9: 5, 10: 5}

print("Adding reviews to the reviews database...")

# Create 10-20 random reviews for a random book for each user:
# for name in namelist:
for name in namelist:

  # Get user_id and review_count:
  user = db.execute("SELECT * FROM users WHERE username = :username", {"username": name}).fetchall()

  user_id = user[0][0]
  user_reviews = user[0][3]

  for rev_num in range(random.randint(10, 30)):
    user_reviews += 1

    # Generate random review rating
    rev_rating = review_dist[random.randint(1, 10)]

    rev_text = review_map[rev_rating][random.randint(0, 4)]

    # Get a random book ID not already reviewed by this user:
    book = db.execute("SELECT * FROM books WHERE id NOT IN (SELECT book_id FROM reviews WHERE user_id=:user_id) ORDER BY RANDOM() LIMIT 1", {"user_id": user_id}).fetchall()

    book_id = book[0][0]

    # Generate a semi-random review date
    year = str(2020)
    month = f'{random.randint(1, 3):02}'
    day = f'{random.randint(1, 28):02}'

    hr  = f'{random.randint(0, 23):02}'
    mins = f'{random.randint(0, 59):02}'
    sec = f'{random.randint(0, 59):02}'

    timestamp = year+"-"+month+"-"+day+" "+hr+":"+mins+":"+sec+"+00"

    # Insert Review into Reviews Table
    db.execute("INSERT INTO reviews (user_id, book_id, text, rating, date) VALUES(:user_id, :book_id, :text, :rating, :date)", {"user_id": user_id, "book_id": book_id, "text": rev_text, "rating":rev_rating, "date": timestamp})


    #print("Added Review: BookID: "+str(book_id)+", Review: "+rev_text+",Rating: "+str(rev_rating)+", Username: "+name)

    # Update books table with review count and avg review score:
    book_reviews = db.execute("SELECT COUNT(*), AVG(rating) FROM reviews WHERE book_id=:book_id", {"book_id": book_id}).fetchall()

    num_reviews = book_reviews[0][0]
    avg_review = round(float(book_reviews[0][1]),2)

    db.execute("UPDATE books SET review_count=:review_count, average_rating=:average_rating WHERE id=:book_id", {"review_count": num_reviews, "average_rating": avg_review, "book_id": book_id})


  # Update the number of reviews by a user in user table:
  db.execute("UPDATE users SET num_reviews=:num_reviews WHERE id=:id", {"num_reviews": user_reviews, "id": user_id})

db.commit()

print("Review import completed!")
