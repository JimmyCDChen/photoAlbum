import cgi, cgitb
import urllib
import webapp2
import jinja2
import os, sys
import datetime
from Queue import Queue
from threading import Thread, Lock
import time
from google.appengine.ext import db
from google.appengine.api import users
import gdata.photos.service
import gdata.media

albumRef = {}
albumPhoto = {}
numProducer = 1
numConsumer = 1

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

#def producer(threadID, albumID):
#    global photoQueue
#    user = users.get_current_user()
#    gd_client = gdata.photos.service.PhotosService()
#    photoList = gd_client.GetFeed('/data/feed/api/user/%s/albumid/%s?kind=photo' % (user, albumID))
#
#    for photo in photoList.entry:
##        with stdout_mutex:
 #           print "111"
 #           photoQueue.put(photo)
 #           time.sleep(0.1)

photoQueue = Queue()

           
# this is executed in another threading.Thread object
def consumer(queue, numPhoto, lock):
#    global photoQueue
    lock.acquire()
    for i in range(int(numPhoto)):
        print "I'm trying", i
        photo = queue.get()

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
        print "a photo has been added to Queue"
        photoQueue.task_done()

    # release when all photo are added into db        
    lock.release()

class Retrieve(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        albumName = self.request.get('albumName')
        photoAlbumID = albumRef[albumName]
        numPhoto = albumPhoto[albumName]

#        joinable = []
#        # Call producer to retrieve photos
#        for i in range(numProducer):
#            t = threading.Thread(target=producer, args=(i, photoAlbumID))
#            joinable.append(t)
#            t.start()

        # Clear all photo data stored in the db
        photoAll = Photo.all()
        db.delete(photoAll)

        gd_client = gdata.photos.service.PhotosService()
        photoList = gd_client.GetFeed('/data/feed/api/user/%s/albumid/%s?kind=photo' % (user, photoAlbumID))


        lock = Lock()

        for photo in photoList.entry:
            photoQueue.put(photo)

        # start consumer
        for i in range(numConsumer):
            worker = Thread(target=consumer, args=(photoQueue, numPhoto, lock))
            worker.start()

#        for thread in joinable:
#            thread.join()
        photoQueue.join()

        sys.stdout.write("All photo has been added into Queue.\n")
        # All consumer thread are finished, empty photoQueue
#        with stdout_mutex:
        print "All done"

        lock.acquire()
        time.sleep(0.5)
        allPhoto = Photo.all()
        print allPhoto.count()

        template_values = {
                'user': user,
                'allPhoto': allPhoto,
                'albumName': albumName,
        }
        template = jinja_environment.get_template('photo.html')
        lock.release()
        self.response.out.write(template.render(template_values))

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
                    albumPhoto[album.title.text] = album.numphotos.text
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
        
        template = jinja_environment.get_template('Index.html')
        self.response.out.write(template.render(template_values))

app = webapp2.WSGIApplication([('/', MainPage),
                                ('/Retrieve', Retrieve)],
                               debug=True)
                               