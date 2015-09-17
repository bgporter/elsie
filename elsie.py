#! /usr/bin/env python

'''
   elsie.py -- Flask/MongoDb music library viewer. 
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

from flask import Flask 
from flask import send_file
from flask import render_template
from flask import request

from pymongo import MongoClient

import datetime
import os
import pprint
import re
app = Flask(__name__)

## !!! Things to move into config !!!
app.debug = True

kMongoIp = "192.168.1.8"
kMusicBase = '/Volumes/zappa_files/music/'



## !!! Things to move into config !!!



db = MongoClient(kMongoIp)
albums = db['test_albums']['albums']

@app.route("/")
def index():
   '''
      Main index page of the app (after logging in). 

      Should show links to alphabetical artist pages and date range pages.
   '''

   letters = [chr(i+65) for i in range(26)]

   return render_template('index.html', title="Hello", letters=letters)


@app.route("/artist/<artist>/")
def artist(artist):
   '''
      Finds a list of all albums that the specified artist is listed on. 
      'artist' is in our path-friendly format "Name-With-Dashes", not the 
      nice display name.

      This is a little more complex than it seems because we need to account
      for both album artists and track artists (as used on compilations, etc.), so we
      do two separate queries and combine the results manually. 
   '''

   def AlbumToTuple(album):
      return (
         album['year'],
         album['artist'],
         album['album'],
         album['artistPath'],
         album['albumPath'],
         )

   # get the list of all albums where this artist is the album artist. 
   artistList = albums.find({u"artistPath": artist})
   # ...and also the list of all albums where this artist is listed on at least 
   # one track. 
   trackArtists = albums.find({"tracks": {"$elemMatch": {"trackArtistPath": artist}}})

   # ...and since there are albums where the album artist and trach artist are 
   # repeated, we need to make sure we don't repeat them.
   union = set()

   for album in artistList:
      union.add(AlbumToTuple(album))

   for album in trackArtists:
      union.add(AlbumToTuple(album))

   albumList = [dict(year=i[0], artist=i[1], title=i[2], artistPath=i[3], 
      albumPath=i[4]) for i in sorted(list(union))]

   # ...we'll need to convert the list ot tuples back into a list of 
   # dicts. 

   title = u"Artist: {0}".format(artist)

   return render_template('artist.html', title=title, albums=albumList)


@app.route("/alpha/<letter>/")
def alpha(letter):
   '''
      List all artists beginning with a specified letter (or in reality as 
         a potentially useful hack any specifed prefix.)

      The app will only expose this as links to single letters, but you can 
      hack the URL and get e.g. anything that Bill Frisell has released 
      (whether as himself, Bill Frisell Quartet, etc.) by using the URL
      Bill%20Frisell.

   Again, because we're also looking on compilations, we need to look at
   both artists (album level) and track artists (track level)

   '''
   if letter.isdigit():
      # match any string starting with a digit.
      pattern = re.compile(r"^\d.*")
      title = "Artists: 0-9"
   else:
      pattern = re.compile(r"^{0}.*".format(letter), re.IGNORECASE)
      title = "Artists: {0}".format(letter)
   cursor = albums.find({"artist":  pattern})

   artists = set()
   for album in cursor:
      artists.add((album['artist'], album['artistPath']))

   trackArtists = albums.find({"tracks": {"$elemMatch": {"trackArtistPath": pattern}}})

   for album in trackArtists:
      for track in album['tracks']:
         if pattern.match(track['trackArtist']):      
            artists.add((track['trackArtist'], track['trackArtistPath']))

   artists = [dict(artist=i[0], path=i[1]) for i in sorted(list(artists))]


   return render_template("alpha.html", title=title, artists=artists)

@app.route("/album/<artist>/<album>")
def album(artist, album):
   '''
      Display a single album given its artistPath and albumPath. 
   '''
   theAlbum = albums.find_one({'artistPath': artist, 'albumPath': album})
   p = pprint.PrettyPrinter()

   return "<pre>{0}</pre>".format(p.pformat(theAlbum))


class BadDateError(Exception):
   pass

def IntToDate(val):
   val = int(val)
   val = max(val, 2000)
   strVal = "{0}".format(val)
   strLen = len(strVal)
   if strLen not in (4, 6, 8):
      raise BadDateError

   if 4 == strLen:
      strVal += '0101'
   elif 6 == strLen:
      strVal += '01'

   try:
      return datetime.datetime.strptime(strVal, "%Y%m%d")
   except ValueError:
      raise BadDateError


@app.route("/date/<int:fromDate>/")
@app.route("/date/<int:fromDate>/<int:toDate>/")
def date(fromDate, toDate=None):
   '''
      Finds all albums that have had at least one track added to the collection
      after the date 'fromDate' (and optionally, before the date 'toDate').
      Dates are passed in in one of these formats as strings:
      YYYY
      YYYYMM
      YYYYMMDD

      If we receive a date with fewer than 8 characters, we append '01' or
      '0101' as needed to snap to the beginning of the specified year or month. 

   '''
   try:
      fromDate = IntToDate(fromDate)
      if toDate:
         toDate = IntToDate(toDate)
   except BadDateError:
      return "Badly formatted date"


   matchDates = {"$gte": fromDate}
   if toDate:
      matchDates["$lt"] = toDate

   cur = albums.find({"tracks": {"$elemMatch": {"added": matchDates}}})


   txt = u"\n".join([u"{0}: {1}".format(a['artist'], a['album']) for a in cur])

   return u"<pre>{0}</pre>".format(txt).encode("utf-8")


@app.route("/track/<artist>/<album>/<fileName>")
def track(artist, album, fileName):
   '''
      MP3 files (and cover art, eventually) are not stored in our regular
      static directory that other web app assets are served from, so we need
      a separate method to handle these files.

      See the notes in the Flask docs about configuring the Flask app to set
      USE_X_SENDFILE in production where the server supports it so the server
      is actually doing the file serving, not our Flask process.

      TODO: We need to accept a query string like "download=1" to indicate that
      we want to download the file as an attachment instead of listening to it. 

   '''
   filePath = os.path.join(kMusicBase, artist, album, fileName)
   download = request.args.get("download", "0")
   return send_file(filePath, None, download=="1")


if __name__ == "__main__":
   app.run()
