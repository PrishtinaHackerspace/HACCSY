HACCSY
========

HACCSY abreviation stands for Hackerspace Access Control and Checkin System and that's pretty much what it does.

HACCSY app is meant to run on a RaspberryPi that’s connected to internet and the front door electric strike lock. It does the job of a simple Check in System and Door Access Control System (2 in 1), it queries a REST service by handing it the scanned in RFID card reader and it will return ‘true’ if the key owner owes less than 2 months worth of their monthly payment. It will return ‘false’ otherwise. It does the same for checking in and out. The computer would then send the signal to the door lock actuator to open it if returned true or do nothing if false. It has a check IN/OUT button to indicate Check IN or Check OUT. It also has an LCD backlight display that displays messages for the user, and an RGB LED that turns RED for Access Denied, GREEN for Access Granted and WHITE to indicate offline mode. Through the REST API, you can also make it available for others to see if the hackerspace is open or not. See working example on the website header at www.prishtinahackerspace.org

HACCSY is built with the following hardware and electronic components:
* Raspberry Pi
* USB RFID reader (hidraw0)
* AdaFruit LCD screen,
* 12V Power supply (12V LED power supply)
* 2 push buttons (Check in/out button, Exit button)
* Electric strike lock.
* N-Channel Mosfet (FK106269)
* Mosfet Resistor 1/4W ~47 kOhm
* Display Resistor 1/4W 470 Ohm
* Display Pot 10 kOhm
* 3x LED resistors ~330 Ohm
* Protection Diode 1N4007
* Snubber Resistor 100 Ohm
* Snubber Capacitor 0.47 uF 100V (not electrolythic)

See a demo video here: https://www.youtube.com/watch?v=QnXSiL62yJ0
Pics from the buildout: http://www.prishtinahackerspace.org/haccsy-hackerspace-access-control-and-check-in-system/

## Credits ##

HACCSY's code is based on ACON<br />
https://github.com/MelbourneMakerSpace/RFIDLock

This code is broken into two parts to make HACCSY work with Seltzer.<br />
https://github.com/elplatt/seltzer

***Code Author***: Altin Ukshini - altin.uskhini@gmail.com<br />
***Hardware and wiring***: Dijon Vula - dijonvula@gmail.com


## Wiring schema ##

<img src="https://github.com/PrishtinaHackerspace/HACCSY/raw/master/schema.jpg" align="center" width="100%" alt="Schema" /><br />
Credits: Dijon Vula - dijonvula@gmail.com<br/>
***Note***: We will update the shcema soon, until then, please use a Snubber or an <a href="http://i.imgur.com/tChKv.png">reverse-biased diode</a> at the electric strike lock to eliminate any noise / inductive kick in the circuit - this usually affects the LCD screen and will make it display scrambled characters.

## Installation ##

The python files stored in the RaspberryPi folder go in the /home/pi folder.
The Seltzer PHP files need to be uploaded via FTP to the same web server where you've installed Seltzer.
It should line up where this "api" folder is under the "crm" folder so that the URL looks like "http://yourserver.com/crm/api/query.php....."

If you don't want it to interface with Seltzer you could take out the part that updates the whitelist file and just populate the file manually with the valid users and their RFID serial numbers.  The whitelist file should have a JSON array like this:

	[{"firstName":"Josh","lastName":"Pritt","serial":"8045AB453449"},{"firstName":"Tony","lastName":"Bellomo","serial":"6554557774BC"},{"firstName":"Arlo","lastName":"Del Rosario","serial":"4944D8938D11"}]

There are several variables to set.  They are all at the top and usually are ALL CAPS.  Change these values if you need to such as the USERNAME and PASSWORD for your email server or HTTPAuth authenticating with htaccess when using REST API.

You need to run a few commands on the Raspberry Pi command line (terminal) to get it to run the Python scripts correctly.

	sudo apt-get install python-dev python-rpi.gpio

Then get the AdaFruit LCD screen library and setup the I2C pins on the GPIO by following these directions:<br />
https://learn.adafruit.com/adafruit-16x2-character-lcd-plus-keypad-for-raspberry-pi/usage

***NOTE:*** In our case, we have used different pins, so when testing the libraries, make sure to use our pin setup!

Finally, set up the RPi so that it runs the main python script as soon as it boots up as root user:

	sudo su
	crontab -e

add this to the end of the cron:

	@reboot python /home/pi/HACCSY.py & python /home/pi/UpdateWhiteList.py & python /home/pi/Watchdog.py &
	@reboot bash /home/pi/WifiTest.sh
	
then save and exit and reboot the pi

If you're using a Wifi USB adapter, edit /etc/network/interfaces/ and at the wlan0 configuration add
	allow-hotplug wlan0
	#and
	wireless-power off
	
Your configuration should look somewhat like this:
	auto lo
	iface lo inet loopback

	iface etho0 dhcp
	auto eth0
	allow-hotplug eth0
	iface eth0 inet manual

	auto wlan0
	allow-hotplug wlan0
	iface wlan0 inet dhcp
	wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
	wireless-power off

Here's another tweak for the power management configuration<br />
Create a new file:

	sudo nano /etc/modprobe.d/8192cu.conf

add

	options 8192cu rtw_power_mgnt=0 rtw_enusbss=0

then save and exit and reboot the pi.

The following should output 0 after reboot

	cat /sys/module/8192cu/parameters/rtw_power_mgnt



