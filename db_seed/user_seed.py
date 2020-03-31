# Seeds User Database with Users and then posts 10-20 random reviews per user
import os
import csv
import random

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

print("Adding users to users table")
# Add each user to the user table in the database:
for name in namelist:

  # Check username not already in database:
  username_test = db.execute("SELECT * FROM users WHERE username = :username", {"username": name}).fetchall()

  # If username is unique then add to database:
  if not username_test:

    hash_pass = generate_password_hash("autouserpassword\"3$5^")

    db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", {"username": name, "hash": hash_pass})

    #print(f"Added user: {name} to users table.")

  else:
    print(f"Username: {name} already in use! Not added to users table.")

  db.commit()

print("User import completed!")


