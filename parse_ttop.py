#!/usr/bin/env python

import re
import sys

import dateutil.parser

TOTAL_HEAP_ALLOCATION_RATE = re.compile(r".*heap allocation rate (.*)$")
RATESTRING = re.compile(r"^(-?\d+)(.*\/s)$")
THREAD = re.compile(r"\[(\d+)\] user= *(-?\d+\.\d+)\% sys= *(-?\d+\.\d+)\% alloc= *(-?\d+.*\/s) *\- *(.*)$")

def data_rate_to_megabytes_per_second(ratestring):
    rate_and_units = RATESTRING.match(ratestring)
    if rate_and_units:
        rate = rate_and_units.group(1)
        units = rate_and_units.group(2)
        rate = int(rate)
        if units == "b/s":
            rate = 1.0 * rate / (1024**2)
        if units == "kb/s":
            rate = 1.0 * rate / 1024
        return rate
    else: 
        raise "Garbage ratestring"

if len(sys.argv) != 2:
    raise "NEED EXACTLY A FILENAME\n"

records = []

# states in the state machine
S_GET_DATETIME = 1
S_GET_TOTAL_HEAP_ALLOCATION_RATE = 2
S_GET_THREAD_RECORD = 3

state = S_GET_DATETIME

with open(sys.argv[1],"r") as f:
    for line in f:
        
        if state == S_GET_DATETIME:
            if "Process summary" in line:
                try:
                    dt = dateutil.parser.parse(line.split(" ")[0])
                    print dt

                    # need to look at what graph programs want to consume
                    rec = {"datetime" : dt}
                    state = S_GET_TOTAL_HEAP_ALLOCATION_RATE
                except:
                    continue

        elif state == S_GET_TOTAL_HEAP_ALLOCATION_RATE:
            heap_allocation_rate = TOTAL_HEAP_ALLOCATION_RATE.match(line)
            if heap_allocation_rate:
                print data_rate_to_megabytes_per_second( heap_allocation_rate.group(1) )
                state = S_GET_THREAD_RECORD

        elif state == S_GET_THREAD_RECORD:
            # handle the "  no safe points" line -- just move on til we find a "["
            if line[0:2] == "  ":
                continue

            # after checking the above special case, if we find something other
            # than a "[", record this record, then transition back to looking for a new record
            if line[0] != "[":
                state = S_GET_DATETIME
                # FIXME: RECORD RECORD INTO LIST OR EMIT IT OR SOMETHING
                continue

            print line
            thread_info = THREAD.match(line)
            print "*" + str(thread_info.groups()) + "*"


#print sorted(records, cmp=lambda x: x[0])
