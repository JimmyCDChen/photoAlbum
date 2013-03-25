import cgi, cgitb
import urllib
import webapp2
import jinja2
import os
import time
import threading
import Queue
import datetime
from google.appengine.ext import db
from google.appengine.api import users
import gdata.photos.service
import gdata.media
import gdata.geo

albumRef = {}

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
    
class Photo(db.Model):
    photoid = db.StringProperty()
    author = db.StringProperty()
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


class Retrieve(webapp2.RequestHandler):
    photoQueue = Queue.Queue()
    stdout_mutex = threading.Lock()

    def get(self):
        user = users.get_current_user()
        albumName = self.request.get('albumName')
        photoAlbumID = albumRef[albumName]
        gd_client = gdata.photos.service.PhotosService()
        photoList = gd_client.GetFeed('/data/feed/api/user/%s/albumid/%s?kind=photo' % (user, photoAlbumID))

        # Clear all photo data stored in the db
        photoAll = Photo.all()
        db.delete(photoAll)

        for photo in photoList.entry:
            newPhoto = Photo()
            newPhoto.photoid = photo.gphoto_id.text
            newPhoto.thumbnail = photo.media.thumbnail[2].url
            newPhoto.author = photo.media.credit.text
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

            newPhoto.put()
        
        allPhoto = Photo.all()

        template_values = {
                'user': user,
                'allPhoto': allPhoto,
                'albumName': self.request.get('albumName'),
        }
        
        template = jinja_environment.get_template('photo.html')
        self.response.out.write(template.render(template_values))

    # this is executed in one threading.Thread object
    def producer(ID):
        global photoQueue
        user = users.get_current_user()
        gd_client = gdata.photos.service.PhotosService()
        photoList = gd_client.GetFeed('/data/feed/api/user/%s/albumid/%s?kind=photo' % (user, ID))

        for photo in photoList.entry:
            with stdout_mutex:
                photoQueue.put(photo)
                time.sleep(0.05)

    # this is executed in another threading.Thread object
    def consumer():
        global photoQueue
        while True:
            try:
                photo = photoQueue.get(block=false)
            except Queue.Empty:
                # queue is empty
                pass
            else:
                with stdout_mutex:
                    newPhoto = Photo()
                    newPhoto.photoid = photo.gphoto_id.text
                    newPhoto.thumbnail = photo.media.thumbnail[2].url
                    newPhoto.author = photo.media.credit.text
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
                time.sleep(0.05)


class MainPage(webapp2.RequestHandler):
    def get(self):

        user = users.get_current_user()
        albumID = []
        albumTitle = []
        albumPhotoNum = []
        if user is not None:
            logInOut = users.create_logout_url(self.request.uri)
            greeting = "Please Enter Your Picasa Album Address:"
            gd_client = gdata.photos.service.PhotosService()

            try:
                albumList = gd_client.GetUserFeed(user=user)

                for album in albumList.entry:
                    albumID.append(album.gphoto_id.text)
                    albumRef[album.title.text] = album.gphoto_id.text
                    albumTitle.append(album.title.text)
                    albumPhotoNum.append(album.numphotos.text)
            except:
                pass
        else:
    
            logInOut = users.create_login_url(self.request.uri)
            greeting = "Please Login to continue."
                                           
        template_values = {
                'user': user,
                'logInOut': logInOut,
                'greeting': greeting,
                'albumInfo': zip(*(albumTitle, albumID, albumPhotoNum)),
        }
        
        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(template_values))
    
app = webapp2.WSGIApplication([('/', MainPage),
                                ('/Retrieve', Retrieve)],
                               debug=True)
                               