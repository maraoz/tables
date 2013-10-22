#!/usr/bin/env python


import webapp2, json, jinja2, os, logging, datetime
from model import Table, Seat, EMPTY, RESERVED, OCCUPIED
from blockchain import new_address, btc2satoshi, callback_secret_valid, get_tx

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

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
        SEATS_PER_TABLE = 3
        if len(Seat.get_all()) == 0:
            for price in [0.001, 0.01, 0.1]:
                t = Table(price=btc2satoshi(price))
                t.put()
                for n in xrange(SEATS_PER_TABLE):
                    seat = Seat(table=t, number=n, purchase_addr=new_address(), state=EMPTY)
                    seat.table = t
                    seat.put()
                
        return {"success":True}

class CallbackHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(self.handle())

    def get_pay_addr(self, tx):
        return tx.get("inputs")[0].get("prev_out").get("addr")
    
    def process_bet(self, tx, address, better):
        pass
    
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
            result = self.process_bet(tx, address, better)
        
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

class SeatReserveHandler(JsonAPIHandler):
    def handle(self):
        price = int(self.request.get("price"))
        n = int(self.request.get("n"))
        if not price or not n:
            return {"success": False, "error": "parameter not found"}
        seat = Seat.get(price, n)
        if not seat:
            return {"success": False, "error": "seat not found"}
        address = seat.reserve()
        if not address:
            return {"success": False, "error": "seat already reserved"}
        return {"success":True, "address": address}

    
app = webapp2.WSGIApplication([
    ('/((?!api).)*', StaticHandler),
    # API
    #frontend
    ('/api/tables/list', TablesListHandler),
    ('/api/tables/get', TableInfoHandler),
    ('/api/seat/reserve', SeatReserveHandler),
    #backend
    ('/api/bootstrap', BootstrapHandler),
    ('/api/callback', CallbackHandler),
], debug=True)

