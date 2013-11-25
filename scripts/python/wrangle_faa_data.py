
import csv

def fix_csv(csvfile):
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
            print ",".join(row)
            count += 1

fix_csv("data/faa/On_Time_On_Time_Performance_2013_1.csv")

def print_column_names(csvfile):
    with open(csvfile) as csvdata:
        reader = csv.reader(csvdata)
        for row in reader:
            for column_name in row:
                print column_name
            return

def transpose_some_rows(csvfile):
    columns = []
    first = True
    count = 0
    with open(csvfile) as csvdata:
        reader = csv.reader(csvdata)
        for row in reader:
            if first:
                for item in row:
                    columns.append([item])
                first = False
                continue
            i = 0
            for item in row:
                columns[i].append(item)
                i += 1
            count += 1
            if count > 2:
                break
    for row in columns:
        print row

def add_id(csvfile):
    count = 0
    with open(csvfile) as csvdata:
        reader = csv.reader(csvdata)
        for row in reader:
            row.insert(0, count)
            print ",".join([str(r) for r in row])
            count += 1
