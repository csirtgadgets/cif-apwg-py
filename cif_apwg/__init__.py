#!/usr/bin/env python

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import logging
import textwrap
import os.path
import os
import sys
from datetime import datetime, timedelta
from pprint import pprint
import json
import requests
from cif.sdk.client import Client as CIFClient
import yaml

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s[%(lineno)s] - %(message)s'
DEFAULT_CONFIG = ".cif.yml"
LIMIT = 10000000
APWG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
CIF_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
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

    p.add_argument("--token", dest="token", help="specify token")
    p.add_argument("--remote", dest="remote", help="specify the CIF remote")
    p.add_argument("--group", dest="group", help="specify CIF group [default: %(default)s]", default="everyone")

    # apwg options

    p.add_argument("--limit", dest="limit", help="limit the number of records processed [default: %(default)s",
                   default=LIMIT)
    p.add_argument("--apwg-token", dest="apwg_token", help="specify an APWG token", required=True)
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

    if os.path.isfile(args.config):
            f = file(args.config)
            config = yaml.load(f)
            f.close()
            if not config['client']:
                raise Exception("Unable to read " + args.config + " config file")
            config = config['client']
            for k in config:
                if not options.get(k):
                    options[k] = config[k]

    if not os.path.isdir(options["cache"]):
        os.makedirs(options["cache"])

    end = datetime.utcnow()

    lastrun = os.path.join(options["cache"], "lastrun")
    logger.debug(lastrun)
    if os.path.exists(lastrun):
        with open(lastrun) as f:
            start = f.read()
    else:
        hours = int(options["past_hours"])
        start = end - timedelta(hours=hours, seconds=-1)

    logger.info("start:{}".format(start))
    logger.info("end:{}".format(end))

    uri = "{}/{}/?query=date_start:{},date_end:{},format:{},confidence_low:{},confidence_high:{}".format(
        options["apwg_remote"],
        options["apwg_token"],
        start,
        end,
        options["format"],
        options["apwg_confidence_low"],
        options["apwg_confidence_high"],
    )

    logger.debug("apwg url:{}".format(uri))

    session = requests.Session()
    session.headers['User-Agent'] = 'py-cif-apwg/0.0.0a'
    logger.info("pulling apwg data")
    body = session.get(uri)
    body = json.loads(body.content)
    body = body[1:]

    if len(body):
        if options.get("limit"):
            body = body[:int(options["limit"])]

        body = [
            {
                "observable": e["entry"]["url"].lower(),
                "reporttime": datetime.strptime(e["entry"]["date_discovered"], "%Y-%m-%dT%H:%M:%S+0000").strftime(
                    "%Y-%m-%dT%H:%M:%SZ"),
                "tags": ["phishing", e["entry"]["brand"].lower()],
                "confidence": 85,
                "tlp": "amber",
                "group": options["group"]

            } for e in body]

        logger.info("submitting {} observables to CIF: {}".format(len(body),options["remote"]))
        cli = CIFClient(**options)
        ret = cli.submit(submit=json.dumps(body))
    else:
        logger.info("nothing new to submit...")

    with open(os.path.join(options["cache"], "lastrun"), "w") as f:
        f.write(str(end))

if __name__ == "__main__":
    main()