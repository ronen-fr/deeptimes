import sys
import argparse
import subprocess
import tempfile
# import os
import pathlib
import datetime
from subprocess import Popen
import re

global stss
stss = []

def main():
    global stss
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-e', '--entries', action='store_true')
    # parser.add_argument('-s', '--osd', help='OSD resources timeline', action='store_true')
    parser.add_argument('infile', type=argparse.FileType('r'))
    args = parser.parse_args()
    sts = []
    # get the initial date from the 1st line in the file
    t0 = on_line(args.infile.readline(), args, datetime.datetime(1, 1, 1, 0, 0, 0))
    for line in args.infile:
        on_line(line, args, t0)

    #prv = 0
    if args.entries:
        for e in stss:
            print(e)
            #if (e[1] < prv):
            #    print('ERROR: out of order')
            #prv = e[1]
    for idx, e in enumerate(stss):
        add_time_of_prev_event(idx, args)
    #toms(test1, args)
    # times(args.file)
    for e in stss:
        if e[2] == 'end':
           d1 = e[1] - e[5]
           d2 = e[1] - e[6]
           print(f"{e[0]} \t{e[1]:10.0f}  {d1:6} {d2:6} {e[2]} {e[3]:20} {e[4]:26} {e[5]:7} {e[6]:7}")


datetime_ptrn_txt = r'(\d{4}-\d{2}-\d{2}T)(\d{2}:\d{2}:\d{2}.\d{3})\+0000'
datetime_ptrn = re.compile(datetime_ptrn_txt)

#event_ptrn_txt = r'.*] scrubber <(\w+)(/)?>: scrubber event --(\(<<\)|\(>>\)) (\w+)$'
event_ptrn_txt = r'.*] scrubber <(\w+)/?>: scrubber event --(<<|>>) (\w+).*$'
event_ptrn = re.compile(event_ptrn_txt)


def on_line(line, args, t0):
    global stss
    if args.verbose:
        print('line:', line)
    parts = line.split()
    if args.verbose:
      print('parts:', parts[0])
    tm1 = times(parts[0], args)
    #dff = datetime.datetime.combine(datetime.date.min, tm1) - datetime.datetime.combine(datetime.date.min, t0)
    #dff = datetime.datetime.combine(datetime.date.min, tm1).timestamp() - datetime.datetime.combine(datetime.date.min, t0).timestamp()
    #dff = tm1.timestamp() - t0.timestamp()
    #df2 = dff.total_seconds() * 1000 + dff.microseconds / 1000
    #ds1a = tm1.total_seconds()*1000
    #ds1b = t0.time.total_seconds()
    #df2 = datetime.timedelta(seconds=(ds1a-ds1b), microseconds=0)
    df2d = tm1 - t0
    df2 = df2d.total_seconds() * 1000
    if args.verbose:
        print('diff:', df2)
    evt = event_n_direc(line, args)
    #rint('tm1:', tm1, 'evt:', evt)
    if args.entries:
        print (f"{tm1} \t{df2:10.0f} {evt[2]} {evt[0]:20} {evt[1]}")
    stss += [(tm1, int(df2), evt[2], evt[0], evt[1])]
    return tm1

# NOT YET: the txt here is from the last ']'
def event_n_direc(txt, args):
    if args.verbose:
        print('txt:', txt)
        print('event_ptrn:', event_ptrn.match(txt))
        print('event_ptrn:', event_ptrn.match(txt).group(1))
        print('event_ptrn:', event_ptrn.match(txt).group(2))
        print('event_ptrn:', event_ptrn.match(txt).group(3))
    if (event_ptrn.match(txt).group(2) == '<<'):
        return (event_ptrn.match(txt).group(1), event_ptrn.match(txt).group(3), "end")
    else:   # (event_ptrn.match(txt).group(2) == '>>'):
        return (event_ptrn.match(txt).group(1), event_ptrn.match(txt).group(3), "frm")


def times(txt, args):
    # convert the timestamp to ms from some epoch
    if args.verbose:
      print('dtm:', datetime_ptrn.match(txt))
      print('dtm:', datetime_ptrn.match(txt).group(2))
    dt_t = datetime_ptrn.match(txt).group(2)
    #dt = datetime.datetime.strptime(dt_t, "%H:%M:%S.%f").time()
    dt = datetime.datetime.strptime(dt_t, "%H:%M:%S.%f")
    if args.verbose:
        print('dt:', dt)
    return dt



def toms(txt, args):
    parts = txt.split()
    if args.verbose:
      print('parts:', parts[0])
      print('dtm:', datetime_ptrn.match(parts[0]))
      print('dtm:', datetime_ptrn.match(parts[0]).group(2))
    dt_t = datetime_ptrn.match(parts[0]).group(2)
    dt = datetime.datetime.strptime(dt_t, "%H:%M:%S.%f").time()
    osd = int(parts[2])
    pg = parts[3]
    op = parts[4:]
    # print('dt:', dt, " -> <<", op, ">>")
    if args.verbose:
        print('osd/pg:', osd, pg)
        print('dt:', dt, " -> <<", op, ">>")
    return (dt, osd, pg, op)


def add_time_of_prev_event(idx, args):
    global stss
    pt = (0, )
    evs = (0, )
    if idx == 0:
        stss[idx] = stss[idx] + pt + evs
        return
    # add the time of the previous event, and another for the length of the event
    if stss[idx][2] == 'end':
        for i in range(idx-1, -1, -1):
            if stss[i][2] == 'end' and stss[i][3] == stss[idx][3] and stss[i][4] == stss[idx][4]:
                #print(
                #    f"adding time of prev event {stss[i][0]} to {stss[idx][0]} a: {stss[i][1]}/{stss[idx][1]} b:{stss[i][3]}/{stss[idx][3]} c:{stss[i][4]}/{stss[idx][4]}")
                pt = (stss[i][1],)
                break
        for i in range(idx-1, -1, -1):
            if stss[i][2] == 'frm' and stss[i][4] == stss[idx][4]:
                evs = (stss[i][1],)
                break
    stss[idx] = stss[idx] + pt + evs

test1 = r'2023-02-27T11:44:27.322+0000 7f4375891700 10 osd.3 pg_epoch: 36455 pg[9.cs0( v 36455\'28682154 (36340\'28672071,36455\'28682154] local-lis/les=36450/36451 n=13996898 ec=4862/4862 lis/c=36450/36450 les/c/f=36451/36451/0 sis=36450) [3,42,79,90,34,52]p3(0) r=0 lpr=36450 luod=36455\'28682152 crt=36455\'28682152 lcod 36455\'28682151 mlcod 36455\'28682151 active+clean+scrubbing+deep [ 9.cs0:  ]  TIME_FOR_DEEP] scrubber <WaitReplicas/>: scrubber event --<< send_scrub_resched)'

main()




#
#def find_last(lst, sought_elt):
#    for r_idx, elt in enumerate(reversed(lst)):
#        if elt == sought_elt:
#            return len(lst) - 1 - r_idx

