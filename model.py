from google.appengine.ext import db


class Table(db.Model):
    timestamp = db.DateTimeProperty(required=True, auto_now_add=True)
    

