import cgi, cgitb
import urllib
import webapp2
import jinja2
import os, time, datetime
from models import Album, Photo
from Queue import Queue
from google.appengine.api import users
import gdata.photos.service
import gdata.media

def render_template(self, template_name, template_vals=None):
    template_path = os.path.join(os.path.dirname(__file__) , 'templates')
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_path))
    template = env.get_template(template_name)
    self.response.out.write(template.render(template_vals))

def writeToDB(photo, nickname):
    newPhoto = Photo()
    newPhoto.owner = nickname
    newPhoto.photoid = photo.gphoto_id.text
    newPhoto.thumbnail = photo.media.thumbnail[2].url
    newPhoto.title = photo.title.text
    try:
        newPhoto.time = datetime.datetime.fromtimestamp(float(photo.exif.time.text) / 1e3)
    except:
        pass
    try:
        newPhoto.exposure = photo.exif.exposure.text
    except:
        pass
    try:
        newPhoto.focallength = photo.exif.focallength.text
    except:
        pass
    try:
        newPhoto.make = photo.exif.make.text
    except:
        pass
    try:
        newPhoto.fstop = photo.exif.fstop.text
    except:
        pass
    try:
        newPhoto.model = photo.exif.model.text
    except:
        pass
    try:
        newPhoto.flash = photo.exif.flash.text
    except:
        pass
    try:
        newPhoto.iso = photo.exif.iso.text
    except:
        pass
    # Add to db after retrieved
    newPhoto.put()
    