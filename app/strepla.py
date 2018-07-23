import requests
import json
from app.utils import ogn_check
from datetime import datetime
from app.model import Contest, ContestClass, Contestant, Pilot, Task, Location, Turnpoint
# from sqlalchemy.sql.expression import true


def list_strepla_contests():
    url = "http://www.strepla.de/scs/ws/competition.ashx?cmd=recent&daysPeriod=700"
    r = requests.get(url)
    json_data = json.loads(r.text.encode('utf-8'))

    print("\nID : Name of past competition - Place of competition")
    print("=================================================================")
    for contest_row in json_data:
        print("{id}: {name} - {Location}".format(**contest_row))

    url = "http://www.strepla.de/scs/ws/competition.ashx?cmd=active&daysPeriod=-1"
    r = requests.get(url)
    # print(r)
    json_data = json.loads(r.text.encode('utf-8'))

    print("\nID : Name of future competition - Place of competition")
    print("=================================================================")
    for contest_row in json_data:
        print("{id}: {name} - {Location}".format(**contest_row))


def get_strepla_contest_body(competition_id):
    contest_url = "http://www.strepla.de/scs/ws/competition.ashx?cmd=info&cId=" + str(competition_id)
    # print(contest_url)
    r = requests.get(contest_url)
    # Test if contest is present
    if (len(r.text)) == 2:
        raise ValueError("This contest does not exist: '{}' Aborting.".format(competition_id))
        return

    contest_data = json.loads(r.text.encode('utf-8'))[0]

    # Process contest location and date info
    parameters = {'end_date': datetime.strptime(contest_data['lastDay'], "%Y-%m-%dT%H:%M:%S"),
                  'name': contest_data['name'],
                  'start_date': datetime.strptime(contest_data['firstDay'], "%Y-%m-%dT%H:%M:%S")}
    contest = Contest(**parameters)

    parameters = {'name': contest_data['Location']}
    location = Location(**parameters)
    contest.location = location

    # Process contest class info
    contest_class_url = "http://www.strepla.de/scs/ws/compclass.ashx?cmd=overview&cid=" + str(competition_id)
    # print(contest_class_url)
    r = requests.get(contest_class_url)
    contest_class_data = json.loads(r.text.encode('utf-8'))

    for contest_class_row in contest_class_data:
        parameters = {'category': contest_class_row['rulename'],
                      'type': contest_class_row['name'],
                      'name': contest_class_row['name']}

        contest_class = ContestClass(**parameters)
        contest_class.contest = contest

        # Process pilots of class
        contestant_url = "http://www.strepla.de/scs/ws/pilot.ashx?cmd=competitors&cId=" + str(competition_id) + "&cc=" + str(contest_class_row['name'])
        print(contestant_url)
        r = requests.get(contestant_url)
        contestant_data = json.loads(r.text.encode('utf-8'))
        if (len(contestant_data) == 0):
            print("Class name not recognized. Aborting.")
            return

        # Check if we have access to the pilot info
        if 'msg' in contestant_data:
            print("=================================\nNo competitors for contest found, please check access rights. \nSkipping import of pilot info.\n=================================")
            continue
            
        for contestant_row in contestant_data:
            parameters = {'aircraft_model': contestant_row['glider_name'],
                          'aircraft_registration': contestant_row['glider_callsign'],
                          'contestant_number': contestant_row['glider_cid'],
                          'handicap': contestant_row['glider_index'],
                          'live_track_id': ogn_check(contestant_row['glider_callsign'], contestant_row['flarm_ID'])}

            contestant = Contestant(**parameters)
            contestant.contest_class = contest_class

            parameters = {'first_name': contestant_row['name'].rsplit(',', 1)[1].replace(' ',""),
                          'last_name': contestant_row['name'].rsplit(',', 1)[0].replace(' ',""),
                          'nationality': contestant_row['country']}
            pilot = Pilot(**parameters)
            pilot.contestant = contestant

    return contest


def get_strepla_class_tasks(competition_id, contest_class_name):
    # This function reads the tasks from a specific contest and class
    # TODO: Include example URL
    # TODO: Generate useful error message, if arguments are not provided
    all_task_url = "https://www.strepla.de/scs/ws/results.ashx?cmd=overviewDays&cID=" + str(competition_id) + "&cc=" + str(contest_class_name)
    r = requests.get(all_task_url)
    all_task_data = json.loads(r.text.encode('utf-8'))
    tasks = list()
    for all_task_data_item in all_task_data:
        # print(task_data_item)
        # print(all_task_data_item['idCD'], all_task_data_item['date'], all_task_data_item['state'])
        if int(all_task_data_item['state']) == 0:
            print("Task not planned for day " + all_task_data_item['date'] + ". Skipping.")
            continue

        if int(all_task_data_item['state']) == 60:
            print(all_task_data_item['date'],": Task neutralized for day. Skipping.")
            continue

        task_url = "http://www.strepla.de/scs/ws/results.ashx?cmd=task&cID=" + str(competition_id) + "&idDay=" + str(all_task_data_item['idCD']) + "&activeTaskOnly=true"
        # print(task_url)
        r = requests.get(task_url)
        if r.status_code != 200:
            print("Error occured while loading task. Competition id: {} idDay = {}".format(competition_id, all_task_data_item['idCD']))
            break

        task_data = json.loads(r.text.encode('utf-8'))
        print("=================================\n",all_task_data_item['date'],"\n",task_data,"\n=================================")
        
        for task_data_item in task_data['tasks']:
            # print(task_data['activeTask'])
            if int(task_data['activeTask']) != int(task_data_item['id']):
                print('Task ID: ', task_data_item['id'], '- This is a passive task, Skipping..')
                continue
            else:
                print('Task ID: ', task_data_item['id'], '- This is an active task. Processing it.')
            
            # print(task_data_item)
            parameters = {'result_status': all_task_data_item['state'],
                          'task_date': datetime.strptime(all_task_data_item['date'], "%Y-%m-%dT%H:%M:%S"),
                          'task_distance': task_data_item['distance'].replace(' km', '')}

            task = Task(**parameters)

            point_index = 0
            for tps in task_data_item['tps']:
                # print("=== tps ===")
                # print(tps)
                if tps['scoring']['type'] == 'LINE':
                    parameters = {'oz_line': True,
                                  'type': 'start',
                                  'oz_radius1': tps['scoring']['width'] / 2}

                elif tps['scoring']['type'] == 'AAT SECTOR':
                    parameters = {'type': 'point',
                                  'oz_radius1': tps['scoring']['radius'],
                                  'oz_radius2': 0,
                                  'oz_angle1': tps['scoring']['radial1'],
                                  'oz_angle2': tps['scoring']['radial2'],
                                  'oz_type': 'symmetric',
                                  'oz_line': False,
                                  'oz_move': False,
                                  'oz_reduce': False}

                elif tps['scoring']['type'] == 'KEYHOLE':
                    parameters = {'type': 'point',
                                  'oz_radius1': tps['scoring']['radiusSector'],
                                  'oz_radius2': tps['scoring']['radiusCylinder'],
                                  'oz_angle1': tps['scoring']['angle'] / 2,
                                  'oz_angle2': 180,
                                  'oz_type': 'symmetric',
                                  'oz_line': False,
                                  'oz_move': False,
                                  'oz_reduce': False}

                    # print("Keyhole TP recognizes.")

                elif tps['scoring']['type'] == 'CYLINDER':
                    parameters = {'type': 'point',
                                  'oz_radius1': tps['scoring']['radius'],
                                  'oz_radius2': 0,
                                  'oz_angle1': 180,
                                  'oz_angle2': 0,
                                  'oz_type': 'symmetric',
                                  'oz_line': False,
                                  'oz_move': False,
                                  'oz_reduce': False}

                    # print("Cylinder TP recognizes.")

                tp_parameters = {'name': tps['tp']['name'],
                                 'latitude': tps['tp']['lat'],
                                 'longitude': tps['tp']['lng'],
                                 'point_index': point_index}

                point_index += 1
                parameters.update(tp_parameters)
                turnpoint = Turnpoint(**parameters)
                # print("=== Turnpoint ===")
                # print(turnpoint.c_igc())
                turnpoint.task = task
                # TODO: Identify task type AAT somehow here

            # task.contest_class = contest_class
            # print(task)
            tasks.append(task)

    return tasks


def get_strepla_contest_all(cID):
    contest = get_strepla_contest_body(cID)
    for contest_class in contest.classes:
        tasks = get_strepla_class_tasks(cID, contest_class.type)
        contest_class.tasks = tasks

    return contest


# Get classes for a specific contest
# https://www.strepla.de/scs/ws/compclass.ashx?cmd=overview&competition_id=403
def get_strepla_contest_classes(cID):
    url = "http://www.strepla.de/scs/ws/compclass.ashx?cmd=overview&cID=" + str(cID)
    r = requests.get(url)
    data = json.loads(r.text.encode('utf-8'))

    for row in data:
        print(row)


def get_strepla_contestants(cID, cc=None):
    import urllib
    # Get contestants of entire competition
    # https://www.strepla.de/scs/ws/pilot.ashx?cmd=competitors&cId=403
    if cc is not None:
        ccc = cc[0]
        with urllib.request.urlopen("https://www.strepla.de/scs/ws/pilot.ashx?cmd=competitors&cId=" + str(cID) + "&cc=" + str(ccc)) as url:
            data = json.loads(url.read().decode())
            if (len(data) == 0):
                print("Class name not recognized. Aborting")
                return

            i = 0
            while i < len(data):
                data_dict = data[i]
                # print(data_dict)
                print(str(data_dict['glider_callsign']) + ": " + str(data_dict['logger1']) + " - " + str(data_dict['name']))
                i += 1

    # Get contestants of specific class
    # https://www.strepla.de/scs/ws/pilot.ashx?cmd=competitors&cId=403&cc=18m
    else:
        with urllib.request.urlopen("https://www.strepla.de/scs/ws/pilot.ashx?cmd=competitors&cId=" + str(cID)) as url:
            data = json.loads(url.read().decode())
            i = 0
            while i < len(data):
                data_dict = data[i]
                # print(data_dict)
                i += 1

# Get List of contest days
# https://www.strepla.de/scs/ws/results.ashx?cmd=overviewDays&cID=403&cc=18m

# Get task of specific day of specific contest
# https://www.strepla.de/scs/ws/results.ashx?cmd=task&cID=400&idDay=5917&activeTaskOnly=false
