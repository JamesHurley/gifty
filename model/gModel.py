#!/usr/bin/python2.4
# -*- coding: UTF-8 -*-
#
# Copyright 2010 James Hurley, Inc. All Rights Reserved

"""Model for Gifty app.

This file controls all aspects of the Gifty model. It creates 3 entity groups
in the datastore (Gift, GiftUser, and Group) and defines helper functions within
each class to be used by the controller files.
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


class Group(db.Model):
  """Specifies the Group model and its 2 different properties.
  
  To map to its users, each GiftUser contains the "groups" property, which
  stores a list of Groups that the user belongs to. This is because a user
  can belong to more than one Group.
  
  The properties are:
  groupName: The name of the Group.
  groupOwnerUserEmail: The email address of the "owner", or creator, of the
    Group.
  """
  
  groupName = db.StringProperty(required=False)
  groupOwnerUserEmail = db.StringProperty(required=False)

  @staticmethod
  def getMembers(thisGroupKey):
    """Fetches the members of a particular Group given the Group's key.
    
    Args:
      thisGroupKey: The key for a Group in the data store.
    
    Returns:
      memberList: The list of GiftUser objects that belong to the given
      key.
    """
    
    memberList = []
    if thisGroupKey:
      query = GiftUser.all()
      query.filter('groups =', thisGroupKey)
      members = query.fetch(1000) # Fetches a list
      for m in members:
        memberList.append(m)
    return memberList

  @staticmethod
  def getGroupKey(thisGroup):
    """Fetches the key of a particular Group given the Group's ID.
    
    Args:
      thisGroup: The numerical ID of a Group. Example: "1008".
    
    Returns:
      thisGroupKey: The Key of the Group.
    """
    
    if thisGroup:
      groupObject = Group.get_by_id(long(thisGroup))
      #thisGroupKey = Group.key(groupObject)
      if groupObject:
        thisGroupKey = Group.key(groupObject)
      else:
        thisGroupKey = ""
    else:
      thisGroupKey = ""
    return thisGroupKey
  

class GiftUser(db.Model):
  """Specifies the GiftUser model and its 6 different properties.
  
  The properties are:
  giftUserEmail: The email address of the user. This is unique to every user.
  giftUserName: This is the email address of user without the @gmail.com. It's a
    legacy field that should be deprecated. 
  giftUserNickname: This is the user's nickname. It's what's displayed in
    theURL, and what others see. The user can change this field in "User
    Settings".
  userVerified: A flag that signals whether a user has logged in before. If set
    to "no", then they are shown a special message when they first log in. Also,
    their friends will see their name "greyed out" on their lists. 
  receiveEmails: A flag that determines whether a user receives daily email
    updates of their lists. This is editable on the "User Settings" page.
  groups: A list that holds all of the groups the user belongs to.
  """
  
  creationDate = db.DateTimeProperty(auto_now_add=True)
  giftUserEmail = db.StringProperty(required=False)
  giftUserName = db.StringProperty(required=False)
  giftUserNickname = db.StringProperty(required=False)
  userVerified = db.StringProperty(default='False')
  receiveEmails = db.StringProperty(default="No")
  groups = db.ListProperty(db.Key)
  
  @staticmethod
  def getCurrentUser():
    """Fetches info on the current logged-in User.
    
    Queries the data store for data on the User who's currently logged-in. 
    
    Args:
      none
      
    Returns:
      A class instance of GiftUser that contains the attributes of the current
      logged-in user.
    """
  
    currentUser = None
    if users.get_current_user():
      query = GiftUser.all()
      query.filter('giftUserEmail =', (users.get_current_user().email()).lower())
      if query.fetch(1): 
        currentUser = query.fetch(1)[0]
    return currentUser

  @staticmethod
  def getUserGroups(userInstance):
    """Fetches the groups that a User belongs to.
    
    Args:
      userInstance: The instance of a particular User.
      
    Returns:
      userGroups: A list of groups that the User belongs to.
    """
    
    userGroups = []
    for group in userInstance.groups:
      groupObject = Group.get_by_id(long(group.id()))
      userGroups.append(groupObject)
    return userGroups
  

class Gift(db.Model):
  """Specifies the Gift model and its 7 different properties.
  
  The properties are:
  requester: The person requesting the gift. May be changed if the purchaser
    decides to delete the gift - the value is then changed to "DELETED BY
    REQUESTER!"
  purchaser: The person who will purchase the gift. By default it is set to
    "None" and can be changed multiple times.
  giftDescription: The name of the gift.
  giftLink: If the requester chooses, he/she can specify a web site to link
    from which to purchase the gift. This is an optional.
  date: The date on which the gift was entered into the system.
  modifiedGift: This field specifies whether a gift has been edited by the
    purchaser. If it has, the value is changed to "edited". This was added
    later when the ability to edit gifts was created.
  group: A reference to what Group the gift belongs to. It references the Group
    model. 
  """
  
  requester = db.StringProperty(required=False)
  purchaser = db.StringProperty(required=False)
  giftDescription = db.StringProperty(multiline=True)
  giftLink = db.StringProperty()
  date = db.DateTimeProperty(auto_now_add=True)
  modifiedGift = db.StringProperty(default="No")
  group = db.ReferenceProperty(Group, collection_name='gifts')


class GiftForm(djangoforms.ModelForm):
  """This is a form class created from a Django model.
  
  It allows us to create form objects for Gift.
  """
  
  class Meta:
    model = Gift


class GroupForm(djangoforms.ModelForm):
  """This is a form class created from a Django model.
  
  It allows us to create form objects for Group.
  """
  
  class Meta:
    model = Group


class GiftUserForm(djangoforms.ModelForm):
  """This is a form class created from a Django model.
  
  It allows us to create form objects for GiftUser.
  """
  
  class Meta:
    model = GiftUser