import cgi, cgitb
import urllib
import webapp2
import jinja2
import os, time, datetime
from models import Album, Photo
from tool import render_template, writeToDB
from Queue import Queue
from threading import Thread, Lock
from google.appengine.ext import db
from google.appengine.api import users
import gdata.photos.service
import gdata.media

numProducer = 1
numConsumer = 1

#def producer(threadID, albumID):
#    global photoQueue
#    user = users.get_current_user()
#    gd_client = gdata.photos.service.PhotosService()
#    photoList = gd_client.GetFeed('/data/feed/api/user/%s/albumid/%s?kind=photo' % (user, albumID))
#
#    for photo in photoList.entry:
##        with stdout_mutex:
 #           photoQueue.put(photo)
 #           time.sleep(0.1)

# this is executed in another threading.Thread object
def consumer(queue, numPhoto, nickname, lock):
#    metadata = [exposure, focallength, make, fstop, model, flash, iso]
    lock.acquire()
    for i in range(int(numPhoto)):
        photo = queue.get()
        writeToDB(photo, nickname)
        queue.task_done()

    # release when all photo are added into db        
    lock.release()

class Retrieve(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        albumName = self.request.get('name')
        nickname = users.get_current_user().nickname()
        
        # Clear all photo data stored in the db
        query = "Where owner = '%s'" % (user)
        allPhoto = Photo.gql(query)
        db.delete(allPhoto)
        # Get selected album with owner
        query = "Where albumName = '%s' AND owner ='%s'" % (albumName, nickname)
        selectedAlbum = Album.gql(query)
        # Pre-select if album is empty
        if selectedAlbum[0].albumPhoto == '0':
            template_values = {
                'user': user,
                'albumName': albumName,
            }
            render_template(self, 'photo.html', template_values)

        gd_client = gdata.photos.service.PhotosService()
        photoList = gd_client.GetFeed('/data/feed/api/user/%s/albumid/%s?kind=photo' % (user, selectedAlbum[0].albumID))

        # initialize Lock and Queue objects
        lock = Lock()
        photoQueue = Queue()

        for photo in photoList.entry:
            photoQueue.put(photo)

        # start consumer
        for i in range(numConsumer):
            worker = Thread(target=consumer, args=(photoQueue, selectedAlbum[0].albumPhoto, nickname, lock))
            worker.start()

#        for thread in joinable:
#            thread.join()
        photoQueue.join()

        # All consumer thread are finished, empty photoQueue
#        with stdout_mutex:
        print "All done"

        lock.acquire()
        time.sleep(1)
        query = "Where owner = '%s'" % (nickname)
        allPhoto = Photo.gql(query)
        print allPhoto.count()

        template_values = {
                'user': user,
                'allPhoto': allPhoto,
                'albumName': albumName,
        }
        lock.release()

        render_template(self, 'photo.html', template_values)

class MainPage(webapp2.RequestHandler):
    def get(self):
    	user = users.get_current_user()
        if user is not None:
            nickname = users.get_current_user().nickname()
            logInOut = users.create_logout_url(self.request.uri)
            greeting = "Please Enter Your Picasa Album Address:"
            gd_client = gdata.photos.service.PhotosService()
            
            # try delete the user's album in the DB
            # pass if can't find.
            try:
                query = "Where owner = '%s'" % (nickname)
                allAlbum = Album.gql(query)
                db.delete(allAlbum)
            except:
                print "no album deleted for %s" % (nickname)
                pass

            # Grab user album list from Google Picasa and store in DB    
            try:
                albumList = gd_client.GetUserFeed(user=user)
                for album in albumList.entry:
                    newAlbum = Album()
                    newAlbum.owner = nickname
                    newAlbum.albumName = album.title.text
                    newAlbum.albumID = album.gphoto_id.text
                    newAlbum.albumPhoto = album.numphotos.text
                    newAlbum.put()
            except:
                print "%s album not added into DB" % (nickname)
                pass
                    # Grab all available albums for the user
            nickname = users.get_current_user().nickname()
            query = "Where owner = '%s'" % (nickname)
            time.sleep(1)
            allAlbum = Album.gql(query)
            print query
            print allAlbum.count()

            template_values = {
                    'user': user,
                    'logInOut': logInOut,
                    'greeting': greeting,
                    'albumInfo': allAlbum,
            }
            return render_template(self, 'index.html', template_values)
        
        else:
            logInOut = users.create_login_url(self.request.uri)
            greeting = "Please Login to continue."

            template_values = {
                'user': user,
                'logInOut': logInOut,
                'greeting': greeting,
            }
            return render_template(self, 'index.html', template_values)
        return render_template(self, 'index.html', template_values)

app = webapp2.WSGIApplication([('/', MainPage),
                                ('/Retrieve/', Retrieve)],
                               debug=True)
                               