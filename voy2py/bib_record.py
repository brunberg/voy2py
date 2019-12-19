import voy2py.hold_recall
import voy2py.item
import voy2py.location
from voy2py.etc import *

class Bib_Record(int):
    def exists(record):
        if isinstance(record, int):
            sql = "select count(*) from bib_master where bib_id = :bid"
            return run(sql, bid=record).fetchone()[0]
        return None

    def __new__(cls, record, exists=None):
        if type(record) is Bib_Record and (exists or record.exists()):
            return record
        elif exists or Bib_Record.exists(record):
            return super(Bib_Record, cls).__new__(cls, record)
        return False

    @property
    def data(self):
        sql = ''' select seqnum, utl_raw.cast_to_raw(record_segment)
                  from bib_data
                  where bib_id = :bid
                  order by seqnum '''
        return b''.join([row[1] for row in run(sql, bid=self)])

    def print(self):
        print(next(pymarc.MARCReader(self.data)))

    class History(list):
        def __init__(self, record):
            sql = ''' select bh.action_date, bh.operator_id,
                        bh.location_id, l.location_name,
                        bh.action_type_id, a.action_type,
                        bh.encoding_level, bh.suppress_in_opac
                      from bib_history bh
                      left join location l
                        on bh.location_id = l.location_id
                      left join action_type a
                        on bh.action_type_id = a.action_type_id
                      where bib_id = :bid
                      order by bh.action_date asc '''
            self += (run(sql, bid=record))

        def pretty(self):
            return ['{} {!s:10} {:4} {!s:{z}20} {!s:>7} {} {}'
                    .format(r[0], r[1], r[2], r[3], r[5], r[6], r[7],
                            z=('<' if r[3] else '>'))
                    for r in self]

    def print_history(self):
        for row in Bib_Record.History(self).pretty(): print(row)

    def holding_locations(self):
        sql = ''' select mm.location_id
                  from mfhd_master mm
                  join bib_mfhd bm on mm.mfhd_id = bm.mfhd_id
                  where bm.bib_id = :bid '''
        return [voy2py.location.Location(row[0])
                for row in run(sql, bid=self)]

    def has_title_requests_at(self, location):
        sql = ''' select count(*)
                  from hold_recall hr
                  join request_group_location rgl
                    on hr.request_group_id = rgl.group_id
                  where bib_id = :bid
                  and request_level = 'T'
                  and request_item_count > 0
                  and location_id = :lid '''
        row = fetch_single(sql, bid=self, lid=location)
        return row[0] if row else None

    def holds_recalls(self, cls=voy2py.hold_recall.Hold_Recall):
        sql = ''' select hold_recall_id
                  from hold_recall
                  where bib_id = :bid '''
        return [cls(row[0], exists=True)
                for row in run(sql, bid=self)]

    def items(record, located_in=None, holding_in=None, tops=1000):
        sql_params = {'bid': record}
        sql = ''' select bi.item_id, ib.item_barcode
                  from bib_item bi
                  left join ( select * from item_barcode
                              where barcode_status = 1 ) ib
                    on bi.item_id = ib.item_id
                  left join mfhd_item mi on bi.item_id = mi.item_id
                  left join mfhd_master mm on mi.mfhd_id = mm.mfhd_id
                  left join item i on bi.item_id = i.item_id
                  where bi.bib_id = :bid '''
        if located_in:
            sql += ''' and ( ( i.perm_location = :lid
                               and i.temp_location = 0 )
                             or i.temp_location = :lid ) '''
            sql_params['lid'] = located_in
        if holding_in:
            sql += ' and mm.location_id = :mlid '
            sql_params['mlid'] = holding_in
        return voy2py.item.Item.List(
                voy2py.item.Item, tops, sql, **sql_params)

    @property
    def title(self):
        sql = ''' select utl_raw.cast_to_raw(title) as title
                  from bib_text
                  where bib_id = :bid '''
        row = fetch_single(sql, bid=self)
        return row[0].decode(WCS8) if row else None
