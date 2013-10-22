from google.appengine.ext import db
from random import randint
import logging

EMPTY, RESERVED, OCCUPIED = 0, 1, 2
SEAT_STATES = [EMPTY, RESERVED, OCCUPIED]

HOUSE_EDGE = 0.2
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
        
        winner = randint(0, len(self.seats))
        players = [seat.owner for seat in self.seats]
        gh = GameHistory(table=self, winner=winner, players=players)
        gh.put()
        return gh
    
    def to_dict_with_seats(self):
        d = self.to_dict()
        d["seats"] = [seat.to_dict() for seat in self.seats]
        return d
    
    @classmethod
    def get(cls, price):
        return cls.all().filter("price =", price).get().to_dict_with_seats()
    
    @classmethod
    def get_all(cls):
        return [table.to_dict_with_seats() for table in cls.all()]
    
class Seat(SerializableModel):
    table = db.ReferenceProperty(Table, collection_name='seats')
    number = db.IntegerProperty(required=True)
    purchase_addr = db.StringProperty(required=True)
    state = db.IntegerProperty(required=True, choices=SEAT_STATES)
    owner = db.StringProperty()
    
    def is_empty(self):
        return self.state == EMPTY
    
    def is_occupied(self):
        return self.state == OCCUPIED
    
    def is_reserved(self):
        return self.state == RESERVED
    
    def reserve(self):
        if not self.is_empty():
            raise ValueError 
        self.state = RESERVED
        self.put()
        return self.purchase_addr
    
    def occupy(self, owner):
        if not self.is_reserved():
            raise ValueError 
        self.owner = owner
        self.state = OCCUPIED
        self.put()
    
    @classmethod
    def get_all(cls):
        return [seat.to_dict() for seat in cls.all().run()]
    

class GameHistory(SerializableModel):
    timestamp = db.DateTimeProperty(required=True, auto_now_add=True)
    table = db.ReferenceProperty(Table, required=True)
    winner = db.IntegerProperty(required=True)
    players = db.StringListProperty(required=True)
    
