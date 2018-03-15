from app.model import Contest, ContestClass
from app import db


def create_active_contests_string():
    result_string = ""
    for contest in db.session.query(Contest):
        for contest_class in contest.classes:
            short_name = contest.name.replace(" ", "").upper() + "_" + contest_class.category.replace("_", "")
            long_name = contest.name + " " + contest_class.category
            result_string += "{{contestname}}{0}{{/contestname}}".format(short_name)
            result_string += "{{contestdisplayname}}{0}{{/contestdisplayname}}".format(long_name)
            result_string += "{{datadelay}}{0}{{/datadelay}}".format(15)
            result_string += "{{utcoffset}}{0}{{/utcoffset}}".format("+01:00")
            result_string += "{{countrycode}}{0}{{/countrycode}}".format(contest.country)
            result_string += "{{site}}{0}{{/site}}".format(contest.location.name)
            result_string += "{{fromdate}}{0}{{/fromdate}}".format(contest.start_date.strftime("%Y%m%d"))
            result_string += "{{todate}}{0}{{/todate}}".format(contest.end_date.strftime("%Y%m%d"))
            result_string += "{{lat}}{0}{{/lat}}".format(contest.location.latitude)
            result_string += "{{lon}}{0}{{/lon}}".format(contest.location.longitude)
            result_string += "{{alt}}{0}{{/alt}}".format(contest.location.altitude if contest.location.altitude is not None else '')

    return result_string


# GET /getcontestinfo?contestname=LIVE&date=20171104&username=ogn&cpassword=ecbad38d0b5a3cf6482e661028b2c60c HTTP/1.1
def create_contest_info_string(contest_name_with_class_category):
    result_string = ""
    contest_name = contest_name_with_class_category.partition("_")[0]
    short_name = contest_name.replace(" ", "").upper()
    contest_class_category = contest_name_with_class_category.partition("_")[2]

    for contest in db.session.query(Contest).filter(ContestClass.category == contest_class_category):
        if contest.name.replace(" ", "").upper() == short_name:
            for task in contest.classes[0].tasks:
                result_string += "{{date}}{0}{{/date}}".format(task.task_date.strftime("%Y%m%d"))
                result_string += "{{task}}{0}{{/task}}".format(1)
                result_string += "{{validday}}{0}{{/validday}}".format(0)
                # "{date}20050903{/date}{task}1{/task}{validday}0{/validday}{date}20050904{/date}{task}1{/task}{validday}0{/validday}\

    return result_string
