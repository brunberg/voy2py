import cx_Oracle

import csv
import pymarc

from db_login import DB_INSTANCE
from db_login import DB_RO_USER
from db_login import DB_RO_PW

WCS8 = 'utf-8'      # Multibyte encoding for wide characters in metadata
LEGL = 'latin-1'             # Legacy 8-bit Latin database character set

db_connection = cx_Oracle.Connection(
        DB_RO_USER, DB_RO_PW, DB_INSTANCE)

def run(sql, **params):
    cursor = db_connection.cursor()
    cursor.execute(sql, params)
    return cursor

def generate_decoded(cursor, prefix='U_', charset=WCS8, fallback=LEGL):
    for row in cursor:
        row = list(row)
        for cnum, (cval, cdes) in enumerate(
                zip(row, cursor.description)):
            if cdes[1] == cx_Oracle.BINARY and None != cval:
                row[cnum] = cval.decode(WCS8) \
                        if cdes[0].startswith(prefix) \
                        else cval.decode(LEGL)
        yield row

def process(file, **params):
    with open(file, 'r') as _inf:
        sql = _inf.read()
    cursor = run(sql, **params)
    generator = generate_decoded(cursor)
    with open('result.csv', 'w') as _outf:
        output = csv.writer(_outf, dialect='excel')
        output.writerow([col[0] for col in cursor.description])
        for row in generator:
            output.writerow(row)

def query(sql, **params):
    cursor = run(sql, **params)
    generator = generate_decoded(cursor)
    print([col[0] for col in cursor.description])
    for satisfaction, row in enumerate(generator):
        if satisfaction < 100:
            print(row)
        else:
            print("...")
            break

def describe(table):
    cursor = run('''select count(*)
                    from all_tables
                    where table_name = upper(:tbl)''', tbl=table)
    if cursor and 1 == cursor.fetchone()[0]:
        query('select * from {} where 1 = 0'.format(table))

def fetch_single(sql, **params):
    cursor = db_connection.cursor()
    cursor.execute(sql, params)
    if cursor:
        row = cursor.fetchone()
        if row and not cursor.fetchone():
            return row
    return False

class CachedRows(list):
    def __init__(self, row_class, tops, sql, **params):
        cursor = db_connection.cursor()
        cursor.execute(sql, params)
        col_names = [col[0] for col in cursor.description]
        for row in cursor.fetchmany(tops):
            item = bless(row[0], row_class, exists=True, classy=True)
            item._cache = {}
            for colno in range(1, len(col_names)):
                item._cache[col_names[colno]] = row[colno]
            self.append(item)
        self.filled = bool(cursor.fetchone())

    @property
    def caches(self):
        return [row._cache for row in self]

    def pretty(self):
        for row in self:
            print(row, row._cache)
        if self.filled:
            print("...")

class Circ_Trans_Archive(int): pass
class Fine_Fee(int):
    class List(CachedRows):
        def pretty(self):
            print('Patron   Item       Barcode     '
                  'FT Created              Amount Balance')
            for row in self:
                print('{:8} {:10} {:11} '
                      '{:2} {:19} {:7.2f} {:7.2f}'.format(
                        row._cache['PATRON_ID'],
                        row._cache['ITEM_ID'],
                        row._cache['ITEM_BARCODE'],
                        row._cache['FINE_FEE_TYPE'],
                        row._cache['CREATE_DATE'].isoformat(' '),
                        row._cache['FINE_FEE_AMOUNT']/100,
                        row._cache['FINE_FEE_BALANCE']/100))
            if self.filled:
                print("...")

def bless(item, row_class, exists=None, classy=None):
    from . import IDENTITY_CLASSES
    if row_class in IDENTITY_CLASSES:    # row_class can test existence,
        if exists:              # ... and we are requested to skip that.
            return row_class(item, exists=True)
    elif not classy:
        return None
    return row_class(item)
