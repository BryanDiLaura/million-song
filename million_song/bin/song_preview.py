#!/usr/bin/env python3

"""
   Bryan DiLaura
   July 2015
   
   This file provides a utility function to get a song's preview url from
   the corresponding song id (can be found in the subset metadata database).
   
   It uses the echo nest and spotify APIs to accomplish this, utilizing the
   pyen and spotipy packages by Paul Lamere (http://MusicMachinery.com).
   
   If a direct conversion of echo nest song id to spotify id cannot be made,
   the function attempts to search for the song manually on spotify. If it 
   still cannot be found, the function returns None. If the url is found, it
   is returned in a string to the caller.
   
   url = getPreview(<echonest song_id>)
   
   Please note:
   This function is not intended to be used with id's that do not exist within
   the echo nest library. It will fail if a garbage ID is passed in. 

"""

import bin.src.spotipy as spotipy
import bin.src.pyen as pyen
import sqlite3


def getPreview(ID):
   
   url = None
   
   #create the echo nest api client (using api key)
   en = pyen.Pyen("KQBEIQGVG1FLQYIHK")
   
   #create the spotify api client
   sp = spotipy.Spotify()

   #send the get request to echo nest API, getting song profile for the specified id
   response = en.get("song/profile", id=ID, bucket=['id:spotify', 'tracks'])
   
   
   try: 
      #parse the response to get the spotify track id
      s = response['songs'][0]['tracks'][0]['foreign_id']
      #send the request to the spotify api for the given song
      results = sp.track(s)
       
      #get the url for the preview of the song 
      url = results['preview_url']
      
   except: 
      pass
   
   
   
   #couldn't find the song based purely on the song id. attempt to search for it
   if url == None:
      
      
      #open up database
      conn = sqlite3.connect("subset_track_metadata.db")
      cursor = conn.cursor()
      
      #get the data for the song
      cursor.execute("SELECT title, artist_name FROM songs WHERE song_id == '{}'".format(ID))
      data = cursor.fetchone()
   
      try:
         track = data[0]
         artist = data[1]
      except:
         url = None
         return url
      
      #put a space on the front so the search query will work correctly
      artist = " " + artist
      
      #do the actual search
      results = sp.search(q=track+artist, limit=1)
      
      #put the results in url
      try:
         url = results['tracks']['items'][0]['preview_url']
      except:
         url = None
         
      conn.close()
      
   
   return url



if __name__ == "__main__":
   
   #these ones should work completely fine using the echo-nest -> spotify conversion 
   testids = []
   testids.append('SOVLGJY12A8C13FBED')
   testids.append('SOGDQZK12A8C13F37C')
   testids.append('SOIWBDR12A8C13A4AC')
   testids.append('SOCWJDB12A58A776AF')
   
   #this song doesn't convert, so has to be searched for manually
   testids.append('SOCGIWH12A8AE4704F')
   
   #note that this function is meant to be used in conjunction with the subset database.
   #if a song does not have an id in the database, it should not be passed into this function.
   
   completed = 0
   
   print("Testing song preview generation...")
   print('-'*30)
   
   #test all the ids
   for sid in testids:
      try: 
         url = getPreview(sid)
         print("id: {} | preview url: {}".format(sid, url))
         completed += 1
      except:
         print("id: {} failed to resolve".format(sid))
   
   
   print('-'*30)
   print("Test complete. {}/5 songs successfully resolved.".format(completed))

