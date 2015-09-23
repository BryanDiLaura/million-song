#!/usr/bin/env python3

"""
   Bryan DiLaura
   July 2015
   
   Launches the cherrypy server in a separate process, before launching the GUI. 
   This is intended to be the primary executable for the application.
"""

from multiprocessing import Process

import bin.mill_song_gui as mill_song_gui
import bin.cherrypy_server as cherrypy_server

p1 = Process(target=cherrypy_server.startGame)
p1.start()

i = mill_song_gui.App()
i.exec_()

p1.terminate()