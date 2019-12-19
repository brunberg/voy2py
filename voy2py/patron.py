import voy2py.item
from .etc import *

class Patron(int):
    def exists(patron):
        if isinstance(patron, int):
            sql = "select count(*) from patron where patron_id = :pid"
            return run(sql, pid=patron).fetchone()[0]
        return None

    def from_barcode(string):
        sql = ''' select distinct patron_id
                  from patron_barcode pb
                  where pb.patron_barcode = :pbc '''
        cursor = run(sql, pbc=string)
        if cursor:
            row = cursor.fetchone()
            if row and not cursor.fetchone():
                return Patron(row[0], exists=True)
        return False

    def from_email(address):
        if (len(address.encode()) != len(address)):  # Won't even try to
            return None                    # handle non-ASCII addresses.
        sql = ''' select distinct pa.patron_id
                  from patron_address pa
                  where pa.address_line1 = :email '''
        cursor = run(sql, email=address)
        if cursor:
            row = cursor.fetchone()
            if row and not cursor.fetchone():
                return Patron(row[0], exists=True)
        return False

    def to_barcode(patron):
        if isinstance(patron, int):
            sql = ''' select distinct patron_barcode
                      from patron_barcode
                      where patron_id = :pid '''
            cursor = run(sql, pid=patron)
            row = cursor.fetchone()
            if row and not cursor.fetchone():
                return row[0]
        return None

    def __new__(cls, patron, exists=None):
        if type(patron) is Patron and (exists or patron.exists()):
            return patron
        elif isinstance(patron, str):
            return Patron.from_barcode(patron)
        elif exists or Patron.exists(patron):
            return super(Patron, cls).__new__(cls, patron)
        return False

    barcode = property(to_barcode)

    @property
    def last_name(self):
        sql = ''' select utl_raw.cast_to_raw(last_name)
                  from patron where patron_id = :pid '''
        row = fetch_single(sql, pid=self)
        return row[0].decode(LEGL) if row else None

    @property
    def pin(self):
        sql = "select patron_pin from patron where patron_id = :pid"
        cursor = run(sql, pid=self)
        if cursor:
            row = cursor.fetchone()
            if row and not cursor.fetchone():
                return row[0]
        return None

    @property
    def email(self):
        sql = ''' select utl_i18n.raw_to_nchar(
                        utl_raw.cast_to_raw(address_line1),
                        'WE8ISO8859P1'
                      ) address
                  from patron_address
                  where patron_id = :pid
                  and address_type = 3 '''
        cursor = run(sql, pid=self)
        if cursor:
            row = cursor.fetchone()
            return row[0] if (row and not cursor.fetchone()
                          ) else False
        return None

    class AccruedFines(CachedRows):
        def __init__(self, patron, tops):
            sql = ''' select fine_fee_id, ff.patron_id, ff.item_id,
                        ff.create_date as ff_create_date,
                        fine_fee_balance, ff.orig_charge_date,
                        ff.due_date as ff_due_date,
                        ff.discharge_date as ff_discharge_date,
                        ct.circ_transaction_id, ct.current_due_date,
                        cta.circ_transaction_id as circ_archive_id,
                        cta.discharge_date as circ_discharge_date
                      from fine_fee ff
                      left join circ_transactions ct
                        on ff.patron_id = ct.patron_id
                        and ff.item_id = ct.item_id
                        and ff.orig_charge_date = ct.charge_date
                      left join circ_trans_archive cta
                        on ff.patron_id = cta.patron_id
                        and ff.item_id = cta.item_id
                        and ff.orig_charge_date = cta.charge_date
                      where ff.patron_id = :pid
                      and ff.fine_fee_type = 8 '''
            super().__init__(Fine_Fee, tops, sql, pid=patron)

    def accrued_fines(patron, tops=100):
        return Patron.AccruedFines(patron, tops)

    class ChargedItems(CachedRows):
        def __init__(self, patron, tops):
            sql = ''' select ct.item_id, ib.item_barcode,
                        ct.charge_date, l.location_name,
                        ct.charge_oper_id, charge_due_date
                      from circ_transactions ct
                      join item_barcode ib on ct.item_id = ib.item_id
                      join location l
                        on ct.charge_location = l.location_id
                      where patron_id = :pid
                      order by charge_date asc '''
            super().__init__(voy2py.item.Item, tops, sql, pid=patron)

    def charged_items(patron, tops=50):
        return Patron.ChargedItems(patron, tops)

    class LastDischargedItems(CachedRows):
        def __init__(self, patron, tops):
            sql = ''' select cta.item_id, item_barcode,
                        circ_transaction_id, discharge_date,
                        discharge_oper_id, discharge_location
                      from circ_trans_archive cta
                      left join item_barcode ib
                        on cta.item_id = ib.item_id
                      where cta.patron_id = :pid
                      and not barcode_status <> 1
                      order by cta.discharge_date desc '''
            super().__init__(voy2py.item.Item, tops, sql, pid=patron)

    def last_discharged_items(patron, tops=1):
        return Patron.LastDischargedItems(patron, tops)
