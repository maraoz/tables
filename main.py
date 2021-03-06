#!/usr/bin/env python


import webapp2, json, jinja2, os, logging, datetime
from model import Table, Seat, EMPTY, RESERVED, OCCUPIED, SEAT_RESERVATION_TIME
from blockchain import new_address, btc2satoshi, callback_secret_valid, get_tx, sendmany

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

HOUSE_EDGE = 0.2
HOUSE_ADDRESS = "1PMFUYoqpGP7n5R4VoBGmfWrcD67bc9eYC"

class StaticHandler(webapp2.RequestHandler):
    def get(self, _):
        name = self.request.path.split("/")[1]
        if name == "":
            name = "index"
            
        values = {
            "name": name
        }
        
        try:
            self.response.write(JINJA_ENVIRONMENT.get_template("/templates/" + name + '.html').render(values))
        except IOError, e:
            self.error(404)
            self.response.write("404: %s not found! %s" % (name, e))

class JsonAPIHandler(webapp2.RequestHandler):
    def post(self):
        self.get()
    def get(self):
        resp = self.handle()
        self.response.headers['Content-Type'] = "application/json"
        dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
        self.response.write(json.dumps(resp, default=dthandler))

class BootstrapHandler(JsonAPIHandler):
    def handle(self):
        p = float(self.request.get("p"))
        SEATS_PER_TABLE = 10
        for price in [p]:
            t = Table(price=btc2satoshi(price))
            t.put()
            for n in xrange(SEATS_PER_TABLE):
                seat = Seat(table=t, number=n, purchase_addr=new_address(), state=EMPTY)
                seat.table = t
                seat.put()
                from time import sleep
                sleep(1)
                
        return {"success":True}

class CallbackHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(self.handle())

    def get_pay_addr(self, tx):
        return tx.get("inputs")[0].get("prev_out").get("addr")
    
    def process_bet(self, address, better, value):
        seat = Seat.get_by_address(address)
        if not seat:
            return {"success": False, "reason": "Seat for address %s not found" % (address)}
        if seat.table.price > value:
            logging.warn("Table price higher than paid value: (%s > %s)" % (seat.table.price, value))
            return "*ok*"
        if not seat.is_reserved():
            logging.warn("Received payment for a seat that isn't reserved: (%s, %s, %s)" % (seat.number, seat.table.price, value))
            return "*ok*" 
        seat.occupy(better)
        return "*ok*"
    
    def handle(self):
        secret = self.request.get("secret")
        if not callback_secret_valid(secret):
            return "error: secret"
        test = self.request.get("test") == "true"
        try:
            tx_hash = self.request.get("transaction_hash")
            address = self.request.get("address")
            value = int(self.request.get("value"))
        except ValueError, e:
            return "error: value error"
        
        if not tx_hash:
            return "error: no transaction_hash"
    
        if not address:
            return "error: no address"
        
        if value <= 0:  # outgoing payment
            return "*ok*"
        
        
        tx = get_tx(tx_hash)
        if not tx:
            return "error: unable to retrieve tx."
        better = self.get_pay_addr(tx)
        
        if not test:
            return self.process_bet(address, better, value) 
        return "*ok*"
    
class TableInfoHandler(JsonAPIHandler):
    def handle(self):
        price = int(self.request.get("price"))
        if not price:
            return {"success": False, "error": "price parameter not found"}
        table = Table.get(price).to_dict_with_seats()
        if not table:
            return {"success": False, "error": "table not found"}
        return {"success":True, "table": table}

class TablesListHandler(JsonAPIHandler):
    def handle(self):
        return {"success":True, "list": Table.get_all()}

class SeatHandler(JsonAPIHandler):
    def handle(self):
        price = int(self.request.get("price"))
        n = int(self.request.get("n"))
        if not price:
            return {"success": False, "error": "parameter not found"}
        seat = Seat.get(price, n)
        if not seat:
            return {"success": False, "error": "seat not found"}
        return self.handle_seat(seat)

class SeatReserveHandler(SeatHandler):
    def handle_seat(self, seat):
        address = seat.reserve()
        if not address:
            return {"success": False, "error": "seat already reserved"}
        return {"success":True, "address": address}

class SeatCancelHandler(SeatHandler):
    def handle_seat(self, seat):
        return {"success": seat.cancel()}


class PayoutTaskHandler(JsonAPIHandler):
    def handle(self):
        for table in Table.all():
            if table.is_ready():
                gh = table.pick_random()
                players = gh.players
                winner_address = players[gh.winner]
                # TODO: should separate payment from table restart
                total_satoshis = table.price * len(players)
                payout = int(total_satoshis * (1 - HOUSE_EDGE))
                sendmany([
                    (winner_address, payout),
                    (HOUSE_ADDRESS, total_satoshis - payout)
                ])
                
                
        return {"success":True}

class UnreserveTaskHandler(JsonAPIHandler):
    def handle(self):
        for seat in Seat.get_reserved():
            seat.check_reservation()
        return {"success":True}

   
app = webapp2.WSGIApplication([
    # cron tasks
    ('/tasks/payout', PayoutTaskHandler),
    ('/tasks/unreserve', UnreserveTaskHandler),
    
    
    # static files
    ('/((?!api).)*', StaticHandler),
    
    # API
    # frontend
    ('/api/tables/list', TablesListHandler),
    ('/api/tables/get', TableInfoHandler),
    ('/api/seat/reserve', SeatReserveHandler),
    ('/api/seat/cancel', SeatCancelHandler),
    # backend
    ('/api/bootstrap', BootstrapHandler),
    ('/api/callback', CallbackHandler),
    
], debug=False)

