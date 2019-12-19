import voy2py.bib_record
import voy2py.location
import voy2py.patron
from .etc import *

class Item(int):
    def exists(item):
        if isinstance(item, int):
            sql = "select count(*) from item where item_id = :iid"
            return run(sql, iid=item).fetchone()[0]
        return None

    def from_barcode(string):
        sql = ''' select distinct item_id
                  from item_barcode ib
                  where ib.item_barcode = :ib '''
        cursor = run(sql, ib=string)
        if cursor:
            row = cursor.fetchone()
            if row and not cursor.fetchone():
                return Item(row[0], exists=True)
        return False

    def to_barcode(item):
        if isinstance(item, int):
            sql = ''' select distinct item_barcode
                      from item_barcode ib
                      where ib.item_id = :iid '''
            cursor = run(sql, iid=item)
            row = cursor.fetchone()
            if row and not cursor.fetchone():
                return row[0]
        return None

    def __new__(cls, item, exists=None):
        if type(item) is Item and (exists or item.exists()):
            return item
        elif isinstance(item, str):
            return Item.from_barcode(item)
        elif exists or Item.exists(item):
            return super(Item, cls).__new__(cls, item)
        return False

    barcode = property(to_barcode)

    @property
    def charged_to(self):
        row = fetch_single(''' select patron_id
                               from circ_transactions
                               where item_id = :iid ''', iid=self)
        return voy2py.patron.Patron(row[0]) if row else None

    @property
    def charge_date(self):
        row = fetch_single(''' select charge_date
                               from circ_transactions
                               where item_id = :iid ''', iid=self)
        return row[0] if row else False

    @property
    def location(self):
        row = fetch_single(''' select perm_location, temp_location
                               from item
                               where item_id = :iid ''', iid=self)
        return (voy2py.location.Location(row[1])
                if row[1] else voy2py.location.Location(row[0])) \
            if row else None

    @property
    def holding_location(self):
        row = fetch_single(''' select location_id
                               from mfhd_item mi
                               join mfhd_master mm
                                 on mi.mfhd_id = mm.mfhd_id
                               where item_id = :iid ''', iid=self)
        return voy2py.location.Location(row[0]) if row else False

    @property
    def perm_location(self):
        sql = 'select perm_location from item where item_id = :iid'
        row = fetch_single(sql, iid=self)
        return voy2py.location.Location(row[0]) if row else False

    @property
    def temp_location(self):
        sql = 'select temp_location from item where item_id = :iid'
        row = fetch_single(sql, iid=self)
        return voy2py.location.Location(row[0]) if row else False

    def bib_records(item):
        sql = "select bib_id from bib_item where item_id = :iid"
        return [voy2py.bib_record.Bib_Record(row[0], exists=True)
                for row in run(sql, iid=item)]

    class List(CachedRows):
        def barcodes(self):
            return [item._cache['ITEM_BARCODE'] for item in self]

    class Status(int):
        class Types(dict):
            def __init__(self):
                sql = ''' select item_status_type, item_status_desc
                          from item_status_type '''
                cursor = db_connection.cursor()
                cursor.execute(sql)
                for row in cursor:
                    self[row[0]] = row[1]

    def statuses(item):
        sql = ''' select item_status, item_status_date
                  from item_status where item_id = :ii '''
        status_list = []
        for row in run(sql, ii=item):
            status = Item.Status(row[0])
            status_list.append((status, row[1]))
        return status_list

    class Type(int):
        @property
        def code(self):
            sql = ''' select item_type_code
                      from item_type
                      where item_type_id = :itid '''
            row = fetch_single(sql, itid=self)
            return row[0] if row else False

        @property
        def name(self):
            sql = ''' select item_type_name
                      from item_type
                      where item_type_id = :itid '''
            row = fetch_single(sql, itid=self)
            return row[0] if row else False

        @property
        def display_name(self):
            sql = ''' select item_type_display
                      from item_type
                      where item_type_id = :itid '''
            row = fetch_single(sql, itid=self)
            return row[0] if row else False

    @property
    def item_type(self):
        sql = 'select item_type_id from item where item_id = :iid'
        row = fetch_single(sql, iid=self)
        return Item.Type(row[0]) if row else False

    @property
    def temp_item_type(self):
        sql = 'select temp_item_type_id from item where item_id = :iid'
        row = fetch_single(sql, iid=self)
        return Item.Type(row[0]) if row else False

    def unpaid_fees(item, tops=100):
        sql = '''
            select ff.fine_fee_id, ff.patron_id,
              ff.item_id, ib.item_barcode,
              ff.fine_fee_type, ff.create_date,
              ff.fine_fee_amount, ff.fine_fee_balance
            from fine_fee ff
            left join item_barcode ib on ff.item_id = ib.item_id
            where ff.item_id = :iid
            and ff.fine_fee_balance > 0
            order by ff.patron_id, ff.create_date desc
        '''
        return Fine_Fee.List(Fine_Fee, tops, sql, iid=item)

    class LastReturnedTransactions(CachedRows):
        def __init__(self, item, tops=1):
            sql = ''' select circ_transaction_id, discharge_date,
                        cta.patron_id, patron_barcode
                      from circ_trans_archive cta
                      left join patron_barcode pb
                        on cta.patron_id = pb.patron_id
                      where cta.item_id = :iid
                      and pb.barcode_status = 1
                      order by cta.discharge_date desc '''
            super().__init__(Circ_Trans_Archive, tops, sql, iid=item)

        def get_patron(self, i=0):
            if (0 == i or type(i) is int) and i < len(self):
                return voy2py.patron.Patron(
                        self[0]._cache['PATRON_ID'], True)

        patron = property(get_patron)

        def pretty(self):
            for item in self:
                print('{} {}'.format(
                        item._cache['PATRON_BARCODE'],
                        str(item._cache['DISCHARGE_DATE'])))

    def last_returned(item, tops=1):
        return Item.LastReturnedTransactions(item, tops)
