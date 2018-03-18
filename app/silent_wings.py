from app.model import Contest, Contestant
from app import db


def create_active_contests_string():
    result_string = ""
    for contest in db.session.query(Contest):
        for contest_class in contest.classes:
            short_name = contest.name.replace(" ", "").upper() + "_" + contest_class.type.replace("_", "").replace("-", "").upper()
            long_name = contest.name + " " + contest_class.type
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
            result_string += "{{alt}}{0}{{/alt}}\n".format(contest.location.altitude if contest.location.altitude is not None else '')

    return result_string


# GET /getcontestinfo?contestname=LIVE&date=20171104&username=ogn&cpassword=ecbad38d0b5a3cf6482e661028b2c60c HTTP/1.1
def create_contest_info_string(contest_name_with_class_type):
    result_string = ""
    contest_name = contest_name_with_class_type.partition("_")[0]
    short_name = contest_name.replace(" ", "").upper()
    contest_class_type = contest_name_with_class_type.partition("_")[2]

    for contest in db.session.query(Contest):
        for contest_class in contest.classes:
            if contest.name.replace(" ", "").upper() == short_name and contest_class.type.replace("_", "").replace("-", "").upper() == contest_class_type:
                for task in contest.classes[0].tasks:
                    result_string += "{{date}}{0}{{/date}}".format(task.task_date.strftime("%Y%m%d"))
                    result_string += "{{task}}{0}{{/task}}".format(1)
                    result_string += "{{validday}}{0}{{/validday}}\n".format(0)
                    # "{date}20050903{/date}{task}1{/task}{validday}0{/validday}{date}20050904{/date}{task}1{/task}{validday}0{/validday}\

    return result_string

def create_cuc_block():
    cuc_header = """[Options]
    Title=Angel Casado OGN-SGP test
    PeriodFrom=0
    PeriodTo=401521
    AvtoSaveFlight=True
    AvtoSaveTime=60
    AvtoPublishTime=-300
    TakeoffAlt=0m
    TaskPicWidth=600
    TaskPicHeight=400
    TaskPicCompression=90
    TaskPicBorder=12
    UtcOffset=1
    NeedLegs=False
    StrictName=False
    UseBinFiles=True
    CommentPrefix=1

    [Warnings]
    HighEnl=300
    AsViolate=True
    MinFinAlt=0m
    MaxFinAlt=10000m
    MaxStartAlt=0m
    MaxAlt=0m
    MaxAltCorr=50.0m
    AltTimeout=0
    StartGsp=0km/h
    FixRate=10
    ValFailed=True

    [SearchPath]
    \\psf\Home\Desktop\Flights\ \n

    """
    cuc_footer = """\n[Starts]\n

    [Day_02/03/2016]
    D02032016-010400000
    
    V,HighEnl=300,AsViolate=True,MinFinAlt=0m,MaxFinAlt=10000m,MaxStartAlt=0m,MaxAlt=0m,MaxAltCorr=50.0m,AltTimeout=0,StartGsp=0km/h,FixRate=10,ValFailed=True
    C301299000000301299000003
    C4223150N00151500ELa Cerdanya - LECD
    C4223150N00151500ELa Cerdanya - LECD
    C4234110N00044360WSanta Cilia - LECI
    C4206290N00028590EBenabarre
    C4203020N00117320EOliana
    C4223150N00151500ELa Cerdanya - LECD
    C4223150N00151500ELa Cerdanya - LECD
    TSK,WpDis=True,MinDis=True,NearDis=0.5km,NearAlt=200.0m,MinFinAlt=0.0km
    XTest day
    E000,0,,,0,0,-1,-1,-1,-1,0,0,-1,-1,0,0,-1,-1,0,0,"",-1,-1,"",-1,,,,,,
    E001,0,,,0,0,-1,-1,-1,-1,0,0,-1,-1,0,0,-1,-1,0,0,"",-1,-1,"",-1,,,,,,
    E002,0,,,0,0,-1,-1,-1,-1,0,0,-1,-1,0,0,-1,-1,0,0,"",-1,-1,"",-1,,,,,,
    E003,0,,,0,0,-1,-1,-1,-1,0,0,-1,-1,0,0,-1,-1,0,0,"",-1,-1,"",-1,,,,,,
    E004,0,,,0,0,-1,-1,-1,-1,0,0,-1,-1,0,0,-1,-1,0,0,"",-1,-1,"",-1,,,,,,
    E005,0,,,0,0,-1,-1,-1,-1,0,0,-1,-1,0,0,-1,-1,0,0,"",-1,-1,"",-1,,,,,,
    """
    print("create_cuc_block was called")
    print("============================")
    print(cuc_header + create_cuc_pilots_block() + cuc_footer)
    print("============================")
    return cuc_header + create_cuc_pilots_block() + cuc_footer

def create_cuc_pilots_block():
    result_list = list()
    result_list.append("[Pilots]")

    for contestant in db.session.query(Contestant):
        pilot = contestant.pilots[0]

        entry_dict = {'first_name': pilot.first_name,
                      'last_name': pilot.last_name,
                      'live_track_id': contestant.live_track_id,
                      'aircraft_model': contestant.aircraft_model,
                      'aircraft_registration': contestant.aircraft_registration,
                      'contestant_number': contestant.contestant_number}

        entry = '"{first_name}","{last_name}",123,"{live_track_id}","{aircraft_model}","{aircraft_registration}","{contestant_number}","",0,"",0,"",1,"",""'.format(**entry_dict)
        result_list.append(entry)

    return "\n".join(result_list)
