import voy2py.bib_record
import voy2py.item
from .etc import *

class Statuses(dict):
    def __init__(self):
        for row in run(''' select hr_status_type, hr_status_desc
                           from hold_recall_status '''):
            self[row[0]] = row[1]

class _ArchivedOrNot(int):
    def exists(hold_recall, tbl=None):
        tbl = tbl if tbl else (hold_recall.TABLE if
                isinstance(hold_recall, _ArchivedOrNot) else None)
        if isinstance(hold_recall, int) and tbl:
            sql = ''' select count(*)
                      from ''' + tbl + '''
                      where hold_recall_id = :hrid '''
            return run(sql, hrid=hold_recall).fetchone()[0]
        return None

    def __new__(cls, hold_recall, exists=None):
        if isinstance(hold_recall, _ArchivedOrNot) and \
                (exists or hold_recall.exists()):
            return hold_recall
        elif exists or _ArchivedOrNot.exists(hold_recall, cls.TABLE):
            return super(_ArchivedOrNot, cls).__new__(cls, hold_recall)
        return False

    @property
    def bib_record(self):
        row = fetch_single(''' select bib_id
                               from ''' + self.TABLE + '''
                               where hold_recall_id = :hrid ''',
                           hrid=self)
        return voy2py.bib_record.Bib_Record(row[0]) if row else False

    def items(self, tops=100):
        return self.Items(self, tops)

class Archived(_ArchivedOrNot):
    TABLE = 'hold_recall_archive'
    ITEMS_TABLE = 'hold_recall_item_archive'

    class Items(CachedRows):
        def __init__(self, hold_recall, tops):
            sql = ''' select item_id, hold_recall_type,
                        hold_recall_status, hold_recall_status_date
                      from ''' + Archived.ITEMS_TABLE + '''
                      where hold_recall_id = :hrid '''
            super().__init__(
                    voy2py.item.Item, tops, sql, hrid=hold_recall)

class Hold_Recall(_ArchivedOrNot):
    TABLE = 'hold_recall'
    ITEMS_TABLE = 'hold_recall_items'

    class Items(CachedRows):
        def __init__(self, hold_recall, tops):
            sql = ''' select item_id, queue_position, hold_recall_type,
                        hold_recall_status, hold_recall_status_date
                      from ''' + Hold_Recall.ITEMS_TABLE + '''
                      where hold_recall_id = :hrid '''
            super().__init__(
                    voy2py.item.Item, tops, sql, hrid=hold_recall)
