import voy2py.bib_record
import voy2py.item
from .etc import *

class Location(int):
    def exists(location):
        if isinstance(location, int):
            sql = ''' select count(*)
                      from location
                      where location_id = :lid '''
            return fetch_single(sql, lid=location)[0]
        return None

    def from_code(code):
        sql = ''' select location_id
                  from location
                  where location_code = :lcode '''
        row = fetch_single(sql, lcode=code)
        return Location(row[0], exists=True) if row else None

    def to_code(location):
        if isinstance(location, int):
            sql = ''' select location_code
                      from location
                      where location_id = :lid '''
            row = fetch_single(sql, lid=location)
            return row[0] if row else False

    def __new__(cls, loc, exists=None):
        if type(loc) is Location and (exists or loc.exists()):
            return loc
        elif isinstance(loc, str):
            return Location.from_code(loc)
        elif exists or Location.exists(loc):
            return super(Location, cls).__new__(cls, loc)

    code = property(to_code)

    @property
    def name(self):
        sql = ''' select utl_i18n.raw_to_nchar(
                      utl_raw.cast_to_raw(location_name),
                      'WE8ISO8859P1'
                    ) as location_name
                  from location
                  where location_id = :lid '''
        row = fetch_single(sql, lid=self)
        return row[0] if row else None

    @property
    def display_name(self):
        sql = ''' select utl_i18n.raw_to_nchar(
                      utl_raw.cast_to_raw(location_display_name),
                      'WE8ISO8859P1'
                    ) as location_display_name
                  from location
                  where location_id = :lid '''
        row = fetch_single(sql, lid=self)
        return row[0] if row else None

    class WithNamesLike(CachedRows):
        def __init__(self, name, tops=1000):
            sql = ''' select location_id, location_code,
                        location_name, location_display_name,
                        suppress_in_opac, mfhd_count
                      from location
                      where location_name like :lname
                      or location_display_name like :lname '''
            super().__init__(Location, tops, sql, lname=name)

    def bib_records(mfhd_loc):
        sql = ''' select distinct bm.bib_id
                  from bib_mfhd bm
                  join mfhd_master mm on bm.mfhd_id = mm.mfhd_id
                  where mm.location_id = :lid '''
        return [voy2py.bib_record.Bib_Record(row[0], exists=True)
                for row in run(sql, lid=mfhd_loc)]

    def items(location):
        sql = ''' select item_id from item where 
                    temp_location = :loc or (
                      temp_location = 0 and perm_location = :loc ) '''
        return [voy2py.item.Item(row[0], exists=True)
                for row in run(sql, loc=location)]

    class PhantomHoldsOfHoldingsItems(CachedRows):
        def __init__(self, location):
            sql = ''' select hold_recall_id, patron_id,
                        hold_recall_type, expire_date '''
