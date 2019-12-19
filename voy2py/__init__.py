''' This is voy2py by Brunberg, J., HelsinkiUni (2017–2019). '''

from .bib_record import Bib_Record
from .hold_recall import Hold_Recall
from .item import Item
from .location import Location
from .patron import Patron

IDENTITY_CLASSES = [
    Bib_Record,
#    Circ_Trans_Archive,
#    Fine_Fee,
    Hold_Recall,
    Item,
    Location,
    Patron,
]

from .etc import describe
from .etc import process
from .etc import query
