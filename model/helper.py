#!/usr/bin/python2.4
# -*- coding: UTF-8 -*-
#
# Copyright 2010 James Hurley, Inc. All Rights Reserved

"""Helper functions for Gifty app.

This file contains helper functions for recurring tasks.
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

import gModel
   

def getFormattedDate(gift):
  """Formats a gift's creation date into readable PDT time.
  
  Args:
    gift: A gift object
    
  Returns:
    A string that's formatted like so: "12/2/09 (23:49 PDT)"
  """
  
  newhour = gift.date - datetime.timedelta(hours=9)
  newhour = str(newhour)
  newhour = newhour[11:13]
  newhour = long(newhour) 
  if newhour > 15:
    if gift.date.day == 1:
      if gift.date.month == 1 or gift.date.month == 2 or gift.date.month == 4 or gift.date.month == 6 or gift.date.month == 8 or gift.date.month == 9 or gift.date.month == 11:
        newday = "31"
      elif gift.date.month == 3:
        if gift.date.year % 4 == 0:
          newday = "29" # leap year
        else:
          newday = "28"
      elif gift.date.month == 5 or gift.date.month == 7 or gift.date.month == 10 or gift.date.month == 12:
        newday = "30"
      if gift.date.month == 1:
        newmonth = "12"
      else:
        newmonth = str(gift.date.month - 1)
    else:
      newday = gift.date.day - 1
      newmonth = str(gift.date.month)
  else:
    newday = gift.date.day
    newmonth = gift.date.month
  newhour = str(newhour)
  newminute = str(gift.date.minute)
  if len(newminute) == 1:
    newminute = newminute + "0"
  newyear = str(gift.date.year)
  newyear = newyear[2:]
  newdate = str(newmonth) + "/" + str(newday) + "/" + newyear + " (" + newhour + ":" + newminute + " PDT)"
  return newdate

