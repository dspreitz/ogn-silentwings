from datetime import date
import requests
import csv
from io import StringIO
from app import db


ddb_entries = None


# Imports OGN DDB into dict
def ddb_import():
    import flarmnet
    import json
    from pathlib import Path

    global ddb_entries
    if ddb_entries is None:
        ddb_url = "http://ddb.glidernet.org/download/"
        flarmnet_url = "http://www.flarmnet.org/files/data.fln"

        # Load the OGN Device Data Base (DDB)
        r = requests.get(ddb_url)
        # print(r.status_code)

        # Check if DDB request was successful
        if r.status_code == 200:
            rows = '\n'.join(i for i in r.text.splitlines() if i[0] != '#')
            data = csv.reader(StringIO(rows), quotechar="'", quoting=csv.QUOTE_ALL)

            ddb_entries = dict()
            for row in data:
                ddb_entries[row[1]] = row[3]

            with open('OGN_DDB.txt', 'w') as file:
                file.write(json.dumps(ddb_entries))  # use `json.loads` to do the reverse

        else:
            if Path("OGN_DDB.txt").is_file():
                with open('OGN_DDB.txt', 'r') as file:
                    ddb_entries = json.loads(file.read())  # use `json.loads` to do the reverse
                    print("Could not reach OGN DDB. Reverting to OGN DDB file stores on disk.")
            else:
                raise ValueError("Error occurred while loading OGN DDB and did not find OGN DDB file on disk.")

        # Load the FlarmNet data base and save it to file
        with open('data.fln', "wb") as file:
            # get request
            response = requests.get(flarmnet_url, 'data.fln')
            if r.status_code == 200:
                # write to file
                file.write(response.content)

            else:
                print("Could not load FlarmNet File from internet.")

        if Path("data.fln").is_file():
            with open('data.fln', 'r') as ffile:
                reader = flarmnet.Reader(ffile)
                for record in reader.read():
                    # print(record.id, record.registration)
                    # If FlarmNet-ID is not already in OGN DDB amend
                    if record.id not in ddb_entries:
                        # print("Adding entry from Flarmnet DB: ",record.id,record.registration)
                        ddb_entries[record.id] = record.registration

        else:
            print("No FlarmNet file found.")

    return ddb_entries


# Performs a lookup in ogn ddb
def ogn_check(aircraft_registration, live_track_id):
    ddb_import()

    if live_track_id == "":
        live_track_id = None

    if aircraft_registration == "":
        aircraft_registration = None

    if aircraft_registration in ddb_entries.values():
        ogn_id = list(ddb_entries.keys())[list(ddb_entries.values()).index(aircraft_registration)]
        # print(aircraft_registration, "OGN DDB lookup found: ", live_track_id)
    else:
        ogn_id = None
        # print(aircraft_registration, "Aircraft registration not found in OGN DDB.", ogn_id, live_track_id)

    if live_track_id is not None:
        # Check if live_track_id is 6 digits long and check if it is a hex number
        if len(live_track_id) == 6:
            try:
                int(live_track_id, 16)
                # print("HEX check passed. 6")

            except ValueError:
                print(aircraft_registration, "The live_track_id provided is no valid HEX number: ", live_track_id)

        elif len(live_track_id) == 8:
            try:
                int(live_track_id[0:2])

            except ValueError:
                print(aircraft_registration, "The live_track_id provided has 8 digits and no valid first two digits: ", live_track_id)

            try:
                int(live_track_id[2:], 16)
                # print("HEX check passed 8")

            except ValueError:
                print(aircraft_registration, "The live_track_id provided has 8 digits and no valid last six digits: ", live_track_id)

        else:
                print(aircraft_registration, "The live_track_id provided has an odd length", live_track_id)

        if ogn_id is not None:
            if (len(live_track_id) == 6 and (ogn_id == live_track_id)) or (len(live_track_id) == 8 and (ogn_id == live_track_id[2:])):
                print(aircraft_registration, "Live_track_id is also in OGN DDB. Registrations match. Plausible ID.", ogn_id, live_track_id)

            else:
                if len(live_track_id) == 6:
                    print(aircraft_registration, "Live_track_id is also in OGN DDB. Registrations DOES NOT match. Check ID.", ogn_id, live_track_id)
                elif len(live_track_id) == 8:
                    pass
                else:
                    print(aircraft_registration, "Live_track_id has strange length. Please check: ", live_track_id)
        else:
            print(aircraft_registration, "Live_track_id is not in OGN DDB. Plausibility check not possible.", ogn_id, live_track_id)

    else:
        if ogn_id is not None:
            print(aircraft_registration, "Live_track_id not provided. Using OGN ID instead.", ogn_id, live_track_id)
            live_track_id = ogn_id

        else:
            print(aircraft_registration, "Live_track_id not provided. OGN ID not found. Using XXXXXX as fake ID.", ogn_id, live_track_id)
            live_track_id = 'XXXXXX'

    return live_track_id


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
    import json
    from pathlib import Path
    
    if Path('GIST_dict.json').is_file():
        with open('GIST_dict.json', 'r') as gist_file:
            gist_dict = json.loads(gist_file.read())  # use `json.loads` to do the reverse
    
    else:
        gist_dict = dict()

    # Provide login to Github via API token
    gh = login(token=app.config['API_TOKEN'])
    # TODO: Check if this was successfull or exit gracefully.

    gh_ratelimit = gh.ratelimit_remaining
    if gh_ratelimit <= 50:
        raise ValueError("Your Github API access rate limit is almost exceeded: '{}' remaining access. Aborting.".format(gh_ratelimit))
    else:
        print("Rate limit remaining: {} access".format(gh_ratelimit))

    # Get Gist-ID from config
    gist_id = app.config['GIST_ID']

    # Generate the gist comment
    gist_comment = task.contest_class.contest.name.replace(" ", "").upper() + "_" + task.contest_class.name.replace("_", "").replace("-", "").upper()

    if gist_comment in gist_dict and gist_id is None:
        gist_id = gist_dict[gist_comment]
        print("Read Gist_ID from file.")
    else:
        print("No Gist_ID found in file.")
    
    files = {}

    # files_filter deactivated to prevent over writing of filter files in github as most contest organizers fail to maintain
    # the correct flarm-ids in the task setting program

    if gist_id is None:
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
        gist_dict[gist_comment] = gist.id
        
    else:
        print("Gist-ID provided, modifying an existing gist.")
        # Get all gits ID of authenticated github user to check if gist ID is valid
        gists = [g.id for g in gh.gists()]
        if gist_id in gists:
            print("The GIST-ID you provided is valid.")
            gist = gh.gist(gist_id)
            if gist_comment not in gist_dict:
                gist_dict[gist_comment] = gist.id

        else:
            # Gist-ID is not valid
            raise ValueError("This gist_id is not valid: '{}' Aborting.".format(gist_id))

        # Edit the gist
        gist.edit(gist_comment, files)
    
    # Write GIST-IDs to file
    with open('GIST_dict.json', 'w') as file:
        print(gist_dict)
        file.write(json.dumps(gist_dict))

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
