#!/usr/bin/env python3


"""
   Bryan Dilaura
   July 2015
   
   This file sets up the logging system for the application.
"""

import logging
from logging.handlers import RotatingFileHandler
import sys


class logger():
   def __init__(self):
      print("initializing logger class!")
      
   def initGuiLogger(self):
      #create a logger
      #could create more of these to have the "logger name" be different 
      self.guiLogger = logging.getLogger("GUI Launcher")
      #what this logger is able to catch
      self.guiLogger.setLevel(logging.DEBUG)
      
      #can also use a timed rotating file handler if desired
      fh = RotatingFileHandler("logs/gui.log", maxBytes=100000, backupCount=5)
      #set what this handler will catch
#       fh.setLevel(logging.INFO)
      
      #create a handler, printing info to console (stderr)
      ch = logging.StreamHandler(sys.stderr)
#       ch.setLevel(logging.INFO)
      #create a formatter, and add it to both the handlers
      formatter = logging.Formatter('%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s')
      fh.setFormatter(formatter)
      ch.setFormatter(formatter)
      #add the handlers to the logger
      self.guiLogger.addHandler(ch)
      self.guiLogger.addHandler(fh)


      self.guiLogger.debug("logger set up. starting the application...")
      self.guiLogger.debug("initializing the application")
      
   def initServerLogger(self):
      #create a logger
      #could create more of these to have the "logger name" be different 
      self.sLogger = logging.getLogger("Server")
      #what this logger is able to catch
      self.sLogger.setLevel(logging.DEBUG)
      
      #can also use a timed rotating file handler if desired
      fh = RotatingFileHandler("logs/server.log", maxBytes=100000, backupCount=5)
      #set what this handler will catch
#       fh.setLevel(logging.INFO)
      
      #create a handler, printing info to console (stderr)
      ch = logging.StreamHandler(sys.stderr)
#       ch.setLevel(logging.INFO)
      #create a formatter, and add it to both the handlers
      formatter = logging.Formatter('%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s')
      fh.setFormatter(formatter)
      ch.setFormatter(formatter)
      #add the handlers to the logger
      self.sLogger.addHandler(ch)
      self.sLogger.addHandler(fh)


      self.sLogger.debug("logger set up. starting the application...")
      self.sLogger.debug("initializing the application")
      
   def initMachineLogger(self):
      #create a logger
      #could create more of these to have the "logger name" be different 
      self.mLogger = logging.getLogger("MachineLearning")
      #what this logger is able to catch
      self.mLogger.setLevel(logging.DEBUG)
      
      #can also use a timed rotating file handler if desired
      fh = RotatingFileHandler("logs/machinelearning.log", maxBytes=100000, backupCount=2)
      #set what this handler will catch
#       fh.setLevel(logging.INFO)
      
      #create a handler, printing info to console (stderr)
      ch = logging.StreamHandler(sys.stderr)
#       ch.setLevel(logging.INFO)
      #create a formatter, and add it to both the handlers
      formatter = logging.Formatter('%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s')
      fh.setFormatter(formatter)
      ch.setFormatter(formatter)
      #add the handlers to the logger
      self.mLogger.addHandler(ch)
      self.mLogger.addHandler(fh)


      self.mLogger.debug("logger set up. starting the application...")
      self.mLogger.debug("initializing the application")
      
      
      
      
if __name__ == "__main__":
   #test to make sure the logger is working properly
   
   
   import re
   
   errors = 0
   
   print("Testing the logging class")
   print("deleting old log files")
   with open("logs/gui.log", 'w'):
      pass
   with open("logs/server.log",'w'):
      pass
   print("done")
   print()
   print("generating loggers and putting in entries")
   try:
      l=logger()
      l.initGuiLogger()
      l.guiLogger.debug("gui: hello world")
      l.initServerLogger()
      l.sLogger.debug("server: hello world")
   except Exception as e:
      print("problem generating logger: ", e)
      errors += 1
      
   
   print("checking to make sure the logs are successfully working")
   f = open("logs/gui.log", 'r')
   file = f.read()
   f.close()
   
   match = re.search("gui: hello world", file)
   
   if not match:
      errors += 1
      print("ERROR: there was a problem with the GUI logger!!!")
   else:
      print("GUI logger working")
      
   f = open("logs/server.log", 'r')
   file = f.read()
   f.close()
   
   match = re.search("server: hello world", file)
   
   if not match:
      errors += 1
      print("ERROR: there was a problem with the server logger!!!")
   else:
      print("Server logger working")
      
      
   print("-"*20)
   print("Logger testing complete. There were {} errors.".format(errors))
   
   
   