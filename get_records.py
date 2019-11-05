#!/usr/bin/env python

import sys
import requests
import json
import time
import argparse
import os

# e.g.
#
# https://www.tele.soumu.go.jp/giteki/num?OF=2&REC=02-08-00-00'
# https://www.tele.soumu.go.jp/giteki/num?OF=2&REC=02-08-00-00&DS=20120101&DE=20140101
#
# export PYTHONWARNINGS="ignore:Unverified HTTPS request"
#

url_base = "https://www.tele.soumu.go.jp/giteki"
url_base += "/{}?OF=2&REC=02-08-00-00"  # num or list
chunk_size_indexes = { 4:50, 5:100, 6:500, 7:1000 } # DC:chunk_size

def send_request(url):
    try:
        res = requests.request("GET", url, verify=False)
    except Exception as e:
        print("ERROR: {}".format(e))
        exit(1)

    if res.ok:
        if res.headers["content-type"].startswith("application/json"):
            return res.json()
        else:
            raise ValueError("content type is not JSON. type={}"
                             .format(res.headers["content-type"]))
    else:
        raise ValueError("HTTP response was not OK. {} {}\n{}"
                         .format(res.status_code, res.reason, res.text))

#
# main
#
ap = argparse.ArgumentParser(
        description="retriving the records in the giteki database.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
ap.add_argument("db_file", nargs="?", help="database in JSON.")
ap.add_argument("--date-from", action="store", dest="date_from",
                help="specify a datetime of the start date > 19260101")
ap.add_argument("--date-to", action="store", dest="date_to",
                help="specify a datetime of the end date < 21001231")
ap.add_argument("--interval", action="store", dest="interval",
                type=int, default=60,
                help="specify an interval in seconds to wait for the next retrieving.")
ap.add_argument("--dc", action="store", dest="chunk_size_index",
                type=int, default=6,
                choices=chunk_size_indexes.keys(),
                help="""specify an index number for the chunk size.
                DC:chunk_size = {}""".format(chunk_size_indexes))
ap.add_argument("--retrieve", action="store_true", dest="retrieve",
                help="specify to retrieve the records.")
ap.add_argument("-v", action="store_true", dest="verbose",
                default=False, help="enable verbose mode.")

opt = ap.parse_args()
output_file = sys.stdout
span = ""
if opt.date_from is not None:
    span += "&DS={}".format(opt.date_from)
if opt.date_to is not None:
    span += "&DE={}".format(opt.date_to)

# get the number of list.
url = url_base.format("num")
url += "{}".format(span)
if opt.verbose:
    print("url = {}".format(url), file=sys.stderr)

ret = send_request(url)
nb_list = int(ret["giteki"]["count"])
chunk_size = chunk_size_indexes[opt.chunk_size_index]

if opt.verbose or not opt.retrieve:
    print("size={}".format(nb_list), file=sys.stderr)

if not opt.retrieve:
    exit(0)

# get the list.
db_in = []
for i in range(0, nb_list, chunk_size):
    if i > 0:
        time.sleep(opt.interval)
    #
    url = url_base.format("list")
    url += "{}&DC={}&SC={}".format(span, opt.chunk_size_index, i+1)
    if opt.verbose:
        print("url = {}".format(url), file=sys.stderr)

    ret = send_request(url)
    if "errs" in ret:
        raise ValueError(ret)
    db_in.extend(ret["giteki"])

#print(json.dumps(db_in, indent="  ", ensure_ascii=False), file=output_file)

if opt.db_file is None:
    fd = sys.stdout
    json.dump(db_in, fd, indent="  ", ensure_ascii=False)
else:
    if os.path.exists(opt.db_file) and os.path.getsize(opt.db_file) != 0:
        with open(opt.db_file) as fd:
            db_out = json.load(fd)
        os.rename(opt.db_file, opt.db_file + ".bak")
        # add new records.
        db_out.extend(db_in)
    else:
        db_out = db_in
    # make a new db.
    with open(opt.db_file,"w") as fd:
        json.dump(db_out, fd, indent="  ", ensure_ascii=False)
