#!/usr/bin/python2

#############################################################################
# Watchdog.py
#############################################################################
# This script is meant to run at boot time. It checks the last modified
# date/time on the configured file.  If that file hasn't been modified
# within the configured time interval (usually 2 minutes) then it will
# execute the configured command (usually to restart the RFID lock script).
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


import os
import time

#this PIDFILE must match the one set in the main 
#HACCSY.py script!
HACCSY_PIDFILE = "/home/pi/HACCSY.pid"

#UpdateWhiteList.py script!
UPDATEWHITELIST_PIDFILE = "/home/pi/UpdateWhiteList.pid"

#this is the command to run the main script.
#this script and the main script should all be in
#the same folder.
COMMAND1 = "python /home/pi/HACCSY.py &"
COMMAND2 = "python /home/pi/UpdateWhiteList.py &"
CHECKWAITTIME = 10 #check every X seconds

#since this script is run at boot time with the main
#door lock script, wait a good while for the main
#script to get started touching the PIDFILEs.
time.sleep(CHECKWAITTIME * 3)

HACCSY_pid = None
UPDATEWHITELIST_pid = None

def readHACCSYPidFile():
	global HACCSY_pid
	with open(HACCSY_PIDFILE,'r') as pidfile:
		HACCSY_pid = pidfile.read()
	print('HACCSY_pid = ' + str(HACCSY_pid))

def readUpdateWhiteListPidFile():
	global UPDATEWHITELIST_pid
	with open(UPDATEWHITELIST_PIDFILE,'r') as upidfile:
		UPDATEWHITELIST_pid = upidfile.read()
	print('UPDATEWHITELIST_pid = ' + str(UPDATEWHITELIST_pid))


readHACCSYPidFile()
readUpdateWhiteListPidFile()

while True:
	time.sleep(CHECKWAITTIME)

	#if the process isn't running then the script must have stopped
	# running for whatever reason.  Run the configured
	# command1 or command2 to restart it.

	if(not os.path.exists("/proc/" + str(HACCSY_pid))):
		#no longer running!
		print "file not running! Running command1: " + COMMAND1
		os.system(COMMAND1)
		#wait a while for it to start, then get the new PID
		time.sleep(CHECKWAITTIME)
		readHACCSYPidFile()

	if(not os.path.exists("/proc/" + str(UPDATEWHITELIST_pid))):
		#no longer running!
		print "file not running! Running command2: " + COMMAND2
		os.system(COMMAND2)
		#wait a while for it to start, then get the new PID
		time.sleep(CHECKWAITTIME)
		readUpdateWhiteListPidFile()
