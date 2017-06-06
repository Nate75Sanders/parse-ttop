#!/usr/bin/env python

import pprint
import re
import sys

import dateutil.parser

TOTAL_HEAP_ALLOCATION_RATE = re.compile(r".*heap allocation rate (.*)$")
RATESTRING = re.compile(r"^(-?\d+)(.*\/s)$")
THREAD = re.compile(r"\[(\d+)\] user= *(-?\d+\.\d+)\% sys= *(-?\d+\.\d+)\% alloc= *(-?\d+.*\/s) *\- *(.*)$")

# sincerely no idea if ttop can show "gb/s" -- probably not very common for the JVM to do this
# maybe I should investigate the code for ttop more closely sometime
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

num_records = 0

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
                    
                    # need to look at what time format graphing programs want to consume
                    rec = {"datetime" : dt, "threads" : []}
                    state = S_GET_TOTAL_HEAP_ALLOCATION_RATE
                except:
                    continue

        elif state == S_GET_TOTAL_HEAP_ALLOCATION_RATE:
            heap_allocation_rate = TOTAL_HEAP_ALLOCATION_RATE.match(line)
            if heap_allocation_rate:
                rec['total_heap_allocation_rate'] = data_rate_to_megabytes_per_second( heap_allocation_rate.group(1) )
                state = S_GET_THREAD_RECORD

        elif state == S_GET_THREAD_RECORD:
            # handle the "  no safe points" line -- just move on til we find a "["
            if line[0:2] == "  ":
                continue

            # after checking the above special case, if we find something other
            # than a "[", record this record, then transition back to looking for a new record
            if line[0] != "[":
                state = S_GET_DATETIME
                records.append(rec)
                num_records += 1
                continue

            thread_info = THREAD.match(line)
          
            if thread_info:
                thread_rec = {}
                thread_rec['thread_id'] = thread_info.group(1)
                thread_rec['user_cpu'] = float( thread_info.group(2) )
                thread_rec['kernel_cpu'] = float( thread_info.group(3) )
                thread_rec['thread_heap_alloc'] = data_rate_to_megabytes_per_second( thread_info.group(4) )
                thread_rec['thread_name'] = thread_info.group(5)

                rec['threads'].append(thread_rec)

pprint.pprint(records)
print num_records
