#!/bin/bash

#title			:WifiTest.sh
#usage 			:bash WifiTest.sh
#description	:This script is meant to be executed on boot. It will check if host is connected in a network and online
#				 , it will try to reconnect, and if it fails, it will reboot the host.
#				 Change wlan0 to eth0 if you're connected with an ethernet cable instead of Wirelessly .
#author 		:Altin Ukshini
#copyright 		:Copyright 2015, Prishtina Hackerspace
#license		:GPL
#version		:1.0.0
#maintainer		:Altin Ukshini
#email 			:altin.ukshini@gmail.com
#==============================================================================

LOG=/home/pi/logs/WifiTest.log 

# GOOGLE IP
IP="8.8.8.8"

while true
do
	sleep 6

	ping -c2 ${IP} > /dev/null

	if [ $? != 0 ]
	then

			message="$(date) -- WiFi DOWN, restarting - message from script  /home/pi/WifiTest.sh"
			# echo >$LOG  empties the file so just the last log is saved

			echo $message >>$LOG

			# Depends which one works for your setup!!
			
			# ifdown --force wlan0
			# ifup wlan0

			ifconfig wlan0 down
			ifconfig wlan0 up

			downcount=$(grep DOWN /home/pi/logs/WifiTest.log | wc -l) # counts the times the letters "DOWN" are in the logfile and passes it to the variable dwncount
			echo ${downcount} >>$LOG

			if ((${downcount} >= 20 )); then

					   echo >$LOG # empty the file
					   sudo reboot

			fi
	else
			message="$(date) -- WiFi UP - message from script  /home/pi/WifiTest.sh"
			# echo >$LOG  empties the file so just the last log is saved
			echo $message >$LOG

	fi

done