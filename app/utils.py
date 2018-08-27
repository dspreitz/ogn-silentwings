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
                
                """
                try:
                    reader = flarmnet.Reader(ffile)
                    for record in reader.read():
                        # print(record.id, record.registration)
                        # If FlarmNet-ID is not already in OGN DDB amend
                        if record.id not in ddb_entries:
                            # print("Adding entry from Flarmnet DB: ",record.id,record.registration)
                            ddb_entries[record.id] = record.registration
                except:
                    print("Could not process Flarmnet data")
                """
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
                live_track_id = live_track_id[2:]

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


def gettrackerdata_GT(trackerid,s,e):
    from websocket import create_connection
    import time, datetime
    
    # Create connection to Glidertracker.de
    ws = create_connection("wss://glidertracker.de:3389/")
    
    # Write header of result string
    result = "{datadelay}1{/datadelay}\n"
    
    
    # print("Sending 'Hello, World'...")
    # ws.send("Hello, World")
    # print("Sent")
    # print("Receiving...")
    # ws.send("VIEW:3.22407|48.49193|9.9|53.86296")
    # ws.send("VIEW:3.22407|48.49193|3.3|53.86296")
    # result =  ws.recv()
    # print("Received '%s'" % result)
    
    # client.requestTrack('06DDA3B3', 1501244359000, Date.now());
    # this.send(`TRACK?${id}|${Math.round(from / 1000)}|${Math.round(to / 1000)}`);
    # start_time = 
    
    # GET /gettrackerdata.php?querytype=getintfixes&contestname=SOARINGSPOT3DTRACKINGINTERFACE%5f18METER&trackerid=FLRDDE1FC&username=ogn&cpassword=ecbad38d0b5a3cf6482e661028b2c60c&starttime=20180303000001&endtime=20180303235959&compression=gzip HTTP/1.0
    
    """
    Silentwing result format
    {datadelay}1{/datadelay}
    1052,20061230045824,-34.60305,138.72063,49.0,0
    1052,20061230045828,-34.60306,138.72067,48.0,0
    <tracker id>,<timestamp>,<latitude>,<longitude>,<altitude>,<status>
    """
    
    # s = "20180709000001"
    # e = "20180709235959"
    # trackerid = "06DDDAA8"
    
    # Format conversion of start and end time 
    start_time = int(time.mktime(datetime.datetime.strptime(s, "%Y%m%d%H%M%S").timetuple()))
    end_time = int(time.mktime(datetime.datetime.strptime(e, "%Y%m%d%H%M%S").timetuple()))
    
    # TRACK?06DDDAA8|1531087201|1531123674 - works
    request = "TRACK?" + trackerid +"|" + str(start_time) + "|" + str(end_time) 
    ws.send(request)
    
    # Glidertracker example answer:
    # 'TRACK:06DDDAA8|51.391533/4.954583/102.0/2018-07-09T08:00:23Z|51.391449/4.954383/102.0/2018-07-09T08:00:34Z|51.391399/4.954150/105.0/2018-07-09T08:00:47Z|51.391335/4.953933/102.0/2018-07-09T08:00:59Z|51.391251/4.953633/102.0/2018-07-09T08:01:17Z|51.391216/4.953450/102.0/2018-07-09T08:01:32Z|51.391151/4.953183/98.0/2018-07-09T08:01:46Z|51.391151/4.953166/98.0/2018-07-09T08:01:47Z|51.391102/4.952883/98.0/2018-07-09T08:02:02Z|51.391048/4.952633/98.0/2018-07-09T08:02:15Z|51.391033/4.952300/98.0/2018-07-09T08:02:32Z|51.391167/4.951950/95.0/2018-07-09T08:02:53Z|51.391232/4.952066/95.0/2018-07-09T08:03:19Z|51.391216/4.952084/95.0/2018-07-09T08:03:59Z|51.391216/4.952084/95.0/2018-07-09T08:04:05Z|51.391232/4.952084/95.0/2018-07-09T08:04:27Z|51.391232/4.952100/95.0/2018-07-09T08:04:47Z|51.391216/4.952100/95.0/2018-07-09T08:05:08Z|51.391232/4.952100/95.0/2018-07-09T08:05:29Z|51.391216/4.952100/98.0/2018-07-09T08:05:49Z|51.391232/4.952100/102.0/2018-07-09T08:06:09Z|51.391216/4.952100/102.0/2018-07-09T08:06:29Z|51.391216/4.952100/98.0/2018-07-09T08:06:50Z|51.391216/4.952100/98.0/2018-07-09T08:06:51Z|51.391216/4.952100/98.0/2018-07-09T08:07:10Z|51.391216/4.952100/98.0/2018-07-09T08:07:19Z|51.391216/4.952084/95.0/2018-07-09T08:07:26Z|'
    
    for string in ws.recv().split('|')[1:]:
        if len(string) > 0:
            lat = string.split('/')[0]
            long = string.split('/')[1]
            alt = string.split('/')[2]
            zeit = time.mktime(datetime.datetime.strptime(string.split('/')[3], "%Y-%m-%dT%H:%M:%SZ").timetuple())
            # 51.391232 4.952100 102.0 2018-07-09T08:21:56Z
            result += str( ID + "," + datetime.datetime.fromtimestamp(int(zeit)).strftime('%Y%m%d%H%M%S') + "," + lat + "," + long + ","  + alt + ",1\n")
            
    print(result)
    
    ws.close()
    return result

# Interface to get historical data from ogn-web-gateway (https://github.com/Turbo87/ogn-web-gateway)
def gettrackerdata_OWG(trackerid,s,e):
    import time, datetime
    start_time = int(time.mktime(datetime.datetime.strptime(s, "%Y%m%d%H%M%S").timetuple()))
    end_time = int(time.mktime(datetime.datetime.strptime(e, "%Y%m%d%H%M%S").timetuple()))
    
    # Write header of result string
    result = "{datadelay}1{/datadelay}\n"
    
    # Example url request to API
    # https://ogn.fva.cloud/api/records/OGN354B61?before=1532367209&after=1532367019
    
    trackerid = "DD989A"
    # TODO: Improve, as this is not universal yet.
    if trackerid.startswith('DD'):
        trackerid_mod = 'FLR' + trackerid
    elif trackerid.startswith('3E'):
        trackerid_mod = 'ICA' + trackerid
    else:
        print(trackerid)
        trackerid_mod = trackerid
    
    # GET /gettrackerdata.php?querytype=getintfixes&contestname=QUALIFIKATIONSMEISTERSCHAFTZWICKAU%5f18M&trackerid=DF0E66&username=ogn&cpassword=ecbad38d0b5a3cf6482e661028b2c60c&starttime=20180807000001&endtime=20180807235959&compression=none HTTP/1.0
    
    
    urlstring = 'https://ogn.fva.cloud/api/records/' + str(trackerid_mod) + '?after=' + str(start_time) + '&before=' + str(end_time)
    # urlstring = 'https://ogn.fva.cloud/api/records/FLRDDBB1B?after=' + str(start_time) + '&before=' + str(end_time)
    # urlstring = 'https://ogn.fva.cloud/api/records/OGN354B61' # + '?before=1532725824' + '&after=1532643024'
    print(urlstring)
    r = requests.get(url = urlstring)
    # print(r.json())
    
    # TODO tracker_id must be integer!
    for tracker_id in r.json():
        # print(r.json()[tracker_id])
        for fix in r.json()[tracker_id]:
            lat = fix.split('|')[2]
            long = fix.split('|')[1]
            alt = fix.split('|')[3]
            zeit = time.mktime(datetime.datetime.fromtimestamp(int(fix.split('|')[0])).timetuple())
            result += str( trackerid + "," + datetime.datetime.fromtimestamp(int(zeit)).strftime('%Y%m%d%H%M%S') + "," + lat + "," + long + ","  + str(alt) + ",1\n")
            
    print("Number of Fixes for this request:" + str(len(result.split('\n'))))
    
    """
    Silentwing result format
    {datadelay}1{/datadelay}
    1052,20061230045824,-34.60305,138.72063,49.0,0
    1052,20061230045828,-34.60306,138.72067,48.0,0
    <tracker id>,<timestamp>,<latitude>,<longitude>,<altitude>,<status>
    """
    # XXXXXX,2018 07 23 20 50 12,48.747850,11.452717,100,1
    # 1052,  2006 12 30 04 58 28,-34.60306,138.72067,48.0,0
    
    return result


