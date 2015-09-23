#!/usr/bin/env python3

"""
   Bryan DiLaura
   June 2015


   script to go through all of the songs in the million song subset and
   creates a database of the tambre information, rather than being 
   forced to go to the files to manually get the data through timely 
   i/o operations.
   
   The main workhorse of this script is the db_creation_class file, which
   contains a class that grabs the information from each file, organizes 
   it in a useful way, and then throws it into the database passed to it. 
   
"""


from dev.db_creation_class import DataDBCreation
import sqlite3
import time

#make the creation class
creation = DataDBCreation()

#open/create the database
conn = sqlite3.connect("../bin/song_audio_data.db")

#create cursor
cursor = conn.cursor()

#if the table already exists, delete it
try:
   cursor.execute("DROP TABLE tambre;")
except:
   pass

#create the tambre table
cursor.execute('''CREATE TABLE tambre(
                  song_id TEXT PRIMARY KEY,
                  average BLOB,
                  variance BLOB);
                  ''')


t1 = time.time()
#get the tambre data from every song
creation.tambreFromAllFiles(cursor )
t2 = time.time()

print(creation.timeElapsed(t1, t2))

#commit and close the database, saving it all
conn.commit()
conn.close()

#stuff to keep track of the songs that are too small, that we had to throw out
print(creation.too_small)
print(len(creation.too_small))
f = open("dont_use.txt", 'w')
for id in creation.too_small:
   f.write(id + "\n")
   
f.close()

