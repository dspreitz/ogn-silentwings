from app.model import Contest
from app import db


# This function prints all available contests and classes
def glidertracker_contests():
    result_string = list()

    for contest in db.session.query(Contest):
        for contest_class in contest.classes:
            if contest_class.type is None: 
                print("None")
            
            else:
                result_string.append(contest_class.name)
                print("ID = {}: {} - Class: {}".format(contest_class.id, contest_class.contest.name, contest_class.name))
            
    """
    for contest in db.session.query(Contest):
        print(contest)
        for contest_class in contest.classes:
            print(contest_class)
                for task in contest_class.tasks:
                    print(task)
    """    

    return result_string
