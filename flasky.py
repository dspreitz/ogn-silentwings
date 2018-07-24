import os
import time, datetime
from app import create_app, db
from app.model import Contest, ContestClass, Contestant, Pilot, Task, Beacon,\
    contest_class
from flask_migrate import Migrate, MigrateCommand
import click
from flask import request
from app.silent_wings import create_active_contests_string, create_contest_info_string, create_cuc
from app.soaringspot import get_soaringspot_contests
from app.strepla import list_strepla_contests
from app.utils import logfile_to_beacons, gist_writer, gettrackerdata_OWG
# from datetime import date
from app.glidertracker import glidertracker_contests

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db,
                Contest=Contest, ContestClass=ContestClass,
                Contestant=Contestant, Pilot=Pilot, Task=Task, Beacon=Beacon)


@app.cli.command()
def create_all():
    """Create the db."""
    db.create_all()


@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@app.cli.command()
def import_soaringspot():
    """Import data from SoaringSpot."""
    contests = get_soaringspot_contests(url=app.config['SOARINGSPOT_BASE_URL'],
                                        client_id=app.config['SOARINGSPOT_CLIENT_ID'],
                                        secret=app.config['SOARINGSPOT_SECRET'])
    db.session.add_all(contests)
    db.session.commit()


@app.cli.command()
@click.option('--logfile', help='path of the logfile')
def import_logfile(logfile):
    """Import an OGN APRS stream logfile."""
    if logfile is None:
        print("You must specify the logfile with option '--logfile'")
        return

    print("Start importing logfile '{}'".format(logfile))
    beacons = logfile_to_beacons(logfile)
    db.session.add_all(beacons)
    db.session.commit()
    print("Inserted {} beacons".format(len(beacons)))


@app.cli.command()
def aprs_connect():
    """Run the aprs client."""
    from ogn.client import AprsClient
    client = AprsClient("Silent Wings Interface")
    client.connect()

    try:
        client.run(callback=lambda x: print(x), autoreconnect=True)
    except KeyboardInterrupt:
        print('\nStop ogn gateway')

    client.disconnect()


@app.cli.command()
def strepla_contests():
    """List all StrePla contests to identify contest ID."""
    list_strepla_contests()


@app.cli.command()
@click.option('--cID', help='ID of Contest')
def import_strepla(cid):
    """Import a StrePla contest from scoring*StrePla"""
    from app.strepla import get_strepla_contest_all
    if cid is None:
        print("You must specify the contest ID with option '--cID'")
        print("Following contests are known:")
        # Output list of known contests
        list_strepla_contests()
        return

    db.session.add(get_strepla_contest_all(cid))
    db.session.commit()


@app.cli.command()
def list_contests_tasks():
    """Lists all contests and tasks from DB"""
    for contest in db.session.query(Contest):
        print(contest)
        for contest_class in contest.classes:
            print(contest_class)
            for task in contest_class.tasks:
                print(task)
    return


@app.cli.command()
# @click.option('--contest', help='Name of Contest')
@click.option('--ccID', help='ID of contest class')
def glidertracker_filter(ccid):
    """Generate a filter list for glidertracker.org"""

    if ccid is None:
        print("You must specify the contest class ID with option '--ccID'")
        glidertracker_contests()
        return

    contest_class_gt = db.session.query(ContestClass).filter(ContestClass.id == int(ccid)).one()
    print("Generating a filter list for glidertracker.org")
    print(contest_class_gt.gt_filter())
    return


@app.cli.command()
@click.option('--tID', help='ID of Task from DB')
def glidertracker_task(tid):
    """Writes a task in glidertracker format"""

    if tid is None:
        print("You must specify the contest ID with option '--tID'")
        print("Following contests are known:")
        # Output list of known contests
        for contest in db.session.query(Contest):
            print(contest)
            for contest_class in contest.classes:
                print(contest_class)
                for task in contest_class.tasks:
                    print(task)

        return

    tid = int(tid) - 1
    tasks = db.session.query(Task)
    if int(tid) > (len(tasks.all()) - 1):
        print("The task ID you provided is too high. Aborting.")
        return

    # gist_writer(task=tasks[int(tid)], gist_content_filter=None)
    gist_writer(task=tasks[int(tid)])


#########################
# Following Sections provides the Silent Wings Viewer interface
# For more details visit http://wiki.silentwings.no/index.php/Tracking_Protocol
#########################


@app.route("/getactivecontests.php")
def route_getactivecontests():
    # Parameters:
    # username=<user name>
    # cpassword=<encrypted password>
    # version=<version number>
    # username = request.args.get('username', type=str)
    # cpassword = request.args.get('cpassword', type=str)
    # version = request.args.get('version', type=str)

    # Example request by SWV:
    # GET /getactivecontests.php?username=ogn&cpassword=ecbad38d0b5a3cf6482e661028b2c60c&version=1.3 HTTP/1.1

    # app.logger.error('getactivecontests.php was called: username = %s version = %s',username,version)

    # Expected return by SWV:
    # {contestname}FAIGP2005{/contestname}{contestdisplayname}1st FAI Grand PrixMondial{/contestdisplayname}{datadelay}15{/datadelay}{utcoffset}+01:00{/utcoffset}
    # {countrycode}FR{/countrycode}{site}St. Auban{/site}{fromdate}20050903{/fromdate}
    # {todate}20050912{/todate}{lat}44.1959{/lat}{lon}5.98849{/lon}{alt}{/alt}
    active_contests = create_active_contests_string()
    print(active_contests)
    return active_contests


@app.route("/getcontestinfo.php")
@app.route("/getcontestinfo")
def route_getcontestinfo():
    # Parameters:
    # username=<user name>
    # cpassword=<encrypted password>
    # contestname=<contest name>
    # date=<YYYYMMDD>
    # username = request.args.get('username', type=str)
    # cpassword = request.args.get('cpassword', type=str)
    contestname = request.args.get('contestname', type=str)
    date = request.args.get('date', type=str)

    if 'date' in request.args:
        # return CUC file
        return create_cuc(contestname, date)
    else:
        return create_contest_info_string(contestname)


@app.route("/gettrackerdata.php")
def route_gettrackerdata():
    import gzip
    from flask import Response
    # Parameters:
    # querytype=getintfixes
    # contestname=<contest name>
    # trackerid=<tracker id>
    # username=<user name>
    # cpassword=<encrypted password>
    # starttime=<YYYYMMDDHHMMSS>
    # endtime=<YYYYMMDDHHMMSS>
    # compression=<none | gzip>
    # querytype = request.args.get('querytype', type=str)
    # contestname = request.args.get('contestname', type=str)
    trackerid = request.args.get('trackerid', type=str)
    # username = request.args.get('username', type=str)
    # cpassword = request.args.get('cpassword', type=str)
    starttime = request.args.get('starttime', type=str)
    endtime = request.args.get('endtime', type=str)
    compression = request.args.get('compression', type=str)

    # GET /gettrackerdata.php?querytype=getintfixes&contestname=SOARINGSPOT3DTRACKINGINTERFACE%5f18METER&trackerid=FLRDDE1FC&username=ogn&cpassword=ecbad38d0b5a3cf6482e661028b2c60c&starttime=20180303000001&endtime=20180303235959&compression=gzip HTTP/1.0
    
    print("gettrackerdata was called!")
    
    # return gettrackerdata_GT(trackerid,starttime,endtime)
    # print(zlib.compress(gettrackerdata_OWG(trackerid,starttime,endtime), -1))
    
    trackerdata = gettrackerdata_OWG(trackerid,starttime,endtime)
    print(trackerdata)
    
    if compression == "gzip":
        return Response(gzip.compress(trackerdata.encode('utf-8'),compresslevel=-1),mimetype='application/gzip')
        # return trackerdata
    else:
        return trackerdata


@app.route("/getprotocolinfo.php")
def route_getprotocolinfo():
    from datetime import date
    from time import time
    # username = request.args.get('username', type=str)
    # cpassword = request.args.get('cpassword', type=str)
    # {version}1.3{/version}{date}20080811{/date}{time}1218457469{/time}
    return "{version}1.3{/version}{date}" + date.today().strftime("%Y%m%d") + "{/date}{time}" + str(int(time())) + "{/time}"


#########################
# Following Sections provides the Silent Wings Studio interface
# For more details visit https://github.com/swingsopen/swtracking/wiki/Tracking-Protocol
#########################
