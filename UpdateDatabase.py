import sys
import socket
import os

import datetime

from DefaultConfig import kMusicBase
from DefaultConfig import kMongoIp
from DefaultConfig import kMp3UtilPath


sys.path.insert(0, kMp3UtilPath)

import fileSource
import fileDestination
import trackHistory

from mutagen.easyid3 import EasyID3

from pprint import pprint

kTrackAttributes = "trackArtist,title,trackNum,genre,bitrate,duration".split(',')

class Album(object):
   def __init__(self):
      self.data = {}
      # we initialize as an empty dict with a list of tracks (which are also dicts)
      self.data['tracks'] = []

   def addTrack(self, mp3File, history):
      try:
         meta = fileDestination.Mp3File(mp3File)
      except IOError:
         # a unicode normalization problem? If not, this will just throw an exception.
         meta = fileDestination.Mp3File(fileDestination.NormalizeFilename(mp3File) )
      pth, fileName = os.path.split(mp3File)
      pth, albumPath = os.path.split(pth)
      pth, artistPath = os.path.split(pth)


      self.data['artist'] = meta.albumArtist
      self.data['artistPath'] = artistPath
      self.data['albumPath'] = albumPath
      self.data['album'] = meta.album
      self.data['year'] = meta.year
      self.data['discNumber'] = meta.discNumber
      trackData = {}
      trackData['fileName'] = fileName
      trackData['trackArtistPath'] = fileDestination.Scrub(meta.trackArtist)

      for attr in kTrackAttributes:
         trackData[attr] = getattr(meta, attr)

      addTimestamp, _ = history.GetTrack(fileName)
      if addTimestamp:
         added = datetime.datetime.fromtimestamp(addTimestamp)
         trackData['added'] = added
      else:
         print u"*** NO HISTORY for ".format(mp3File).encode('utf-8')

      self.data['tracks'].append(trackData)



from pymongo import MongoClient

client = MongoClient(kMongoIp)
db = client.test_albums
albums = db.albums

fs = fileSource.FileSource(kMusicBase)

depth = 0
album = None
history = None
for (t, f) in fs:
   if fileSource.kDirectory == t:
      if 2 == depth:
         print u"HANDLING DIR {0}".format(f).encode('utf-8')
         history = trackHistory.History(f)
         album = Album()
      depth += 1
   elif fileSource.kMusic == t:
      album.addTrack(f, history)

   elif fileSource.kExitDirectory == t:
      depth -= 1
      if 2 == depth:
         # leaving an album directory.
         if len(album.data['tracks']):
            pprint(album.data['album'])
            #albumId = albums.insert_one(album.data).inserted_id
            # !!! Note that the correct unique ID for an album is the tuple
            # (artist, albumName, year, discNum). 
            # consider the case of Weather Report (1970) and again in 1982. 
            result = albums.replace_one({"artist": album.data['artist'], "album": album.data['album'], 
               "year" : album.data['year'], "discNumber": album.data['discNumber']}, 
               album.data, upsert = True)

            print "matched: {0}".format(result.matched_count)
            print "modified: {0}".format(result.modified_count)
            print "upserted: {0}".format(result.upserted_id)
         else: 
            print "*** Leaving dir without tracks"

         album = None
         history = None


