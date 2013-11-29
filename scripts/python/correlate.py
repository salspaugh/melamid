
from json import load
from math import sqrt
from sqlite3 import connect

class Table(object):

    def __init__(self, x, y):
        self.counts = {}
        self.x = x
        self.y = y
        self.row_totals = {}
        self.col_totals = {}
        self.grand_total = 0.
        self.variables = set()

    def init(self, x, y):
        self.variables.add((x,y))
        if not x in self.counts:
            self.counts[x] = {}
        if not y in self.counts[x]:
            self.counts[x][y] = 0.
        if not x in self.row_totals:
            self.row_totals[x] = 0.
        if not y in self.col_totals:
            self.col_totals[y] = 0.

    def increment(self, x, y):
        self.init(x, y)
        self.counts[x][y] += 1.
        self.row_totals[x] += 1.
        self.col_totals[y] += 1.
        self.grand_total += 1.

    def set(self, x, y, value):
        self.init(x, y)
        self.counts[x][y] = value

    def _flesh_out_counts(self):
        for (row, cols) in self.counts.iteritems():
            for col in self.col_totals.keys():
                if not col in cols:
                    self.counts[row][col] = 0.

    def __repr__(self):
        self._flesh_out_counts()
        s = ""
        fixed = []
        for (row, cols) in self.counts.iteritems():
            fixed.append((row, sorted(cols.items(), key=lambda x: x[0])))
        if not fixed:
            return ""
        num_cols = len(self.col_totals) + 1
        cols = [x[0] for x in fixed[0][1]]
        col_widths = [max([len(x[0])+1 for x in fixed])] + \
                        [max([len(str(y))+1 for y in x])+1 for x in fixed[0][1]]
        col_widths = "|".join(["{:<%d}"]*(num_cols)) % tuple(col_widths)
        s = col_widths.format(*([""] + cols)) 
        for row in fixed:
            r = col_widths.format(*([row[0]] + [x[1] for x in row[1]]))
            s = "\n".join([s, r])
        return s

DEBUG = False
def debug(s):
    if DEBUG:
        print s

def compute_correlations(db, table, metadata):
    domains = read_domains(metadata)
    for (x, y) in compute_pairings(metadata):
        contingency_table = compute_contingency_table(x, y, db, table, domains)
        expected_table = compute_expected_table(contingency_table)
        residuals = compute_residuals(contingency_table, expected_table)
        output_residuals(x, y, residuals)

def read_domains(metadata):
    with open (metadata) as metadata:
        metadata = load(metadata)
        metadata = filter(lambda x: x["type"] != "quantitative", metadata)
        names = [column["name"] for column in metadata]
        domains = [column["domain"] for column in metadata]
        metadata = dict(zip(names, domains))
    return metadata

def compute_pairings(metadata):
    debug("Computing pairings.")
    pairs = []
    with open (metadata) as metadata:
        metadata = load(metadata)
        metadata = filter(lambda x: x["type"] != "quantitative", metadata)
        for i in range(len(metadata)):
            columni = metadata[i]
            for j in range(i+1, len(metadata)):
                columnj = metadata[j]
                pairs.append((columni["name"], columnj["name"]))
    return pairs

def compute_contingency_table(colx, coly, db, table, domains):
    debug("Computing contingency tables.")
    contingency_table = Table(colx, coly)
    tuples = select_tuples(colx, coly, db, table)
    for (x, y) in tuples:
        if x in domains[colx] and y in domains[coly] and \
            valid(x, domains[colx]) and valid(y, domains[coly]):
            contingency_table.increment(x, y)
    return contingency_table

def select_tuples(colx, coly, db, table):
    debug("Selecting tuples.")
    db = connect(db)
    statement = "SELECT %s, %s FROM %s" % (colx, coly, table)
    cursor = db.execute(statement)
    return cursor.fetchall()

def valid(value, domain):
    label = domain[value].lower()
    return not ((label.find("missing") > -1) or \
        (label.find("not in sample this wave") > -1) or \
        (label.find("test not comp") > -1) or \
        (label.find("multiple respnse") > -1) or \
        (label.find("legitimate skip") > -1) or \
        (label.find("refusal") > -1))

def compute_expected_table(contingency_table):
    debug("Computing expected tables.")
    expected_table = Table(contingency_table.x, contingency_table.y)
    for (x, xcount) in contingency_table.row_totals.iteritems():
        for (y, ycount) in contingency_table.col_totals.iteritems():
            expected_value = xcount*ycount/contingency_table.grand_total
            expected_table.set(x, y, expected_value)
    return expected_table

def compute_residuals(contingency_table, expected_table):
    debug("Computing residuals.")
    residual_table = Table(contingency_table.x, contingency_table.y)
    for (x, y) in contingency_table.variables:
        observed = contingency_table.counts[x][y]
        expected = expected_table.counts[x][y]
        residual_value = (observed - expected) / sqrt(observed)
        residual_table.set(x, y, residual_value)
    return residual_table 

def output_residuals(x, y, residuals):
    print x, y
    print residuals
    print 

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Compute categorical correlations for a data set.")
    parser.add_argument("db", metavar="DATABASE",
                        help="database containing the data set")
    parser.add_argument("table", metavar="TABLE",
                        help="table containing the data set")
    parser.add_argument("metadata", metavar="METADATA",
                        help="file containing the metadata")
    
    args = parser.parse_args()
    compute_correlations(args.db, args.table, args.metadata) 
