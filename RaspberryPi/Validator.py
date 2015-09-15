#!/usr/bin/python2

#############################################################################
# Validator.py
#############################################################################
# This app is meant to run on a raspberry pi that's connected to the internet and
# the front door electric strike lock. 
# This file contain methods that communicate with the REST API in the seltzer server and 
# validates a given RFID key, retreives whitelist of key owners who owe less than 2 months
# worth of their monthly membership, processes the Check IN or Check OUT, and checks if user
# is Checked IN or Checked OUT.
# It also uses HTTPBasicAuth, bcs the api in seltzer server is protected with a htaccess & htpasswd
# This simple protection prevents anyone to fill up the server with logs of users checking in and out
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


import requests
import json
import pprint
from requests.auth import HTTPBasicAuth


#set this to the URL where you've installed Seltzer.
#it's just the server so don't include the /crm/... part.
#www.yourseltzerserver.com for example
SELTZERSERVER = "www.yourseltzerserver.com"
HTACCESSUSER = "admin"
HTACCESSPASSWD = "admin"

def validate(rfid):
    """
    Validates a given RFID using a REST web service that takes the RFID as input
    and returns a simple 'true' if the key owner has paid their dues in the past
    45 days or 'false' otherwise
    :param rfid: the RFID read from the reader
    :return: True if RFID owner is OK, False otherwise
    """

    # pass the RFID to the REST service
    url = 'http://' + SELTZERSERVER + '/crm/api/query.php?action=doorLockCheck&rfid=' + rfid
    payload = ''
    response = requests.get(url, auth=HTTPBasicAuth(HTACCESSUSER, HTACCESSPASSWD),data=payload, timeout=30.0)

    # the response.content should be 'true' or 'false'
    #pprint.pprint(response.content)
    return json.loads(response.content)

def getWhitelist():
    """
    Gets the most recent whitelist of valid RFID card serial numbers based on member
    payments and up to date accounts.  If fields param is blank it will return all
    the fields from the database. Otherwise pass in a comma separated list of field
    names to return.
    :param fields:
    :return:
    """
    url = 'http://' + SELTZERSERVER + '/crm/api/query.php?action=getRFIDWhitelist'
    payload = ''
    response = requests.get(url, auth=HTTPBasicAuth(HTACCESSUSER, HTACCESSPASSWD),data=payload, timeout=30.0)

    whitelist = json.loads(response.content)
    # pprint.pprint(whitelist)

    return whitelist

def processCheckIn(rfid):
    """
    Checks IN or OUT a user and saves logs in the remote database where the seltzer CRM is.
    :param rfid: the RFID read from the reader
    
    if process has errors it returns a json with:
        hasErrors: 1
        message: ERROR message
    else
        hasErrors: 0
        message: "Check in successful!" or "Checkout successful!"
        firstName: USERS NAME
        lastName: USERS SURNAME
        lastCheckInTime: USERS lastCheckInTime (Y-m-d h:i:s)
        lastCheckOutTime: USERS lastCheckOutTime (Y-m-d h:i:s)
    """

    # pass the RFID to the REST service
    url = 'http://' + SELTZERSERVER + '/crm/api/query.php?action=processCheckIn&rfid=' + rfid
    payload = ''
    response = requests.get(url, auth=HTTPBasicAuth(HTACCESSUSER, HTACCESSPASSWD),data=payload, timeout=30.0)

    #pprint.pprint(response.content)
    return json.loads(response.content)

def isUserCheckedIn(rfid):
    """
    Checks if the rfid owner is already checked in or not
    :param rfid: the RFID read from the reader
    :return: True if RFID owner is checked IN, False otherwise
    """

    # pass the RFID to the REST service
    url = 'http://' + SELTZERSERVER + '/crm/api/query.php?action=isUserCheckedIn&rfid=' + rfid
    payload = ''
    response = requests.get(url, auth=HTTPBasicAuth(HTACCESSUSER, HTACCESSPASSWD),data=payload, timeout=30.0)

    #pprint.pprint(response.content)
    return json.loads(response.content)