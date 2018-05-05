from app.model import Contest
from app import db


# This function prints all available contests and classes
def glidertracker_contests():
    result_string = list()

    for contest in db.session.query(Contest):
        for contest_class in contest.classes:
            result_string.append(contest_class.name)

            print("ID = {}: {} - Class: {}".format(contest_class.id, contest_class.contest.name, contest_class.type))

    return result_string
