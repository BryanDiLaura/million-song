#!/usr/bin/env python3


"""
   Bryan DiLaura
   July 2015
   
   This is a gui launcher for the million-song year guesser. It not only includes the 
   options to select what difficulty you want to use, it also includes a leaderboard,
   and a sampler which shows what the current difficulty will display in the game. 

"""


#qt stuff
from PyQt4 import QtCore
from PyQt4 import QtGui
import sys
import re
import os
#passwords
import bin.src.bcrypt as bcrypt
#database queries
import sqlite3
#launching the browser
import webbrowser
#emailing for password recovery
import smtplib
from email.mime.text import MIMEText
#generating random user strings
import string, random
#logger
from bin.project_logging import logger
import logging


#create the logger for all of the classes to use
l = logger()
l.initGuiLogger()


class App(QtGui.QApplication):
   def __init__(self, logging_level=logging.INFO):
      l.guiLogger.setLevel(logging_level)
      l.guiLogger.info("<START>")
      l.guiLogger.info("Starting application")
      l.guiLogger.debug("initializing the application")
      
      QtGui.QApplication.__init__(self, sys.argv)
      
      self.setApplicationName("Music Wizard")
      
      #init the main window and show it
      self.mainWindow = MW()
      self.mainWindow.show()
      
      l.guiLogger.debug("finished init of main window")
      
      #listener for the application closing via the close button in upper right corner
      self.lastWindowClosed.connect(self.mainWindow.centralWidget.quicksave)
      self.lastWindowClosed.connect(self.notifyEnd)
      
      #setting focus on the password field
      self.mainWindow.centralWidget.passText.setFocus()
      
      l.guiLogger.info("Application fully loaded")
      
   def notifyEnd(self):
      l.guiLogger.info("<END>")



class MW(QtGui.QMainWindow):
   def __init__(self):
      l.guiLogger.debug("MW:__init__<s>")
      
      QtGui.QMainWindow.__init__(self)
      
      #init the central widget and set it for the window
      self.centralWidget = CW(self)
      self.setCentralWidget(self.centralWidget)
      
      l.guiLogger.debug("finished init of central widget")
      
      #resize and set the title
      self.resize(300,100)
      self.setWindowTitle("Music Wizard")
      
      #set the window icon
      self.setWindowIcon(QtGui.QIcon("icons/MD-audio.png"))
      
      #add menubar
      self.mb = QtGui.QMenuBar()
      self.setMenuBar(self.mb)
      
      l.guiLogger.debug("adding all actions")
      
      #add menubar items
      #file
      self.file = QtGui.QMenu("File")
      self.mb.addMenu(self.file)
      self.fileExit = QtGui.QAction("Exit", self.file)
      self.fileExit.setShortcut(QtCore.Qt.Key_Escape)
      self.file.addAction(self.fileExit)
      self.fileExit.triggered.connect(self.exitApp)
      #profile
      self.profile = QtGui.QMenu("Profile")
      self.mb.addMenu(self.profile)
      self.profileNew = QtGui.QAction("New", self.profile)
      self.profileNew.setShortcut(QtCore.Qt.CTRL | QtCore.Qt.Key_N)
      self.profile.addAction(self.profileNew)
      self.profileNew.triggered.connect(self.newProfile)
      self.profileLoad = QtGui.QAction("Load", self.profile)
      self.profileLoad.setShortcut(QtCore.Qt.CTRL | QtCore.Qt.Key_L)
      self.profile.addAction(self.profileLoad)
      self.profileLoad.triggered.connect(self.loadProfile)
      self.profileRecoverPass = QtGui.QAction("Recover Password", self.profile)
      self.profile.addAction(self.profileRecoverPass)
      self.profileRecoverPass.triggered.connect(self.recoverPass)
      self.profileChangePass = QtGui.QAction("Change Password", self.profile)
      self.profile.addAction(self.profileChangePass)
      self.profileChangePass.triggered.connect(self.changePass)
      self.profileDelete = QtGui.QAction("Delete", self.profile)
      self.profile.addAction(self.profileDelete)
      self.profileDelete.triggered.connect(self.deleteProfile)
      #help
      self.help = QtGui.QMenu("Help")
      self.mb.addMenu(self.help)
      self.helpInfo = QtGui.QAction("Information", self.help)
      self.helpInfo.setShortcut(QtCore.Qt.CTRL | QtCore.Qt.Key_H)
      self.help.addAction(self.helpInfo)
      self.helpInfo.triggered.connect(self.showInfo)
      self.helpDebug = QtGui.QAction("Debug", self.help)
      self.helpDebug.setShortcut(QtCore.Qt.CTRL | QtCore.Qt.Key_D)
      self.help.addAction(self.helpDebug)
      self.helpDebug.triggered.connect(self.toggleDebug)
      self.debug = False
      self.helpCredits = QtGui.QAction("Credits", self.help)
      self.help.addAction(self.helpCredits)
      self.helpCredits.triggered.connect(self.showCredits)
      
      #action icons
      self.fileExit.setIcon(QtGui.QIcon("icons/power-standby.png"))
      self.profileNew.setIcon(QtGui.QIcon("icons/add.png"))
      self.profileLoad.setIcon(QtGui.QIcon("icons/download.png"))
      self.profileRecoverPass.setIcon(QtGui.QIcon("icons/help-alt.png"))
      self.profileChangePass.setIcon(QtGui.QIcon("icons/edit.png"))
      self.profileDelete.setIcon(QtGui.QIcon("icons/trash-empty.png"))
      self.helpInfo.setIcon(QtGui.QIcon("icons/info.png"))
      self.helpDebug.setIcon(QtGui.QIcon("icons/bug.png"))
      self.helpCredits.setIcon(QtGui.QIcon("icons/MD-microphone-alt.png"))
      
      l.guiLogger.debug("adding actions finished")
      
      l.guiLogger.debug("MW:__init__<e>")
      
      
   def exitApp(self):
      l.guiLogger.debug("MW:exitApp<s> - exit out of the program")
      if self.isVisible():
         ret = QtGui.QMessageBox.question(self, "Quit?", "Are you sure you want to exit?",
                                  buttons = (QtGui.QMessageBox.No | QtGui.QMessageBox.Yes),
                                  defaultButton = QtGui.QMessageBox.Yes)
      else: ret = QtGui.QMessageBox.Yes
      
      if ret == QtGui.QMessageBox.Yes:
         l.guiLogger.debug("closing out of the program")
         l.guiLogger.info("<END>")
         self.centralWidget.quicksave()
         sys.exit()
      l.guiLogger.debug("decided not to close the program")
        
      l.guiLogger.debug("MW:exitApp<e>") 
      
      
   def newProfile(self):
      l.guiLogger.debug("MW:newProfile<s> - create new profile")
      i = newUserDialog(self.centralWidget.cursor)
      i.exec_()
      
      l.guiLogger.debug("dialog closed")
      
      if (i.success):
         l.guiLogger.debug("committing user to database")
         #commit changes to database
         self.centralWidget.conn.commit()
         
         l.guiLogger.debug("populating with new user information")
         self.centralWidget.nameText.setText(i.userText.text())
         self.centralWidget.passText.setText(i.pass1Text.text())
         
         l.guiLogger.info("Successfully created new profile:"+ i.userText.text())
      else:
         l.guiLogger.info("Decided to not create a new profile")
      
      l.guiLogger.debug("MW:newProfile<e>")
         
      
   def loadProfile(self):
      l.guiLogger.debug("MW:loadProfile<s> - load a profile from database")
      i = LoadUserDialog(self.centralWidget.cursor)
      i.exec_()
      
      l.guiLogger.debug("dialog closed")
      
      if (i.user != None):
         l.guiLogger.debug("populating with loaded user info")
         self.centralWidget.nameText.setText(i.user)
         self.centralWidget.passText.setText("")
         l.guiLogger.info("Successfully loaded profile:"+ i.user)
      else:
         l.guiLogger.debug("no user was selected to load")
      
      l.guiLogger.debug("MW:loadProfile<e>")            
         
         
   def deleteProfile(self):
      l.guiLogger.debug("MW:deleteProfile<s> - delete a profile")
      i = DeleteUserDialog(self.centralWidget.cursor)
      i.exec_()
      
      l.guiLogger.debug("dialog closed")
      
      if (i.success):
         l.guiLogger.debug("user successfully deleted, committing to db")
         self.centralWidget.conn.commit()
         l.guiLogger.info("User: "+ i.userToDelete+ " was successfully deleted and committed")
         
         
         if (self.centralWidget.nameText.text() == i.userToDelete):
            l.guiLogger.debug("the deleted user was the currently selected user. populating with blanks")
            self.centralWidget.nameText.setText("")
            self.centralWidget.passText.setText("")
            
      else:
         l.guiLogger.debug("no user was deleted")
      
      l.guiLogger.debug("MW:deleteProfile<e>")
                                  
                
   def recoverPass(self):
      l.guiLogger.debug("MW:recoverPass<s> - recover a password via email")
      i = LoadUserDialog(self.centralWidget.cursor)
      i.setWindowTitle("Search for user to recover password for")
      i.exec_()
      
      l.guiLogger.debug("exited dialog")
      
      if (i.user != None):
         l.guiLogger.debug("user was selected to recover password for")
         
         self.centralWidget.cursor.execute("SELECT username, email FROM users WHERE username == '{}'".format(i.user))
         data = self.centralWidget.cursor.fetchone()
         
         l.guiLogger.debug("setting new password")
         self.centralWidget.cursor.execute("UPDATE users SET pass = '{}' WHERE username == '{}'".format(bcrypt.hashpw("changeth1sPW", bcrypt.gensalt()), i.user))
         
         l.guiLogger.debug("committing changes")
         self.centralWidget.conn.commit()
         
         l.guiLogger.info("Password successfully changed")
         
         
         l.guiLogger.debug("generating email")
         msg = MIMEText("MUSIC WIZARD PASSWORD RECOVERY PROGRAM \n\nusername: {}\n\ntemporary password: {}\n\nPlease "
                        "change your password as soon as possible using the change password tool, and the temporary password".format(data[0], "changeth1sPW"))
         me = "musicwizardprogram@gmail.com"
         you = data[1]
         
         msg['Subject'] = "password recovery for music wizard"
         msg['From'] = me
         msg['To'] = you
         
         l.guiLogger.debug("connecting to gmail server")
         s = smtplib.SMTP('smtp.gmail.com',587)
         s.ehlo()
         s.starttls()
         s.ehlo()
         s.login("musicwizardprogram@gmail.com", "thisisatest")
         s.sendmail(me, you, msg.as_string())
         s.close()
         
         l.guiLogger.info("Password recovery email successfully sent")
         if self.isVisible():
            QtGui.QMessageBox.information(self, "success!", "An email has been sent to the account associated with that username, resetting the password")
      
      else:
         l.guiLogger.debug("no user was selected to delete")
      
      l.guiLogger.debug("MW:__init__<e>")


   def changePass(self):
      l.guiLogger.debug("MW:changePass<s>")
      i = ChangePassword(self.centralWidget.cursor)
      i.exec_()
      
      l.guiLogger.debug("exited dialog")
      
      if i.success == True:
         l.guiLogger.debug("committing password change to db")
         self.centralWidget.conn.commit()
         l.guiLogger.info("Password successfully changed")
         if self.isVisible():
            QtGui.QMessageBox.information(self, "Success!", "Password successfully changed")
         
      l.guiLogger.debug("MW:changePass<e>")
           
                                     
   def showInfo(self):
      l.guiLogger.debug("MW:showInfo<s> - shows information about the application")
      
      i = infoDialog()
      i.setWindowTitle("Information")
      i.text.setText("MUSIC WIZARD\n\nThis program is a guessing game where the user is up against the computer. The task? Try\nto guess the year when a song came out, based on limited information about the song.\n\nTo begin, create a profile using profile > new. Once this is done, you are ready to\nselect the difficulty you want to play at, and then start the game!\n\nOnce the game is started, a page will launch in your web browser. This is where\nyou will interact with the game, and you can continue playing there as long as you like.\n\nWhen you have finished playing, feel free to close the browser window.\n\nFrom this program, you can also look at the leaderboards, and see how\nyou stack up against the competition. Please note that you must play\nat least 5 games in order to be on the leaderboards.")
      
      i.exec_()
      
      l.guiLogger.debug("MW:showInfo<e>")
      
      
   def showCredits(self):
      l.guiLogger.debug("MW:showCredits<s> - show the credits for the applicatoin")
      
      i = infoDialog()
      i.setWindowTitle("Credits")
      i.text.setText("Application by: Bryan DiLaura \nRelease date: July 2015 \n\nIcons by: interactivemania \n(http://www.interactivemania.com) \n\nMachine Learning by: Scikit-learn \nhttp://scikit-learn.org/stable/ \n\nDataset: Million Song Dataset \n(http://labrosa.ee.columbia.edu/millionsong/) \n\nMusic samples: Spotify API & EchoNest API \n\nUseful Modules: Paul Lamere - spotipy & pyen\n(http://MusicMachinery.com) \n\nWebserver backend: cherrypy\n(http://www.cherrypy.org/)")
      
      i.exec_()
      
      l.guiLogger.debug("MW:showCredits<e>")
      
      
   def toggleDebug(self):
      l.guiLogger.debug("MW:toggleDebug<s> - toggle verbose debugging statements")
      if self.debug:
         l.guiLogger.info("Turning off verbose debuggging")
         self.debug = False
         l.guiLogger.setLevel(logging.INFO)
         l.guiLogger.debug("THIS STATEMENT SHOULDN'T BE SEEN")
         l.guiLogger.info("This statement should appear")
         
      else:
         l.guiLogger.info("Turning on verbose debugging")
         self.debug = True
         l.guiLogger.setLevel(logging.DEBUG)
         l.guiLogger.debug("This statement should appear!")
      
      

class CW(QtGui.QWidget):
   """
   This is the central widget for the music year guessing game.
   It contains the ability to change game settings, start the 
   game, view a sample game turn, view the leaderboard, and 
   manipulate profile options. 
   
   The username field is read only, and must be changed via the 
   profile menu (MAY ADD A BUTTON TO LOAD PROFILES AS WELL).
   
   A password is required for every profile in order to start a
   game. If the correct password is not entered, the user will
   be alerted, and the game cannot be played.
   
   The finer details of the game settings can only be changed
   if using a custom difficulty setting. Games will only be 
   counted for the leaderboard if a standard difficulty setting
   is used. 
   
   The game settings are very much still in progress, and subject
   to change...
   """
   
   def __init__(self,parent):
      l.guiLogger.debug("CW:__init__<s>")
      QtGui.QWidget.__init__(self,parent)
      
      l.guiLogger.debug("connecting to database")
      #connect to user databaes
      self.conn = sqlite3.connect("data/gui/users.db")
      self.cursor = self.conn.cursor()
      self.cursor.execute("PRAGMA foreign_keys = ON;")
      
      
      #create the main layout
      self.mainLayout = QtGui.QVBoxLayout(self)
      
      #have a way to store the state when we close
      self.destroyed.connect(self.quicksave)
      
      l.guiLogger.debug("creating name and password stuff")
      #create the name data field and password
      self.nameAndPassLayout = QtGui.QHBoxLayout()
      self.labelLayout = QtGui.QVBoxLayout()
      self.fieldsLayout = QtGui.QVBoxLayout()
      self.nameAndPassLayout.addLayout(self.labelLayout)
      self.nameAndPassLayout.addLayout(self.fieldsLayout)
      self.nameLabel = QtGui.QLabel("Username:")
      self.nameText = QtGui.QLabel("Please create a new profile!")
      self.nameText.setAlignment(QtCore.Qt.AlignCenter)
      self.nameText.setMinimumHeight(30)
      self.passLabel = QtGui.QLabel("Password:")
      self.passText = QtGui.QLineEdit()
      self.passText.setEchoMode(QtGui.QLineEdit.Password)
      #add everything to layouts
      self.labelLayout.addWidget(self.nameLabel)
      self.labelLayout.addWidget(self.passLabel)
      self.fieldsLayout.addWidget(self.nameText)
      self.fieldsLayout.addWidget(self.passText)
      self.mainLayout.addLayout(self.nameAndPassLayout)
      
      #profile buttons
      self.profileButtonLayout = QtGui.QHBoxLayout()
      self.loadUserButton = QtGui.QPushButton("Load User")
      self.addUserButton = QtGui.QPushButton("New User")
      self.loadUserButton.pressed.connect(self.parent().loadProfile)
      self.addUserButton.pressed.connect(self.parent().newProfile)
      self.profileButtonLayout.addWidget(self.loadUserButton)
      self.profileButtonLayout.addWidget(self.addUserButton)
      self.mainLayout.addLayout(self.profileButtonLayout)
      
      l.guiLogger.debug("creating preferences")
      #create preferences
      self.prefFrame = QtGui.QFrame()
      self.prefFrame.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken) 
      self.prefVLayout = QtGui.QVBoxLayout(self.prefFrame)
      self.prefLabelLayout = QtGui.QHBoxLayout()
      self.prefVLayout.addLayout(self.prefLabelLayout)
      hbarframe = QtGui.QFrame()
      hbarframe.setFrameShape(QtGui.QFrame.HLine)
      self.prefVLayout.addWidget(hbarframe)
      self.prefLayout = QtGui.QHBoxLayout()
      self.prefVLayout.addLayout(self.prefLayout)
      #difficulty settings...
      self.diffLayout = QtGui.QVBoxLayout()
      self.diffLabel = QtGui.QLabel("Difficulty")
      self.diffRadioE = QtGui.QRadioButton("Easy")
      self.diffRadioM = QtGui.QRadioButton("Medium")
      self.diffRadioH = QtGui.QRadioButton("Hard")
      self.diffRadioC = QtGui.QRadioButton("Custom")
      self.diffRadioE.setCheckable(True)
      self.diffRadioM.setCheckable(True)
      self.diffRadioH.setCheckable(True)
      self.diffRadioC.setCheckable(True)
      self.diffRadioE.setChecked(True)
#       self.diffLayout.addWidget(self.diffLabel)
      self.prefLabelLayout.addWidget(self.diffLabel)
      self.diffLayout.addWidget(self.diffRadioE)
      self.diffLayout.addWidget(self.diffRadioM)
      self.diffLayout.addWidget(self.diffRadioH)
      self.diffLayout.addWidget(self.diffRadioC)
      self.prefLayout.addLayout(self.diffLayout)
      #display settings...
      self.dispLayout = QtGui.QVBoxLayout()
      self.dispLabel = QtGui.QLabel("Display")
      self.dispCheckTitle = ReadOnlyQCheckbox(self, "Title")
      self.dispCheckArtist = ReadOnlyQCheckbox(self, "Artist")
      self.dispCheckAlbum = ReadOnlyQCheckbox(self, "Album")
#       self.dispLayout.addWidget(self.dispLabel)
      self.prefLabelLayout.addWidget(self.dispLabel)
      self.dispLayout.addWidget(self.dispCheckTitle)
      self.dispLayout.addWidget(self.dispCheckArtist)
      self.dispLayout.addWidget(self.dispCheckAlbum)
      #more display settings go here!
      self.prefLayout.addLayout(self.dispLayout)
      #sample and feedback text
      self.samplefeedLayout = QtGui.QVBoxLayout()
      self.feedback = QtGui.QLabel("woo")
      self.feedback.setWordWrap(True)
      self.feedback.setMinimumWidth(140)
      self.feedback.setMaximumWidth(140)
#       self.samplefeedLayout.addWidget(self.feedback)
      self.sampleButton = QtGui.QPushButton("Sample")
      self.samplefeedLayout.addWidget(self.sampleButton)
      self.prefLayout.addLayout(self.samplefeedLayout)
      self.prefLabelLayout.addWidget(QtGui.QLabel())
      #year range slider
      self.yearLabel = QtGui.QLabel("Year Range: ____ - ____")
      self.yearLabel.setAlignment(QtCore.Qt.AlignCenter)
      self.prefVLayout.addWidget(self.yearLabel)
      self.range = RangeSlider(self, QtCore.Qt.Horizontal)
      self.range.setMinimum(1926)
      self.range.setMaximum(2010)
      self.range.setLow(1926)
      self.range.setHigh(2010)
      self.range.sliderMoved.connect(self.yearRangeChange)
      self.range.sliderMoved.emit(0)
      self.prefVLayout.addWidget(self.range)
      
      
      #all connections
      self.diffRadioE.toggled.connect(self.difficultyChange)
      self.diffRadioM.toggled.connect(self.difficultyChange)
      self.diffRadioH.toggled.connect(self.difficultyChange)
      self.diffRadioC.toggled.connect(self.difficultyChange)
      self.diffRadioE.toggled.emit(True) #manually trigger so i don't have to set up myself...
      self.sampleButton.pressed.connect(self.sample)
      
      #put the frame into the main layout
      self.mainLayout.addWidget(self.prefFrame)
      
      l.guiLogger.debug("adding buttons")
      #leaderboard and start game buttons
      self.buttonsLayout = QtGui.QHBoxLayout()
      self.leaderButton = QtGui.QPushButton("Leaderboards")
      self.startButton = QtGui.QPushButton("Start Game")
      self.buttonsLayout.addWidget(self.leaderButton)
      self.buttonsLayout.addWidget(self.startButton)
      self.mainLayout.addLayout(self.buttonsLayout)
      self.leaderButton.pressed.connect(self.leader)
      self.startButton.pressed.connect(self.start)
      
      l.guiLogger.debug("doing a quickload")
      #load in previous session's settings
      self.quickload()
      
      
      l.guiLogger.debug("CW:__init__<e>")
      
         
   def difficultyChange(self):
      l.guiLogger.debug("CW:difficultyChange<s> - change the difficulty")
      if self.diffRadioE.isChecked():
         l.guiLogger.info("Difficulty changed to easy")
         self.dispCheckTitle.setChecked(True)
         self.dispCheckArtist.setChecked(True)
         self.dispCheckAlbum.setChecked(True)
         self.dispCheckTitle.setDisabled(True)
         self.dispCheckAlbum.setDisabled(True)
         self.dispCheckArtist.setDisabled(True)
         self.feedback.setText("Oh look at the little baby!")
         self.range.setHigh(2010)
         self.range.setLow(1926)
         self.range.setDisabled(True)
      if self.diffRadioM.isChecked():
         l.guiLogger.info("Difficulty changed to medium")
         self.dispCheckTitle.setChecked(True)
         self.dispCheckArtist.setChecked(True)
         self.dispCheckAlbum.setChecked(False)
         self.dispCheckTitle.setDisabled(True)
         self.dispCheckAlbum.setDisabled(True)
         self.dispCheckArtist.setDisabled(True)
         self.feedback.setText("Let's play")
         self.range.setHigh(2010)
         self.range.setLow(1926)
         self.range.setDisabled(True)
      if self.diffRadioH.isChecked():
         l.guiLogger.info("Difficulty changed to hard")
         self.dispCheckTitle.setChecked(True)
         self.dispCheckArtist.setChecked(False)
         self.dispCheckAlbum.setChecked(False)
         self.dispCheckTitle.setDisabled(True)
         self.dispCheckAlbum.setDisabled(True)
         self.dispCheckArtist.setDisabled(True)
         self.feedback.setText("Here we go...")
         self.range.setHigh(2010)
         self.range.setLow(1926)
         self.range.setDisabled(True)
      if self.diffRadioC.isChecked():
         l.guiLogger.info("Difficulty changed to hard")
         #handled in ReadOnlyQcheckbox
         self.feedback.setText("NOTE: Custom games will not be scored, and will not have a leaderboard entry")
         self.range.setDisabled(False)
         self.dispCheckTitle.setDisabled(False)
         self.dispCheckAlbum.setDisabled(False)
         self.dispCheckArtist.setDisabled(False)
      
      l.guiLogger.debug("CW:difficultyChange<e>")

      
   def quicksave(self):
      l.guiLogger.debug("CW:quicksave<s> - save the most recent user's information to a file")
      l.guiLogger.info("Quicksaving")
      
      f = open("data/gui/quicksave.txt", 'w')
      f.write("LAST_USER={}\n".format(self.nameText.text()))
      
      f.write("SETTINGS: ")
      if self.diffRadioE.isChecked():
         f.write("DIFF=E,")
      if self.diffRadioM.isChecked():
         f.write("DIFF=M,")
      if self.diffRadioH.isChecked():
         f.write("DIFF=H,")
      if self.diffRadioC.isChecked():
         f.write("DIFF=C, ")
         f.write("TITLE={}, ".format(self.dispCheckTitle.isChecked()))
         f.write("ARTIST={}, ".format(self.dispCheckArtist.isChecked()))
         f.write("ALBUM={}, ".format(self.dispCheckAlbum.isChecked()))
         f.write("YEARS_HIGH={}, ".format(self.range.high()))
         f.write("YEARS_LOW={},".format(self.range.low()))
      
      f.close()
      
      l.guiLogger.debug("CW:quicksave<e>")
         
         
   def quickload(self):
      l.guiLogger.debug("CW:quickload<s> - load the most recent user's prefs from file")
      l.guiLogger.info("Quickloading")
      
      if not os.path.isfile("data/gui/quicksave.txt"):
         l.guiLogger.warning("no quicksave file found. This is should either be the first run, or the file was deleted somehow")
         l.guiLogger.debug("CW:quickload<e>")
         return
      
      f = open("data/gui/quicksave.txt", 'r')
      settings = f.read()
      
      
      try:
         #restore name
         name = re.search("LAST_USER=(\w{0,100})", settings)
         self.nameText.setText(name.group(1))
         
         #restore difficulty
         diff_m = re.search("SETTINGS: DIFF=(\w),", settings)
         diff = diff_m.group(1)
          
         if diff == "E":
            self.diffRadioE.setChecked(True)
         if diff == "M":
            self.diffRadioM.setChecked(True)
         if diff == "H":
            self.diffRadioH.setChecked(True)
         if diff == "C":
            self.diffRadioC.setChecked(True)
            
            #restore custom settings
            set_m = re.search("TITLE=(\w{4,5}), ARTIST=(\w{4,5}), ALBUM=(\w{4,5}), YEARS_HIGH=([0-9]{4}), YEARS_LOW=([0-9]{4}),", settings)
            
            self.dispCheckTitle.setChecked(set_m.group(1) == "True")
            self.dispCheckArtist.setChecked(set_m.group(2) == "True")
            self.dispCheckAlbum.setChecked(set_m.group(3) == "True")
            self.range.setHigh(int(set_m.group(4)))
            self.range.setLow(int(set_m.group(5)))
            self.range.sliderMoved.emit(0)
            
         l.guiLogger.info("Successfully quickloaded")
         
      except Exception as e:
         l.guiLogger.error("Quicksave file corrupted. exception: "+ e)
         l.guiLogger.error("settings = "+ settings)
         
      l.guiLogger.debug("CW:quickload<e>")
      
         
   def yearRangeChange(self):
      #for the sake of sanity, I'm not going to put a log statement here...
      high = self.range.high()
      low = self.range.low()
      self.yearLabel.setText("Year Range: {} - {}".format(low, high))
   
   
   def sample(self):
      l.guiLogger.debug("CW:sample<s> - generate a sample game board")
      l.guiLogger.info("Generating sample game")
      
      rick = 'https://p.scdn.co/mp3-preview/c6b919edf8c7d742474f8f48dffed06fcd49cf00'
      title = "Never+Gonna+Give+You+Up"
      artist = "Rick+Astley"
      album = "Big+Tunes+-+Back+2+The+80s"
      
      url = "http://localhost:8080/sample?"
      
      url += "gen=F"
      
      url += "&url=" + rick
      
      if self.dispCheckTitle.isChecked():
         url += "&title=" + title
      
      if self.dispCheckArtist.isChecked():
         url += "&artist=" + artist
      
      if self.dispCheckAlbum.isChecked():
         url += "&album=" + album
         
      if self.diffRadioC.isChecked():
         url += "&minYr=" + str(self.range.low())
         url += "&maxYr=" + str(self.range.high())
         
      l.guiLogger.debug("attempting to open webpage")
      try: webbrowser.open_new_tab(url)
      except Exception as e:
         l.guiLogger.debug("something went wrong: "+ e)
         l.guiLogger.debug("url = "+ url)
         
      l.guiLogger.debug("CW:sample<e>")
      
      
   def leader(self):
      l.guiLogger.debug("CW:leader<s> - display the leaderboards")
      
      lead = leaderboardDialog(self.cursor)
      
      lead.exec_()
      
      l.guiLogger.debug("CW:leader<e>")
      
      
   def start(self):
      l.guiLogger.debug("CW:start<s> - launches a webpage with the game url")
      result = self.checkPW()
      
      if result == True:   
         l.guiLogger.debug("password was correct")
         
         self.cursor.execute("SELECT id FROM users WHERE username =='{}'".format(self.nameText.text()))
         data = self.cursor.fetchone()
         user = data[0]
         
         if self.diffRadioE.isChecked():
            webbrowser.open_new_tab("http://localhost:8080/gameTurn?diff=E&user=" + user)
            l.guiLogger.info("Starting easy game with user id: "+ user)
         if self.diffRadioM.isChecked():
            webbrowser.open_new_tab("http://localhost:8080/gameTurn?diff=M&user=" + user)
            l.guiLogger.info("Starting medium game with user id: "+ user)
         if self.diffRadioH.isChecked():
            webbrowser.open_new_tab("http://localhost:8080/gameTurn?diff=H&user=" + user)
            l.guiLogger.info("Starting hard game with user id: "+ user)
         if self.diffRadioC.isChecked():
            url = "http://localhost:8080/gameTurn?diff=C&user=" + user
            disp = "&disp="
            if self.dispCheckTitle.isChecked():
               disp += "t"
            if self.dispCheckArtist.isChecked():
               disp += "A"
            if self.dispCheckAlbum.isChecked():
               disp += "a"
            url += disp
            
            url += "&minYr=" + str(self.range.low())
            url += "&maxYr=" + str(self.range.high())
            webbrowser.open_new_tab(url)
            l.guiLogger.info("Starting custom game with user id: "+ user)
            l.guiLogger.debug("url = "+ url)
               
      if result == False:
         l.guiLogger.warning("Incorrect password")
         l.guiLogger.debug("user = "+ self.nameText.text())
         if self.isVisible():
            QtGui.QMessageBox.warning(self, "Wrong Password", "That password was incorrect for that username.")
         
      l.guiLogger.debug("CW:start<e>")
      
        
   def checkPW(self):
      l.guiLogger.debug("CW:checkPW<s> - checks the password against the one in the db")
      
      #checks the inputted password against the one in the user database
      
      #get password from database
      self.cursor.execute("SELECT pass FROM users WHERE username == '{}'".format(self.nameText.text()))
      res = self.cursor.fetchone()
      
      #if the user doesn't already exist
      if res == None:
         l.guiLogger.warning("Attempted to check the password for a user that doesn't exist")
         if self.isVisible():
            QtGui.QMessageBox.warning(self, "Problem checking password", "The username you are attempting to check the password for doesn't exist in the database! Please create a username by using the profile menu")
         
      #check the password 
      if (bcrypt.hashpw(self.passText.text(), res[0]) == res[0]):
         l.guiLogger.info("Correct password")
         l.guiLogger.debug("CW:checkPW<e>")
         return True
      else:
         l.guiLogger.info("Incorrect password")
         l.guiLogger.debug("CW:checkPW<e>")
         return False
      
      
   
class leaderboardDialog(QtGui.QDialog):
   """
   This is the leaderboard dialog, which contains the leaderboards for
   the three standardized difficulties. 
   
   This will probably have to load the leaderboard from a database at
   some point, once I get scoring implemented...
   ...so for now it just has placeholders.
   """
   
   def __init__(self, cursor):
      l.guiLogger.debug("leaderboardDialog:__init__<s> - show the leaderboards")
      
      QtGui.QDialog.__init__(self)
      
      self.setWindowTitle("Leaderboard")
      self.resize(20,40)
      
      self.mainLayout = QtGui.QVBoxLayout(self)
      
      self.tabWindow = QtGui.QTabWidget()
      
      size = 75
      
      #get scores from easy database
      l.guiLogger.debug("getting scores from easy db")
      cursor.execute("SELECT username, avg FROM easy WHERE games >= 5 ORDER BY avg DESC LIMIT 30;")
      data = cursor.fetchone() 
      easyframe = QtGui.QFrame()
      easylayout = QtGui.QVBoxLayout(easyframe)
      i = 1
      while data != None:
         easyitemlayout = QtGui.QHBoxLayout()
         frame1 = QtGui.QFrame()
         frame1.setFrameShape(QtGui.QFrame.VLine)
         easyitemlayout.addWidget(frame1)
         easyitemname = QtGui.QLabel(str(i)+". "+str(data[0]))
         easyitemname.setMaximumWidth(size*2)
         easyitemname.setMinimumWidth(size*2)
         easyitemlayout.addWidget(easyitemname)
         frame2 = QtGui.QFrame()
         frame2.setFrameShape(QtGui.QFrame.VLine)
         easyitemlayout.addWidget(frame2)
         easyitemscore = QtGui.QLabel(str(data[1]))
         easyitemscore.setMaximumWidth(size)
         easyitemscore.setMinimumWidth(size)
         easyitemlayout.addWidget(easyitemscore)
         frame3 = QtGui.QFrame()
         frame3.setFrameShape(QtGui.QFrame.VLine)
         easyitemlayout.addWidget(frame3)
         easylayout.addLayout(easyitemlayout)
         data = cursor.fetchone()
         i += 1
      
      if i == 1:
         self.tabWindow.addTab(QtGui.QLabel("Those babies! None of them even tried!"), "Easy")
      else:
         self.tabWindow.addTab(easyframe, "Easy")
      
      #get scores from medium database
      l.guiLogger.debug("getting scores from medium db")
      cursor.execute("SELECT username, avg FROM medium WHERE games >= 5 ORDER BY avg DESC LIMIT 30;")
      data = cursor.fetchone() 
      medframe = QtGui.QFrame()
      medlayout = QtGui.QVBoxLayout(medframe)
      i = 1
      while data != None:
         meditemlayout = QtGui.QHBoxLayout()
         frame1 = QtGui.QFrame()
         frame1.setFrameShape(QtGui.QFrame.VLine)
         meditemlayout.addWidget(frame1)
         meditemname = QtGui.QLabel(str(i)+". "+str(data[0]))
         meditemname.setMaximumWidth(size*2)
         meditemname.setMinimumWidth(size*2)
         meditemlayout.addWidget(meditemname)
         frame2 = QtGui.QFrame()
         frame2.setFrameShape(QtGui.QFrame.VLine)
         meditemlayout.addWidget(frame2)
         meditemscore = QtGui.QLabel(str(data[1]))
         meditemscore.setMaximumWidth(size)
         meditemscore.setMinimumWidth(size)
         meditemlayout.addWidget(meditemscore)
         frame3 = QtGui.QFrame()
         frame3.setFrameShape(QtGui.QFrame.VLine)
         meditemlayout.addWidget(frame3)
         medlayout.addLayout(meditemlayout)
         data = cursor.fetchone()
         i += 1
      
      if i == 1:
         self.tabWindow.addTab(QtGui.QLabel("There is nobody here!"), "Medium")
      else:
         self.tabWindow.addTab(medframe, "Medium")
      
      #get scores from hard database
      l.guiLogger.debug("getting scores from hard db")
      cursor.execute("SELECT username, avg FROM hard WHERE games >= 5 ORDER BY avg DESC LIMIT 30;")
      data = cursor.fetchone() 
      hardframe = QtGui.QFrame()
      hardlayout = QtGui.QVBoxLayout(hardframe)
      i = 1
      while data != None:
         harditemlayout = QtGui.QHBoxLayout()
         frame1 = QtGui.QFrame()
         frame1.setFrameShape(QtGui.QFrame.VLine)
         harditemlayout.addWidget(frame1)
         harditemname = QtGui.QLabel(str(i)+". "+str(data[0]))
         harditemname.setMaximumWidth(size*2)
         harditemname.setMinimumWidth(size*2)
         harditemlayout.addWidget(harditemname)
         frame2 = QtGui.QFrame()
         frame2.setFrameShape(QtGui.QFrame.VLine)
         harditemlayout.addWidget(frame2)
         harditemscore = QtGui.QLabel(str(data[1]))
         harditemscore.setMaximumWidth(size)
         harditemscore.setMinimumWidth(size)
         harditemlayout.addWidget(harditemscore)
         frame3 = QtGui.QFrame()
         frame3.setFrameShape(QtGui.QFrame.VLine)
         harditemlayout.addWidget(frame3)
         hardlayout.addLayout(harditemlayout)
         data = cursor.fetchone()
         i += 1
         
      if i == 1:
         self.tabWindow.addTab(QtGui.QLabel("This place is deserted..."), "Hard")
      else:
         self.tabWindow.addTab(hardframe, "Hard")
      
       
      self.mainLayout.addWidget(self.tabWindow)
      
      l.guiLogger.debug("leaderboardDialog:__init__<e>")



class infoDialog(QtGui.QDialog):
   """
   This is a basic information dialog used for both credits and information.
   After initializing this class self.text must be set to whatever should 
   populate the dialog. This can be done by using 
   self.text.setText("<random text>"). 
   """
   
   
   def __init__(self):
      l.guiLogger.debug("infoDialog:__init__<s> - show a dialog with just text on it")
      QtGui.QDialog.__init__(self)
      
      self.mainLayout = QtGui.QVBoxLayout(self)
      
      self.text = QtGui.QLabel("you gotta change this from the function!")
      
      self.mainLayout.addWidget(self.text)
      l.guiLogger.debug("infoDialog:__init__<e>")

      

class newUserDialog(QtGui.QDialog):
   """
   This dialog is used to add a new user to the database. The
   user puts in the information, and the class will dynamically
   check the input to make sure that it is well-formed. Assuming
   everything is well formed, the user will be added to the
   database. The username and password can be accessed through
   self.userText.text() and self.pass1Text.text() for population
   of the central widget.
   
   NOTE: the database changes will not be permanent unless a 
         connection.commit() is called after this dialog is 
         closed!!!
   """
   
   def __init__(self, db_cursor):
      l.guiLogger.debug("newUserDialog:__init__<s> - add a new user to the db")
      QtGui.QDialog.__init__(self)
      
      self.cursor = db_cursor
      
      self.setWindowTitle("Add New User")
      
      self.mainLayout = QtGui.QVBoxLayout(self)
      
      #flag for if the user was successfully created
      self.success = False
      
      #instructions
      self.instructions = QtGui.QLabel("Please enter all of the following information carefully:")
      self.instructions.setWordWrap(True)
      self.mainLayout.addWidget(self.instructions)
      
      #frame stuff
      self.infoFrame = QtGui.QFrame()
      self.infoFrame.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
      self.infoLayout = QtGui.QVBoxLayout(self.infoFrame)
      
      #create objects
      self.emailLabel = QtGui.QLabel("Email (used for password recovery)")
      self.emailText = QtGui.QLineEdit()
      self.userLabel = QtGui.QLabel("Username")
      self.userText = QtGui.QLineEdit()
      self.passLabel = QtGui.QLabel("Password")
      self.pass1Text = QtGui.QLineEdit()
      self.passConfLabel = QtGui.QLabel("Confirm Password")
      self.errorLabel = QtGui.QLabel("")
      self.errorLabel.setStyleSheet("QLabel {color : red; }")
      self.pass2Text = QtGui.QLineEdit()
      
      #add to frame/layout
      self.infoLayout.addWidget(self.emailLabel)
      self.infoLayout.addWidget(self.emailText)
      self.infoLayout.addWidget(self.userLabel)
      self.infoLayout.addWidget(self.userText)
      self.infoLayout.addWidget(self.passLabel)
      self.infoLayout.addWidget(self.pass1Text)
      self.infoLayout.addWidget(self.passConfLabel)
      self.infoLayout.addWidget(self.pass2Text)
      self.infoLayout.addWidget(self.errorLabel)
      #add to main
      self.mainLayout.addWidget(self.infoFrame)
      
      #make them password fields
      self.pass1Text.setEchoMode(QtGui.QLineEdit.Password)
      self.pass2Text.setEchoMode(QtGui.QLineEdit.Password)
      
      #add buttons
      self.buttonLayout = QtGui.QHBoxLayout()
      self.create = QtGui.QPushButton("Create")
      self.cancel = QtGui.QPushButton("Cancel")
      self.buttonLayout.addWidget(self.cancel)
      self.buttonLayout.addWidget(self.create)
      self.mainLayout.addLayout(self.buttonLayout)
      
      self.create.setEnabled(False)
      
      #change some tab ordering
      self.setTabOrder(self.pass2Text, self.create)
      self.setTabOrder(self.create, self.cancel)
      
      #set primary focus to the email field
      self.emailText.setFocus()
      
      #add listeners
      self.create.pressed.connect(self.addUser)
      self.cancel.pressed.connect(self.cancelPress)
      self.emailText.editingFinished.connect(self.checkInput)
      self.userText.editingFinished.connect(self.checkInput)
      self.pass1Text.textChanged.connect(self.checkInput)
      self.pass2Text.textChanged.connect(self.checkInput)
      
      l.guiLogger.debug("newUserDialog:__init__<e>")
      

   def addUser(self):
      l.guiLogger.debug("newUserDialog:addUser<s> - actually add the user")
      
      try:
         self.cursor.execute("INSERT INTO users VALUES ('{}', '{}', '{}', '{}');".
                             format(self.userText.text(),
                                    bcrypt.hashpw(self.pass1Text.text(), bcrypt.gensalt()),
                                    self.emailText.text(),
                                    self.randomword(15)))
      except Exception as e:
         l.guiLogger.error("There was a problem adding the user: "+ str(e))
         if self.isVisible():
            QtGui.QMessageBox.critical(self, "Database Entry Error",
                                     "Something went wrong creating the new user. Error: {}".format(str(e)))
         l.guiLogger.debug("newUserDialog:addUser<e>")
         return
         
      l.guiLogger.info("User: "+ self.userText.text()+ " was successfully added to db")
      self.success = True
      self.close()

      l.guiLogger.debug("newUserDialog:addUser<e>")
   
   
   def cancelPress(self):
      l.guiLogger.debug("newUserDialog:cancelPress<s> - cancel and close the dialog")
      l.guiLogger.info("Canceling making a new user")
      l.guiLogger.debug("newUserDialog:cancelPress<e>")
      self.close()

   
   def checkInput(self):
      l.guiLogger.debug("newUserDialog:checkInput<s> - check for valid input")
      
      if not (self.emailText.text() == ""):
         #check if a valid email was entered
         match = re.search("\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,4}\\b", self.emailText.text())
         if ( not match):
            self.errorLabel.setText("Enter a valid email address")
            self.create.setEnabled(False)
            l.guiLogger.debug("email invalid")
            l.guiLogger.debug("newUserDialog:checkInput<e>")
            return
         else: self.errorLabel.setText("")
         
         if not (self.userText.text() == ""):
            #check if username already exists
            self.cursor.execute("SELECT email FROM users WHERE username == '{}';".format(self.userText.text()))
            ret = self.cursor.fetchone()
            if ret != None:
               self.errorLabel.setText("That username already exists")
               self.create.setEnabled(False)
               l.guiLogger.debug("user already exists")
               l.guiLogger.debug("newUserDialog:checkInput<e>")
               return
            else: self.errorLabel.setText("")

            if not (self.pass1Text.text() == "" or self.pass2Text.text() == ""): 
               #check password
               if (self.pass1Text.text() != self.pass2Text.text()):
                  self.errorLabel.setText("Passwords Don't Match!")
                  self.create.setEnabled(False)
                  l.guiLogger.debug("passwords don't match")
                  l.guiLogger.debug("newUserDialog:checkInput<e>")
                  return
            
               else:
                  #all things pass, enable button and turn off error label
                  self.errorLabel.setText("")
                  #enable the create button
                  self.create.setEnabled(True)
                  l.guiLogger.debug("all fields valid")
         
      l.guiLogger.debug("newUserDialog:checkInput<e>")
      
      
   def randomword(self, length=15):
      l.guiLogger.debug("newUserDialog:randomword<s> - generate random string of ascii chars")
      try: a = ''.join(random.choice(string.ascii_letters) for i in range(length))
      except Exception as e:
         a = "error"
         l.guiLogger.error("There was a problem: "+ str(e))
         l.guiLogger.debug("length")
      
      l.guiLogger.debug("newUserDialog:randomword<e>")
      return a

            
      
class LoadUserDialog(QtGui.QDialog):
   """
   This class is used for loading a user from the database into
   the central widget. The user can search by either username
   or email address. Once a username has been found, the dialog
   closes itself, and puts the username to be populated into 
   the self.user variable.
   """
   
   def __init__(self, db_cursor):
      l.guiLogger.debug("LoadUserDialog:__init__<s> - load a user from db")
      QtGui.QDialog.__init__(self)
      
      self.setWindowTitle("Load User")
      
      #something to store the username, used to populate the main widget
      self.user = None
      
      #get the database cursor
      self.cursor = db_cursor
      
      self.mainLayout = QtGui.QVBoxLayout(self)
      
      self.infoFrame = QtGui.QFrame()
      self.infoFrame.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
      self.infoLayout = QtGui.QVBoxLayout(self.infoFrame)
      
      #username and email search fields
      self.userLabel = QtGui.QLabel("Username")
      self.userText = QtGui.QLineEdit()
      self.emailLabel = QtGui.QLabel("Email")
      self.emailText = QtGui.QLineEdit()
      self.infoLayout.addWidget(self.userLabel)
      self.infoLayout.addWidget(self.userText)
      self.infoLayout.addWidget(self.emailLabel)
      self.infoLayout.addWidget(self.emailText)
      self.mainLayout.addWidget(self.infoFrame)
      #return connections
      self.userText.returnPressed.connect(self.searchForUser)
      self.emailText.returnPressed.connect(self.searchForUser)
      
      #buttons
      self.buttonLayout = QtGui.QHBoxLayout()
      self.cancel = QtGui.QPushButton("Cancel")
      self.search = QtGui.QPushButton("Search")
      self.buttonLayout.addWidget(self.cancel)
      self.buttonLayout.addWidget(self.search)
      self.mainLayout.addLayout(self.buttonLayout)
      
      #button connections
      self.cancel.pressed.connect(self.exitDialog)
      self.search.pressed.connect(self.searchForUser)
      
      #some tab/focus stuff
      self.setTabOrder(self.emailText, self.search)
      self.setTabOrder(self.search, self.cancel)
      self.userText.setFocus()
      
      l.guiLogger.debug("LoadUserDialog:__init__<e>")
      
      
   def exitDialog(self):
      #cancel
      l.guiLogger.info("Canceling loading user")
      l.guiLogger.debug("user="+ self.user)
      self.close()
      
      
   def searchForUser(self):
      #search by username first, if applicable
      l.guiLogger.debug("LoadUserDialog:searchForUser<s> - search the database for user via email or username")
      if self.userText.text() != "":
         self.cursor.execute("SELECT username FROM users WHERE username == '{}';".format(self.userText.text()))
         ret = self.cursor.fetchone()
         
         #there was a username found, so use it
         if ret != None:
            self.user = ret[0]
            l.guiLogger.info("Found user: "+ self.user+ " via username. Closing the dialog.")
            self.close()
         
         #nothing found by that search query
         else:
            l.guiLogger.warning("Couldn't find that username")
            if self.isVisible():
               QtGui.QMessageBox.warning(self, "User Not Found", "Could not find that username. Please try again, or searching by email only.")
            self.userText.setText("")
            self.emailText.setText("")
            return
         
      #if no username is provided, search by email
      if self.emailText.text() != "":
         self.cursor.execute("SELECT username FROM users WHERE email == '{}';".format(self.emailText.text()))
         ret = self.cursor.fetchall()
         
         #found something
         if len(ret) != 0:
            #if there are multiple users under that email run the dialog
            if len(ret) > 1:
               l.guiLogger.debug("found at least 1 user via the email: "+ self.emailText.text())
               self.i = UserNameSelect(ret)
               if self.isVisible():
                  self.i.exec_()
               
               #set the user and close
               if self.i.selectedUser != None:
                  self.user = self.i.selectedUser
                  l.guiLogger.info("Found user: "+ self.user+ " via email. Closing the dialog.")
                  self.close()
            
            #only one username was returned, so use that one
            else:
               self.user = ret[0][0]
               l.guiLogger.info("Found user: "+ self.user+ " via email. Closing the dialog.")
               self.close()
         
         #couldn't find anything associated with the email entered
         else:
            l.guiLogger.warning("Couldn't find any users for the email: "+ self.emailText.text())
            if self.isVisible():
               QtGui.QMessageBox.warning(self, "User Not Found", "Could not find any usernames associated with that email. Please try again.")
            self.userText.setText("")
            self.emailText.setText("")
            return
         
      l.guiLogger.debug("LoadUserDialog:searchForUser<e>")



class UserNameSelect(QtGui.QDialog):
   """
   This is a helper dialog for the loadUserDialog class. It displays 
   username options in a passed list from a database query, and when 
   one is selected, (and the button pressed) the dialog closes, and
   the selection is put into the self.selectedUser variable.
   
   """
   
   
   def __init__(self, userlist):
      l.guiLogger.debug("UserNameSelect:__init__<s> - helper dialog if there is more than 1 user returned from a search")
      QtGui.QDialog.__init__(self)
      
      self.selectedUser = None
      
      self.mainLayout = QtGui.QVBoxLayout(self)
      
      self.users = userlist
      
      self.instructions = QtGui.QLabel("Please select the correct user")   
      self.selection = QtGui.QListWidget()
      self.go = QtGui.QPushButton("Select")
      
      self.mainLayout.addWidget(self.instructions)
      self.mainLayout.addWidget(self.selection)
      self.mainLayout.addWidget(self.go)
      self.mainLayout.setAlignment(self.go, QtCore.Qt.AlignRight)
      
      #add usernames to listwidget
      for u in self.users:
         self.selection.addItem(QtGui.QListWidgetItem(u[0]))
      
      self.go.pressed.connect(self.makeSelection)
      l.guiLogger.debug("UserNameSelect:__init__<e>")
      
      
   def makeSelection(self):
      self.selectedUser = self.selection.currentItem().text()
      l.guiLogger.info("Selected user: "+ self.selectedUser+". Closing dialog.")
      self.close()
      
      
      
class DeleteUserDialog(QtGui.QDialog):
   """
   This dialog is intended for deleting users from the database.
   It utilizes the LoadUserDialog in order to find the user to 
   delete, and then, assuming the password entered matches, 
   deletes the user. 
   
   NOTE: the database changes will not be permanent unless a 
         connection.commit() is called after this dialog is 
         closed!!!
   """
   
   def __init__(self, db_cursor):
      l.guiLogger.debug("DeleteUserDialog:__init__<s> - select and delete a user")
      QtGui.QDialog.__init__(self)
      
      self.setWindowTitle("Delete User")
      
      #something to store the username, used to populate the main widget
      self.userToDelete = None
      
      #flag to not if we have successfully deleted a profile
      self.success = False
      
      #get the database cursor
      self.cursor = db_cursor
      
      self.mainLayout = QtGui.QVBoxLayout(self)
      
      #instructions
      self.instr = QtGui.QLabel("Search for a username and enter the correct password to delete a user.")
      self.instr.setWordWrap(True)
      self.mainLayout.addWidget(self.instr)
      
      #username and password fields
      self.infoFrame = QtGui.QFrame()
      self.infoFrame.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
      self.infoLayout = QtGui.QVBoxLayout(self.infoFrame)
      #objects
      self.userLabel = QtGui.QLabel("Username:")
      self.userText = QtGui.QLabel("(please search for user)")
      self.search = QtGui.QPushButton("Search")
      self.passLabel = QtGui.QLabel("Password")
      self.passText = QtGui.QLineEdit()
      self.passText.setEchoMode(QtGui.QLineEdit.Password)
      self.delete = QtGui.QPushButton("Delete")
      self.delete.setEnabled(False)
#       self.cancel = QtGui.QPushButton("Cancel")
      #add to layout
      self.infoLayout.addWidget(self.userLabel)
      self.infoLayout.addWidget(self.userText)
      self.infoLayout.addWidget(self.passLabel)
      self.infoLayout.addWidget(self.passText)
      self.infoLayout.addWidget(self.search)
      #buttons layout
      self.buttonLayout = QtGui.QHBoxLayout()
#       self.buttonLayout.addWidget(self.cancel)
      self.buttonLayout.addWidget(self.delete)
      
      #add everything to main
      self.mainLayout.addWidget(self.infoFrame)
      self.mainLayout.addLayout(self.buttonLayout)
      
      #button connections
      self.search.pressed.connect(self.searchForUser)
      self.delete.pressed.connect(self.deleteUser)

      #set starting focus on the search button
      self.search.setFocus()
      
      l.guiLogger.debug("DeleteUserDialog:__init__<e>")
      
      
   def searchForUser(self):
      #create an instance of the load user dialog, repurposed for finding a user to delete
      l.guiLogger.debug("DeleteUserDialog:searchForUser<s> - open up load user dialog to search for user to delete")
      i = LoadUserDialog(self.cursor)
      i.setWindowTitle("Find A User To Delete")
      if self.isVisible():
         i.exec_()
      
      if i.user != None:
         self.userToDelete = i.user
         self.userText.setText(self.userToDelete)
         self.delete.setEnabled(True)
         self.passText.setFocus()
         l.guiLogger.info("Selected user: "+ i.user)
      else:
         l.guiLogger.info("Canceled searching for user")
         if self.userToDelete == None:
            self.delete.setEnabled(False)
         self.search.setFocus()
         
      l.guiLogger.debug("DeleteUserDialog:searchForUser<e>")
   
   
   def deleteUser(self):
      l.guiLogger.debug("DeleteUserDialog:deleteUser<s> - delete all the data associated with a user")
      
      #are we allowed to delete
      if (self.delete.isEnabled()):
         #check the password
         if (self.checkPass()):
            #make sure we are ok to delete
            if self.isVisible():
               ret = QtGui.QMessageBox.question(self, "Delete User?",
                                      "Are you sure you want to delete all data associated with user: ".format(self.userToDelete), 
                                      buttons=(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No), 
                                      defaultButton=QtGui.QMessageBox.Yes)
            else: ret = QtGui.QMessageBox.Yes
            if ret == QtGui.QMessageBox.Yes:
               l.guiLogger.debug("attempting to delete all data for user")
               #delete, set success and close
               try:
                  try: self.cursor.execute("DELETE FROM easy WHERE username == '{}'".format(self.userToDelete))
                  except: l.guiLogger.debug("no easy score to delete")
                  try: self.cursor.execute("DELETE FROM medium WHERE username == '{}'".format(self.userToDelete))
                  except: l.guiLogger.debug("no medium score to delete")
                  try: self.cursor.execute("DELETE FROM hard WHERE username == '{}'".format(self.userToDelete))
                  except: l.guiLogger.debug("no hard score to delete")
                  self.cursor.execute("DELETE FROM users WHERE username == '{}'".format(self.userToDelete))
                  self.success = True
                  l.guiLogger.info("User: "+ self.userToDelete+ " successfully deleted. Closing dialog")
                  self.close()
               except Exception as e:
                  l.guiLogger.info("There was some sort of error deleting user: "+ self.userToDelete)
                  l.guiLogger.error("error: "+ str(e))
                  if self.isVisible():
                     QtGui.QMessageBox.critical(self, "Database Error", 
                                             "Something went wrong when deleting the user. Error: {}".format(str(e)))   
                  self.close()
         
         #the password was incorrect
         else:
            l.guiLogger.debug("password incorrect, cannot delete user")
            if self.isVisible():
               QtGui.QMessageBox.warning(self, "Incorrect Password",
                                      "The password provided is incorrect. You must know the password in order to delete a user.")
            self.passText.setFocus()
         
      else:
         l.guiLogger.debug("delete button not enabled")
         
      l.guiLogger.debug("DeleteUserDialog:deleteUser<e>")
      
               
   def checkPass(self):
      #checks the inputted password against the one in the user database
      #reimplemented version of what is in the central widget. It should 
      #not need to find the username, as it has to be loaded properly from the 
      #load user dialog
      l.guiLogger.debug("DeleteUserDialog:checkPass<s> - check the password in order to delete the user")
      
      if self.userToDelete == None:
         l.guiLogger.debug("there is no user to check the password for")
         l.guiLogger.debug("DeleteUserDialog:checkPass<e>")
         return
      
      #get password from database
      self.cursor.execute("SELECT pass FROM users WHERE username == '{}'".format(self.userText.text()))
      res = self.cursor.fetchone()
         
      #check the password 
      if (bcrypt.hashpw(self.passText.text(), res[0]) == res[0]):
         l.guiLogger.info("Correct password")
         l.guiLogger.debug("DeleteUserDialog:checkPass<e>")
         return True
      else:
         l.guiLogger.info("Incorrect password")
         l.guiLogger.debug("DeleteUserDialog:checkPass<e>")
         return False
      


class ChangePassword(QtGui.QDialog):
   """
   This dialog is intended to allow users to change their passwords. 
   It must be passed a database cursor in order to make changes.
   
   self.success contains a boolean which can be checked to determine if 
   the password change was successful.
   
   NOTE: The database must be committed after the dialog closes.
   
   """
   
   def __init__(self, cursor):
      l.guiLogger.debug("ChangePassword:__init__<s> - dialog to change the password of a user")
      QtGui.QDialog.__init__(self)
      
      #flag for successfully change
      self.success = False
      
      #db cursor
      self.cursor = cursor
      
      self.setWindowTitle("Change Password")
      
      self.mainLayout = QtGui.QVBoxLayout(self)
      
      #username stuff
      self.userFrame = QtGui.QFrame()
      self.userFrame.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
      self.userFrameLayout = QtGui.QVBoxLayout(self.userFrame)
      self.userLabel = QtGui.QLabel("Username:")
      self.userText = QtGui.QLabel("Please search for user")
      self.userText.setAlignment(QtCore.Qt.AlignCenter)
      self.searchButton = QtGui.QPushButton("Search")
      self.searchButton.pressed.connect(self.userSearch)
      self.userFrameLayout.addWidget(self.userLabel)
      self.userFrameLayout.addWidget(self.userText)
      self.userFrameLayout.addWidget(self.searchButton)
      self.mainLayout.addWidget(self.userFrame)
      
      #password stuff
      self.passFrame = QtGui.QFrame()
      self.passFrame.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
      self.passFrameLayout = QtGui.QVBoxLayout(self.passFrame)
      self.oldPassLabel = QtGui.QLabel("Old Password:")
      self.oldPassText = QtGui.QLineEdit()
      self.oldPassText.setEchoMode(QtGui.QLineEdit.Password)
      self.oldPassText.setEnabled(False)
      self.newPass1Label = QtGui.QLabel("New Password:")
      self.newPass1Text = QtGui.QLineEdit()
      self.newPass1Text.setEchoMode(QtGui.QLineEdit.Password)
      self.newPass1Text.setEnabled(False)
      self.newPass2Label = QtGui.QLabel("Confirm:")
      self.newPass2Text = QtGui.QLineEdit()
      self.newPass2Text.setEchoMode(QtGui.QLineEdit.Password)
      self.newPass2Text.setEnabled(False)
      self.passFrameLayout.addWidget(self.oldPassLabel)
      self.passFrameLayout.addWidget(self.oldPassText)
      self.passFrameLayout.addWidget(self.newPass1Label)
      self.passFrameLayout.addWidget(self.newPass1Text)
      self.passFrameLayout.addWidget(self.newPass2Label)
      self.passFrameLayout.addWidget(self.newPass2Text)
      self.mainLayout.addWidget(self.passFrame)
      
      #commit button
      self.commitChangeButton = QtGui.QPushButton("Change Password")
      self.commitChangeButton.pressed.connect(self.commitPasswordChange)
      self.commitChangeButton.setEnabled(False)
      self.mainLayout.addWidget(self.commitChangeButton)
      
      #connections
      self.oldPassText.editingFinished.connect(self.enableCommit)
      self.newPass1Text.textChanged.connect(self.enableCommit)
      self.newPass2Text.textChanged.connect(self.enableCommit)
      self.oldPassText.editingFinished.connect(self.checkPW)
      self.newPass2Text.textChanged.connect(self.check)
      
      #debug label
      self.debugLabel = QtGui.QLabel()
      self.debugLabel.setStyleSheet("QLabel {color : red; }")
      self.debugLabel.setWordWrap(True)
      self.mainLayout.addWidget(self.debugLabel)
      
      l.guiLogger.debug("ChangePassword:__init__<e>")
      
       
   def userSearch(self):
      l.guiLogger.debug("ChangePassword:userSearch<s> - use the LoadUserDialog to find a user to change the password of")
      #search for user and enable password fields
      i = LoadUserDialog(self.cursor)
      i.setWindowTitle("Search for user")
      i.exec_()
      
      if i.user != None:
         self.userText.setText(i.user)
         self.oldPassText.setEnabled(True)
         self.newPass1Text.setEnabled(True)
         self.newPass2Text.setEnabled(True)
         self.oldPassText.setFocus()
         l.guiLogger.info("User: "+ i.user+ " has been selected to change password")
         l.guiLogger.debug("ChangePassword:userSearch<e>")
         return
      
      l.guiLogger.debug("no user was selected")
      l.guiLogger.debug("ChangePassword:userSearch<e>")


   def commitPasswordChange(self):
      l.guiLogger.debug("ChangePassword:commitPasswordChange<s> - commit the password change to the db")
      #when the commit button is pressed update the password, assuming password fields are satisfied
      if self.checkPassword() and self.checkConfirm():
         try: self.cursor.execute("UPDATE users SET pass = '{}' WHERE username = '{}';".format(bcrypt.hashpw(self.newPass1Text.text(), bcrypt.gensalt()), self.userText.text()))
         except Exception as e: l.guiLogger.error("Something went wrong changing password: "+ str(e))
         l.guiLogger.info("password successfully updated for user: "+ self.userText.text())
         self.success = True
         l.guiLogger.debug("ChangePassword:commitPasswordChange<e>")
         self.close()
         
      else:
         if not self.checkPassword():
            l.guiLogger.debug("old password is not correct")
            if self.isVisible():
               QtGui.QMessageBox.warning(self, "Old Password Incorrect", "The old password is not correct for that username. You must have the old password in order to change the password. If needed, please recover the password using the email recovery tool.")
         elif not self.checkConfirm():
            l.guiLogger.debug("new passwords to not match")
            if self.isVisible():
               QtGui.QMessageBox.warning(self, "New Passwords Don't Match", "Please make sure the new passwords match!")
            
      l.guiLogger.debug("ChangePassword:commitPasswordChange<e>")
      
   
   def checkPassword(self):
      l.guiLogger.debug("ChangePassword:checkPassword<s> - compares the 'old password' with the one in the database")
      #checks the inputted password against the one in the user database
      
      #get password from database
      self.cursor.execute("SELECT pass FROM users WHERE username == '{}'".format(self.userText.text()))
      res = self.cursor.fetchone()
         
      #check the password 
      if (bcrypt.hashpw(self.oldPassText.text(), res[0]) == res[0]):
         l.guiLogger.info("Correct password")
         l.guiLogger.debug("ChangePassword:checkPassword<e>")
         return True
      else:
         l.guiLogger.info("Incorrect password")
         l.guiLogger.debug("ChangePassword:checkPassword<e>")
         return False
   
   
   def checkConfirm(self):
      #check to make sure new passwords match
      if self.newPass1Text.text() == self.newPass2Text.text():
         return True
      else:
         return False
      
      
   def enableCommit(self):
      #enable the commit button
      
      #this happens so frequently, I don't want to log it...it's pretty simple, and I highly doubt it'll cause problems
      if not (self.oldPassText.text() == "" and self.newPass1Text.text() == "" and self.newPass2Text.text() == ""):
         self.commitChangeButton.setEnabled(True)
         self.commitChangeButton.setDefault(True)
      else:
         self.commitChangeButton.setEnabled(False) 
         
         
   def check(self): 
      #debug label handler for comparing the new passwords
      #this happens so frequently, I don't want to log it...it's pretty simple, and I highly doubt it'll cause problems
      if not self.checkConfirm():
         self.debugLabel.setText("New passwords do not match!")
      else:
         self.debugLabel.setText("")
         
         
   def checkPW(self):
      #debug label handler for checking the old password
      #this happens so frequently, I don't want to log it...it's pretty simple, and I highly doubt it'll cause problems
      if not self.checkPassword():
         self.debugLabel.setText("Old password is not correct!")
      else:
         self.debugLabel.setText("")



class ReadOnlyQCheckbox(QtGui.QCheckBox):
   #as it reads...it's a read only qcheckbox
   #this is a simple enough object, I don't feel it's necessary to log
   def __init__(self, parent, words):
      QtGui.QCheckBox.__init__(self)
      self.setText(words)
      self.p = parent
      
   def mouseReleaseEvent(self, blah):
      if self.p.diffRadioC.isChecked():
         if self.isChecked():
            self.setChecked(False)
         else:
            self.setChecked(True)



class RangeSlider(QtGui.QSlider):
   """ 
      Class taken from: https://www.mail-archive.com/pyqt@riverbankcomputing.com/msg22889.html
      
      NOTE THE CHANGES FOR ENABLING/DISABLING WHEN CUSTOM IS SELECTED
      
      A slider for ranges.
      
      This class provides a dual-slider for ranges, where there is a defined
      maximum and minimum, as is a normal slider, but instead of having a
      single slider value, there are 2 slider values.
      
      This class emits the same signals as the QSlider base class, with the 
      exception of valueChanged
   """
   
   def __init__(self, parent, *args):
      
      l.guiLogger.debug("Creating RangeSlider")
      
      super(RangeSlider, self).__init__(*args)
      
      self.parent = parent  
        
      self._low = self.minimum()
      self._high = self.maximum()
      
      self.pressed_control = QtGui.QStyle.SC_None
      self.hover_control = QtGui.QStyle.SC_None
      self.click_offset = 0
        
      # 0 for the low, 1 for the high, -1 for both
      self.active_slider = 0

   def low(self):
      return self._low

   def setLow(self, low):
      self._low = low
      self.update()

   def high(self):
      return self._high

   def setHigh(self, high):
      self._high = high
      self.update()
        
        
   def paintEvent(self, event):
      # based on http://qt.gitorious.org/qt/qt/blobs/master/src/gui/widgets/qslider.cpp

      painter = QtGui.QPainter(self)
      style = QtGui.QApplication.style() 
        
      for i, value in enumerate([self._low, self._high]):
         opt = QtGui.QStyleOptionSlider()
         self.initStyleOption(opt)

         # Only draw the groove for the first slider so it doesn't get drawn
         # on top of the existing ones every time
         if i == 0:
            opt.subControls = QtGui.QStyle.SC_SliderHandle#QtGui.QStyle.SC_SliderGroove | QtGui.QStyle.SC_SliderHandle
         else:
            opt.subControls = QtGui.QStyle.SC_SliderHandle

         if self.tickPosition() != self.NoTicks:
            opt.subControls |= QtGui.QStyle.SC_SliderTickmarks

         if self.pressed_control:
            opt.activeSubControls = self.pressed_control
            opt.state |= QtGui.QStyle.State_Sunken
         else:
            opt.activeSubControls = self.hover_control

         opt.sliderPosition = value
         opt.sliderValue = value                                  
         style.drawComplexControl(QtGui.QStyle.CC_Slider, opt, painter, self)
            
        
   def mousePressEvent(self, event):
      if self.parent.diffRadioC.isChecked():
         event.accept()
           
         style = QtGui.QApplication.style()
         button = event.button()
           
         # In a normal slider control, when the user clicks on a point in the 
         # slider's total range, but not on the slider part of the control the
         # control would jump the slider value to where the user clicked.
         # For this control, clicks which are not direct hits will slide both
         # slider parts
                   
         if button:
            opt = QtGui.QStyleOptionSlider()
            self.initStyleOption(opt)
            
            self.active_slider = -1
            
            for i, value in enumerate([self._low, self._high]):
               opt.sliderPosition = value                
               hit = style.hitTestComplexControl(style.CC_Slider, opt, event.pos(), self)
               if hit == style.SC_SliderHandle:
                  self.active_slider = i
                  self.pressed_control = hit
                    
                  self.triggerAction(self.SliderMove)
                  self.setRepeatAction(self.SliderNoAction)
                  self.setSliderDown(True)
                  break
            
            if self.active_slider < 0:
               self.pressed_control = QtGui.QStyle.SC_SliderHandle
               self.click_offset = self.__pixelPosToRangeValue(self.__pick(event.pos()))
               self.triggerAction(self.SliderMove)
               self.setRepeatAction(self.SliderNoAction)
         else:
            event.ignore()
                                
   def mouseMoveEvent(self, event):
      if self.parent.diffRadioC.isChecked():
         if self.pressed_control != QtGui.QStyle.SC_SliderHandle:
            event.ignore()
            return
           
         event.accept()
         new_pos = self.__pixelPosToRangeValue(self.__pick(event.pos()))
         opt = QtGui.QStyleOptionSlider()
         self.initStyleOption(opt)
           
         if self.active_slider < 0:
            offset = new_pos - self.click_offset
            self._high += offset
            self._low += offset
            if self._low < self.minimum():
               diff = self.minimum() - self._low
               self._low += diff
               self._high += diff
            if self._high > self.maximum():
               diff = self.maximum() - self._high
               self._low += diff
               self._high += diff            
         elif self.active_slider == 0:
            if new_pos >= self._high:
               new_pos = self._high - 1
            self._low = new_pos
         else:
            if new_pos <= self._low:
               new_pos = self._low + 1
            self._high = new_pos
   
         self.click_offset = new_pos
   
         self.update()
   
         self.emit(QtCore.SIGNAL('sliderMoved(int)'), new_pos)
            
   def __pick(self, pt):
      if self.orientation() == QtCore.Qt.Horizontal:
         return pt.x()
      else:
         return pt.y()
           
           
   def __pixelPosToRangeValue(self, pos):
      opt = QtGui.QStyleOptionSlider()
      self.initStyleOption(opt)
      style = QtGui.QApplication.style()
        
      gr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderGroove, self)
      sr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderHandle, self)
        
      if self.orientation() == QtCore.Qt.Horizontal:
         slider_length = sr.width()
         slider_min = gr.x()
         slider_max = gr.right() - slider_length + 1
      else:
         slider_length = sr.height()
         slider_min = gr.y()
         slider_max = gr.bottom() - slider_length + 1
            
      return style.sliderValueFromPosition(self.minimum(), self.maximum(),
                                             pos-slider_min, slider_max-slider_min,
                                             opt.upsideDown)



def test():
   #testing components that seem testable
   
   
   total_errors = 0
   successes = 0
   
   #create the application because apparently I have to do that to test...
   #note that the logging level is set to critical, just for sanity's sake
   a = App(logging.CRITICAL)
   
   
   print("BEGINNING TESTS ON mill_song_gui")
   print("-"*30)
   
   
   #---------------------------------------------------------------------
   #--------------------------password verification----------------------
   #---------------------------------------------------------------------
   print("Testing password verification")
   errors = 0
   #create a user to test on
   conn = sqlite3.connect("data/gui/users.db")
   cursor = conn.cursor()
   
   cursor.execute("INSERT OR REPLACE INTO users VALUES ('{}','{}','{}','{}');".
                  format("testuser",
                         bcrypt.hashpw("testPW", bcrypt.gensalt()),
                         "testuseremail@test.com",
                         "thisisarandomstringanddoesntmatter"))
   conn.commit()
   
   #get the central widget
   cw = a.mainWindow.centralWidget
   
   #update the user and password fields
   cw.nameText.setText("testuser")
   cw.passText.setText("testPW")
   
   #test that the password works
   if not cw.checkPW():
      errors +=1
      print("ERROR1: checkPW returned false when it should have returned true")
   else:
      successes += 1
      print("Test 1 Successful")
      
   #put in a wrong password
   cw.nameText.setText("testuser")
   cw.passText.setText("thisisnotcorrect")
   
   #test if that password works
   if cw.checkPW():
      errors +=1
      print("ERROR2: checkPW returned true when it should have returned false")
   else:
      successes += 1
      print("Test 2 Successful")
      
   if errors == 0:
      print("all password verification tests successful")
   total_errors += errors
   print("-" * 30)
   
   
   
   #---------------------------------------------------------------------
   #--------------------------new user dialog----------------------------
   #---------------------------------------------------------------------
   print("Testing new user dialog")
   errors = 0
   
   i = newUserDialog(cursor)
   
   #-----------------------testing turning on submit button----------------
   #try bad email input
   i.emailText.setText("not a good email")
   i.checkInput()
   if i.create.isEnabled():
      errors += 1
      print("ERROR3: create user is enabled with invalid email address")
   else:
      successes += 1
      print("Test 3 Successful")
      
   #good email input
   i.emailText.setText("abetteremail@test.com")
   i.checkInput()
   if i.errorLabel.text() != "":
      errors +=1
      print("ERROR4: incorrectly flagging a valid email")
   else:
      successes += 1
      print("Test 4 Successful")

   #a user that already exists
   i.userText.setText("testuser")
   i.checkInput()
   if i.create.isEnabled():
      errors += 1
      print("ERROR5: create user enabled for a user that already exists in db")
   else:
      successes += 1
      print("Test 5 Successful")

   #a user that doesn't exist in db
   cursor.execute("DELETE FROM users WHERE username == 'testuser'")
   conn.commit()
   i.checkInput()
   if i.errorLabel.text() != "":
      errors += 1
      print("ERROR6: incorrectly flagging a valid new user")
   else:
      successes += 1
      print("Test 6 Successful")
   
   #two passwords that don't match
   i.pass1Text.setText("hello")
   i.pass2Text.setText("world")
   i.checkInput()
   if i.create.isEnabled():
      errors +=1
      print("ERROR7: create user enabled when passowrds do not match")
   else:
      successes += 1
      print("Test 7 Successful")
   
   #two passowrds that don't match
   i.pass2Text.setText("hello")
   i.checkInput()
   if not i.create.isEnabled():
      errors += 1
      print("ERROR8: create user not enabled when it should be")
   else:
      successes += 1
      print("Test 8 Successful")

   #--------------------test actaully adding the user-------------------
   
   try:
      i.addUser()
      print("Test 9 Successful")
   except Exception as e:
      print("ERROR9: not able to add new user. Reason: ", e)
   
   conn.commit()

   #-----------------test that id strings are reasonably unique-----------
   
   lis = []
   
   for n in range(10000+1):
      #note, 15 is the current value being used in code!
      ranstr = i.randomword()
      if ranstr in lis:
         errors +=1
         print("ERROR10: random strings for user ids are not unique enough")
      lis.append(ranstr)
   
   if n == 10000:
      print("Test 10 Successful")
      successes += 1
   
   if errors == 0:
      print("all new user dialog tests successful")
   total_errors += errors
   print("-" * 30)
   
   i.close()

   #---------------------------------------------------------------------
   #-------------------------load user dialog----------------------------
   #---------------------------------------------------------------------
   errors = 0
   print("Testing load user dialog")
   
   #search for user that exist within db
   i = LoadUserDialog(cursor)
   i.userText.setText("testuser")
   i.searchForUser()
   if i.user != "testuser":
      errors += 1
      print("ERROR11: couldn't find a user that should be there")
   else:
      successes += 1
      print("Test 11 Successful")
   
   #try a user that doesn't exist in db
   cursor.execute("DELETE FROM users WHERE username =='testuser'")
   i = LoadUserDialog(cursor)
   i.userText.setText("testuser")
   i.searchForUser()      
   if i.user != None:
      errors += 1
      print("ERROR12: found a user that doesn't exist in db")
   else:
      successes += 1
      print("Test 12 Successful")
   
   #find a user by email
   cursor.execute("INSERT OR REPLACE INTO users VALUES ('{}','{}','{}','{}');".
                  format("testuser",
                         bcrypt.hashpw("testPW", bcrypt.gensalt()),
                         "testuseremail@test.com",
                         "thisisarandomstringanddoesntmatter"))
   cursor.execute("DELETE FROM users WHERE username == 'testuser2'")
   conn.commit()
   i = LoadUserDialog(cursor)
   i.userText.setText("")
   i.emailText.setText("testuseremail@test.com")
   i.searchForUser()
   if i.user != "testuser":
      errors += 1
      print("ERROR13: couldn't find a user via email")
   else:
      successes += 1
      print("Test 13 Successful")
      
   #find a user when there are more than one result for an email. (this also tests the UserNameSelect dialog, indirectly)
   cursor.execute("INSERT OR REPLACE INTO users VALUES ('{}','{}','{}','{}');".
                  format("testuser2",
                         bcrypt.hashpw("testPW", bcrypt.gensalt()),
                         "testuseremail@test.com",
                         "thisisarandomstringanddoesntmatter"))
   conn.commit()
   i = LoadUserDialog(cursor)
   i.userText.setText("")
   i.emailText.setText("testuseremail@test.com")
   i.searchForUser()
   i.i.selection.setCurrentRow(0)
   i.i.makeSelection()
   if i.i.selectedUser == None:
      errors += 1
      print("ERROR14: couldn't find a user via email, with more than one result from search") 
   else:
      successes += 1
      print("Test 14 Successful")
   
   if errors == 0:
      print("all load user dialog tests successfully")
   total_errors += errors
   print("-"*30)
   
   #---------------------------------------------------------------------
   #-------------------------delete user dialog--------------------------
   #---------------------------------------------------------------------
   errors = 0
   print("Testing delete user dialog")
   
   #note do not need to test search functionality because load user class has
   #already been tested. This also means that userText should never have an
   #invalid username
   
   #attempt to delete user
   i = DeleteUserDialog(cursor)
   i.userText.setText("testuser2")
   i.userToDelete = "testuser2"
   i.passText.setText("testPW")
   i.delete.setEnabled(True)
   i.deleteUser()
   if not i.success:
      errors +=1
      print("ERROR15: couldn't delete a user successfully")  
   else:print("Test 15 Successful") 
   conn.commit()
   
   #test bad password
   i = DeleteUserDialog(cursor)
   i.userText.setText("testuser")
   i.userToDelete = "testuser"
   i.delete.setEnabled(True)
   i.passText.setText("not the right pw")
   if i.checkPass():
      errors +=1
      print("ERROR16: allowed an incorrect password")
   else:
      successes += 1
      print("Test 16 Successful")
      
   #test good password
   i.passText.setText("testPW")
   if not i.checkPass():
      errors += 1
      print("ERROR17: disallowed a correct password")
   else:
      successes += 1
      print("Test 17 Successful")
   
   
   if errors == 0:
      print ("all delete user dialog tests passed successfully")
   total_errors += errors
   print('-'*30)
   
   #---------------------------------------------------------------------
   #-----------------------change password dialog------------------------
   #---------------------------------------------------------------------
   errors = 0
   print("Testing change password dialog")
   
   #note: don't need to test selecting a user because it is recycled from 
   #load user code.
   
   #testing changing the password, with the wrong old password and non-matching new pswds
   i = ChangePassword(cursor)
   i.userText.setText("testuser")
   i.oldPassText.setText("not the right pass")
   i.newPass1Text.setText("testPW2")
   i.newPass2Text.setText("not matching")
   if i.checkPassword():
      errors += 1
      print("ERROR17: allowed an incorrect old password")
   else:
      successes += 1
      print("Test 17 Successful")
   if i.checkConfirm():
      errors += 1
      print("ERROR18: allowed non-matching new passwords")
   else:
      successes += 1
      print("Test 18 Successful")
   
   #correct input
   i.oldPassText.setText("testPW")
   i.newPass2Text.setText("testPW2")
   i.commitPasswordChange()
   if not i.success:
      errors += 1
      print("ERROR19: was unsuccessful at changing password")
   else:
      successes += 1
      print("Test 19 Successful")
      
      
   if errors == 0:
      print("all change password dialog tests successful")
   total_errors += errors
   print("-"*30)
   
   
   
   #---------------------------------------------------------------------
   #---------------------------finish report-----------------------------
   #---------------------------------------------------------------------
   print("tests successfully finished! Hurray!")
   print("number of total errors = ", total_errors)
   print("{}/19 tests successful".format(19-total_errors))
   return total_errors


if __name__ == "__main__":
#    a = App(logging_level=logging.INFO)
#    a.exec_()
   
   test()
   