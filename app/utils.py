from datetime import date
import requests
import csv
from io import StringIO
from app import db


# Imports OGN DDB into dict
def ddb_import():
    ddb_url = "http://ddb.glidernet.org/download/"
    r = requests.get(ddb_url)
    rows = '\n'.join(i for i in r.text.splitlines() if i[0] != '#')
    data = csv.reader(StringIO(rows), quotechar="'", quoting=csv.QUOTE_ALL)

    ddb_entries = dict()
    for row in data:
        ddb_entries[row[1]] = row[3]

    return ddb_entries


def process_beacon(raw_message, reference_date=None):
    from ogn.parser import parse, ParseError
    if raw_message[0] != '#':
        try:
            message = parse(raw_message, reference_date)
        except NotImplementedError as e:
            print('Received message: {}'.format(raw_message))
            print(e)
            return None
        except ParseError as e:
            print('Received message: {}'.format(raw_message))
            print('Drop packet, {}'.format(e.message))
            return None
        except TypeError as e:
            print('TypeError: {}'.format(raw_message))
            return None
        except Exception as e:
            print(raw_message)
            print(e)
            return None

        if message['aprs_type'] == 'status' or message['beacon_type'] == 'receiver_beacon':
            return None
        else:
            subset_message = {k: message[k] for k in message.keys() & {'name', 'address', 'timestamp', 'latitude', 'longitude', 'altitude', 'track', 'ground_speed', 'climb_rate', 'turn_rate'}}
            return subset_message


def open_file(filename):
    """Opens a regular or unzipped textfile for reading."""
    import gzip
    f = open(filename, 'rb')
    a = f.read(2)
    f.close()
    if (a == b'\x1f\x8b'):
        f = gzip.open(filename, 'rt')
        return f
    else:
        f = open(filename, 'rt')
        return f


def logfile_to_beacons(logfile, reference_date=date(2015, 1, 1)):
    from .model import Beacon
    fin = open_file(logfile)
    beacons = list()
    for line in fin:
        message = process_beacon(line.strip(), reference_date=reference_date)
        if message is not None:
            beacon = Beacon(**message)
            beacons.append(beacon)

    fin.close()
    return beacons


# def gist_writer(gist_content_filter=None, task=None):
def gist_writer(task):
    from github3 import login
    from flasky import app

    # Provide login to Github via API token
    gh = login(token=app.config['API_TOKEN'])

    # Get Gist-ID from config
    gist_id = app.config['GIST_ID']

    # Generate the gist comment
    gist_comment = task.contest_class.contest.name.replace(" ", "").upper() + "_" + task.contest_class.type.replace("_", "").replace("-", "").upper()

    files = {}
    files_filter = {
        'filter': {
            'content': task.contest_class.gt_filter()
        }
    }
    files.update(files_filter)

    files_task = {
        'task': {
            'content': task.to_xml()
        }
    }
    files.update(files_task)

    if gist_id is None:
        # No Gist-ID provided, creating a new gist
        print('No Gist-ID provided, creating a new Gist.')
        gist = gh.create_gist(gist_comment, files, public=True)

    else:
        print("Gist-ID provided, modifying an existing gist.")
        # Get all gits ID of authenticated github user to check if gist ID is valid
        gists = [g.id for g in gh.gists()]
        if gist_id in gists:
            print("The GIST-ID you provided is valid.")
            gist = gh.gist(gist_id)

        else:
            # Gist-ID is not valid
            raise ValueError("This gist_id is not valid: '{}' Aborting.".format(gist_id))

        # Edit the gist
        gist.edit(gist_comment, files)

    contestants_filter_gist_url = "https://gist.github.com/" + str(gist.owner) + "/" + str(gist.id) + "/raw/filter"
    print("You filter Gist address is:  {}".format(contestants_filter_gist_url))
    # Update DB with gist content filter URL: active_task_gist_url
    # task.contest_class.contestants_filter_gist_url = contestants_filter_gist_url - not working as task is not known

    active_task_gist_url = "https://gist.github.com/" + str(gist.owner) + "/" + str(gist.id) + "/raw/task"
    print("You task Gist address is:  {}".format(active_task_gist_url))
    print("Your glidertracker.org URL is:\nhttp://glidertracker.org/#tsk={}&lst={}".format(active_task_gist_url, contestants_filter_gist_url))
    # Update DB with gist content filter URL: active_task_gist_url
    task.contest_class.active_task_gist_url = active_task_gist_url
    db.session.commit()

    return gist.html_url
