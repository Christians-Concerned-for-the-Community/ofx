#!/usr/bin/env python3

# dtd.py
#
# Script that reads DTD files from the OFX spec and outputs
# lists of aggregates and elements to a new json file.
#
# Stephen Sorley, 7/20/2024

import argparse
import json

# Helper function for testing if strings are empty or not.
def isBlank(str):
    return (not str) or str.isspace()

argparser = argparse.ArgumentParser("dtd.py")
argparser.add_argument("inputs", nargs="+")
argparser.add_argument("-o","--output",default="output.json")
args = argparser.parse_args()

elements = set()
aggregates = set()

for filename in args.inputs:
    with open(filename, 'r', newline='') as file:
        while line := file.readline():
            if line.startswith('<!ELEMENT '):
                # Parse out the tag name.
                names = line.split()[1]

                if '(' in names:
                    # Remove wrapping parenthesis, if any.
                    names = names[names.find('(')+1:names.rfind(')')]

                    # Split by comma, if there are multiple element names.
                    names = names.split(',')
                else:
                    names = [names]

                # Add it to either elements or aggregates list.
                for name in names:
                    if " - - " in line:
                        aggregates.add(name)
                    else:
                        elements.add(name)


elementList = list(elements)
aggregateList = list(aggregates)

elementList.sort()
aggregateList.sort()

out = {
    "elements": elementList,
    "aggregates": aggregateList
}

with open(args.output, "w", newline='') as file:
    file.write(json.dumps(out))