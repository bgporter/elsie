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

from flask import abort
from flask import Flask 
from flask import redirect
from flask import render_template
from flask import request
from flask import Response
from flask import send_file
from flask import url_for

import flask_login
from flask_login import login_required

from pymongo import MongoClient

import collections
import datetime
import glob
import os
import pprint
import re

from MonthArithmetic import Month
from dictTupleAdapter import DictTupleAdapter
import user

import zipstream


## !!! Things to move into config !!!

from DefaultConfig import kMusicBase
from DefaultConfig import kMongoIp




app = Flask(__name__)

## !!! Things to move into config !!!

app.config.from_object('DefaultConfig')

## MongoDb setup.
db = MongoClient(kMongoIp)
albums = db['test_albums']['albums']


# get flask-login set up.
loginManager = flask_login.LoginManager()
loginManager.login_view = "login"
loginManager.init_app(app)

@loginManager.user_loader
def loadUser(userId):
   return user.loadUser(db, userId)









@app.route("/")
@login_required
def index():
   '''
      Main index page of the app (after logging in). 

      Should show links to alphabetical artist pages and date range pages.
   '''

   letters = [chr(i+65) for i in range(26)]

   # get stuff added in the last 7, 30, 90, 180, 365 days.
   recent = []
   today = datetime.date.today()
   kDateFormat = "%Y%m%d"
   toDateStr = today.strftime(kDateFormat)
   for days in (7, 30, 90, 180, 365):
      fromDate = today - datetime.timedelta(days)
      recent.append({ "days" : days, 
            "from" : fromDate.strftime(kDateFormat),
            "to" : toDateStr
         })



   # build a list of date ranges going back a few months
   kRecentMonths = 12

   thisMonth = Month()
   thisYear = thisMonth.year



   # start at this month and work backwards
   years = []
   year = {"year": thisYear, "months": [] }
   years.append(year)
   for i in range(kRecentMonths):
      monthDict = {
         "from": str(thisMonth), 
         "to": str(thisMonth.Next()),
         "short": thisMonth.Formatted("%b"),
         "long": thisMonth.Formatted("%B"),
         "full": thisMonth.Formatted("%b %Y")
         }
      year['months'].append(monthDict)
      thisMonth = thisMonth.Previous()
      if thisMonth.year != thisYear:
         thisYear = thisMonth.year
         year = {"year": thisYear, "months": [] }
         years.append(year)

   # we may have just added an empty year dict to the end of our 
   # years list. If so, get rid of it.
   if 0 == len(years[-1]['months']):
      years.pop()



   return render_template('index.html', title="Home", letters=letters, 
      recent=recent, years=years)



@app.route("/login", methods=["GET", "POST"])
def login():
   if "POST" == request.method:
      email = request.form['email']
      pw = request.form['password']
      remember = request.form.get('remember')
      remember = remember is not None
      print 'remember = {0}'.format(repr(remember))
      target = 'login'
      if email and pw:
         # can't log in if something's blank
         u = user.loadUser(db, email)
         if u:
            if u.authenticate(pw):
               flask_login.login_user(u, remember=remember)
               next = request.args.get('next')
               ## !!! check to make sure this is okay?
               target = next

      target = target or 'index'
      redirecturl = url_for(target)
      return redirect(redirecturl)
   else:
      return render_template("login.html", title="Elsie: Login")


@app.route("/logout")
def logout():
   flask_login.logout_user()
   return redirect(url_for("index"))

@app.route("/artist/<artist>/")
@login_required
def artist(artist):
   '''
      Finds a list of all albums that the specified artist is listed on. 
      'artist' is in our path-friendly format "Name-With-Dashes", not the 
      nice display name.

      This is a little more complex than it seems because we need to account
      for both album artists and track artists (as used on compilations, etc.), so we
      do two separate queries and combine the results manually. 
   '''

   dta = DictTupleAdapter('year', 'artist', 'album', 'artistPath', 'albumPath')

   # get the list of all albums where this artist is the album artist. 
   artistList = albums.find({u"artistPath": artist})
   # ...and also the list of all albums where this artist is listed on at least 
   # one track. 
   trackArtists = albums.find({"tracks": {"$elemMatch": {"trackArtistPath": artist}}})

   # ...and since there are albums where the album artist and trach artist are 
   # repeated, we need to make sure we don't repeat them.
   union = set()

   artistName = None

   for album in artistList:
      artistName = album['artist']
      union.add(dta.DictToTuple(album))

   for album in trackArtists:
      if not artistName:
         for track in album['tracks']:
            if track['trackArtistPath'] == artist:
               artistName = track['trackArtist']
               break
      union.add(dta.DictToTuple(album))

   albumList = [dta.TupleToDict(i) for i in sorted(list(union))]

   print albumList

   title = u"{0}".format(artistName)

   return render_template('artist.html', title=title, albums=albumList)


@app.route("/alpha/<letter>/")
@login_required
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
@login_required
def album(artist, album):
   '''
      Display a single album given its artistPath and albumPath. 
   '''
   theAlbum = albums.find_one({'artistPath': artist, 'albumPath': album})
   p = pprint.PrettyPrinter()

   title = u"{0}: {1}".format(theAlbum['artist'], theAlbum['album'])
   pageTitle = u'<a href="{0}">{1}</a>: {2}'.format(
      url_for('artist', artist=theAlbum['artistPath']), 
      theAlbum['artist'], theAlbum['album'])

   print pageTitle
   return render_template('album.html', title=title, pageTitle=pageTitle, album=theAlbum)

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
@login_required
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
         if toDate < fromDate:
            # doesn't make sense if they're out of order; swap!
            fromDate, toDate = toDate, fromDate
   except BadDateError:
      # !!! this should really be raising an HTTP error
      return "Badly formatted date"


   matchDates = {"$gte": fromDate}
   if toDate:
      matchDates["$lt"] = toDate

   cur = albums.find({"tracks": {"$elemMatch": {"added": matchDates}}})

   ## build a structure to associate each album with a date that at least
   # one track was added to the collection.
   # 
   addDates = collections.defaultdict(set)

   print "From Date = {0}".format(fromDate)


   def InRange(date):
      retval = False
      if date >= fromDate.date():
         retval = True
         if toDate and date > toDate.date():
            retval = False
      return retval

   dta = DictTupleAdapter('artist', 'album', 'artistPath', 'albumPath',  'year')

   for album in cur:
      #print album['album']
      for track in album['tracks']:
         #print track['title'], track['added']
         try:
            dateAdded = track['added'].date()
            if InRange(dateAdded):
               addDates[dateAdded].add(dta.DictToTuple(album))
         except KeyError:
            # there's a track that doesn't have an add date. Ignore.
            pass


   # okay -- now what we have is a dict that maps dates where something was added
   # to a list of tuples that represent albums added on that date. We need to turn this 
   # into a list of dicts that each contain 
   # - that date
   # - a list of album dicts.
   # that the template will be able to display.
   
   days = []
   for key in sorted(addDates.keys()):
      day = {"date": key.strftime("%b %d, %Y")}
      day['albums'] =  [dta.TupleToDict(t) for t in sorted(list(addDates[key]))]
      days.append(day)

   # prep links for navigation to earlier/later periods
   # We'll create a pair of dicts that will hold from: and (optional) to:
   # strings in the YYYYMM format for the Previous and Next (if meaningful)
   # links that we'll display
   
   previous = {"to" : None}
   next = {"to" : None}
   monthRange = 1
   fromDate = Month(fromDate)
   if toDate:
      toDate = Month(toDate)
      monthRange = fromDate.Range(toDate)

   previous['from'] = str(fromDate.Previous(monthRange))
   next['from'] = str(fromDate.Next(monthRange))
   if toDate:
      previous['to'] = str(toDate.Previous(monthRange))
      next['to'] = str(toDate.Next(monthRange))

   if toDate:
      if fromDate.year == toDate.year:
         fromFmt = "%B"
      else:
         fromFmt = "%B %Y"
      if 1 == fromDate.Range(toDate):
         title = "Added in {0}".format(fromDate.Formatted("%B %Y"))
      else:
         title = "Added between {0} - {1}".format(
            fromDate.Formatted(fromFmt), 
            toDate.Formatted("%B %Y"))
   else:
      title = "Added in/after {0}".format(fromDate.Formatted("%B %Y"))

   return render_template("date.html", title=title, days=days, prev=previous, next=next)


@app.route('/year/<int:year>')
@login_required
def year(year):
   '''
      Get and display all albums with a release date of the specified year.
   '''
   cur = albums.find({"year": str(year)})
   cur.sort("artist")
   title= "{0} Releases".format(year)
   return render_template("year.html", title=title, albums=cur, prev=year-1, next=year+1)

@app.route("/track/<artist>/<album>/<fileName>")
@login_required
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
   try:
      return send_file(filePath.encode('utf-8'), None, download=="1")
   except IOError:
      abort(404)


@app.route("/zip/<artist>/<album>")
def zip(artist, album):
   '''
      create a zip file containing the requested artist/album, and return it.

   '''

   import sys
   print sys.version

   def ArchiveName(artist,album, f):
      fileName = os.path.split(f)[1]
      return os.path.join(artist.encode('utf-8'), album.encode('utf-8'), fileName)

   def generator(artist, album):
      z = zipstream.ZipFile()
      files = glob.glob(os.path.join(kMusicBase, artist, album, "*.mp3").encode('utf-8'))
      for f in sorted(files):
         z.write(f, arcname=ArchiveName(artist, album, f))

      for chunk in z:
         yield chunk

   response = Response(generator(artist, album), mimetype='application/zip')
   response.headers['Content-Disposition'] = 'attachment; filename={}.zip'.format(album)
   return response



if __name__ == "__main__":
   app.run()
