""" Helper functions for READ-RATE applications """

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


def validate_pass(password):
    """Checks password string for minimum length and a least one number and one letter"""

    if len(password) < 8:
        return False

    letter = False
    number = False
    numbers = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    letters = list(map(chr, range(97, 123)))

    for i in range(len(password)):
        if password[i] in numbers:
            number = True
        if password[i].lower() in letters:
            letter = True

    if letter and number:
        return True
    else:
        return False


def form_time(review_list):
    """Function takes a list of reviews and formats the review date from a timestamp to 01 Jan 2019 etc """

    for review in review_list:

        print(type(review[3]))

        review[3] = review[3].strftime('%d %b %Y')

    return review_list