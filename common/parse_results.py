# usage: python parse_results.py <perflog_path> <output_string> <start string> <end string>

import sys

perflog_path = sys.argv[1]
output_string = sys.argv[2]
start_string = sys.argv[3]
end_string = sys.argv[4]

# read the perflog file
start_ticks = -1
end_ticks = -1
with open(perflog_path, 'r') as file:
    lines = file.readlines()
    for line in lines:
        if start_string in line:
            start_ticks = int(line.split()[1])
        if end_string in line:
            end_ticks = int(line.split()[1])

assert start_ticks != -1 and end_ticks != -1, "Didn't found start or end ticks, perflog must contain start and end strings"
# print decimal number with 2 decimal places (extend if necessary)
print(output_string, "{:.10f}".format((end_ticks - start_ticks) / 2e9) + "ms")

