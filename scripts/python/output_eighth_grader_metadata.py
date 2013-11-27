
from sqlite3 import connect

import json

class Column(object):
    
    def __init__(self, name):
        self.name = name
        self.label = ""
        self.type = "nominal"
        self.domain = {}

    def jsonify(self):
        d = {}
        d["name"] = self.name
        d["label"] = self.label
        d["type"] = self.type
        d["domain"] = self.domain
        return d

def read_column_names(schema):
    columns = {}
    with open(schema) as schema:
        for line in schema.readlines():
            line = line.strip()
            if not ("TEXT" in line or "INTEGER" in line):
                continue
            name = line.strip(",").split(" ")[0]
            columns[name] = Column(name)
    return columns

def read_metadata(schema, metadata):
    columns = read_column_names(schema)
    with open(metadata) as metadata:
        last_columns = []
        codes = False
        for line in metadata.readlines():
            line = line.strip()
            if line.find("BY") == 0 or line.find("G8") == 0 or line.find("F1") == 0:
                column = line.split(" ")
                name = column[0].lower()
                label = " ".join(column[1:]).strip()
                column = columns.get(name, None)
                if column:
                    column.label = label
                    last_columns.append(column)
            if line.find("------") == 0:
                codes = False
                last_columns = []
            if line.find("Code") == 0:
                codes = True
                continue
            if codes:
                line = line.split(" ")
                value = line[0]
                label = " ".join(line[1:]).strip()
                for column in last_columns:
                    column.domain[value] = label
    return columns

def output_metadata(schema, metadata):
    columns = read_metadata(schema, metadata)
    columns = columns.values()
    columns = [c.jsonify() for c in columns]
    print json.dumps(columns, indent=4, separators=(',', ': '))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Output a metadata file \
                        about the domain of each column for the NELS data.")
    parser.add_argument("schema", metavar="SCHEMA_FILE",
                        help="the SQL schema file")
    parser.add_argument("metadata", metavar="METADATA_FILE", 
                        help="the codebook")
    args = parser.parse_args()
    output_metadata(args.schema, args.metadata)

