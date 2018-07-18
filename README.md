# ogn-silentwings

[![Build Status](https://travis-ci.org/Meisterschueler/ogn-silentwings.svg?branch=master)](https://travis-ci.org/Meisterschueler/ogn-silentwings)
[![Coverage Status](https://img.shields.io/coveralls/Meisterschueler/ogn-silentwings.svg)](https://coveralls.io/r/Meisterschueler/ogn-silentwings)

A connector between  [Open Glider Network](http://wiki.glidernet.org/) and [Silent Wings](http://www.silentwings.no).
The ogn-silentwings module saves all received beacons into a database with [SQLAlchemy](http://www.sqlalchemy.org/).
It connects to the OGN aprs servers with [python-ogn-client](https://github.com/glidernet/python-ogn-client).

Additionally, it can request contest information (participants and tasks) from SoaringSpot and StrePla, which is then used to:
- generate filter and task files for glidertracker.org
- support the data output to Silentwings

Note: Presently, only Python3.6 is supported.


## Installation and Setup
1. Checkout the repository

   ```bash
   git clone https://github.com/Meisterschueler/ogn-silentwings.git
   ```

   It is recommended, that you install ogn-silentwings requirements in a virtual environment
   ```bash
   python3 -m venv ./venv
   source ./venv/bin/activate
   ```


2. Install python requirements

    ```bash
    pip install -r requirements.txt
    ```

3. Mofiy github3 according to:
https://github.com/sigmavirus24/github3.py/issues/845

4. Provide your GIT API Token from GitHub to enable ogn-silentwings to write GIST files
GitHub.com GISTs are used to publish the task and filter file online, so that GliderTracker.org can access theses files. To generate a GitHub API token, create a GitHub user account, click on account --> settings --> Developer Settings --> Personal access tokens. Give the token a name under token description (e.g. ogn-silentwings) and check only the gist (Create gist) checkbox. Hit generate token and then copy the token and save it in the ~/.bash_profile file.

Add following line to your .bash_profile
```bash
export GIT_API_TOKEN="_your_token_here_"
```

## StrePla Workflow for 2D live-Tracking with GliderTracker.org

1. Enter ogn-silentwings directory
```
cd ogn-silentwings
```

2. Activate your virtual environment and export flasky into environment
```
source venv/bin/activate && export FLASK_APP=flasky.py
```

3. Remove exisiting database files
```
rm data*
```

4. Create new empty database
```
flask create_all
```

5. Display and overview of all available StrePla contests
```
flask import_strepla
```

6. Import a selected contest
```
flask import_strepla --cID 514
```

7. Display all tasks (of all classes) of the selected contest
```
flask glidertracker_task
```

8. Generate participant filter and task file for selected task and upload it to GIST and provide complete 2D tracking URL
(Repeat this step for all contest classes)
```
flask glidertracker_task --tID 35
```






## License
Licensed under the [AGPLv3](LICENSE).
