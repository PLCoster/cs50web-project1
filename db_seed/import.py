
# Imports Data from books.csv into books table in DB:
import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

print("Importing Books")

# Open books csv file
f = open("books.csv")
reader = csv.reader(f)

# Skip Header
next(reader)

for isbn, title, author, year in reader:

  # Add each book to books table
  db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", {"isbn": isbn, "title": title, "author": author, "year": year})

  #print(f"Added book: {title} by {author}, ISNB: {isbn}, Published: {year}.")
db.commit()

print("Book Import Complete!")