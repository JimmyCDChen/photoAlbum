from google.appengine.ext import db

class Album(db.Model):
    owner = db.StringProperty()
    albumName = db.StringProperty()
    albumID = db.StringProperty()
    albumPhoto = db.StringProperty()

class Photo(db.Model):
    photoid = db.StringProperty()
    owner = db.StringProperty()
    title = db.StringProperty()
    time = db.DateTimeProperty(auto_now_add=True)
    exposure = db.StringProperty()
    focallength = db.StringProperty()
    make = db.StringProperty()
    fstop = db.StringProperty()
    model = db.StringProperty()
    flash = db.StringProperty()
    iso = db.StringProperty()
    thumbnail = db.StringProperty()