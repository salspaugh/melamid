
import csv

from collections import defaultdict

def fix_csv(csvfile, numcols):
    first = True
    count = 0
    with open(csvfile) as csvdata:
        reader = csv.reader(csvdata)
        for row in reader:
            if first:
                first = False
                continue
            row = [r.replace(",", "") for r in row]
            row.insert(0, str(count))
            print ",".join(row[:numcols])
            count += 1

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Print CSV file to be SQLite3 readable.")
    parser.add_argument("csvfile", metavar="CSVFILE",
                        help="the CSV file to be printed")
    parser.add_argument("numcols", metavar='N', type=int,
                        help="the number of columsn the CSV file should have")
    
    args = parser.parse_args()
    fix_csv(args.csvfile, args.numcols)
