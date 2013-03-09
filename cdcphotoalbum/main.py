#!/usr/bin/env python
import cgi, cgitb
import datetime
import urllib
import webapp2
import jinja2
import os
import thread
import re
from django.shortcuts import render_to_response
from xml.etree import ElementTree

from google.appengine.ext import db
from google.appengine.api import users

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
    
class Categories(db.Model):
  author = db.StringProperty()
  category = db.StringProperty()

# Insert or edit a new item into a category
class Category(webapp2.RequestHandler):
  def post(self):

    user = users.get_current_user().nickname()
    submit = self.request.get('submit')
    newcat = self.request.get('content')
    response =""
    
    if submit == "Add":
      checkcategory = Categories.all().filter("category =", newcat).get()
      if checkcategory is None:
        newcategory = Categories()
        newcategory.author = self.request.get('user')
        newcategory.category = self.request.get('content')
        newcategory.put()
      else:
        response = "This category name is used, please choose another name."
        
    elif submit == "Delete":
      deletename = self.request.get('deletename')
      checkcategory = Categories.all().filter("category =", deletename).filter("author =", user).get()
      checkitem = Item.all().filter("categories =", deletename).filter("author =", user)
      if checkcategory is None:
        # The old name doesn't exist in the database
        response = "This item does not exist. Plese enter a valid item name to delete."
      else:
        if checkcategory.author == user:
          db.delete(checkcategory)
          db.delete(checkitem)
          response = "You have successfully delete an item."
        else:
          response = "This item is not owned by you, no changes made"  
    
    self.redirect('/?' + urllib.urlencode({'categories': self.request.get('content')}) + urllib.urlencode({'response': response}))
  
class Item(db.Model):
  author = db.StringProperty()
  categories = db.StringProperty()
  item = db.StringProperty()
  win = db.IntegerProperty()
  lose = db.IntegerProperty()
  percentage = db.StringProperty()

def percentage(part, whole):
  return 100 * float(part)/float(whole)
  
# Insert or edit a new item into a category
class Itembook(webapp2.RequestHandler):
  def get(self):

    user = users.get_current_user().nickname()
    category = self.request.get('category')
    item_input = self.request.get('content')
    choice = self.request.get('choice')
    item1_old = self.request.get('item1')
    item2_old = self.request.get('item2')   
    greeting =""
    submit = self.request.get('submit')
    
    # get category owner
    catowner = Categories.all().filter("category =", category).get()
    
    if submit == "Vote":
      # edit the voting result
      if choice == "1":
        # choose 1st choice
        item = Item.all().filter("categories =", category).filter("item =", item1_old).get()
        item.win = item.win +1
        item.percentage = "{0:.0f}%".format(percentage(item.win, (item.win + item.lose)))
        item.put()
        
        item = Item.all().filter("categories =", category).filter("item =", item2_old).get()
        item.lose = item.lose +1
        item.percentage = "{0:.0f}%".format(percentage(item.win, (item.win + item.lose)))
        item.put()
        
        greeting = "You choose %s over %s" % (item1_old, item2_old)
      elif choice == "2":
        # choose 2nd choice
        item = Item.all().filter("categories =", category).filter("item =", item2_old).get()
        item.win = item.win +1
        item.percentage = "{0:.0f}%".format(percentage(item.win, (item.win + item.lose)))
        item.put()
        
        item = Item.all().filter("categories =", category).filter("item =", item1_old).get()
        item.lose = item.lose +1
        item.percentage = "{0:.0f}%".format(percentage(item.win, (item.win + item.lose)))
        item.put()
        greeting = "You choose %s over %s" % (item2_old, item1_old)
    
    if catowner is None or user == catowner.author:
      if submit == "Add":        
          # New category with items to add
          if item_input != "" :
              checkitem = Item.all().filter("categories =", category).filter("item =", item_input).get()
              if checkitem is None:
                  # add new item into category
                  item = Item()
                  item.author = users.get_current_user().nickname()
                  item.categories = category
                  item.item = item_input
                  item.win = 0
                  item.lose = 0
                  item.percentage = "-"
                  item.put()
                  greeting = "Item %s is added into Category %s" % (item_input, category)
              else:
                  greeting = "This item exists in the category already."
      elif submit == "Edit":
          oldname = self.request.get('oldname')
          newname = self.request.get('newname')
          checkitem = Item.all().filter("categories =", category).filter("author =", user).filter("item =", oldname).get()
          if checkitem is None:
              # The old name doesn't exist in the database
              greeting = "This item does not exist. Plese enter a valid item name to change."
          else:
              if checkitem.author == user:
                  checkitem.item = newname
                  checkitem.put()
                  greeting = "You have successfully edit an item."
              else:
                  greeting = "This item is not owned by you, no changes made"
      elif submit == "Delete":
          deletename = self.request.get('deletename')
          checkitem = Item.all().filter("categories =", category).filter("author =", user).filter("item =", deletename).get()
          if checkitem is None:
              # The old name doesn't exist in the database
              greeting = "This item does not exist. Plese enter a valid item name to delete."
          else:
              if checkitem.author == user:
                  db.delete(checkitem)
                  greeting = "You have successfully delete an item."
              else:
                  greeting = "This item is not owned by you, no changes made"
      elif submit == "DeleteALL":
          checkitem = Item.all().filter("categories =", category).filter("author =", user)
          test = checkitem.get()
          if test is None:
              # The old name doesn't exist in the database
              greeting = "No item exists."
          else:
              if test.author == user:
                  db.delete(checkitem)
                  greeting = "You have successfully made change."
              else:
                  greeting = "This item is not owned by you, no changes made"
    else:
      greeting ="Sorry, only the owner of this category can make changes."
      
    # For voting purposes
    itemlist = Item.all().filter("categories =", category).order("-win")
    itemlist_total = itemlist.count()
    if itemlist_total >= 2:
        one = random.randrange(0, itemlist_total)
        two = random.randrange(0, itemlist_total)
        while one == two:
            two = random.randrange(0, itemlist_total)
        item_one = itemlist[one]
        item_two = itemlist[two]        
    else:
        item_one = "NULL"
        item_two = "NULL"        
        
    template_values = {
        'user': user,
        'owner': catowner.author,
        'category': category,
        'item_one': item_one,
        'item_two': item_two,
        'greeting': greeting,
        'itemlist': itemlist,
    }
        
    template = jinja_environment.get_template('item.html')
    self.response.out.write(template.render(template_values))

class Item(db.Model):
  author = db.StringProperty()
  categories = db.StringProperty()
  item = db.StringProperty()
  win = db.IntegerProperty()
  lose = db.IntegerProperty()
  percentage = db.StringProperty()
  date = db.DateTimeProperty(auto_now_add=True)

def percentage(part, whole):
  return 100 * float(part)/float(whole)

class MainPage(webapp2.RequestHandler):
    def get(self):
        # verify if the user is logged in or logged out
        submit = self.request.get('submit')
        
        response = self.request.get('response')
        greeting = "Please enter the album url to begin."
        noAlbum = True


        return render_to_response(request, 'index.html', locals())
                                   
#        template = jinja_environment.get_template('index.html')
#        self.response.out.write(template.render(template_values))
            
    
app = webapp2.WSGIApplication([('/', MainPage)],
                               debug=True)
                               
