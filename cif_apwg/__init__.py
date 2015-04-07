#!/usr/bin/env python

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import logging
import textwrap
import os.path
import sys
from datetime import datetime, timedelta
from pprint import pprint
import json
import requests

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s[%(lineno)s] - %(message)s'
DEFAULT_CONFIG = ".cif.yml"
LIMIT = 10000000
APWG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
APWG_REMOTE = "https://ecrimex.net/ubl/query"

def main():
    p = ArgumentParser(
        description=textwrap.dedent('''\
        example usage:
            $ cif-apwg -v
        '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='cif-apwg'
    )

    p.add_argument("-v", "--verbose", dest="verbose", action="count",
                   help="set verbosity level [default: %(default)s]")
    p.add_argument('-d', '--debug', dest='debug', action="store_true")

    p.add_argument("--config", dest="config", help="specify a configuration file [default: %(default)s]",
                   default=os.path.join(os.path.expanduser("~"), DEFAULT_CONFIG))

    p.add_argument("--limit", dest="limit", help="limit the number of records processed [default: %(default)s",
                   default=LIMIT)
    p.add_argument("--token", dest="token", help="specify token")

    p.add_argument("--apwg-token", dest="apwg_token", help="specify an APWG token")
    p.add_argument("--format", dest="format", default="json")
    p.add_argument("--cache", dest="cache", default=os.path.join(os.path.expanduser("~"), ".cif/apwg"))
    p.add_argument("--apwg-remote", dest="apwg_remote", default=APWG_REMOTE)
    p.add_argument("--past-hours", dest="past_hours", help="number of hours to go back and retrieve", default="24")
    p.add_argument("--apwg-confidence-low", dest="apwg_confidence_low", default="85")
    p.add_argument("--apwg-confidence-high", dest="apwg_confidence_high", default="100")

    args = p.parse_args()

    loglevel = logging.WARNING
    if args.verbose:
        loglevel = logging.INFO
    if args.debug:
        loglevel = logging.DEBUG

    console = logging.StreamHandler()
    logging.getLogger('').setLevel(loglevel)
    console.setFormatter(logging.Formatter(LOG_FORMAT))
    logging.getLogger('').addHandler(console)
    logger = logging.getLogger(__name__)

    options = vars(args)

    hours = int(options["past_hours"])
    end = datetime.now()
    start = end - timedelta(hours=hours, seconds=-1)

    print datetime.strftime(start, APWG_DATE_FORMAT), datetime.strftime(end, APWG_DATE_FORMAT)

    uri = "{}/{}/?query=date_start:{},date_end:{},format:{},confidence_low:{},confidence_high:{}".format(
        options["apwg_remote"],
        options["apwg_token"],
        start,
        end,
        options["format"],
        options["apwg_confidence_low"],
        options["apwg_confidence_high"],
    )

    print uri

if __name__ == "__main__":
    main()