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
from cifsdk.client import Client
import yaml

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s[%(lineno)s] - %(message)s'
DEFAULT_CONFIG = ".cif.yml"
LIMIT = 10000000
APWG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
CIF_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
APWG_REMOTE = "https://api.ecrimex.net/phish"
TLP = "red"
CONFIDENCE = 85


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
    p.add_argument('--no-verify-ssl', action="store_true", default=False)

    # apwg options

    p.add_argument("--limit", dest="limit", help="limit the number of records processed")
    p.add_argument("--apwg-token", help="specify an APWG token", required=True)
    p.add_argument("--format", default="json")
    p.add_argument("--cache", default=os.path.join(os.path.expanduser("~"), ".cif/apwg"))
    p.add_argument("--apwg-remote",  default=APWG_REMOTE)
    p.add_argument("--past-hours", help="number of hours to go back and retrieve", default="24")
    p.add_argument("--apwg-confidence-low", default="65")
    p.add_argument("--apwg-confidence-high", default="100")
    p.add_argument('--tlp', default=TLP)
    p.add_argument('--confidence', default=CONFIDENCE)

    p.add_argument("--dry-run", help="do not submit to CIF", action="store_true")

    p.add_argument("--no-last-run", help="do not modify lastrun file", action="store_true")

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
            start = f.read().strip("\n")
            start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S.%f')
    else:
        hours = int(options["past_hours"])
        start = end - timedelta(hours=hours, seconds=-1)

    logger.info("start:{0}".format(start))
    logger.info("end:{0}".format(end))

    uri = "{}?t={}&from_date={}&end_date={}&confidence_low=90&pretty_print".format(
        options['apwg_remote'],
        options["apwg_token"],
        start.strftime('%s'),
        end.strftime('%s')
    )

    logger.debug("apwg url: {0}".format(uri))

    session = requests.Session()
    session.headers['User-Agent'] = 'cif-apwg-py/0.0.2a'
    logger.info("pulling apwg data")
    body = session.get(uri)
    body = json.loads(body.content)

    body = body['_embedded']['phish']

    if len(body):
        if options.get("limit"):
            body = body[-int(options["limit"]):]

        body = [
            {
                "observable": e["url"].lower().lstrip('3d'),
                "reporttime": datetime.fromtimestamp(e["modified"]).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "firsttime": datetime.fromtimestamp(e["date_discovered"]).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "lasttime": datetime.fromtimestamp(e['date_discovered']).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "tags": ["phishing", e["brand"].lower()],
                "confidence": options["confidence"],
                "tlp": options["tlp"],
                "group": options["group"],
                "otype": "url",
                "provider": "apwg.org",
                "application": ["http", "https"]

            } for e in reversed(body)]

        logger.info("start of data: {0}".format(body[len(body)-1]["reporttime"]))
        logger.info("end of data: {0}".format(body[0]["reporttime"]))
        if not options.get("dry_run"):
            logger.info("submitting {0} observables to CIF: {1}".format(len(body), options["remote"]))
            verify_ssl = True
            if options['no_verify_ssl']:
                verify_ssl = False
            cli = Client(options['token'], remote=options['remote'], verify_ssl=verify_ssl)
            ret = cli.submit(body)
        else:
            pprint(body)
            logger.info("dry run, skipping submit...{}".format(len(body)))
    else:
        logger.info("nothing new to submit...")

    if not options.get("no_last_run") and not options.get("dry_run"):
        with open(os.path.join(options["cache"], "lastrun"), "w") as f:
            f.write(str(end))

if __name__ == "__main__":
    main()