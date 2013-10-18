#!/usr/bin/env python


import webapp2, json, jinja2, os, logging, datetime
from model import Table, Seat, EMPTY, RESERVED, OCCUPIED
from blockchain import new_address, btc2satoshi

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
    
class TablesListHandler(JsonAPIHandler):
    def handle(self):
        return {"success":True, "list": Table.get_all()}

    
app = webapp2.WSGIApplication([
    ('/((?!api).)*', StaticHandler),
    # API
    #frontend
    ('/api/tables/list', TablesListHandler),
    #backend
    ('/api/bootstrap', BootstrapHandler),
], debug=True)

