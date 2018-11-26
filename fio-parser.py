#!/usr/bin/env python3
#
# fio-parser
#
#

import sys
import os
import getopt
import re
import time
from datetime import datetime
import csv
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')

col_names = ["job", "cluster", "buffered", "group", "threads", "rdate", 
     "files", "filesize", "fileunit", "mode", "aggrb", "bw",
     "rw", "bs", "bsunit", "ioengine", "iodepth"]

# CSV file output handler
def output_csv_file(fh, data, delimiter):
    writer = csv.writer(fh, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    writer.writerows(data)

def get_fio_logs(path):
    fio_logs = []

    for dir_name, directories, files in os.walk(path):
        if files:
            for name in files:
                if not 'stderr' in name:
                    fname = os.path.join(dir_name, name)
                    fio_logs.append(fname)
    return fio_logs

def parse_log(fname):
    logging.debug("parsing: %s" %(fname))
    f = open(fname, 'rb')
    job = ""
    cluster = os.path.basename(fname).split("-")[1]
    group = 999
    buffered = (0 if 'unbuffered' in fname else 1)
    threads = 999
    rdate = ""
    files = 0
    filesize = 0
    fileunit = ""
    mode = ""
    aggrb = ""
    bw = ""
    rw = ""
    bs = 0
    bsunit = ""
    ioengine = ""
    iodepth = 0
    for line in f.readlines():
        line = line.decode('utf-8', 'ignore').rstrip()
        if re.match(r'^.*groupid=\d+', line):
# fio-ssdnode-read-unbuffered-block_512k-size_2G-threads_1: (groupid=0, jobs=1): err= 0: pid=3551804: Sun Oct  7 14:16:29 2018
            g = re.search('([^\s]+): \(groupid\=(\d+).*? jobs=(\d).*?: (\w+ \w+\s+\d+ \d+:\d+:\d+ \d+)', line)
            job = g.group(1)
            group = int(g.group(2))
            threads = int(g.group(3))
            rdate = g.group(4)
            # Sat Oct  6 07:56:49 2018
            rdate = datetime.strptime(rdate, '%c')
            rdate = rdate.strftime("%Y-%m-%d %H:%M:%S")
        elif 'Laying out IO file' in line:
# fio-ssdnode-read-unbuffered-block_512k-size_2G-threads_1: Laying out IO file(s) (4 file(s) / 8192MB)
            g = re.search('\((\d+) file.*? (\d+)(\w+)\)', line)
            files = int(g.group(1))
            filesize = int(g.group(2))/files
            fileunit = g.group(3)
#   read : io=136245MB, bw=581307KB/s, iops=567, runt=240002msec
#   write: io=80338MB, bw=342773KB/s, iops=334, runt=240002msec
        elif ' read :' in line or ' write:' in line:
            g = re.search('(read |write): .*? bw=(\d+.*?), ', line)
            mode = g.group(1).rstrip().lower()
            bw = g.group(2)
            if bw.endswith("KB/s"):
                bw = str(round(int(bw[:-4])/1024))
            elif bw.endswith("MB/s"):
                bw = str(int(round(float(bw[:-4]))))
        elif 'READ:' in line or 'WRITE:' in line:
# READ: io=131951MB, aggrb=562988KB/s, minb=562988KB/s, maxb=562988KB/s, mint=240001msec, maxt=240001msec
            g = re.search('(READ|WRITE): .*? aggrb=(\d+.*?), ', line)
            if not g:
# READ: bw=568MiB/s (595MB/s), 568MiB/s-568MiB/s (595MB/s-595MB/s), io=133GiB (143GB), run=240001-240001msec
                g = re.search('(READ|WRITE): .*?bw=(\d+.*?) ', line)
            mode = g.group(1).lower()
            aggrb = g.group(2)
            if aggrb.endswith("KB/s"):
                aggrb = str(round(int(aggrb[:-4])/1024))
            elif aggrb.endswith("MB/s"):
                aggrb = str(int(round(float(aggrb[:-4]))))
        elif 'ioengine=' in line:
# rw=rw, bs=512K-512K/512K-512K/512K-512K, ioengine=psync, iodepth=1
# fio-ssdnode-read-unbuffered-block_512k-size_2G-threads_1: (g=0): 
# rw=rw, bs=(R) 512KiB-512KiB, (W) 512KiB-512KiB, (T) 512KiB-512KiB, ioengine=psync, iodepth=1
            g = re.search('rw=(\w+), bs=(\d+)(\w+).*?, ioengine=(\w+), iodepth=(\d+)', line)
            if not g:
                g = re.search('rw=(\w+), bs=.*?(\d+)(\w+).*, ioengine=(\w+), iodepth=(\d+)', line)
            # print(repr(g))
            rw = g.group(1).lower()
            bs = int(g.group(2))
            bsunit = g.group(3)
            ioengine = g.group(4)
            iodepth = int(g.group(5))

    f.close()

    row = {"job": job, "cluster": cluster, "buffered": buffered, "group": group, "threads": threads, "rdate": rdate, 
         "files": files, "filesize": filesize, "fileunit": fileunit, "mode": mode, "aggrb": aggrb, "bw": bw,
         "rw": rw, "bs": bs, "bsunit": bsunit, "ioengine": ioengine, "iodepth": iodepth}
    logging.debug( ", ".join(["%s: %s " %(n, str(row[n])) for n in col_names]))
    if group == 999 or aggrb == "" or bw == "":
        logging.warn("Parse error with file: %s" % (fname))
    return row

        # buffered/unbuffered - direct=0/1
        # read/rwrite -  rw=readwrite,rwmixread=100, rwmixwrite=0/rw=readwrite, rwmixread=0, rwmixwrite=100
        # nrfiles - 4
        # blksize - BS="16k 64k 128k 512k 1024k"
        # filesize - FS="1G 2G 4G"
        # ioengine - psync
        # nrthreads - FIO_NUM_THREADS="1 2 4 8" numjobs=$threads
        # cluster - from name TMPD="/mnt/openhpc/pxh/fio-tests/ /mnt/ssdnode/pxh/fio-tests/ /mnt/nvmenode/pxh/fio-tests/"
        # beginning:
        # fio-read-unbuffered-block_1024k-size_1G-threads_1: (groupid=0, jobs=1): err= 0: pid=1068708: Sat Oct  6 07:56:49 2018
        # io rate: aggrb
        # Run status group 0 (all jobs):
        #   READ: io=83184MB, aggrb=354916KB/s, minb=354916KB/s, maxb=354916KB/s, mint=240001msec, maxt=240001msec
        # Run status group 0 (all jobs):
        #  WRITE: io=76897MB, aggrb=328074KB/s, minb=328074KB/s, maxb=328074KB/s, mint=240013msec, maxt=240013msec
    

def print_help():
    print("%s [-h] [-i|--dir DIRECTORY] [-o|--out file.csv] [-d|--debug]" % (sys.argv[0]))


def main(argv):
    
    try:
        opts, args = getopt.getopt(argv,"hdi:o:", ["dir=","out=", "debug"])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    
    fho = None

    for opt, arg in opts:
        if (opt == '-h'):
            print_help()
            sys.exit()
        elif (opt in ("-d","--debug")):
            logging.getLogger().setLevel(logging.DEBUG)
        elif (opt in ("-i","--dir")):
            log_files = get_fio_logs(arg)
        elif (opt in ("-o","--out")):
            fho = open(arg, 'w')

    if fho == None:
        fho = sys.stdout
    
    # parse log files
    fio_readings = []
    for fname in log_files:
        readings = parse_log(fname)
        fio_readings.append(readings)

    logging.info("Number of jobs: %d" % len(fio_readings))


    rows = [[r[c] for c in col_names] for r in fio_readings]

    # output as CSV again
    logging.info("column names out: " + str(col_names))
    rows.insert(0, col_names)

    output_csv_file(fho, rows, ",")


if __name__ == "__main__":
    main(sys.argv[1:])
