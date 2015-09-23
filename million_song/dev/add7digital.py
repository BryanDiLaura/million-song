#!/usr/bin/env python3

"""
   Bryan DiLaura
   Jun 2015
   
   THIS IS NO LONGER NEEDED! USING SPOTIFY AND ECHO NEST API NOW!!!
   
   This is a basic script that adds the 7digital id's to the 
   subset_track_metadata.db database. 
   
   NOTE: the path to the database you are wanting to use must
   be passed to the add7digital class.
   
   It does this by using the add7digital class, which is 
   implemented in the db_creation_class file. Visit that
   file for more information.


"""


from dev.db_creation_class import add7digital


a = add7digital("../bin/subset_track_metadata.db")

a.gather()