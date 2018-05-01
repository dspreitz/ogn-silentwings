from datetime import date
import requests
import csv
from io import StringIO


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


def gist_writer(gist_id=None, gist_filter=None, gist_task=None, gist_comment=None):
    from github3 import login
    from flasky import app

    if (gist_filter is None) and (gist_task is None):
        raise ValueError("Please provide gist_filter or gist_task to gist_writer. Aborting.")

    # Provide login to Github via API token
    gh = login(token=app.config['API_TOKEN'])

    files = {}
    if gist_filter:
        files_filter = {
            'filter': {
                'content': gist_filter
            }
        }
        files.update(files_filter)

    if gist_task:
        files_task = {
            'task': {
                'content': gist_task
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

    if gist_filter:
        print("You Gist address is:  https://gist.github.com/{}/{}/raw/filter".format(gist.owner, gist.id))

    if gist_task:
        print("You Gist address is:  https://gist.github.com/{}/{}/raw/task".format(gist.owner, gist.id))

    return gist.html_url
