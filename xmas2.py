#!/usr/bin/python2.4
# -*- coding: UTF-8 -*-
#
# Copyright 2011 James Hurley, Inc. All Rights Reserved

"""The script that powers the Gifty app! Cleanup!

This file controls all aspects of the Gifty model. It creates 3 entity groups
in the datastore (Gift, GiftUser, and Group) and maps classes to different
aspects of the site.

Trying to remove index-old.
"""

__author__ = "jhurley@gmail.com (James Hurley)"

import cgi
import datetime
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.db import djangoforms
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import mail
import os

from model import gModel
from model import helper

class LoginCheck(webapp.RequestHandler):
  """This is a superclass that checks if the user is logged-in."""

  def check_login(self):

    # Determine whether the user is logged in or not.
    if users.get_current_user():
      self.ldapName = (users.get_current_user().nickname()).lower()
      url = users.create_logout_url("/")
      self.login_link = '<a href="' + url + '">Log out</a>'
      self.url = url

      # Test to see if the User has ever signed into the product before, or has 
      # already been added to a group by a friend. If not, create them in the 
      # GiftUser entity.
      if gModel.GiftUser.getCurrentUser() == None:
        giftuser = gModel.GiftUser()
        giftuser.giftUserName = (users.get_current_user().nickname()).lower()
        giftuser.giftUserEmail = (users.get_current_user().email()).lower()
        giftuser.giftUserNickname = (users.get_current_user().nickname()).lower()
        giftuser.groups = []
        giftuser.put()
      currentUser = gModel.GiftUser.getCurrentUser()          
      self.nickname = currentUser.giftUserNickname
            
      # Return a list of the Groups that the logged-in User belongs to.
      self.userGroups = gModel.GiftUser.getUserGroups(currentUser)      

    else:
      url = users.create_login_url(self.request.uri)
      self.url = url
      self.login_link = '<a href="' + url + '">Log in</a>'
      self.nickname = ""
      self.ldapName = ""
      self.userGroups = [] 
      

class MainPage(LoginCheck):
  """This class controls the main page of the site, index.html."""
  
  def get(self):
    
    self.check_login()
  
    nameInURL = self.request.get('n')
    thisGroup = self.request.get('gid')
    
    belongsInGroup = "no"
    if thisGroup:
      thisGroupKey = gModel.Group.getGroupKey(thisGroup)
    else:
      thisGroupKey = 0
 
    # Check the gid in the URL to verify that the logged-in user is a member of that group.
    for group in self.userGroups:
      if str(group.key().id()) == thisGroup:
        belongsInGroup = "yes"
 
    # Populate list of all names in the current Group, given the Group's Key in the data store  
    validNames = []
    validNamesList = gModel.Group.getMembers(thisGroupKey)
    for names in validNamesList:
      validNames.append((names.giftUserName,names.giftUserNickname))
    
    # Identify the User Name of the person whose page the User is viewing.
    # TODO: Change this when we eliminate the need for giftUserName later
    theName = ""
    for uName, nick in validNames:
      if nick == nameInURL:
        theName = uName
    
    # Two queries; one for the gifts the User has chosen to purchase, and one for the gifts the User has requested
    myPurchasedGifts = gModel.Gift.gql("WHERE purchaser = :1 AND group = :2 ORDER BY date",
                                theName, thisGroupKey)
    myGifts = gModel.Gift.gql("WHERE requester = :1 AND group = :2 ORDER BY date",
                          theName, thisGroupKey)
    
    # Reformat the time for each gift so it's in PDT 
    myGiftList = []
    for gift in myGifts:
      formattedDate = helper.getFormattedDate(gift)
      myGiftList.append((gift.key().id(), formattedDate, gift.giftDescription, gift.giftLink, gift.purchaser, gift.modifiedGift))
 
    # 'myGiftList' is the list of groups the logged-in User is requesting.
    # 'myPurchasedGifts' is the list of groups the logged-in User is purchasing.
    # 'url' is the link to either log in or log out
    # 'url_linktest' is the word "Log in" or "Log out"
    # 'nickname' is the name of the person who's logged in. 
    # 'ldapName' is the username of the person logged in. It's used to determine whether a valid user has logged in, and how to display the view of the gift lists.
    # 'validNames' is the list of tuples we use to check against.
    # 'thisGroup' is the ID of the Group currently being viewed
    # 'userGroups' is the list of Groups that the User belongs to
    # 'nameInURL' is the name displayed in the URL. Used to determine which gift list to view.

    template_values = {
      'myGiftList': myGiftList,
      'myPurchasedGifts': myPurchasedGifts,
      'login_link': self.login_link,
      'nickname': self.nickname,
      'ldapName': self.ldapName,
      'validNames': validNames,
      'thisGroup': thisGroup,
      'userGroups': self.userGroups,
      'nameInURL': nameInURL,
      'url': self.url,
      'belongsInGroup': belongsInGroup,
      }
    
    path = os.path.join(os.path.dirname(__file__), 'index.html')
    
    self.response.out.write(template.render(path, template_values))
    

class EnterGift(webapp.RequestHandler):
  """This class is called when the user wants to enter a new gift."""   

  def post(self):
    thisUserNickname = self.request.get('n')
    thisGroup = self.request.get('gid')
    
    gift = gModel.Gift()
    gift.requester = (users.get_current_user().nickname()).lower()
    gift.giftDescription = self.request.get('giftDescription')
    gift.group = gModel.Group.getGroupKey(thisGroup)    
    gift.group.put()
    
    if gift.giftDescription:
      gift.giftLink = self.request.get('giftLink')
      
      if gift.giftLink: 
        ## Check to make sure the description has http:// in it
        try:
          gift.giftLink.index('http://')
        except ValueError:
          gift.giftLink = 'http://' + gift.giftLink
        
      gift.put()
    
    self.redirect('/?gid='+str(thisGroup)+'&n='+thisUserNickname)


class PurchaseGift(webapp.RequestHandler):
  """This class is called when the user wants to purchase/reserve a gift."""
  
  def post(self):
    giftId = self.request.get('purchasedGift')
    thisGroup = int(self.request.get('_gid'))
    thisUserNickname = self.request.get('_n')
    
    if giftId:  # Check in case you hit 'purchase gift' w/o choosing anything
      item = gModel.Gift.get_by_id(long(giftId))
      ## TODO: FIX THIS WHEN I FIX THE REALNICKNAME VS NICKNAME THING 
      item.purchaser = (users.get_current_user().nickname()).lower()
      item.put()
    self.redirect('/?gid='+str(thisGroup)+'&n='+thisUserNickname)

    
class EditGift(LoginCheck):
  """This class controls the EditPage page."""
  
  def get(self):
    giftId = int(self.request.get('id'))
    thisGroup = int(self.request.get('gid'))
    nickname = self.request.get('n')
    item = gModel.Gift.get_by_id(giftId)
    
    self.check_login()
    
    template_values = {
      'thisGroup' : thisGroup,
      'giftId': giftId,
      'giftDescription': item.giftDescription,
      'giftLink': item.giftLink,
      'nickname': nickname,
      'login_link': self.login_link,
      'ldapName': self.ldapName,
      }

    path = os.path.join(os.path.dirname(__file__), 'editGift.html')
    self.response.out.write(template.render(path, template_values))
    
  def post(self):
    giftId = self.request.get('_id')
    thisGroup = int(self.request.get('_gid'))
    nickname = self.request.get('_n')
    editOrDelete = self.request.get('editOrDelete')
    item = gModel.Gift.get_by_id(long(giftId))
    
    if editOrDelete == 'edit': 
      newGiftDescription = self.request.get('newGiftDescription')
      newGiftLink = self.request.get('newGiftLink')
      
      item.giftDescription = newGiftDescription
      item.giftLink = newGiftLink
      item.modifiedGift = "Edited"
      
    elif editOrDelete == 'delete':
      item.requester = "DELETED BY REQUESTER!"
    ## TODO: Trigger email to purchaser if exists
        
    item.put()
    self.redirect('/?gid='+str(thisGroup)+'&n='+nickname)


class RemoveGift(webapp.RequestHandler):
  """This class is called when the user wants to remove a gift that they
  originally agreed to purchase/reserve.
  """
  
  def get(self):
    giftId = int(self.request.get('id'))
    thisGroup = int(self.request.get('gid'))
    nickname = self.request.get('n')
    
    item = gModel.Gift.get_by_id(long(giftId))
    item.purchaser = None
    item.put()
    self.redirect('/?gid='+str(thisGroup)+'&n='+nickname)


class EditUserSettings(LoginCheck):
  """This class controls the editUserSettings page."""

  def get(self):
    
    self.check_login()
    
    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      userEmail = (users.get_current_user().email()).lower()
      nickname = self.request.get('n')
    
      # Determine whether to pre-fill the checkbox next to the user's
      # "receive emails" box.
      currentUser = gModel.GiftUser.getCurrentUser()
      if currentUser.receiveEmails == "Yes":
        checkedOrNot = "checked='Yes'"
      else:
        checkedOrNot = ""

      template_values = {
        'email': userEmail,
        'nickname': nickname,
        'login_link': self.login_link,
        'ldapName': self.ldapName,
        'checkedOrNot': checkedOrNot,
        }
     
      path = os.path.join(os.path.dirname(__file__), 'editUserSettings.html')
      self.response.out.write(template.render(path, template_values))

    else:
      self.redirect('/')
    

  def post(self):
    
    newEmailSettings = self.request.get('newEmailSettings')
    newNickname = self.request.get('newNickname')
    if newNickname:    
      currentUser = gModel.GiftUser.getCurrentUser()      
      currentUser.giftUserNickname = newNickname
      currentUser.receiveEmails = newEmailSettings
      currentUser.put()
    self.redirect('/')


class CreateGroup(LoginCheck):
  """This class controls the createGroup page."""
  
  def get(self):
    
    self.check_login()
    
    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      userEmail = (users.get_current_user().email()).lower()
    
      nickname = self.request.get('n')
      thisGroup = self.request.get('gid')
      url = users.create_logout_url(self.request.uri)

      # Duplicate code from above. Refactor later!
      # Query the datastore for the groups that this user is in, and display them in the FE
      userGroups = []    
      currentUser = gModel.GiftUser.getCurrentUser()
      
      # Return a list of the Groups that the logged-in User belongs to.
      userGroups = gModel.GiftUser.getUserGroups(currentUser)     
      
      if thisGroup:
        thisGroupData = gModel.Group.get_by_id(long(thisGroup))
      else:
        thisGroupData = ""
    
      template_values = {
        'email': userEmail,
        'nickname': nickname,
        'login_link': self.login_link,
        'ldapName': self.ldapName,
        'userGroups': userGroups,
        'thisGroup': thisGroup,
        'thisGroupData': thisGroupData,
        }
    
      path = os.path.join(os.path.dirname(__file__), 'createGroup.html')
      self.response.out.write(template.render(path, template_values))
    
    else:
      self.redirect('/')
    
  def post(self):
    
    ## First, create the new group, assign it its owner, and put it into the datastore.
    
    nickname = self.request.get('_n')
    sendEmailOrNot = self.request.get('sendEmailOrNot')
    newGroupName = self.request.get('newGroupName')
    group = gModel.Group()
    group.groupName = newGroupName
    group.groupOwnerUserEmail = (users.get_current_user().email()).lower()
    group.put()
    
    ## Then, look up the existing User entity for the person creating the group and attach this group to that entity
        
    currentUser = gModel.GiftUser.getCurrentUser()
    currentUser.groups.append(group.key())
    currentUser.put()
    
    ## Then traverse through the 10 fields on CreateGroup.html and add them to the group and datastore (if necessary)
    ## TODO: Rewrite this in jQuery
    i = 1
    while i < 11: ## There are 10 fields for now on the CreateGroup.html page.
      currentFriendEmail = "newFriendEmail" + str(i)
      currentFriendNickname = "newFriendNickname" + str(i)
      
      friendEmail = self.request.get(currentFriendEmail)
      friendNickname = self.request.get(currentFriendNickname)
      
      friendEmail = friendEmail.lower()
      
      ## Check to make sure this is a valid email address
      try:
        friendEmail.index('@')
        isAnEmail = "true"
        
        ## Check in case no nickname was entered
        if friendNickname == "":
          friendNickname = (friendEmail[0:(friendEmail.index('@'))]).lower()
      except ValueError:
        isAnEmail = "false"

      ## Check if user already exists in the datastore and we can just append the group to them
      if isAnEmail == 'true':
        
        try:
          # strip away only the str before the @ sign
          checkIfUser = gModel.GiftUser.gql("WHERE giftUserName = :1", friendEmail[:friendEmail.index('@')].lower())
          giftuser = checkIfUser.get()
          giftuser.giftUserEmail ## Just test to see if email exists in this checkIfUser result. If not, create the user below. NOTE: FIGURE OUT A WAY TO DO THIS MORE ELEGANTLY LATER          
          
        except AttributeError:
          giftuser = gModel.GiftUser()
          giftuser.giftUserName = (friendEmail[0:(friendEmail.index('@'))]).lower()
          giftuser.giftUserEmail = friendEmail
          giftuser.giftUserNickname = friendNickname
          giftuser.userVerified = 'False'
      
        giftuser.groups.append(group.key())
        giftuser.put()
        
        if sendEmailOrNot == "Yes":
          message = mail.EmailMessage(sender="Gifty <giftyannounce@gmail.com>",
                                subject="You've Been Invited to a Gifty Group")
          message.to = friendEmail
          #message.to = "jameshurley@gmail.com"
          message.body = """
          Your friend %s has invited you to join their Gifty group. 
        
          Gifty is a web application that lets you create & share lists of gifts with your friends and family.
        
          Visit http://www.giftyapp.com to log in and check out the group that's been created for you. Thanks! 
        
          The Gifty Team
          """ % (nickname)
        
          #message.send()
        
      i=i+1                            
    self.redirect('/')
    
    
class UpdateGroupName(webapp.RequestHandler):

  def post(self):
  
    thisGroup = self.request.get('_gid')
    thisGroup = long(thisGroup)
    
    thegroup = gModel.Group.get(db.Key.from_path('Group', thisGroup))
    data = gModel.GroupForm(data=self.request.POST, instance=thegroup)
    entity = data.save(commit=False)
    
    newGroupName = self.request.get('newGroupName')
    entity.groupName = newGroupName
    entity.put()
    self.redirect('/')
  
    
class AboutPage(LoginCheck):

  def get(self):
    
    self.check_login()
    
    nickname = self.request.get('n')
    thisGroup = self.request.get('gid')
    url = users.create_logout_url(self.request.uri)
    
    template_values = {
      'nickname': self.nickname,
      'thisGroup': thisGroup,
      'login_link': self.login_link,
      'ldapName': self.ldapName,
    }
    path = os.path.join(os.path.dirname(__file__), 'about.html')
    self.response.out.write(template.render(path, template_values))


class ContactPage(LoginCheck):

  def get(self):
    
    self.check_login()
    
    nickname = self.request.get('n')
    thisGroup = self.request.get('gid')
    url = users.create_logout_url(self.request.uri)
    
    template_values = {
      'nickname': self.nickname,
      'thisGroup': thisGroup,
      'login_link': self.login_link,
      'ldapName': self.ldapName,
    }
    path = os.path.join(os.path.dirname(__file__), 'contact.html')
    self.response.out.write(template.render(path, template_values))    
  

class CronSend(webapp.RequestHandler):
  
  def get(self):
  
    def seconds_ago(time_s):
      return datetime.datetime.now() - datetime.timedelta(seconds=time_s)
  
    my_query = gModel.Gift.all().filter("date >", seconds_ago(24*60*60))
    results = my_query.fetch(limit=1000) ## May need to refactor later since limit is 1000
    
    giftset = []
    affectedGroups = []
    theNicknames = {}
  
    enterstring = """
    """
  
    # Create two sets of tuples - one to hold gifts and one to hold groups. 
    for gift in results:
      if gift.requester != "DELETED BY REQUESTER!":
        giftset.append((gift.giftDescription, gift.group.key(), gift.requester))
      
      try:
        #print gift.giftDescription
        affectedGroups.index((gift.group.key(), gift.group.groupName))
      except ValueError:
        affectedGroups.append((gift.group.key(), gift.group.groupName))
  
    for thisgroupkey, thisgroupname in affectedGroups:
      groupMembers = gModel.GiftUser.gql("WHERE groups = :1", thisgroupkey)
    
      recipients = ""
      for member in groupMembers:
        theNicknames[member.giftUserName] = member.giftUserNickname
        if member.receiveEmails == "Yes":
          recipients = recipients + member.giftUserEmail + ","
    
      recipients = recipients[0:len(recipients)-1] # Getting rid of trailing comma
    
      giftstring = ""
      
      for thisgift in giftset:
        if thisgift[1] == thisgroupkey:
          giftstring = giftstring + thisgift[0] + " was added by " + theNicknames[thisgift[2]] + "." + enterstring
    
      giftstring = giftstring[0:len(giftstring)-2] # Getting rid of trailing comma
    
      message = mail.EmailMessage(sender="Gifty <giftyannounce@gmail.com>",
                                subject="Updates to your Gifty group")
      message.to = "giftyannounce@gmail.com"
      message.bcc = recipients
      #message.bcc = "jhurley@gmail.com"
      message.body = """
      Hello! This is an automated message to let you know that there have been updates to your Gifty group "%s". The following items were added within the past 24 hours:
    
      %s
    
      Log in to http://giftyapp.com to check it out!
      
      Sincerely,
      Your friendly neighborhood Giftybot
    
      """ % (thisgroupname,giftstring)
     
      message.send()     
      #print message.body


class Bookmarklet(webapp.RequestHandler):
  
  def get(self):
    loggedIn = "True"
    userGroups = []
    if users.get_current_user():
      currentUser = gModel.GiftUser.getCurrentUser()
      userGroups = gModel.GiftUser.getUserGroups(currentUser)
    else:
      loggedIn = "False"

    template_values = {
      'userGroups' : userGroups,
      'loggedIn' : loggedIn,
      }
  
    path = os.path.join(os.path.dirname(__file__), 'frame.html')
    self.response.out.write(template.render(path, template_values))  
  
  def post(self):
    groupId = self.request.get('_groupId')
    giftDescription = self.request.get('_giftDescription')
    giftLink = self.request.get('_giftLink')
    
    gift = gModel.Gift()
    gift.requester = (users.get_current_user().nickname()).lower()
    gift.giftDescription = giftDescription
    gift.group = gModel.Group.getGroupKey(groupId)
    gift.giftLink = giftLink
    gift.put()
    
    # Hardcoded URL is at:
    # index.html (link to bookmarklet)
    # bookmarklet.js (line 21)

class Index2(webapp.RequestHandler):

  def get(self):

    template_values = {
      }
  
    path = os.path.join(os.path.dirname(__file__), 'index2.html')
    self.response.out.write(template.render(path, template_values))  

class CreateGroup2(LoginCheck):
  """This class controls the createGroup page."""
  
  def get(self):
    
    self.check_login()
    
    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      userEmail = (users.get_current_user().email()).lower()
    
      nickname = self.request.get('n')
      thisGroup = self.request.get('gid')
      url = users.create_logout_url(self.request.uri)

      # Duplicate code from above. Refactor later!
      # Query the datastore for the groups that this user is in, and display them in the FE
      userGroups = []    
      currentUser = gModel.GiftUser.getCurrentUser()
      
      # Return a list of the Groups that the logged-in User belongs to.
      userGroups = gModel.GiftUser.getUserGroups(currentUser)     
      
      if thisGroup:
        thisGroupData = gModel.Group.get_by_id(long(thisGroup))
      else:
        thisGroupData = ""
    
      template_values = {
        'email': userEmail,
        'nickname': nickname,
        'login_link': self.login_link,
        'ldapName': self.ldapName,
        'userGroups': userGroups,
        'thisGroup': thisGroup,
        'thisGroupData': thisGroupData,
        }
    
      path = os.path.join(os.path.dirname(__file__), 'createGroup2.html')
      self.response.out.write(template.render(path, template_values))
    
    else:
      self.redirect('/')




application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/createGroup', CreateGroup),
                                      ('/editUserSettings', EditUserSettings),
                                      ('/enterGift', EnterGift),
                                      ('/purchaseGift', PurchaseGift),
                                      ('/editGift', EditGift),
                                      ('/removeGift', RemoveGift),
                                      ('/updateGroupName', UpdateGroupName),
                                      ('/about', AboutPage),
                                      ('/contact', ContactPage),
                                      ('/tasks/cronj', CronSend),
                                      ('/bookmarklet', Bookmarklet),
                                      ('/index2', Index2),
                                      ('/createGroup2', CreateGroup2)],
                                      debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()