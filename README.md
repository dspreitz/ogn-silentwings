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

   ```
   git clone https://github.com/Meisterschueler/ogn-silentwings.git
   ```

2. Install python requirements

    ```
    pip install -r requirements.txt
    ```

3. Modify flarmnet according to:
https://github.com/Turbo87/flarmnet.py/commit/2b74d03200bd82713dd262a3ff7d2cf6cc8c76f2

4. Mofiy github3 according to:
https://github.com/sigmavirus24/github3.py/issues/845



## License
Licensed under the [AGPLv3](LICENSE).
