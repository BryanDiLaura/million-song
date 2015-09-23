#!/usr/bin/env python3

"""
   Bryan DiLaura
   July 2015
   
   This class is an implementation of a cherrypy webserver, which runs all of 
   the required pieces to server the game's frontend via html requests. Once the
   startGame class is initialized, the webserver is started and ready to use.
   
   At this point all requests are being routed through localhost on port 8080, so, 
   for example, to see the index of the system you could use the following url in 
   a browser (after the server is started):
   
   http://localhost:8080/
   
   
   
   NOTES:
   
   - a large portion of this game is not a "bulletproof" implementation.
      There are many ways how someone who was determined enough, could
      break the game in a variety of ways. I tried to prevent all of the 
      easy ones that I could think of, but there is no way that I got them all.
   
   - I have had no way to test this in a true "server and client" setup,
      on separate machines. I think that it will work, assuming all of
      the DNS and cherrypy stuff are set up correctly, but I can't be sure.
   
   - I am fairly sure that the session stuff is working, but it is really hard to
      test. From what I can tell, it all seems to work fine, but there is a possibility
      that if there are enough clients attached all at once, things could break.
   
"""



import cherrypy
import os

import bin.song_preview as song_preview
import bin.machine_learning as machine_learning
import sqlite3
import random, string

from bin.project_logging import logger
import logging

l = logger()
l.initServerLogger()



DEATH_OR_GLORY = "https://p.scdn.co/mp3-preview/5cb9ef2ec5bd2b131db259b03017b28f941ac17e"

class game(object):
   def __init__(self):
      l.sLogger.debug("game:__init__<s>")
      
      #create a guesser
      try: self.g = machine_learning.guesser()
      except Exception as e:
         l.sLogger.error("Couldn't get the guesser! Problem: " + str(e))
      
      #make some local variables that we can use
      self.compGuess = None
      self.correct = None
      self.songID = None
      self.lastSongID = None
      
      l.sLogger.debug("game:__init__<e>")
      
      
   
   @cherrypy.expose
   def index(self):
      l.sLogger.debug("game:index<s> - showing the index html page")
      l.sLogger.debug("game:index<e>")
      return """
            <!DOCTYPE html>
            <html>
            <head>
               <link rel="stylesheet" href="/css/layout.css">
            </head>
            
            <body>
               <h1>This application was written by Bryan DiLaura.</h1>
            </body>
            </html>
            """
            
            
            
   @cherrypy.expose
   def gameTurn(self, user=None, diff=None, disp=None , minYr=1926, maxYr=2010):
      
      l.sLogger.debug("game:gameTurn<s> - create a randomly generated turn for the game")
      
      l.sLogger.debug("variables passed: ")
      l.sLogger.debug("user="+str(user))
      l.sLogger.debug("diff="+str(diff))
      l.sLogger.debug("disp="+str(disp))
      l.sLogger.debug("minYr="+str(minYr))
      l.sLogger.debug("maxYr="+str(maxYr))

      title = None
      artist = None
      album = None
      
      self.conn = sqlite3.connect("subset_track_metadata.db")
      self.cursor = self.conn.cursor()

      preview = None
      tries = 0
      
      cherrypy.session['diff'] = diff
      
      
      #guarentee we get a preveiw
      while preview == None and tries <100:
         l.sLogger.debug("generating a random song")
         tries += 1
         self.songID, self.compGuess, self.correct = self.g.getRandSong()
         
         #make sure the song is in the year range specified
         if self.correct >= int(minYr) and self.correct <= int(maxYr):
            cherrypy.session['songID'] = self.songID
            cherrypy.session['compGuess'] = self.compGuess
            cherrypy.session['correct'] = self.correct
            cherrypy.session['disp'] = disp
            cherrypy.session['minYr'] = minYr
            cherrypy.session['maxYr'] = maxYr
            cherrypy.session['session'] = ""
            
            preview = song_preview.getPreview(self.songID)
            
            self.cursor.execute("SELECT title, artist_name, release FROM songs WHERE song_id == '{}'".format(self.songID))
            
            data = self.cursor.fetchone()
            
            if diff != None:
               if diff == "H" or diff == "M" or diff == "E":
                  try: title = data[0]
                  except: l.sLogger.debug("couldn't get track title")
               
               if diff == "M" or diff == "E":
                  try: artist = data[1]
                  except: l.sLogger.debug("couldn't get artist name")
               
               if diff == "E":
                  try: album = data[2]
                  except: l.sLogger.debug("couldn't get album name")
                  
               #custom game
               if diff == "C":
                  if 't' in disp:
                     try: title = data[0]
                     except: l.sLogger.debug("couldn't get track title")
                     
                  if 'A' in disp:
                     try: artist = data[1]
                     except: l.sLogger.debug("couldn't get artist name")
                     
                  if 'a' in disp:
                     try: album = data[2]
                     except: l.sLogger.debug("couldn't get album name")
         
      if tries == 100:
         return "<font size='7'>Sorry, could not find a song of that type. Please try again with different settings.</font>"
      
      l.sLogger.debug("preview url="+preview)
      
      #this is a html file that is dynamically added to, depending on parameters passed in the url
      html = """
         <!DOCTYPE html>
         <html>
         <head>
         <link rel="stylesheet" href="/css/layout.css" type="text/css" />
         <style>
            .center{
                margin: auto;
                width: 60%;
                padding: 10px;
            }
            input[type=submit] {
               width: 10em;  height: 2em;
            }
         </style>
         <script type="text/javascript">
               window.history.forward();
               function noBack(){window.history.forward();}
         </script>
         </head>
         
         <body onload="noBack();" onpageshow="if (event.persisted) noBack();" onunload="">
         <br><br><br><br><br>"""
      
      #Title, artist, and album parameters. If nothing is provided in url, nothing is shown
      if (title != None):
         html +="""
            <div class="center" id="header">
               <font size="10">Title: """+title+"""</font>
            </div>
            <br>"""
            
      if (artist != None):
         html +="""
            <div class="center" id="header">
               <font size="10">Artist: """+artist+"""</font>
            </div>
            <br>"""
      if (album != None):
         html +="""      
            <div class="center" id="header">
               <font size="10">Album: """+album+"""</font>
            </div>"""
         
      #NOTE THE INCLUSION OF THE URL HERE!!!   
      html +="""
         <div class="center">
            <br><br><br><br>
            <font size="5">Listen:</font>
            <br>
                <audio controls>
               <source src="""+preview+""" type="audio/mpeg" align="center">
               Your browser doesn't support playing audio. C'mon...update the browser.
            </audio>
         </div>
      
         <div class="center">
            <br><br><br><br>
            <font size='5'>I think it came out in:  </font>
      
            <form method="get", action="checkAnswer?">
               <select id="guess" name="guess">
                  <option value="0">----</option>"""
                  
      #if the maxYr or minYr are provided, they come as strings. Convert to ints just in case
      maxYr = int(maxYr)
      minYr = int(minYr)
      
      #generate the year spinner
      for i in range(maxYr, minYr-1, -1):
         html += '<option value ="' + str(i) + '">' + str(i) + '</option>'
         
         
      #finish up the remaining html code   
      html +="""        
               </select>
                  <br><br><br>
                  <input type="submit" value="Guess">
                  <input type="hidden" name="user" value='"""+str(user)+"""'/>
                  <input type="hidden" name="session" value='"""+self.randomword(20)+"""'/>
            </form>
               
         </div>
         
         </body>
         
         </html>
         """
         
#       #prevent cheating 
      self.session = None
      
      l.sLogger.info("Showing gameTurn for songid:"+str(self.songID))
      
      l.sLogger.debug("game:gameTurn<e>")
      
      #return the html to be displayed
      return html
   
   
   
   @cherrypy.expose
   def sample(self, gen=True, user=None, url=DEATH_OR_GLORY, diff=None, title=None, artist=None, album=None, minYr=1926, maxYr=2010):
      
      l.sLogger.debug("game:sample<s> - generates a webpage where everything can be specified. Used for samples")
      
      l.sLogger.debug("parameters:")
      l.sLogger.debug("gen="+str(gen))
      l.sLogger.debug("user="+str(user))
      l.sLogger.debug("url="+str(url))
      l.sLogger.debug("diff="+str(diff))
      l.sLogger.debug("title="+str(title))
      l.sLogger.debug("artist="+str(artist))
      l.sLogger.debug("album="+str(album))
      l.sLogger.debug("minYr="+str(minYr))
      l.sLogger.debug("maxYr="+str(maxYr))
      
      #disables the guess button
      
      #generate song randomly
      if gen == "F":
         generate = False
         preview = url
      else:
         generate = True
         self.conn = sqlite3.connect("subset_track_metadata.db")
         self.cursor = self.conn.cursor()
         
      if generate:
         preview = None
         
         cherrypy.session['diff'] = diff
         
         #guarentee we get a preveiw
         while preview == None:
            self.songID, self.compGuess, self.correct = self.g.getRandSong()
            
            cherrypy.session['songID'] = self.songID
            cherrypy.session['compGuess'] = self.compGuess
            cherrypy.session['correct'] = self.correct
            
            preview = song_preview.getPreview(self.songID)
            
            self.cursor.execute("SELECT title, artist_name, release FROM songs WHERE song_id == '{}'".format(self.songID))
            
            data = self.cursor.fetchone()
            
            if diff != None:
               if diff == "H" or diff == "M" or diff == "E":
                  try: title = data[0]
                  except: l.sLogger.debug("couldn't get track title")
               
               if diff == "M" or diff == "E":
                  try: artist = data[1]
                  except: l.sLogger.debug("couldn't get artist name")
               
               if diff == "E":
                  try: album = data[2]
                  except: l.sLogger.debug("couldn't get album name")
               
         
      
      
      #this is a html file that is dynamically added to, depending on parameters passed in the url
      html = """
         <!DOCTYPE html>
         <html>
         <head>
         <link rel="stylesheet" href="/css/layout.css" type="text/css" />
         <style>
            .center{
                margin: auto;
                width: 60%;
                padding: 10px;
            }
         </style>
         <script type="text/javascript">
               window.history.forward();
               function noBack(){window.history.forward();}
         </script>
         </head>
         
         <body onload="noBack();" onpageshow="if (event.persisted) noBack();" onunload="">
         <br><br><br><br><br>"""
      
      #Title, artist, and album parameters. If nothing is provided in url, nothing is shown
      if (title != None):
         html +="""
            <div class="center" id="header">
               <font size="10">Title: """+title+"""</font>
            </div>
            <br>"""
            
      if (artist != None):
         html +="""
            <div class="center" id="header">
               <font size="10">Artist: """+artist+"""</font>
            </div>
            <br>"""
      if (album != None):
         html +="""      
            <div class="center" id="header">
               <font size="10">Album: """+album+"""</font>
            </div>"""
         
      #NOTE THE INCLUSION OF THE URL HERE!!!   
      html +="""
         <div class="center">
            <br><br><br><br>
            <font size="5">Listen:</font>
            <br>
                <audio controls>
               <source src="""+preview+""" type="audio/mpeg" align="center">
               Your browser doesn't support playing audio. C'mon...update the browser.
            </audio>
         </div>
      
         <div class="center">
            <br><br><br><br>
            <font size='5'>I think it came out in:  </font>
      
            
               <select id="guess" name="guess">
                  <option value="0">----</option>"""
                  
      #if the maxYr or minYr are provided, they come as strings. Convert to ints just in case
      maxYr = int(maxYr)
      minYr = int(minYr)
      
      #generate the year spinner
      for i in range(maxYr, minYr-1, -1):
         html += '<option value ="' + str(i) + '">' + str(i) + '</option>'
         
         
      #finish up the remaining html code   
      html +="""        
               </select>
                  <br><br><br>
                  <input type="submit" value="Guess">
                  <input type="hidden" name="user" value='"""+str(user)+"""'/>
               
         </div>
         
         </body>
         
         </html>
         """
      
      l.sLogger.info("Generating webpage for song: "+ str(title))
      l.sLogger.debug("game:sample<e>")
      
      #return the html to be displayed
      return html
   
   
   
   @cherrypy.expose
   def checkAnswer(self, guess, user, session):
      
      l.sLogger.debug("game:checkAnswer<s> - checks the user's answer against the acutal, provides scoring feedback, and updates appropriate db")
      
      l.sLogger.debug("parameters:")
      l.sLogger.debug("guess="+str(guess))
      l.sLogger.debug("user="+str(user))
      l.sLogger.debug("session="+str(session))
      
      
      #get the users database
      self.uconn = sqlite3.connect("data/gui/users.db")
      self.ucursor = self.uconn.cursor()
      self.ucursor.execute("PRAGMA foreign_keys = ON;")

      #convert the user id into the username
      self.ucursor.execute("SELECT username FROM users WHERE id == '{}'".format(user))
      data = self.ucursor.fetchone()
      if data == None:
         return "<font size=5>Error 406: Something went wrong with the username. Please re-launch the game.</font>"
      self.username = data[0]
      
      #check for no guess
      if int(guess) == 0:
         l.sLogger.info("There was a request with a null guess. Redirecting...")
         para = "diff=" + str(cherrypy.session['diff']) + "&user=" + user
         if cherrypy.session['disp'] != None:
            para += "&disp="+str(cherrypy.session['disp'])
                           
         if int(cherrypy.session['minYr']) != 1926:
            para += "&minYr="+str(cherrypy.session['minYr'])
         
         if int(cherrypy.session['maxYr']) != 2010:
            para += "&maxYr="+str(cherrypy.session['maxYr'])
         html = """
               <html>
               <head>
               <link rel="stylesheet" href="/css/layout.css" type="text/css" />
               <style>
                  .center{
                      margin: auto;
                      width: 60%;
                      padding: 10px;
                  }
                  
               </style>
               
               
               
               </head>
               
               <body>
                  <font size=7>Make sure you actually guess! Going to a new song...</font>
                  <meta http-equiv="refresh" content='2;URL=http://localhost:8080/gameTurn?"""+para+"""'>
               </body>
               
               </html>
         """
         l.sLogger.debug("game:checkAnswer<e>")
         
         return html
      
      
      
      #check for refresh exploit
      if self.session == session:
         l.sLogger.info("user tried to refresh, redirecting...")
         html = """<!DOCTYPE html>
               <html>
               <head>
               <link rel="stylesheet" href="/css/layout.css" type="text/css" />
               <style>
                  .center{
                      margin: auto;
                      width: 60%;
                      padding: 10px;
                  }
               </style>
               </head>
               
               <body>
               <br>
               <div class="center">
                  <font size="10">Continue the game?</font>
               
                  <br>
                  <form type="get" action="gameTurn">
                     <input type="submit" value="Play another" />
                        <input type="hidden" name="diff" value='"""+str(cherrypy.session['diff'])+"""' />
                        <input type="hidden" name="user" value='"""+str(user)+"""'/>"""
                           
         if cherrypy.session['disp'] != None:
                           html += """<input type="hidden" name="disp" value='"""+str(cherrypy.session['disp'])+"""'/>"""
                           
         if int(cherrypy.session['minYr']) != 1926:
                           html += """<input type="hidden" name="minYr" value='"""+str(cherrypy.session['minYr'])+"""'/>"""
         
         if int(cherrypy.session['maxYr']) != 2010:
                           html += """<input type="hidden" name="maxYr" value='"""+str(cherrypy.session['maxYr'])+"""'/>"""
         html +="""
                     </form>
                        <p>   </p>
                     <form type="get" action="saveScore">
                           <input type="submit" value="Quit">
                     </form>
                  </div>
                  
                  </body>
                  </html>
                  
                  """
         l.sLogger.debug("game:checkAnswer<e>")
         return html
      #set the session for refresh exploit
      self.session = session
      
      #store the users guess
      self.guess = guess
      

      #calculate the winner
      userMargin = abs(int(guess) - int(cherrypy.session['correct']))
      compMargin = abs(int(cherrypy.session['compGuess']) - int(cherrypy.session['correct']))
      
      if userMargin == compMargin:
         l.sLogger.debug("the game was a tie")
         winner = "Tie"
         roundScore = 0
      elif userMargin < compMargin:
         l.sLogger.debug("the user won the round")
         winner = self.username
         roundScore = compMargin
      else:
         l.sLogger.debug("the computer won the round")
         winner = "Computer"
         roundScore = 0 - userMargin
         
      if int(guess) == int(cherrypy.session['correct']):
         roundScore += 20
         
         
      #get the user's score
      d = cherrypy.session['diff']
      l.sLogger.debug("attempting to get score from database "+d)
      if d == "E":
         #try to get it directly
         try: 
            self.ucursor.execute("SELECT games, avg FROM easy WHERE username == '{}'".format(self.username))
            data = self.ucursor.fetchone()
            
            games = data[0]
            score = data[1]
            
            userScore = score + roundScore
            
            self.ucursor.execute("UPDATE easy SET games = {}, avg = {} WHERE username == '{}'".format(games +1, userScore, self.username))
            
         #this is the first game
         except:
            self.ucursor.execute("INSERT INTO easy VALUES ('{}', {}, {});".format(self.username, 1, roundScore))
            
            userScore = roundScore
            
      if d == "M":
         #try to get it directly
         try: 
            self.ucursor.execute("SELECT games, avg FROM medium WHERE username == '{}'".format(self.username))
            data = self.ucursor.fetchone()
            
            games = data[0]
            score = data[1]
            
            userScore = score + roundScore
            
            self.ucursor.execute("UPDATE medium SET games = {}, avg = {} WHERE username == '{}'".format(games +1, userScore, self.username))
            
         #this is the first game
         except:
            self.ucursor.execute("INSERT INTO medium VALUES ('{}', {}, {});".format(self.username, 1, roundScore))
            
            userScore = roundScore
            
      if d == "H":
         #try to get it directly
         try: 
            self.ucursor.execute("SELECT games, avg FROM hard WHERE username == '{}'".format(self.username))
            data = self.ucursor.fetchone()
            
            games = data[0]
            score = data[1]
            
            userScore = score + roundScore
            
            self.ucursor.execute("UPDATE hard SET games = {}, avg = {} WHERE username == '{}'".format(games +1, userScore, self.username))
            
         #this is the first game
         except:
            self.ucursor.execute("INSERT INTO hard VALUES ('{}', {}, {});".format(self.username, 1, roundScore))
            
            userScore = roundScore
            
      if d == "C":
         userScore = "(Custom Game)"
            
         
      self.uconn.commit()
         

      
      html ="""<!DOCTYPE html>
               <html>
               <head>
               <link rel="stylesheet" href="/css/layout.css" type="text/css" />
               <style>
                  .center{
                      margin: auto;
                      width: 60%;
                      padding: 10px;
                  }
                  input[type=submit] {
                     width: 10em;  height: 2em;
                  }
               </style>
               </head>
               
               <body>
                  <br><br><br><br><br>
                  
                  <div class="center" id="header">
                     <font size="10">Winner: """+winner+"""</font>
                  </div>
                  <br>
                  
                  <div class="center" id="header">
                     <font size="10">"""+self.username+"""'s Guess: """+ guess +"""</font>
                  </div>
                  <br>
                  
                  <div class="center", id="header">
                     <font size="10">Computer's Guess: """+str(cherrypy.session['compGuess'])+""" </font>
                  </div>
                  <br>
                  
                  <div class="center" id="header">
                     <font size="10">Actual Year: """+str(cherrypy.session['correct'])+"""</font>
                  </div>
                  <br>
                  
                  <div class="center" id="header">
                     <font size="10">This Round's Score: """+str(roundScore)+"""</font>
                  </div>
                  <br>
                  
                  <div class="center" id="header">
                     <font size="10">Overall Score: """+str(userScore)+"""</font>
                  </div>
                  <br><br>
                  
                  <div class="center">
                     <form type="get" action="gameTurn">
                        <input type="submit" value="Play another" />
                        <input type="hidden" name="diff" value='"""+str(cherrypy.session['diff'])+"""' />
                        <input type="hidden" name="user" value='"""+str(user)+"""'/>"""
                        
      if cherrypy.session['disp'] != None:
                        html += """<input type="hidden" name="disp" value='"""+str(cherrypy.session['disp'])+"""'/>"""
                        
      if int(cherrypy.session['minYr']) != 1926:
                        html += """<input type="hidden" name="minYr" value='"""+str(cherrypy.session['minYr'])+"""'/>"""
      
      if int(cherrypy.session['maxYr']) != 2010:
                        html += """<input type="hidden" name="maxYr" value='"""+str(cherrypy.session['maxYr'])+"""'/>"""
                     
                     
      html +="""
                     </form>
                     <p>   </p>
                     <form type="get" action="saveScore">
                        <input type="submit" value="Quit">
                     </form>
                     
                  </div>
                  
               </body>
               
               </html>
               """
      
      l.sLogger.info("Showing the round report")
      l.sLogger.debug("game:checkAnswer<e>")
      
      return html
#       return "User guess: " + str(guess) + " | Comp guess: " + str(cherrypy.session['compGuess']) + " | Actual: " + str(cherrypy.session['correct'])



   @cherrypy.expose
   def saveScore(self):
      l.sLogger.debug("game:saveScore<s> - shows a 'thanks for playing', and asks them to close the window")
      l.sLogger.debug("game:saveScore<e>")
      
      return"""<!DOCTYPE html>
               <html>
               <head>
               <link rel="stylesheet" href="/css/layout.css" type="text/css" />
               <style>
                  .center{
                      margin: auto;
                      width: 60%;
                      padding: 10px;
                  }
               </style>
               
               </head>
               
               <body>
               <br><br><br><br>
               <div class="center" id="header">
                  <font size="10">Thanks for playing!</font>
                  <br>
                  <font size="5">Please exit the window</font>
               </div>
               <br><br><br>
               <div class="center" id="header">
                  <font size="10">Game created by: Bryan DiLaura</font>
               </div>
               
               </body>
               </html>
            """
         
         
            
   def randomword(self, length=20):
      l.sLogger.debug("newUserDialog:randomword<s> - generate random string of ascii chars")
      try: a = ''.join(random.choice(string.ascii_letters) for i in range(length))
      except Exception as e:
         a = "error"
         l.sLogger.error("There was a problem: "+ str(e))
         l.sLogger.debug("length")
      
      l.sLogger.debug("newUserDialog:randomword<e>")
      return a
   
   
  
class startGame():
   #a launcher for the entire server, making sure the correct config is given to it
   def __init__(self, loglevel = logging.INFO):  
      
      l.sLogger.setLevel(loglevel)
      
      #config file to be used. It tells the server where the css resources are
      conf = {
              '/': {
                    'tools.sessions.on':True
                    },
              
              '/css': {
                       'tools.staticdir.on': True,
                       'tools.staticdir.dir': os.path.join(os.getcwd(), 'data/gui/styles')#'/home/brdi4739/workspace/million_song/data/gui/styles'
                       }
              }
      
      
      cherrypy.quickstart(game(), '/', config = conf)
  

         
if __name__ == "__main__":
   
   startGame()
