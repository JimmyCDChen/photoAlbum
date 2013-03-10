import cgi, cgitb
import urllib
import webapp2
import jinja2
import os
import thread
from google.appengine.ext import db
from google.appengine.api import users
import gdata.photos.service
import gdata.media
import gdata.geo
import feedparser


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
    

class Photo(db.Model):
  id = db.IntegerProperty()
  author = db.StringProperty()
  title = db.StringProperty()


class Retrieve(webapp2.RequestHandler):
    QUEUE = []
    def get(self):
        user = users.get_current_user()
        photoAlbum = self.request.get('albumName')
        gd_client = gdata.photos.service.PhotosService()
        albums = gd_client.GetUserFeed(user=user)


	# this is executed in one threading.Thread object
    def producer():
        global QUEUE
        while True:
            i = produce_item()
            QUEUE.append(i)

        gd_client = gdata.photos.service.PhotosService()

	# this is executed in another threading.Thread object
    def consumer():
        global QUEUE
        while True:
            try:
                i = QUEUE.pop(0)
            except IndexError:
                # queue is empty
                continue

            consume_item(i)


# Function to retrive the user's public album list
def getAlbumList(userName):
        gd_client = gdata.photos.service.PhotosService()
        albumList = gd_client.GetUserFeed(user=userName)
        albumInfo = []
        for album in albumList:
            albumInfo.append(album.gphoto_id.text)
            albumInfo.append(album.title.text)
            albumInfo.append(album.numphotos.text)

        return albumInfo

class MainPage(webapp2.RequestHandler):
    def get(self):

    	user = users.get_current_user()

        if user is not None:
            logInOut = users.create_logout_url(self.request.uri)
            greeting = "Please Enter Your Picasa Album Address:"
            albumsInfo = Retrieve(user)
            print albumsInfo
        else:
    
            logInOut = users.create_login_url(self.request.uri)
            greeting = "Please Login to continue."
                                           
        template_values = {
        		'user': user,
        		'logInOut': logInOut,
                'greeting': greeting,
                'albumsInfo': albumsInfo,
        }
        
        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(template_values))

#authSubUrl = GetAuthSubUrl();
#print '<a href="%s">Login to your Google account</a>' % authSubUrl

            
    
app = webapp2.WSGIApplication([('/', MainPage),
                                ('/Retrieve', Retrieve)],
                               debug=True)
                               