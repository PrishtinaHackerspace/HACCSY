#!/usr/bin/python2

#############################################################################
# HACCSY.py
#############################################################################
# HACCSY (Hackerspace Access Control and Checkin System) app is meant to 
# run on a raspberry pi that's connected to internet and
# the front door electric strike lock. 
# It does the job of a simple Checkin System and Door Access Control System (2in1)
# It queries a REST service by handing it the scanned in RFID card reader and
# it will return 'true' if the key owner owes less than 2 months worth of
# their monthly payment. It will return 'false' otherwise.
# It does the same for checking in and out.
# The computer would then send the signal to the door lock actuator to
# open it if returned true or do nothing if false.  It has a check IN/OUT button to indicate
# Check IN or Check OUT. It also has an LCD backlit display that displays messages for the user,
# and an RGB LED that turns RED for Access Denied, GREEN for Access Granted and WHITE to indicate offline mode
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


import serial
import socket
import re, sys, signal, os, time, datetime
import RPi.GPIO as GPIO
import Validator
import Adafruit_CharLCD as LCD
import smtplib
import os
import logging
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler




##################################
# LOGS
##################################

# This is the master log file that shows which card scanned in
# at what time/date and other events / errors.
HACCSYLogFile='/home/pi/logs/HACCSY.log'

# Make all log messages look like this:
# 12/12/2015 11:46:36 AM is when this event was logged.
# logging.basicConfig(level='INFO',filename=HACCSYLogFile, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# Log Raspberry Pi RFID events
HACCSY_log_formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
HACCSY_my_handler = RotatingFileHandler(HACCSYLogFile, mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=0)
HACCSY_my_handler.setFormatter(HACCSY_log_formatter)
HACCSY_my_handler.setLevel(logging.INFO)
HACCSY_app_log = logging.getLogger('root')
HACCSY_app_log.setLevel(logging.INFO)
HACCSY_app_log.addHandler(HACCSY_my_handler)


##################################
# GPIO Pins
##################################

# We will be using GPIO.BOARD mode so these are the physical pin numbers,
# NOT the GPIO## pin numbers!

########################
#GPIO.setmode(GPIO.BCM)
########################

# Raspberry Pi LCD pin configuration:
# Redeclaring pins from original library "Adafruit_CharLCD"
lcd_rs        = 7
lcd_en        = 8
lcd_d4        = 25
lcd_d5        = 24
lcd_d6        = 23
lcd_d7        = 18
lcd_backlight = 14

# Define LCD column and row size for 16x2 LCD.
lcd_columns = 16
lcd_rows    = 2

# Buttons
DoorLockPin = 27  # connected to maglock
CheckinButtonPin = 10 # Button to check in and check out
################################
#ExitButtonPin = 11 # Button to open door from inside
################################

# RGB LED next to LCD screen
blueLED = 3
greenLED = 2
redLED = 4


##############################
#GPIO.setup(ExitButtonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
##############################
GPIO.setup(DoorLockPin, GPIO.OUT)
GPIO.setup(CheckinButtonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(greenLED, GPIO.OUT)
GPIO.setup(redLED, GPIO.OUT)
GPIO.setup(blueLED, GPIO.OUT)

LOCKED = GPIO.LOW
UNLOCKED = GPIO.HIGH

# Lock the door on boot
GPIO.output(DoorLockPin, LOCKED)

##################################
# Other variables
##################################


# comment out the device you are not using.
# in this case we have our RFID reader hooked to the usb port
# not GPIO UART pins
# SERIALDEVICE = '/dev/ttyAMA0' #GPIO UART pins
SERIALDEVICE = '/dev/hidraw0' #USB serial

# the whitelist file is updated via "UpdateWhiteList.py" file once a day with all the members
# who have paid their dues.  This file "whitelist.txt" is checked first when a
# card is swiped for very fast access without having to wait
# for the REST query. If not found in whitelist it will then
# do the REST query in case they were just added to the DB. 

WHITELISTFILENAME = 'whitelist.txt'
WHITELISTPATH = "/home/pi/" + WHITELISTFILENAME

#this message is shown on the LCD screen while it waits for an RFID card swipe.
readyMessage = "Prishtina\nHackerspace"


####################
# Email stuff for when bad cards or new cards are scanned
# it will email you!
####################
SMTPSERVER = "smtp.gmail.com:587"
USERNAME = "YOURUSERNAME@gmail.com"
PASSWORD = "YOURPASSWORD"
FROM = "YOURUSERNAME@gmail.com"


#this PID file is used by the watchdog script to make sure
# this script is restarted if it ever quits.
PIDFILE = "/home/pi/HACCSY.pid"

#list of valid rfid cards.
CARDS = []

#LCD variable for initialisation
lcd = None



##################################
# Methods
##################################

# Returns True if host is reachable
def is_connected():
  try:
	# see if we can resolve the host name -- tells us if there is
	# a DNS listening
	host = socket.gethostbyname('www.yourseltzerserver.org')
	# connect to the host -- tells us if the host is actually
	# reachable
	s = socket.create_connection((host, 80), 2)
	return True
  except:
	 pass
  return False

# Initializes LCD screen in lcd variable declared above
def initLCDScreen():
	# set up the LCD object for writing messages
	try:
		global lcd
		global readyMessage

		HACCSY_app_log.info("Initializing LCD screen.")

		lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows, lcd_backlight)

		lcd.clear()
		lcd.message('Initializing.')
		time.sleep(0.5)

		lcd.clear()
		lcd.message('Initializing..')
		time.sleep(0.5)

		lcd.clear()
		lcd.message('Initializing...')
		time.sleep(0.5)

		HACCSY_app_log.info("LCD screen initialized OK!")
	except Exception as ex:
		HACCSY_app_log.info("Error trying to init LCD screen: " + str(ex.message))

# Updates local whitelist on boot if host reachable
def updateLocalWhitelistOnBoot():
	# get the latest whitelist from the Seltzer DB on script boot and save to file
	if is_connected():
		try:

			print "Updating the local whitelist..."
			HACCSY_app_log.info('Updating local whitelist to file: ' + WHITELISTFILENAME)
			whitelist = Validator.getWhitelist()
			with open(WHITELISTPATH, "w+") as text_file:
				# text_file.write(str(whitelist))
				json.dump(whitelist,text_file)
			HACCSY_app_log.info("Updated whitelist to file OK")
			print "Updated whitelist OK!"

		except Exception as ex:
			HACCSY_app_log.info("Couldn't update the whitelist." + str(ex.message))
			print "couldn't update the witelist"

# Reads local whitelist and returns the json string from whitelist
def readLocalWhitelist():
	#read the whitelist file and return an array of serial numbers
	#:return: ARRAY
	HACCSY_app_log.info('Reading local whitelist file: ' + WHITELISTFILENAME)
	serialWhiteList = []
	try:
		with open(WHITELISTPATH, "r") as text_file:
			whitelistData = json.load(text_file)
			#pprint.pprint(whitelistData)
			for record in whitelistData:
				serialNum = str(record["serial"])
				if len(serialNum) > 5:
					serialWhiteList.append(serialNum)
	except Exception:
		HACCSY_app_log.info('Whitelist not found or empty or badly formatted JSON.')
	
	HACCSY_app_log.info('Read whitelist file OK. Got whitelist: ' + str(serialWhiteList))
	
	return serialWhiteList

# Connects with GMAIL smtp and sends an email as notification for specified actions
def sendEmail(toEmail, emailSubject, emailMessage):
	HACCSY_app_log.info('Sending email to: ' + toEmail + " ====> " + emailMessage)
	try:
		global SMTPSERVER
		global USERNAME
		global PASSWORD
		global FROM

		#Next, log in to the server
		server = smtplib.SMTP(SMTPSERVER)
		server.ehlo()
		server.starttls()

		#This will need to change if the password ever changes on our gmail account!!!
		server.login(USERNAME, PASSWORD)

		emailMessage = emailMessage

		#Send the mail
		msg = "\r\n".join([
		  "From: HACCSY <" + FROM + ">",
		  "To: " + toEmail,
		  "Subject: " + emailSubject,
		  "",
		  emailMessage
		  ])

		server.sendmail(FROM, toEmail, msg)
		HACCSY_app_log.info('Email sent OK.')

	except Exception as ex:
		HACCSY_app_log.info("Error trying to send email: " + str(ex.message))

# Writes the script pid to HACCSI.pid file so that 
# Watchdog script can monitor if HACCSY.py is still running
def writePidFile():
	try:
		pid = os.getpid()
		with open(PIDFILE, "w+") as text_file:
			text_file.write(str(pid))
	except Exception as ex:
		HACCSY_app_log.info("Error while writing PID file " + PIDFILE + ": " + str(ex.message))

# Reads data stream from RFID USB device, convertis data stream to numeric value
def getSerialNoFromDevice(dev = "/dev/hidraw0"):
	"""
	Get barcode.

	This function reads an hidraw data stream from a barcode scanner
	returns the numeric value of the barcode scnned.

	Parameters
	----------
	dev : str, optional
		Full path hidraw device from which to read hidraw data stream.
		Default path is `/dev/hidraw0`.

	Returns
	-------
	barcode : str
		String representation of numerical value of scanned barcode.

	"""
	hiddev = open(dev, "rb")
 
	barcode = ''

	continue_looping = True

	k = 0

	while continue_looping:
		report = hiddev.read(8)

		# print "k value: ", k
		k += 1

		for i in report:
			j = ord(i)
			# # print j
			if j == 0:
				# print "j = ", j
				continue

			if j == 0x1E:
				barcode += '1'
				# print "j = ", j
				continue
			elif j == 0x1F:
				barcode += '2'
				# print "j = ", j
				continue
			elif j == 0x20:
				barcode += '3'
				# print "j = ", j
				continue
			elif j == 0x21:
				barcode += '4'
				# print "j = ", j
				continue
			elif j == 0x22:
				barcode += '5'
				# print "j = ", j
				continue
			elif j == 0x23:
				barcode += '6'
				# print "j = ", j
				continue
			elif j == 0x24:
				barcode += '7'
				# print "j = ", j
				continue
			elif j == 0x25:
				barcode += '8'
				# print "j = ", j
				continue
			elif j == 0x26:
				barcode += '9'
				# print "j = ", j
				continue
			elif j == 0x27:
				barcode += '0'
				# print "j = ", j
				continue
			elif j == 0x28:
				# print "j = ", j
				# print barcode
				hiddev.close()
				continue_looping = False
				break
			else:
				pass
				# print "+++ Melon melon melon +++"
				# print "j = ", j
				# hiddev.close()
				# continue_looping = False
				# break

	return barcode

# Manages RGB LED color based on given parameter.
# It tirns the parameter color on, and turns off all other colors
# Ofc there are more options to this, but we're using only Red, Green, Blue, White, and all OFF.
def RGBLED(color):

	if (color == "red"):
		GPIO.output(blueLED, GPIO.LOW)
		GPIO.output(greenLED, GPIO.LOW)

		GPIO.output(redLED, GPIO.HIGH) # turn on RED

	elif (color == "blue"):
		GPIO.output(greenLED, GPIO.LOW)
		GPIO.output(redLED, GPIO.LOW)

		GPIO.output(blueLED, GPIO.HIGH) # turn on BLUE

	elif (color == "green"):
		GPIO.output(blueLED, GPIO.LOW)
		GPIO.output(redLED, GPIO.LOW)

		GPIO.output(greenLED, GPIO.HIGH) # turn on GREEN

	elif (color == "white"):
		GPIO.output(blueLED, GPIO.HIGH)
		GPIO.output(redLED, GPIO.HIGH) # turn on ALL = WHITE
		GPIO.output(greenLED, GPIO.HIGH)

	elif (color == "off"):
		GPIO.output(blueLED, GPIO.LOW)
		GPIO.output(redLED, GPIO.LOW) # tunr all off
		GPIO.output(greenLED, GPIO.LOW)

	else:
		pass

# Blinks 2 color values from above 3 times 
# You can use RGBLEDBlink("white", "off"), to turn RGB led on and off 3 times
def RGBLEDBlink(color1, color2):
	RGBLED(color1)
	time.sleep(0.5)
	RGBLED(color2)
	time.sleep(0.5)
	RGBLED(color1)
	time.sleep(0.5)
	RGBLED(color2)
	time.sleep(0.5)
	RGBLED(color1)

# Writes a given message to LCD and sets a delay of 
# X seconds (it helps to slow down messages when showing them one after the other)
def writeLCDMessage(newmessage, delay):
	try:
		global lcd
		lcd.clear()
		lcd.message(newmessage)
		time.sleep(delay)
	except Exception as ex:
		HACCSY_app_log.info("Error writing LCD message: " + str(ex.message))

# It makes sure to open door if program exits
def signal_handler(signal, frame):
	# print "Closing HACCSY Script"
	global pipe
	HACCSY_app_log.info("============Closing HACCSY Script.============")
	GPIO.output(DoorLockPin, UNLOCKED)  # Unlock the door on program exit
	GPIO.cleanup()
	os.close(pipe)
	ser.close()
	sys.exit(0)

# Sets GPIO pin for door electric strike lock on and off
def unlock_door(duration):
	HACCSY_app_log.info("Unlocking door for %d seconds." % duration)
	GPIO.output(DoorLockPin, UNLOCKED)
	RGBLED("green")
	time.sleep(duration)
	GPIO.output(DoorLockPin, LOCKED)
	HACCSY_app_log.info("Door locked.")
	writeLCDMessage(readyMessage,0)
	RGBLED("blue")



##################################
# Main
##################################

if __name__ == '__main__':

	HACCSY_app_log.info("====================Starting HACCSY Script==========================")

	initLCDScreen()

	serialNo = ''
	pipe = os.pipe()
	rfidPattern = re.compile(b'[\W_]+')
	signal.signal(signal.SIGINT, signal_handler)

	# write this process's ID to the PIDFILE so our watchdog script
	# can check if this script is still running or crashed.
	writePidFile()

	# Turn off RGB led on boot
	RGBLED("off")

	# Update whitelist on boot
	writeLCDMessage('Updating\nWhitelist...',0.5)
	updateLocalWhitelistOnBoot()
	
	# HACCSY is ready!
	writeLCDMessage('HACCSY ready!',1)


	while True:

		writeLCDMessage(readyMessage,0) # Write readyMessage on screen, indicate RPi RFID is waiting card swipe
		RGBLED("blue") # Turn blue led on, indicate RPi RFID is waiting card swipe

		# Wait for user input to swipe card
		serialNo = getSerialNoFromDevice(SERIALDEVICE)
		match = rfidPattern.sub('', serialNo)

		HACCSY_app_log.info('RFID card scanned: ' + str(serialNo))

		# writeLCDMessage('Press & Hold\nbutton',1)
		# writeLCDMessage('to: Check IN/OUT',1)
		
		# writeLCDMessage('Waiting user\ninput... 2',1)
		writeLCDMessage('Waiting user\ninput.',0.3)
		writeLCDMessage('Waiting user\ninput..',0.3)
		writeLCDMessage('Waiting user\ninput...',0.3)


		#####################################################################################################
		#######                                    ONLINE
		#####################################################################################################

		# Online mode uses REST if user not found in local whitelist and as well does the Check IN/OUT process
		if is_connected():

			HACCSY_app_log.info("HOST REACHED - ONLINE AUTHENTICATION MODE")

			if match:

				# If user has pressed the Check IN/OUT button after swiping RFID card
				# enter the Check IN/OUT process
				if not GPIO.input(CheckinButtonPin):

					HACCSY_app_log.info("Check IN/OUT Button pressed")
					
					# PRINT LCD
					writeLCDMessage('Checking...',0)

					CARDS = readLocalWhitelist()

					if match in CARDS:

						HACCSY_app_log.info('Card authorized via whitelist: ' + str(match))

						# PRINT LCD
						writeLCDMessage('Whitelist OK!', 1)

						# Communicate with REST API to process Check IN/OUT
						checkInJsonResponse = Validator.processCheckIn(match)
						HACCSY_app_log.info('processCheckIn() json response: ' + str(checkInJsonResponse))
						checkInJsonString_errors = checkInJsonResponse['hasErrors']
						checkInJsonString_message = checkInJsonResponse['message']
						checkInJsonString_firstName = checkInJsonResponse['firstName']
						checkInJsonString_lastName = checkInJsonResponse['lastName']

						if (checkInJsonString_errors == 0):

							HACCSY_app_log.info('processCheckIn() json string: ' + str(checkInJsonString_errors) + ' errors | ' + checkInJsonString_firstName + ' ' + checkInJsonString_lastName + ' | ' + str(match) + ' | ' + checkInJsonString_message)
							
							if (checkInJsonString_message == "Checkin successful!"):

								HACCSY_app_log.info('Checked IN. ACCESS GRANTED: ' + str(match))

								writeLCDMessage('Check IN\nsuccessful!',1)
								writeLCDMessage('Happy Hacking\n' + checkInJsonString_firstName,1)
								writeLCDMessage('Access Granted!',0)
							   
								HACCSY_app_log.info('UNLOCKING DOOR')
								unlock_door(5)

							else :

								HACCSY_app_log.info('Checked OUT:' + str(match))
								# PRINT LCD
								RGBLED("green")
								writeLCDMessage('Check OUT\nsuccessful!',1)
								writeLCDMessage('Bye ' + checkInJsonString_firstName,2)

						else :

							# PRINT LCD
							writeLCDMessage('ERROR:\n' + checkInJsonString_message,5)
							HACCSY_app_log.info('ERROR: Could not Check IN/OUT user. | ' + checkInJsonString_message )


					else:

						HACCSY_app_log.info('RFID not found in whitelist. Checking with REST: ' + str(match))

						#not in the local whitelist, check REST web service
						jsonResponse = Validator.validate(match)
						HACCSY_app_log.info('validate() json response: ' + str(jsonResponse))
						jsonString = jsonResponse[0]
						HACCSY_app_log.info('validate() json string: ' + jsonString)

						if (jsonString == "True"):

							HACCSY_app_log.info('Card authorized via REST service.')

							# PRINT LCD
							writeLCDMessage('Auth w/ REST',1)

							checkInJsonResponse = Validator.processCheckIn(match)
							HACCSY_app_log.info('processCheckIn() json response: ' + str(checkInJsonResponse))
							checkInJsonString_errors = checkInJsonResponse['hasErrors']
							checkInJsonString_message = checkInJsonResponse['message']
							checkInJsonString_firstName = checkInJsonResponse['firstName']
							checkInJsonString_lastName = checkInJsonResponse['lastName']


							if (checkInJsonString_errors == 0):

								HACCSY_app_log.info('processCheckIn() json string: ' + str(checkInJsonString_errors) + ' errors | ' + checkInJsonString_firstName + ' ' + checkInJsonString_lastName + ' | ' + str(match) + ' | ' + checkInJsonString_message)
								
								if (checkInJsonString_message == "Checkin successful!"):

									HACCSY_app_log.info('Checked IN. ACCESS GRANTED: ' + str(match))

									# PRINT LCD
									writeLCDMessage('Check IN\nsuccessful!',1)
									writeLCDMessage('Happy Hacking\n' + checkInJsonString_firstName,1)
									writeLCDMessage('Access Granted!',0)
									
									HACCSY_app_log.info('UNLOCKING DOOR')
									unlock_door(5)

								else :

									FID_app_log.info('Checked OUT:' + str(match))

									# PRINT LCD
									writeLCDMessage('Check OUT\nsuccessful!',1)
									writeLCDMessage('Bye ' + checkInJsonString_firstName,2)
									

							else :

								writeLCDMessage('ERROR:\n' + checkInJsonString_message,2)

								HACCSY_app_log.info('ERROR: Could not Check IN/OUT user. | ' + checkInJsonString_message )

						else:

							HACCSY_app_log.info('RFID serial not found or member payments are due. Access Denied.')
							# PRINT LCD
							RGBLED("red")
							writeLCDMessage('Unauthorized\nAccess Denied!',1)

							sendEmail("info@yourseltzerserver.com", "[HACCSY] - UNAUTHORIZED ACCESS ", "ONLINE MODE\n===>Check IN/OUT Button pressed\n==>RFID not in whitelist, checked with REST:\nRFID serial not found or member payments are due.\nRFID: " + serialNo)

				else :


					HACCSY_app_log.info("Check IN/OUT Button ((NOT)) pressed")

					# PRINT LCD
					writeLCDMessage('Checking...',0)

					CARDS = readLocalWhitelist()

					if match in CARDS:

						jsonResponse = Validator.isUserCheckedIn(match)
						jsonString = jsonResponse[0]
						HACCSY_app_log.info('isUserCheckedIn() json string: ' + jsonString)

						HACCSY_app_log.info('Card authorized via whitelist: ' + str(match))
						
						if (jsonString == "True"):

							writeLCDMessage('Access Granted!',0)
							
							HACCSY_app_log.info('Member already Checked IN | Member card: ' + str(match))

							HACCSY_app_log.info('UNLOCKING DOOR')
							unlock_door(5)

						else :
							
							# PRINT LCD
							RGBLED("red")
							writeLCDMessage('Access Denied!\nPlease Check IN',1)

							HACCSY_app_log.info('Access Denied, Member was not Checked IN | Member card: ' + str(match))

							sendEmail("info@yourseltzerserver.com", "[HACCSY] - UNAUTHORIZED ACCESS ", "ONLINE MODE\n===>Check IN/OUT Button NOT pressed\nUser tried to access without Checking IN.\nRFID: " + serialNo)


					else:

						HACCSY_app_log.info('RFID serial not found or member payments are due. Access Denied.')
						# PRINT LCD
						RGBLED("red")
						writeLCDMessage('Unauthorized.\nAccess Denied!',1)

						sendEmail("info@yourseltzerserver.com", "[HACCSY] - UNAUTHORIZED ACCESS ", "ONLINE MODE\n===>Check IN/OUT Button NOT pressed\nRFID serial not found or member payments are due.\nRFID: " + serialNo)


		#####################################################################################################
		#######                                    OFFLINE
		#####################################################################################################

		# Offline mode only uses the local whitelist, no REST
		else :

			RGBLEDBlink("white", "off")

			HACCSY_app_log.info("OFFLINE - HOST COULD NOT BE REACHED - OFFLINE AUTHENTICATION MODE")

			if match:
				 
				# PRINT LCD
				writeLCDMessage('Checking...\n'+str(match),0)

				CARDS = readLocalWhitelist()

				if match in CARDS:

					HACCSY_app_log.info('OFFLINE - ' + 'Card authorized via whitelist: ' + str(match))

					# PRINT LCD
					writeLCDMessage('Whitelist OK!',1)

					HACCSY_app_log.info('OFFLINE - ACCESS GRANTED for RFID: ' + str(match))

					# PRINT LCD
					writeLCDMessage('Access Granted!\nWelcome!',0)

					HACCSY_app_log.info('OFFLINE - UNLOCKING DOOR')
					unlock_door(5)

				else:

					HACCSY_app_log.info('OFFLINE - ' + 'Card NOT authorized via whitelist.' + str(match))
					HACCSY_app_log.info('OFFLINE - RFID serial not found or member payments are due. ACCESS DENIED for RFID: ' + str(match))

					# PRINT LCD
					RGBLED("red")
					writeLCDMessage('Unauthorized.\nAccess denied!',1)


		serialNo = ''
		#match = ''