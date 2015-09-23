#!/usr/bin/env python3

#data exploration on the million song Database


import os
import sys
import numpy as np
import time
import datetime
import sqlite3


NUM_COV_SAMPLES = 10


t1 = time.time()

#get paths to the dataset
path = "/home/brdi4739/Downloads/MillionSongSubset"
path_data = os.path.join(path, "data")
path_addf = os.path.join(path, "AdditionalFiles")

#sanity check
if not(os.path.isdir(path) and os.path.isdir(path_addf) and os.path.isdir(path_data)):
   print("something is wrong with the paths...")

# print(path)
# print(path_data)
# print(path_addf)

#get path to the python api provided by MSD and sanity check
code_path = "/home/brdi4739/Downloads/MSongsDB"
if not os.path.isdir(code_path):
   print("something wrong with code path...")
   
#add the code path to the system python path, so we can import the code
sys.path.append(os.path.join(code_path, "PythonSrc"))

#import the getters
import hdf5_getters as GETTERS


#simple function to get time elapsed 
def timeElapsed(start, stop):
   return str(datetime.timedelta(seconds = stop - start))


t2 = time.time()




# print(timeElapsed(t1, t2))

#explore the databases...
"""to explore the databases open the database in 
   a sqlite3 shell, and run the command:
      .schema
   this will show all of the tables in the dataset,
   as well as any other useful information
"""

def timbreData(h5_file):
   #grab the tambre data
   h5 = GETTERS.open_h5_file_read(h5_file)
   full_timbre = np.array(GETTERS.get_segments_timbre(h5))
   #get how big the size of the array is
   row, col = full_timbre.shape
   
   #get the average values for the 12 tambre profile vectors 
   avg_timbre = np.mean(full_timbre, axis = 0)
   
   #make it a two dimentional numpy array so things later will work...
   avg_timbre = np.expand_dims(avg_timbre, axis = 0)
   
   #find the step size (this will throw out up to NUM_COV_SAMPLES -1 segments)
   step = (row - (row % NUM_COV_SAMPLES)) / NUM_COV_SAMPLES
   
#    print (avg_timbre.shape)
#    print (step)
   
   #setup some basic counters and indexes
   i = 0
   index1 = 0
   index2 = step - 1
   
   data = []
   
   #for each chunk of the song
   while (i < NUM_COV_SAMPLES):
      
      sample = []
      #in each of the 12 timbre signitures
      for j in range(col):
         
#          print(j)
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
   
   print(avg_timbre.shape)
   print(data_np.shape)
   
   #put the average timbre and other data together in the same numpy array
   ret = np.concatenate((avg_timbre, data_np))
   
   song_id = GETTERS.get_song_id(h5)
   
   song_id = song_id.decode("UTF-8")
   
#    print(ret.shape)
#    print(ret)
   #close the file
   h5.close()
   
   
   return avg_timbre, data_np, song_id
      
   
   
   
   
   

t1 = time.time()
avg, data, song_id = timbreData("TRBDBGX128F92F3BC9.h5")
t2 = time.time()

jesus = timbreData("TRBFBQG128F9313C6D.h5")
other = timbreData("TRALKHV128F4270340.h5")

print(timeElapsed(t1, t2))

# a = plt.figure(1)
# plt.plot(death[:][:], 'g')
# 
# b = plt.figure(2)
# plt.plot(jesus[:][:], 'r')
# 
# c = plt.figure(3)
# plt.plot(other[:][:], 'b')
# 
# plt.show()


conn = sqlite3.connect("test.db")

cursor = conn.cursor()

try:
   cursor.execute("DROP TABLE test1;")
except:
   pass

cursor.execute('''CREATE TABLE test1(
                  song_id TEXT PRIMARY KEY,
                  averages BLOB,
                  tambre BLOB);''')

print(song_id)

cursor.execute("INSERT INTO test1 VALUES ('{}', '{}', '{}');".format(song_id, avg.tolist(), data.tolist()))

cursor.execute("SELECT * FROM test1;")

row = cursor.fetchall()

song_id = row[0][0]

avg = np.array(row[0][1])

data = np.array(row[0][2])

print(row)

print("song_id: ", song_id)

print("average: ", avg)

print("data: ", data)


# #open up a h5 file
# h5 = GETTERS.open_h5_file_read("TRBFBQG128F9313C6D.h5")
# #get the timbre array (huge number of rows!)
# timbre = np.array(GETTERS.get_segments_timbre(h5))
# h5.close()
# 
# # print(timbre.shape)
# # print(timbre)
# 
# print (np.ma.cov(timbre).shape)
# 
# timbre_norm = np.mean(timbre, axis = 0)
# 
# # print(timbre_norm.shape)   
# 
# print (timbre_norm)
# 
# 
# 
# #open up a h5 file
# h5 = GETTERS.open_h5_file_read("TRALKHV128F4270340.h5")
# #get the timbre array (huge number of rows!)
# timbre = np.array(GETTERS.get_segments_timbre(h5))
# h5.close()
# 
# # print(timbre.shape)
# # print(timbre)
# 
# timbre_norm = np.mean(timbre, axis = 0)
# 
# # print(timbre_norm.shape)   
# 
# print (timbre_norm)


