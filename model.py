from google.appengine.ext import db
from random import randint
import datetime

EMPTY, RESERVED, OCCUPIED = 0, 1, 2
SEAT_STATES = [EMPTY, RESERVED, OCCUPIED]

SEAT_RESERVATION_TIME = datetime.timedelta(minutes=5)

class SerializableModel(db.Model):
    def to_dict(self):
        return db.to_dict(self)
    
class Table(SerializableModel):
    price = db.IntegerProperty(required=True)  # in satoshis
    
    def is_ready(self):
        return all(seat.is_occupied() for seat in self.seats)
    
    def is_full(self):
        return not any(seat.is_empty() for seat in self.seats)
    
    def pick_random(self):
        if not self.is_ready():
            raise ValueError
        
        players = [seat.owner for seat in sorted(self.seats, key= lambda x: x.number)]
        winner = randint(0, len(players)-1)
        gh = GameHistory(table=self, winner=winner, players=players)
        gh.put()
        for seat in self.seats:
            seat.free()
        return gh
    
    def to_dict_with_seats(self):
        d = self.to_dict()
        d["seats"] = [seat.to_dict() for seat in self.seats]
        return d
    
    @classmethod
    def get(cls, price):
        return cls.all().filter("price =", price).get()
    
    @classmethod
    def get_all(cls):
        un = [table.to_dict_with_seats() for table in cls.all()]
        un.sort(key=lambda table: table["price"], reverse=True)
        return un
    
class Seat(SerializableModel):
    table = db.ReferenceProperty(Table, collection_name='seats')
    number = db.IntegerProperty(required=True)
    purchase_addr = db.StringProperty(required=True)
    state = db.IntegerProperty(required=True, choices=SEAT_STATES)
    owner = db.StringProperty()
    reserved_since = db.DateTimeProperty()
    
    def is_empty(self):
        return self.state == EMPTY
    
    def is_occupied(self):
        return self.state == OCCUPIED
    
    def is_reserved(self):
        return self.state == RESERVED
    
    def reserve(self):
        if not self.is_empty():
            return None
        self.state = RESERVED
        self.reserved_since = datetime.datetime.now()
        self.put()
        return self.purchase_addr
    
    def occupy(self, owner):
        if not self.is_reserved():
            return False
        self.owner = owner
        self.state = OCCUPIED
        self.put()
        return True

    def free(self):
        self.owner = None
        self.reserved_since = None
        self.state = EMPTY
        self.put()
        return True
    
    def cancel(self):
        if not self.is_reserved():
            return False
        self.owner = None
        self.reserved_since = None
        self.state = EMPTY
        self.put()
    
    def check_reservation(self):
        now = datetime.datetime.now()
        if now > self.reserved_since + SEAT_RESERVATION_TIME:
            self.free()
    
    @classmethod
    def get_reserved(cls):
        return cls.all().filter("state =", RESERVED)
    
    @classmethod
    def get_all(cls):
        return [seat.to_dict() for seat in cls.all().run()]
    
    @classmethod
    def get(cls, price, n):
        table = Table.get(price)
        if not table:
            return None
        return cls.all().filter("table =", table).filter("number =", n).get()
    
    @classmethod
    def get_by_address(cls, address):
        return cls.all().filter("purchase_addr =", address).get()
    

class GameHistory(SerializableModel):
    timestamp = db.DateTimeProperty(required=True, auto_now_add=True)
    table = db.ReferenceProperty(Table, required=True)
    winner = db.IntegerProperty(required=True)
    players = db.StringListProperty(required=True)
    
