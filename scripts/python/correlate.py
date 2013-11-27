
import math

class Table(object):

    def __init__(self):
        self.counts = {}
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

def read_domains(db, table):
    pass

def compute_pairings(dbtab):
    pass

def select_tuples(colx, coly, dbtab):
    pass

def compute_contingency_table(colx, coly, dbtab, domains):
    table = Table()
    tuples = select_tuples(colx, coly, dbtab)
    for (x, y) in tuples:
        if x in domains[x] and y in domains[y]:
            table.increment(x, y)
    return table

def compute_expected_table(contingency_table):
    expected_table = Table()
    for (x, xcount) in contingency_table.row_totals.iteritems():
        for (y, ycount) in contingency_table.col_totals.iteritems():
            expected_value = xcount*ycount/contingency_table.grand_total
            expected_table.set(x, y, expected_value)
    return expected_table

def compute_residuals(contingency_table, expected_table):
    residual_table = Table()
    for (x, y) in contingency_table.variables:
        observed = contigency_table.counts[x][y]
        expected = expected_table.counts[x][y]
        residual_value = (observed - expected) / math.sqrt(observed)
        residual_table.set(x, y, residual_value)
    return residual_table 

def output_residuals(x, y, residuals):
    pass

def compute_correlations(dbtab):
    domains = read_domains(dbtab)
    for (x, y) in compute_pairings(dbtab):
        contigency_table = compute_contingency_table(x, y, dbtab, domains)
        expected_table = compute_expected_table(x, y)
        residuals = compute_residuals(contigency_table, expected_table)
        output_residuals(x, y, residuals)
