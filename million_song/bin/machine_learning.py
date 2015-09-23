#!/usr/bin/env python3


"""
   Bryan DiLaura
   Jun 2015
   
   This file is the class implementation of the guesser. If this file has not already been 
   run on the machine, it will build and train a learner using information from the 
   databases generated using "add7digital" and "database_creation" python scripts. If 
   everything has already been generated, it loads in everything that it needs.
   
   Once everything is initialized, the guesser is ready to go. You can get a song to
   guess on by calling getRandSong, which will return the song_id, the machine's guess, 
   and the correct answer. An example can be seen below:
   
   g = guesser()
   song_id, guess, correct = g.getRandSong()
   
   
   GUESSER EVALUATION:
   At this point the learner has an accuracy of, on average, being within 7 years of the 
   correct answer (testing on 600 songs). There are a few songs that performs extremely 
   poorly on. These tend to be older songs (<1980). I am willing to bet that if I was
   able to use a larger dataset, the accuracy would increase for these values significantly.
   I imagine they are currently being thrown out as outliers, and not really carrying any 
   weight in the regression calculation. With a larger dataset, there would be more points
   clustered in that region, and they, as a whole, would carry more weight, and could 
   actually be a reasonable prediction. 

"""




from sklearn import preprocessing
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn import linear_model
from sklearn.externals import joblib

import sqlite3
import numpy as np
import time
import datetime
from random import randint

import bin.project_logging as project_logging
import logging

l = project_logging.logger()
l.initMachineLogger()



class guesser():
   def __init__(self, number_for_test = 600, log_level=logging.INFO):
      l.mLogger.setLevel(log_level)
      l.mLogger.debug("guesser:__init__<s> - create a guesser, either by loading from file, or from scratch")
      self.test_number = number_for_test
      
      #if we have already generated the datasets and learners, just load them in
      try:
         self.clf = joblib.load('data/learner_{}.pk1'.format(self.test_number))
         self.X = joblib.load('data/songs_{}.pk1'.format(self.test_number))
         self.y = joblib.load('data/years_{}.pk1'.format(self.test_number))
         self.song_id_list = joblib.load('data/song_ids_{}.pk1'.format(self.test_number))
         
         l.mLogger.info("Successfully loaded guesser from file.")
         l.mLogger.debug("guesser:__init__<e>")
         
         
      #things haven't been generated, so they need to be generated
      except:
         l.mLogger.info("Need to generate a guesser. This will take a few minutes")
         t1 = time.time()
         
         #connect to both of the required databases, and create cursors on each of them
         try:
            conn_data = sqlite3.connect("song_audio_data.db")
            data_cursor = conn_data.cursor()
            conn_meta = sqlite3.connect("subset_track_metadata.db")
            meta_cursor = conn_meta.cursor()
         except Exception as e:
            l.mLogger.error("Couldn't connect to the required databases. Problem="+str(e))
            exit()
         
         #a flag mark if it is the first song retrieved, and have to init the arrays
         first_time = True
         
         #a list holding song ids...not terribly confusing there
         self.song_id_list = []
         
         #run sqlite command to get everything from tambre dataset
         data_cursor.execute("SELECT * FROM tambre;")
         
         #get data from first song
         d = data_cursor.fetchone()
         
         #while there are still things to retrieve
         while (d != None):
            
            #get the song id, average tambre, and tambre data (note that the last two are pickled!)
            song_id = d[0]
            avg = self.unpickle(d[1])
            data = self.unpickle(d[2])
            
            #put the song id into the list
            self.song_id_list.append(song_id)
            
            #get other metadata about song
            meta_cursor.execute("SELECT duration, artist_familiarity, "\
                                "artist_hotttnesss, artist_id, year FROM songs WHERE song_id == '{}';".format(song_id))
            metadata = meta_cursor.fetchone()
      
            #Throw out songs that don't have year information
            if (metadata[4] != 0):
            
               #first time through, init X, y, and artist ID's
               if first_time:
                  X_incomplete = np.concatenate((avg[:], data[:], metadata[0:2]))
                  self.y = np.array([metadata[4]])
                  IDs = np.array([metadata[3]])
                  first_time = False
               else:
                  #otherwise, add the new row
                  X_incomplete = np.vstack([X_incomplete, np.concatenate((avg[:], data[:], metadata[0:2]))])
                  self.y = np.concatenate((self.y, np.array([metadata[4]])))
                  IDs = np.concatenate((IDs, np.array([metadata[3]])))
               
            
            #get the next line of the database         
            d = data_cursor.fetchone()
            
         t2 = time.time()
         
         #tell the user how long it took to get everything
         l.mLogger.debug("finished loading. this took: " +str(self.timeElapsed(t1, t2)))
   
   
         #Tokenize the artist IDs
         vectorizer = TfidfVectorizer()
         vectorizer.fit_transform(IDs[:])
         #use the vocabulary dictionary and append to the X vector the artist ID
         self.X = np.append(X_incomplete[0], vectorizer.vocabulary_[IDs[0].lower()])
         for row in (range(X_incomplete.shape[0])[1:]):   
            temp = np.append(X_incomplete[row], vectorizer.vocabulary_[IDs[row].lower()])
            self.X = np.vstack([self.X, temp])
          
   
         #normalize the data for the machine learning to be more accurate
         self.X = preprocessing.scale(self.X)
         
         #tell the user how many songs there are to choose from
         l.mLogger.debug("number of songs: "+ str(self.X.shape[0]))
   
         #create the learner. 
         #decided on this one because was able to get error down the best with this one compared to svr. 
         self.clf = linear_model.Lasso(alpha = .3)
   #       clf = svm.SVR(C = 300, kernel='rbf')
         
         #train...
         l.mLogger.debug("training...") 
         self.clf.fit(self.X[0:-self.test_number],self.y[0:-self.test_number])
         l.mLogger.debug("Done!")
         
         
         #save the learner to file, giving it persistence
         l.mLogger.debug("saving learner to file...")
         joblib.dump(self.clf, 'data/learner_{}.pk1'.format(self.test_number), compress = 9)
         
         #save datasets to files as well
         l.mLogger.debug("saving datasets to file...")
         joblib.dump(self.X, 'data/songs_{}.pk1'.format(self.test_number), compress = 9)
         joblib.dump(self.y, 'data/years_{}.pk1'.format(self.test_number), compress = 9)
         joblib.dump(self.song_id_list, 'data/song_ids_{}.pk1'.format(self.test_number), compress = 9)
         
         l.mLogger.info("Done.")
         l.mLogger.debug("guesser:__init__<e>")
      
      
   def getRandSong(self):
      #generate a random song and the associated prediction and correct answer
      l.mLogger.info("generating random song and associated guess")
      #generate a random index
      rand_index = randint(0,self.test_number)
      
      #grab all the information...
      song_id = self.song_id_list[-rand_index]
      prediction = int(self.clf.predict(self.X[-rand_index])[0])    
      correct = self.y[-rand_index]
      
      #return everything as a tuple
      return song_id, prediction, correct
      
   
      
      
   def unpickle(self, content):
      #unpickles data from database, put in there as a glob. returns a numpy array of floats
      test = content.replace('[', '').replace(']', '').replace(' ', '')
      temp = []
      for nums in test.split(','):
         temp.append(float(nums))
      #turn into numpy array
      return np.array(temp)
      
      
   
   def timeElapsed(self, start, stop):
      #simple function to get time elapsed 
      return str(datetime.timedelta(seconds = stop - start))
         
         
         
if __name__ == '__main__':
   g = guesser()
    
   for i in range(5):
       
      songID, pred, cor = g.getRandSong()
       
      print("songID: {}  prediction: {}  answer: {}".format(songID, pred, cor))
   
   
   #do some evaluation on how well it is estimating the year
   avg_err = []
   avg_yr_off = []
     
   for i in range(600): 
     
      prediction = g.clf.predict(g.X[-i])[0].round()
      error = abs(((prediction - g.y[-i])/g.y[-i])*100.0)
      years_off = abs(g.y[-i] - prediction)
        
      avg_err.append(error)
      avg_yr_off.append(years_off)
        
      print("actual: {}  prediction: {}  years off: {}  error: {}".format(g.y[-i], prediction, years_off, error))
     
   print("The average error was: ", np.mean(avg_err))
   print("The average years off was: ", np.mean(avg_yr_off))

