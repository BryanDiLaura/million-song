#!/usr/bin/env python3
"""
   Bryan DiLaura
   June 2015


   This is the implementation of a class to get the tambre data
   from almost (some are thrown out, because they are too small)
   every song in the Million Song dataset. 
   
   The database cursor that is required for some of the functions
   should be of a database in the form/structure:
   
   conn = sqlite3.connect("test.db")
   cursor = conn.cursor()
   cursor.execute('''CREATE TABLE tambre(
                     song_id TEXT PRIMARY KEY,
                     average BLOB,
                     variance BLOB);
                     ''')
                     
   Each entry into the database is the tambre data associated with 
   every song. The average is the average tambre across the entire 
   song, for each of the 12 tambre types. This is of the form of a 
   1x12 array. Variance is a 10x12 array, that contains a variance
   measure of the song, split into 10 chunks, divided by the tambre
   types. This allows for some degree of information of how the song
   changes over time to be preserved, and can be used in the machine
   learning.  
   
"""

import os
import sqlite3
import sys
import time
import datetime
import numpy as np
import glob
from builtins import str

NUM_SAMPLES = 10

#get path to the python api provided by MSD and sanity check
code_path = "/home/brdi4739/Downloads/MSongsDB"
if not os.path.isdir(code_path):
   print("something wrong with code path...")
   
#add the code path to the system python path, so we can import the code
sys.path.append(os.path.join(code_path, "PythonSrc"))

#import the getters
import hdf5_getters as GETTERS


class DataDBCreation():
   def __init__(self):
      #get paths to the dataset
      self.path = "/home/brdi4739/Downloads/MillionSongSubset"
      self.path_data = os.path.join(self.path, "data")
      self.path_addf = os.path.join(self.path, "AdditionalFiles")
      
      #sanity check
      if not(os.path.isdir(self.path) and os.path.isdir(self.path_addf) and os.path.isdir(self.path_data)):
         print("something is wrong with the paths...")
         
      #list to hold the songs that we cannot use because there aren't the required number of segments
      self.too_small = []
      
      


   #simple function to get time elapsed 
   def timeElapsed(self, start, stop):
      return str(datetime.timedelta(seconds = stop - start))
   
   
   #driver function to run function on every file in h5 dataset
   def tambreFromAllFiles(self, cursor, test = False):
      count = 0
      #go through the root directory and iterate through each directory
      for root, dirs, files in os.walk(self.path_data):
         
         #put all the files with the .h5 extension into a list
         files = glob.glob(os.path.join(root,'*.h5'))
         
         #count them...
         count += len(files)
         
#          print(files)
         
         if(not test):
            #apply function to every file
            for f in files:
               print(f)
               self.getTambre(f, cursor)
            
      #return the count, for testing purposes
      return count
      
      
   def getTambre(self, file, cursor):
      
      #get the tambre data from the file
      avg, data, song_id = self.tambreData(file)
      
      #is it a throw out song?
      if avg.all() == 0:
         #put the song id into the list
         self.too_small.append(song_id)
         return
      
      #put it into the database
      cursor.execute("INSERT INTO tambre VALUES ('{}', '{}', '{}');".format(song_id, avg.tolist(), data.tolist()))
      
      
      
      
   def tambreData(self, h5_file):
      #grab the tambre data
      h5 = GETTERS.open_h5_file_read(h5_file)
      full_timbre = np.array(GETTERS.get_segments_timbre(h5))
      
      #get how big the size of the array is
      row, col = full_timbre.shape
      
      #get the song id
      song_id = GETTERS.get_song_id(h5)
      
      #convert it into a string so it can be actually used
      song_id = song_id.decode("UTF-8")
      
      #throw out songs that don't have enough samples
      if row < NUM_SAMPLES *13:
         h5.close()
         return np.array([0,0]), np.array([0,0]), song_id
      
      
      #get the average values for the 12 tambre profile vectors 
      avg_timbre = np.mean(full_timbre, axis = 0)
      
      #make it a two dimentional numpy array so things later will work...
      avg_timbre = np.expand_dims(avg_timbre, axis = 0)
      
      #find the step size (this will throw out up to NUM_COV_SAMPLES -1 segments)
      step = (row - (row % NUM_SAMPLES)) / NUM_SAMPLES
      
      
      #setup some basic counters and indexes
      i = 0
      index1 = 0
      index2 = step - 1
      
      data = []
      
      #for each chunk of the song
      while (i < NUM_SAMPLES):
         
         sample = []
         #in each of the 12 timbre signitures
         for j in range(col):
            
            #compute the variance of of the chunk, and put it in the sample array
            sample.append(np.var(full_timbre[index1:index2][j]))
         
         #put the full sample array into the data
         data.append(sample)
         #update everything
         i+=1
         index1 += step
         index2 += step
      
      #convert the completed data aray to a numpy array
      data_np = np.array(data)
      
      
      #put the average timbre and other data together in the same numpy array
#       ret = np.concatenate((avg_timbre, data_np))
      
      
      #close the file
      h5.close()
      
      #return everything in a tuple, so can be individually inserted into the db
      return avg_timbre, data_np, song_id 
      
      

class add7digital():
   def __init__(self, db):
      #get paths to the dataset
      self.path = "/home/brdi4739/Downloads/MillionSongSubset"
      self.path_data = os.path.join(self.path, "data")
      self.path_addf = os.path.join(self.path, "AdditionalFiles")
      
      #sanity check
      if not(os.path.isdir(self.path) and os.path.isdir(self.path_addf) and os.path.isdir(self.path_data)):
         print("something is wrong with the paths...")
         
      #connect to database
      self.conn = sqlite3.connect(db)
      self.cursor = self.conn.cursor()
      
      
      #attempt to add column
      try:
         self.cursor.execute("ALTER TABLE songs ADD COLUMN track_7digitalid INT;")
      except Exception as e:
         print("The column has already been created")
         print(e)
         
      
   def gather(self, test = False):
      count = 0
      #go through the root directory and iterate through each directory
      for root, dirs, files in os.walk(self.path_data):
         
         #put all the files with the .h5 extension into a list
         files = glob.glob(os.path.join(root,'*.h5'))
         
         #count them...
         count += len(files)
         
#          print(files)
         
         if(not test):
            #apply function to every file
            for f in files:
               print(f)
               self.get7DigitalIDs(f)
               
      
      #after going through all the files, commit and close the database
      self.conn.commit()
      self.conn.close()
            
      #return the count, for testing purposes
      return count
   
   def get7DigitalIDs(self, file):
      
      #get the 7digital id
      h5 = GETTERS.open_h5_file_read(file)
      id7 = GETTERS.get_track_7digitalid(h5)
      song_id = GETTERS.get_song_id(h5).decode("UTF-8")

#       print(id7)
      
      #put it into the database
      try:
         self.cursor.execute("UPDATE songs SET track_7digitalid = {} WHERE song_id == '{}';".format(id7, song_id))
         self.conn.commit()
      except Exception as e:
         print ("couldn't insert into database")
         print ("reason: ", e)
         h5.close()
         return -1
      #close the h5 file
      h5.close()
      
      return 0



#unit tests for classes
if __name__ == "__main__":
   
   
   
   PRINT_SUCCESSES = False
   
   if (not PRINT_SUCCESSES):
      print("NOTE: \tPRINT_SUCCESSES is turned off. This means that only failures will print.")
      print("\tIf you want to print the successes, change this value to True")
      print("-"*80)
   
   
   #-------------------------------------------------------------------------------------
   #--                            test DataDBCreation class                            --
   #-------------------------------------------------------------------------------------
   
   print("testing DataDBCreation class...")
   
   
   if PRINT_SUCCESSES: print("testing the db_creation_class...")
   
   c = DataDBCreation()
   
   if PRINT_SUCCESSES: print("class successfully created")
   
   conn = sqlite3.connect("TEST.db")
   cursor = conn.cursor()
   
   try:
      cursor.execute("DROP TABLE tambre;")
   except:
      pass
   
   cursor.execute("CREATE TABLE tambre(song_id TEXT PRIMARY KEY, average GLOB, data GLOB);")
   
   
   #-------------------------------------------------------------------------------------
   #--                           test tambreData function                              --
   #-------------------------------------------------------------------------------------
   #this song is one that shouldn't pass, because it is too small
   avg, data, song_id = c.tambreData("TRBGEHK12903CEEFC0.h5")
   if (avg.all() != 0):
      print("DataDBCreation::timbreData function failed: bad input returned incorrectly")
      print("avg = ", avg)
   else:
      if PRINT_SUCCESSES: print("timbreData function passed for bad input")
      
   #this song is one that should pass just fine, without problem
   avg, data, song_id = c.tambreData("TRBDBGX128F92F3BC9.h5")
   if (avg.shape != (1,12)):
      print("DataDBCreation::timbreData function failed: shape of average not correct!")
      print("shape = ", avg.shape)
   elif (data.shape != (10,12)):
      print("DataDBCreation::timbreData function failed: shape of data not correct!")
      print("shape = ", data.shape)
   elif (type(song_id) != str):
      print("DataDBCreation::timbreData function failed: problem with the song_id type")
      print("type = ", type(song_id))
   else:
      if PRINT_SUCCESSES: print("timbreData function passed for good input")
   
      
   
   #-------------------------------------------------------------------------------------
   #--                           test getTambre function                               --
   #-------------------------------------------------------------------------------------
   
   #try the bad input file
   c.getTambre("TRBGEHK12903CEEFC0.h5", cursor)
   cursor.execute("SELECT * FROM tambre")
   ret = cursor.fetchall()
   if (len(ret) != 0):
      print("DataDBCreation::getTambre function something was put into the database when it shouldn't have been!")
      print("returned from database: ", ret)
   else:
      if PRINT_SUCCESSES: print("getTambre function passed for bad input")
   
   #good input
   c.getTambre("TRBDBGX128F92F3BC9.h5", cursor)
   cursor.execute("SELECT * FROM tambre;")
   ret = cursor.fetchall()
   if( len(ret) == 0):
      print("DataDBCreation::getTambre function There is nothing in the database, when there should have been something entered")
      
   else:
      if PRINT_SUCCESSES: print("getTambre function passed for good input")
      
      

   #-------------------------------------------------------------------------------------
   #--                      test tambreFromAllFiles function                           --
   #-------------------------------------------------------------------------------------
   
   ret = c.tambreFromAllFiles(cursor, test=True)
   
   if (ret != 10000):
      print("DataDBCreation::tambreFromAllFiles function failed: didn't touch every file")
      print("number of files: ", ret)
   else:
      if PRINT_SUCCESSES: print("tambreFromAllFiles passed")
      
      
      
   conn.commit()
   
   #-------------------------------------------------------------------------------------
   #--                            test add7digital class                               --
   #-------------------------------------------------------------------------------------
   
   print("testing add7digital class...")
   
   try:
      cursor.execute("DROP TABLE songs;")
   except:
      pass
   
   cursor.execute("CREATE TABLE songs(song_id TEXT PRIMARY KEY, average GLOB, data GLOB);")
   cursor.execute("INSERT INTO songs SELECT song_id, average, data FROM tambre;")
   conn.commit()
   
   a = add7digital("TEST.db")
   
   if PRINT_SUCCESSES: print("add7digital class successfully created")
   
   
   
   #-------------------------------------------------------------------------------------
   #--                      test get7DigitalIDs function                               --
   #-------------------------------------------------------------------------------------
      
   #try a track that doesn't have a track_id in the database
   ret = a.get7DigitalIDs("TRBGEHK12903CEEFC0.h5")
   
   if not ret != -1:
      print("add7digital::get7DigitalIDs function added an id for a song that didn't exist in the db!")
   else:
      if PRINT_SUCCESSES: print("add7digital::get7DigitalIDs successfully passed bad input")
   
   #now try one that should work correctly
   ret = a.get7DigitalIDs("TRBDBGX128F92F3BC9.h5")
   
   if ret != 0:
      print("add7digital::get7DigitalIDs function failed for some reason...")
   else:
      if PRINT_SUCCESSES: print("add7digital::get7DigitalIDs successfully passed good input")
      
      
   #-------------------------------------------------------------------------------------
   #--                            test gather function                                 --
   #-------------------------------------------------------------------------------------
      
   ret = a.gather(test=True)
   
   if ret != 10000:
      print("add7digital::gather function did not touch every file")
   else:
      if PRINT_SUCCESSES: print("add7digital::gather successfully touched every file")
   
      
      
      
   print("testing finished!")