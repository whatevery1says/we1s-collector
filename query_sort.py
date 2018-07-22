"""Querysort for WE1S (WhatEvery1Says)
"""

def find(substr, infile, outfile):
  with open(infile) as a, open(outfile, 'w') as b:
   for line in a:
    if substr in line:
     b.write(line)
 
# Example usage:
find('the arts', 'queries_7.20.18_rows2-401_all.csv', 'queries_7.20.18_rows2-401_arts.csv')
