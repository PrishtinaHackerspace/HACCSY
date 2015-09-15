#!/usr/bin/python2

#############################################################################
# UpdateWhiteList.py
#############################################################################
# This script is meant to run at boot time. It updates the whitelist file
# everyday at X hour
# Altin Ukshini
# altin.ukshini@gmail.com
# Sep 20, 2015
#############################################################################
__author__ = "Altin Ukshini"
__copyright__ = "Copyright 2015, Prishtina Hackerspace"
__credits__ = ["https://github.com/MelbourneMakerSpace/RFIDLock"]

__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Altin Ukshini"
__email__ = "altin.ukshini@gmail.com"


import socket
import os
import Validator
import time, datetime
import json
from datetime import datetime

# The whitelist file is updated once a day with all the members
# who have paid their dues.  This file is checked first when a
# card is swiped for very fast access without having to wait
# for the REST query. If not found in whitelist it will then
# do the REST query in case they were just added to the DB. 

WHITELISTFILENAME = 'whitelist.txt'
WHITELISTPATH = "/home/pi/" + WHITELISTFILENAME
WHITELISTUPDATEHOUR = 1 # update at this hour every day (24 hour clock)
UPDATEWAITTIME = 100 # number of seconds to wait between bad attempts to update the whitelist
whitelistUpdatedToday = False
lastUpdateTime = time.time()


#this PID file is used by the watchdog script to make sure
# this script is restarted if it ever quits.
PIDFILE = "/home/pi/UpdateWhiteList.pid"


##################################
# Methods
##################################

def writePidFile():
	try:
		pid = os.getpid()
		with open(PIDFILE, "w+") as text_file:
			text_file.write(str(pid))
	except Exception as ex:
		RFID_app_log.info("Error while writing PID file " + PIDFILE + ": " + str(ex.message))

def updateLocalWhitelist():
	# get the latest whitelist from the Seltzer DB and save to file
	if is_connected():
		try:
			global lastUpdateTime
			global whitelistUpdatedToday
			global UPDATEWAITTIME
			currentTime = time.time()

			if ((currentTime - lastUpdateTime) > UPDATEWAITTIME ):
				print "Updating the local whitelist..."
				whitelist = RFIDValidator.getWhitelist()
				with open(WHITELISTPATH, "w+") as text_file:
					# text_file.write(str(whitelist))
					json.dump(whitelist,text_file)
				print "Updated whitelist OK!"
				whitelistUpdatedToday = True
				lastUpdateTime = time.time()

		except Exception as ex:
			print "Couldn't update the whitelist." + str(ex.message)
			# print "couldn't update the witelist"
			lastUpdateTime = time.time()

def is_connected():
  try:
	# see if we can resolve the host name -- tells us if there is
	# a DNS listening
	host = socket.gethostbyname('www.prishtinahackerspace.org')
	# connect to the host -- tells us if the host is actually
	# reachable
	s = socket.create_connection((host, 80), 2)
	return True
  except:
	 pass
  return False


##################################
# Main
##################################

if __name__ == '__main__':

	# write this process's ID to the PIDFILE so our watchdog script
	# can check if this script is still running or crashed.
	writePidFile()

	while True:
		
		# Update the whitelist every night at 1 am
		if datetime.now().hour == WHITELISTUPDATEHOUR:
			if whitelistUpdatedToday == False:
				updateLocalWhitelist()

		# After whitelist update hour, set the flag back.
		# This keeps it from updating constantly for the whole hour!
		if datetime.now().hour  == (WHITELISTUPDATEHOUR + 1):
			whitelistUpdatedToday = False

		# wait a bit before looping again
		time.sleep(5)