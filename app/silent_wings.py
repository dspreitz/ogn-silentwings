from app.model import Contest, Contestant, Beacon
from app import db

from datetime import timezone
from app.model.contestant import Contestant
from app.model.turnpoint import Turnpoint
# from _asyncio import Task
from tests.test_soaringspot import turnpoints_document


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
                # TODO: Understand this and possibly correct.
                for task in contest.classes[0].tasks:
                    result_string += "{{date}}{0}{{/date}}".format(task.task_date.strftime("%Y%m%d"))
                    result_string += "{{task}}{0}{{/task}}".format(1)
                    result_string += "{{validday}}{0}{{/validday}}".format(1)
                    # "{date}20050903{/date}{task}1{/task}{validday}0{/validday}{date}20050904{/date}{task}1{/task}{validday}0{/validday}\

    return result_string


def create_tracker_data(tracker_id):
    result_list = list()
    result_list.append("{datadelay}6{/datadelay}")
    query = db.session.query(Beacon) \
        .filter(Beacon.address == tracker_id) \
        .order_by(Beacon.timestamp)

    for beacon in query:
        result_list.append("{0},{1},{2},{3},{4},1".format(
            beacon.address,
            int(beacon.timestamp.replace(tzinfo=timezone.utc).timestamp()),
            beacon.latitude,
            beacon.longitude,
            int(beacon.altitude)))

    return '\n'.join(result_list)


def create_cuc_pilots_block(contest_name_with_class_type):
    contest_name = contest_name_with_class_type.partition("_")[0]
    contest_class_type = contest_name_with_class_type.partition("_")[2]

    result_list = list()
    result_list.append("[Pilots]")

    for contestant in db.session.query(Contestant):
        # TODO: If multiple contests are in db this will fail. Implement if for contest name
        # print(contestant.contest_class.name.upper())
        if contestant.contest_class.name.upper() == contest_class_type:
            pilot = contestant.pilots[0]
            entry_dict = {'first_name': pilot.first_name,
                          'last_name': pilot.last_name,
                          'live_track_id': contestant.live_track_id,
                          'aircraft_model': contestant.aircraft_model,
                          'aircraft_registration': contestant.aircraft_registration,
                          'contestant_number': contestant.contestant_number}
    
            # TODO: Fix encoding so that umlaute are properly displayed in SWV
            entry = '"{first_name}","{last_name}",*0,"{live_track_id}","{aircraft_model}","{aircraft_registration}","{contestant_number}","",0,"",0,"",1,"",""'.format(**entry_dict)
            result_list.append(entry)

    result_list.append("\n[Starts]\n")
    print("\n".join(result_list))
    return "\n".join(result_list)

def create_cuc_tp_block(contest_name_with_class_type,date):
    import datetime
    contest_name = contest_name_with_class_type.partition("_")[0]
    contest_class_type = contest_name_with_class_type.partition("_")[2]
    # print(contest_class_type)
    n = 0
    result_list = list()
    for contest in db.session.query(Contest):
        for contest_class in contest.classes:
            if contest.name.replace(" ", "").upper() == contest_name and contest_class.type.replace("_", "").replace("-", "").upper() == contest_class_type:
                last_task = contest_class.tasks[-1]
                for turnpoint in last_task.turnpoints:
                    entry = turnpoint.c_igc()
                    result_list.append(entry)
                    
                    # Repeat first TP twice - This is is the start Point
                    if n == 0:
                        result_list.append(entry)
                    
                    n += 1
    
    # Write the last line twice - This is the finish point
    result_list.append(entry)
    
    
    # Definition of the IGC task file description
    # C D D M M Y Y H H M M S S F D F M F Y I I I I T T T E X T S T R I N G CR LF
    # C 3 0 1 2 9 9 0 0 0 0 0 0 3 0 1 2 9 9 0 0 0 0 0 3
    # Description          Size            Element            Remarks
    # Date                 6 bytes         DDMMYY             Valid characters 0-9
    # Time                 6 bytes         HHMMSS             Valid characters 0-9
    # Flight Date          6 bytes         FDFMFY             Valid characters 0-9
    # Task ID              4 bytes         IIII               Valid characters 0-9
    # of Task TPs          2 bytes         TT                 Valid characters 0-9
    
    # entry = "C301299000000301299000003"
    # Header line of IGC task file description is ignored by Silent Wings Viewer
    entry = "C" + date[6:8] + date[4:6] + date[2:4] + "000000" + date[6:8] + date[4:6] + date[2:4] + "0001" + str(n-1).zfill(2) + "\n"
    return entry + "\n".join(result_list)


def create_cuc(contestname, date):
    # import datetime
    result_list = list()
    # Generate Header of CUC file
    entry = "[Options]\nTitle=OGN-Silent Wings test\nPeriodFrom=0\nPeriodTo=401521\nAvtoSaveFlight=True\nAvtoSaveTime=60\nAvtoPublishTime=-300\nTakeoffAlt=0m\nTaskPicWidth=600\nTaskPicHeight=400\nTaskPicCompression=90\nTaskPicBorder=12\nUtcOffset=1\nNeedLegs=False\nStrictName=False\nUseBinFiles=True\nCommentPrefix=1\n\n[Warnings]\nHighEnl=300\nAsViolate=True\nMinFinAlt=0m\nMaxFinAlt=10000m\nMaxStartAlt=0m\nMaxAlt=0m\nMaxAltCorr=50.0m\nAltTimeout=0\nStartGsp=0km/h\nFixRate=10\nValFailed=True\n\n[SearchPath]\n\\psf\Home\Desktop\Flights\ \n"
    result_list.append(entry)

    # Generate [Pilot] Block of CUC file
    entry = create_cuc_pilots_block(contestname)
    result_list.append(entry)

    #  Generate [Date] Block of CUC file
    entry = "[Day_" + date[6:8] + "/" + date[4:6] + "/" + date[0:4] + "]\nD" + date[6:8] + date[4:6] + date[0:4] + "-010400000"
    result_list.append(entry)

    # Generate Footer of CUC file
    entry = "V,HighEnl=300,AsViolate=True,MinFinAlt=0m,MaxFinAlt=10000m,MaxStartAlt=0m,MaxAlt=0m,MaxAltCorr=50.0m,AltTimeout=0,StartGsp=0km/h,FixRate=10,ValFailed=True"
    result_list.append(entry)
    
    result_list.append(create_cuc_tp_block(contestname,date))
    # result_list.append("C4223150N00151500ELa Cerdanya - LECD\nC4223150N00151500ELa Cerdanya - LECD\nC4234110N00044360WSanta Cilia - LECI\nC4206290N00028590EBenabarre\nC4203020N00117320EOliana\nC4223150N00151500ELa Cerdanya - LECD\nC4223150N00151500ELa Cerdanya - LECD\n")
    result_list.append("TSK,WpDis=True,MinDis=True,NearDis=0.5km,NearAlt=200.0m,MinFinAlt=0.0km\nXTest day")
    entry = 'E000,0,,,0,0,-1,-1,-1,-1,0,0,-1,-1,0,0,-1,-1,0,0,"",-1,-1,"",-1,,,,,,\nE001,0,,,0,0,-1,-1,-1,-1,0,0,-1,-1,0,0,-1,-1,0,0,"",-1,-1,"",-1,,,,,,\nE002,0,,,0,0,-1,-1,-1,-1,0,0,-1,-1,0,0,-1,-1,0,0,"",-1,-1,"",-1,,,,,,\nE003,0,,,0,0,-1,-1,-1,-1,0,0,-1,-1,0,0,-1,-1,0,0,"",-1,-1,"",-1,,,,,,\nE004,0,,,0,0,-1,-1,-1,-1,0,0,-1,-1,0,0,-1,-1,0,0,"",-1,-1,"",-1,,,,,,\nE005,0,,,0,0,-1,-1,-1,-1,0,0,-1,-1,0,0,-1,-1,0,0,"",-1,-1,"",-1,,,,,,\n'
    result_list.append(entry)

    print("=========================")
    print("\n".join(result_list))
    print("=========================")
    return "\n".join(result_list)
