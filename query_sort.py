"""Querysort for WE1S (WhatEvery1Says)
"""

def find(substr, infile, outfile):
    """copy any lines with matching string from infile to outfile"""
    with open(infile) as fin, open(outfile, 'w') as fout:
        for line in fin:
            if substr in line:
                fout.write(line)

# Example usage:
find('the arts',
     'queries_7.20.18_rows2-401_all.csv',
     'queries_7.20.18_rows2-401_arts.csv')
