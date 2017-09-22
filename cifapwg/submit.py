#!/usr/bin/env python

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import logging
import textwrap
import os.path
import os
from datetime import datetime, timedelta
from pprint import pprint
import json
from cifsdk.client import Client

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s[%(lineno)s] - %(message)s'
DEFAULT_CONFIG = ".cif.yml"
LIMIT = 10000000
APWG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
CIF_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
APWG_REMOTE = os.getenv('APWG_REMOTE')
APWG_TOKEN = os.getenv('APWG_TOKEN')
TLP = "red"
CONFIDENCE = 85

CIF_REMOTE = os.getenv('CIF_REMOTE', 'http://localhost:5000')
CIF_TOKEN = os.getenv('CIF_TOKEN', None)


def main():
    p = ArgumentParser(
        description=textwrap.dedent('''\
        example usage:
            $ export APWG_REMOTE=https://api.apwg.org/endpoint
            $ export APWG_TOKEN=123123123
            
            $ export CIF_REMOTE=https://csirtgadgets.org
            $ export CIF_TOKEN=123412341234
            $ cif-apwg-submit -v
        '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='cif-apwg-submit'
    )

    p.add_argument("-v", "--verbose", dest="verbose", action="count",
                   help="set verbosity level [default: %(default)s]")
    p.add_argument('-d', '--debug', dest='debug', action="store_true")

    p.add_argument('--no-verify-ssl', action="store_true", default=False)

    # apwg options

    p.add_argument("--limit", dest="limit", help="limit the number of records processed")
    p.add_argument("--cache", default=os.path.join(os.path.expanduser("~"), ".cif/apwg_submit"))
    p.add_argument("--past-minutes", help="number of hours to go back and retrieve", default=10)
    p.add_argument("--apwg-confidence", default="90")

    # cif options
    p.add_argument('--tlp', default=TLP)
    p.add_argument('--altid-tlp', default=TLP)
    p.add_argument('--altid')
    p.add_argument('--confidence', default=CONFIDENCE)
    p.add_argument('--tags', default="phishing")
    p.add_argument('--otype', default='url')
    p.add_argument('--itype', default='url')
    p.add_argument('--filters', default=None)
    p.add_argument('--group', default="everyone")

    p.add_argument("--dry-run", help="do not submit to CIF", action="store_true")

    p.add_argument("--no-last-run", help="do not modify lastrun file", action="store_true")

    args = p.parse_args()

    filters = {
        "confidence": args.confidence,
        "tags": args.tags.split(','),
        "otype": args.otype,
        "itype": args.itype,
        "group": args.group,
    }

    if args.filters:
        for e in args.filters.split('&', 1):
            k = e.split('=', 1)
            filters[k[0]] = k[1]


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

    if not APWG_REMOTE and not args.dry_run:
       print("\nAPWG_REMOTE missing.\nConsult with support@ecrimex.net for more information")
       raise SystemExit

    if not os.path.isdir(args.cache):
        os.makedirs(args.cache)

    end = datetime.utcnow()

    lastrun = os.path.join(args.cache, "lastrun")
    logger.debug(lastrun)
    if os.path.exists(lastrun):
        with open(lastrun) as f:
            start = f.read().strip("\n")
            start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S.%f')
    else:
        minutes = int(args.past_minutes)
        start = end - timedelta(minutes=minutes, seconds=-1)

    start = start.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    end = end.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    logger.info("start:{0}".format(start))
    logger.info("end:{0}".format(end))

    filters['reporttime'] = start
    filters['reporttimeend'] = end

    logger.debug(json.dumps(filters, indent=4))

    # get data
    verify_ssl = True
    if args.no_verify_ssl:
        verify_ssl = False

    from apwgsdk.client import Client as APWGClient
    apwg = APWGClient()
    cli = Client(CIF_TOKEN, remote=CIF_REMOTE, verify_ssl=verify_ssl)
    data = cli.search(limit=args.limit, filters=filters)

    for d in data:
        if d.get('observable'):
            d['indicator'] = d['observable']

        if args.altid and not d.get('altid', '').startswith(args.altid):
            logger.debug('skipping.. %s' % d['indicator'])
            # if the altid doesn't match, skip it..
            continue

        if logger.getEffectiveLevel() == logging.DEBUG:
            logger.debug("%s" % json.dumps(d, indent=4))

        if args.dry_run:
            logger.info(json.dumps(d, indent=4))
            continue

        if logger.getEffectiveLevel() == logging.DEBUG:
            logger.debug('sending: %s' % json.dumps(d, indent=4))
        else:
            logger.info('sending: %s' % d['indicator'])

        # submit to apwg
        try:
            r = apwg.indicators_create(indicator=d['indicator'], confidence=args.apwg_confidence,
                                       description='phishing', lasttime=d['lasttime'])

            logger.info('indicator created successfully: {}'.format(r['id']))
            if args.debug:
                pprint(r)

        except Exception as e:
            logger.debug(e)
            logger.error('error creating indicator')

    if not args.no_last_run and not args.dry_run:
        with open(os.path.join(args.cache, "lastrun"), "w") as f:
            f.write(str(end))

if __name__ == "__main__":
    main()
