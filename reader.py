#!/usr/bin/env python

import sys
import json
import re
import math
from dateutil.parser import parse as date_parse
import argparse

stat_keys = [
        "name",
        "organName",
        "radioEquipmentCode",
        "spuriousRules",
        "techCode",
        ]

def sanitize(d):
    ignore_keys = [
            "attachmentFileCntForCd1",
            "attachmentFileCntForCd2",
            "attachmentFileKey",
            "attachmentFileName",
            "bodySar",
            "no",
            "note",
            "organName",
            "radioEquipmentCode",
            "spuriousRules",
            "techCode",
            ]
    for k in ignore_keys:
        del(d["gitekiInfo"][k])

unit_map = {
        "k": 1000,
        "ｋ":1000,
        "M": 1000000,
        "Ｍ":1000000,
        "G": 1000000000,
        "Ｇ":1000000000
        }

def get_unit(u):
    if u is None:
        return 1
    return unit_map[u]

re_band = re.compile("([\d\.]+)([kｋMＭGＧ])[HＨ][zｚ]")
re_band_range = re.compile("([\d\.]+)〜([\d\.]+)([kｋMＭGＧ])[HＨ][zｚ]")
re_tx_power_W = re.compile("(?P<val>[\d\.]+)(?P<unit>[mｍ]?)[WＷ]")
re_tx_power_dBm = re.compile("(?P<val>[\d\.]+)[dｄ][BＢ][mｍ]")
re_ch_width = re.compile("([\d\.]+)([kｋMＭGＧ])[HＨ][zｚ]間隔")

def set_band(d):
    freq_list = []
    band_freq = 0
    # check range type.
    r_all = re_band_range.finditer(d["gitekiInfo"]["elecWave"])
    for r in r_all:
        unit = get_unit(r.group(3))
        if band_freq > unit:
            # ignore it as guessed as a channel width.
            continue
        band_freq = unit
        freq_list.append(float(r.group(1)) * unit)
        freq_list.append(float(r.group(2)) * unit)
    # check list type.
    r_all = re_band.finditer(d["gitekiInfo"]["elecWave"])
    for r in r_all:
        unit = get_unit(r.group(2))
        if band_freq > unit:
            # ignore it as guessed as a channel width.
            continue
        band_freq = unit
        freq_list.append(float(r.group(1)) * unit)
    # get max and min freq.
    freq_max = -1
    freq_min = -1
    for freq in freq_list:
        if freq_min == -1:
            freq_min = freq
            freq_max = freq
            continue
        if freq_max < freq:
            freq_max = freq
            continue
        if freq_min > freq:
            freq_min = freq
            continue
    d["freq_min"] = freq_min
    d["freq_max"] = freq_max

def set_tx_power(d):
    r = re_tx_power_W.search(d["gitekiInfo"]["elecWave"])
    if r is None:
        r = re_tx_power_dBm.search(d["gitekiInfo"]["elecWave"])
        if r is None:
            n = 0
        else:
            n = math.pow(10., (float(r["val"])/10.))
    elif r["unit"] == "":
        n = float(r["val"]) * 1000
    else:
        # mW
        n = float(r["val"])
    d["tx_power"] = n

def set_ch_width(d, target=None):
    r = re_ch_width.search(d["gitekiInfo"]["elecWave"])
    if r is None:
        # if there is no infomation, it should be included.
        d["ch_width"] = 0
    else:
        ch_width = float(r.group(1)) * get_unit(r.group(2))
        d["ch_width"] = ch_width

def within_period(d):
    if dt_from > date_parse(d["gitekiInfo"]["date"]):
        return False
    elif dt_to < date_parse(d["gitekiInfo"]["date"]):
        return False
    else:
        return True

#
# main
#
ap = argparse.ArgumentParser(
        description="a reader of the response from GITEKI db.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
ap.add_argument("db_file", help="database in JSON.")
ap.add_argument("--name", action="store", dest="name",
                help="specify a vendor name.")
ap.add_argument("--date-from", action="store", dest="date_from",
                default="19700101",
                help="specify a datetime of the start date")
ap.add_argument("--date-to", action="store", dest="date_to",
                default="29990101",
                help="specify a datetime of the end date")
ap.add_argument("--max-tx-power", action="store", dest="max_tx_power",
                type=float, default=20.0,
                help="specify the maximum Tx power, includes the number")
ap.add_argument("--min-tx-power", action="store", dest="min_tx_power",
                type=float, default=1.0,
                help="specify the minimum Tx power, not includes the number")
ap.add_argument("--ch-width", action="store", dest="ch_width",
                default=None,
                help="specify a channel width interested.")
ap.add_argument("--specific-ch-width", action="store_true",
                dest="specific_ch_width",
                help="specify that the channel width specified only be taken.")
ap.add_argument("--show-others", action="store_true", dest="show_others",
                help="enable to show other recoreds.")
ap.add_argument("-v", action="store_true", dest="verbose",
                help="enable verbose mode.")
ap.add_argument("--show-stat", action="store_true", dest="show_stat",
                help="specify to show the statistics.")

opt = ap.parse_args()
dt_from = date_parse(opt.date_from)
dt_to = date_parse(opt.date_to)
output_file = sys.stdout

# load db
if opt.db_file == "-":
    db = json.load(sys.stdin)
else:
    db = json.load(open(opt.db_file))

db_target = []
db_others = []
db_stat = {
        "total_size": len(db)
        }

# take only 920MHz, 20mW band.
for d in db:
    set_band(d)
    set_tx_power(d)
    set_ch_width(d)

    if not opt.verbose:
        sanitize(d)

    if opt.name is not None and opt.name not in d["gitekiInfo"]["name"]:
        db_others.append(d)
        continue
    #
    if not within_period(d):
        db_others.append(d)
        continue
    # check if it's for 920MHz.
    if d["freq_max"] > 928000000 or d["freq_min"] < 920600000:
        db_others.append(d)
        continue
    # check if it's 20mW.
    if d["tx_power"] > opt.max_tx_power or d["tx_power"] <= opt.min_tx_power:
        db_others.append(d)
        continue
    # check the channel width
    if d["ch_width"] == 0 and opt.specific_ch_width is True:
        db_others.append(d)
        continue
    #
    if opt.ch_width is not None and d["ch_width"] != opt.ch_width:
        db_others.append(d)
        continue

    # passed all checks.
    db_target.append(d)

db_stat["target_size"] = len(db_target)
db_stat["others_size"] = len(db_others)

def add_stat(d):
    for n in stat_keys:
        x1 = db_stat.setdefault(n, {})
        x2 = x1.setdefault(d["gitekiInfo"][n], 0)
        x1[d["gitekiInfo"][n]] += 1

def make_stat(db):
    if len(db) != 0:
        for d in db:
            add_stat(d)
        # sort by descending order.
        for n in stat_keys:
            db_stat[n] = dict(sorted(db_stat[n].items(), key=(lambda k:k[1]),
                                    reverse=True))
        return db_stat
    else:
        return db_stat

#
if not opt.show_others:
    db = db_target
else:
    db = db_others

d = { "target": sorted(db_target, key=(lambda k:k["gitekiInfo"]["date"]),
                        reverse=True) }
if opt.verbose:
    d["stat"] = make_stat(db)
print(json.dumps(d, indent="  ", ensure_ascii=False), file=output_file)

