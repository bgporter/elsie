#! /usr/bin/env python

'''
   user.py -- MongoDb user code to work with Flask-Login.
   Fall 2015, Bg Porter

   The MIT License (MIT)

   Copyright (c) 2015 Brett g Porter

   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction, including without limitation the rights
   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   copies of the Software, and to permit persons to whom the Software is
   furnished to do so, subject to the following conditions:

   The above copyright notice and this permission notice shall be included in all
   copies or substantial portions of the Software.

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   SOFTWARE.

'''

import pymongo

from flask_login import UserMixin

import os
import hashlib

class User(UserMixin):
   def __init__(self, userId, salt, hashed):
      self.userId = userId
      self.salt = salt
      self.hashed = hashed

   def authenticate(self, rawPassword):
      pw = rawPassword.encode('utf-8')
      hashed = generateHash(pw, self.salt)
      return hashed == self.hashed

   def get_id(self):
      # required overload
      return self.userId



def getUserDb(db):
   return db['test_albums']['users']

def loadUser(db, userId):
   users = getUserDb(db) 
   theUser = users.find_one({"userId": userId})
   retval = None
   if theUser:
      #pprint(theUser)
      salt = hexToSalt(theUser['salt'])
      retval = User(theUser['userId'], salt, theUser['hashed'])
   return retval


def generateHash(pw, salt):
   h = hashlib.sha256()
   h.update(salt+pw)
   return h.hexdigest()


def saltToHex(s):
   return ''.join("{0:02x}".format(ord(i)) for i in s)

def hexToSalt(s):
   def chunkify(s):
      rest = s
      while rest:
         chunk, rest = rest[:2], rest[2:]
         yield chunk

   return ''.join(chr(int(i, 16)) for i in chunkify(s))


def addOrUpdateUser(db, userId, rawPassword):
   '''
      Given a userId and password, either update the database with a new 
      password hash and salt or create a brand new one.
   '''
   salt = os.urandom(32)
   hashed = generateHash(rawPassword, salt)

   userData = {"userId": userId, "salt": saltToHex(salt), "hashed": hashed}

   #pprint(userData)
   users = getUserDb(db)
   result = users.replace_one({"userId": userId}, userData, upsert=True)



if __name__ == "__main__":
   mongo = pymongo.MongoClient('zappa')

   #mongo.test_albums.users.drop()
   import sys
   user = sys.argv[1]
   pw = sys.argv[2]

   addOrUpdateUser(mongo, user, pw)

