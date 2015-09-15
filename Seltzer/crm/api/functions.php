<?php 


include('db.inc.php');

//This function cleans the input from
// malicious strings and returns the clean
// version.  There might be a better way
// to do this but this works for the most
// part.  :/
function testInput($data) 
{
  $data = trim($data);
  $data = stripslashes($data);
  $data = htmlspecialchars($data);
  return $data;
}

//This function takes in an RFID alpha numeric string 
//and a comma separated list of field names to return.
//The RFID belongs to the member and the fields are the 
//ones you want to have back.
function getMemberInfoByRFID($rfid,$fieldNames)
{  
  global $con;
  
  $rfid = testInput($rfid);
  $fieldNames = testInput($fieldNames);
  
  $memberInfo = array();

  if($fieldNames == "")
  {
  	$fieldNames = "*";
  }

  //first build the query
  $query = "SELECT " . $fieldNames . " FROM 
			(
			`key` k
			LEFT JOIN  `contact` c ON k.cid = c.cid
			)
			WHERE k.serial = '" . $rfid . "'";
  
  //then get the matching member
  $result = mysqli_query($con, $query) 
		  or die(json_encode(array("getMemberInfoByRFIDQueryERROR" => mysql_error())));
 
  //then stick the member info into an assoc array
  $memberInfo = mysqli_fetch_assoc($result);    

  return $memberInfo;
}

//This function returns the unix timestamp of the last payment made
// for the member with the given RFID.
function getMemberLastPaymentTimestamp($rfid)
{ 
  global $con;
  
  $rfid = testInput($rfid);
  
  $memberInfo = array();

  //first see if the key is even in the system.
  //We could just do a big join all at once but we wouldn't know
  // if the key or the member was not found, etc.
  $query = "SELECT cid FROM `key` WHERE serial = '" . $rfid . "'";
  
  //then get the matching member
  $result = mysqli_query($con, $query) 
		  or die(json_encode(array("getKeyQueryERROR"=>mysql_error())));
		  
  $keyRow = mysqli_fetch_assoc($result);    

  if($keyRow == 0)
  {
  	return array("ERROR"=>"No key found for RFID: " . $rfid);
  }

  //then get the last payment entered for this member
  $query = "SELECT UNIX_TIMESTAMP(MAX(date)) FROM payment WHERE value > 0 and credit = " . $keyRow['cid'];
  
  $result = mysqli_query($con, $query) 
		  or die(json_encode(array("getPaymentQueryERROR"=>mysql_error())));
 
  $paymentInfo = mysqli_fetch_array($result);
  
  $timestamp = $paymentInfo[0];
  
  if($timestamp == NULL)
  {
  	return array("ERROR"=>"No payments found for key owner.");
  }
  
  $iso8601 = date('c', $timestamp);
  
  $jsonResponse = array("timestamp"=>$timestamp,"iso8601"=>$iso8601);
  return $jsonResponse;
}

//action=getRFIDWhitelist
//returns JSON array of all key serial values for all members who owe less than 2 months
// of their monthly plan's dues.
function getRFIDWhitelist()
{
	global $con;
	
	$whiteList = array();
	
	//get everyone's plan prices and balances and check here
	$balances = payment_accounts();
	foreach ($balances as $cid => $bal) {
		//now get this member's monthly plan amount
		$memberData = member_data(array("cid"=>$cid));
		$planAmount = $memberData[0]["membership"][0]["plan"]["price"];
		$firstName = $memberData[0]["contact"]["firstName"];
		$lastName = $memberData[0]["contact"]["lastName"];
		$memberBalance = $bal['value'] / 100;
        if ($memberBalance <= ($planAmount * 2) || $memberBalance == 0) {
            //this member has paid their dues. Add to whitelist.
            //get their key serial and add that too!
            $query = "SELECT serial FROM `key` WHERE char_length(serial) > 5 and cid = " . $cid;
            $result = mysqli_query($con, $query) 
		  		or die(json_encode(array("getRFIDWhitelistQueryERROR"=>mysqli_error($con))));
            $r = mysqli_fetch_assoc($result);
            $serial = $r["serial"];
            if ($serial != NULL)
            {
				$whiteList[] = array("firstName"=>$firstName,"lastName"=>$lastName,"serial"=>$serial);	
			}
        }
    }
	
	return $whiteList;
}

//action=doorLockCheck&rfid=<scanned RFID>
//returns JSON string TRUE if key owner has a balance less than 2 times
// their current montly plan price, FALSE or error string if not.
function doorLockCheck($rfid)
{
	global $con;
	
	$rfid = testInput($rfid);
	
	//get the key owner and their current membership plan
	$query = "SELECT c.cid, p.price
				FROM ((
				`key` k
				LEFT JOIN  `contact` c ON k.cid = c.cid
				)
				LEFT JOIN `membership` m ON m.cid = c.cid
				)
				LEFT JOIN `plan` p ON p.pid = m.pid
				where k.serial = '" . $rfid . "'";
				
	$result = mysqli_query($con, $query) 
		  or die(json_encode(array("doorLockCheckQueryERROR"=>mysqli_error($con))));
 
 	//if no rows returned then that key wasn't even found in the DB
 	if(mysqli_num_rows($result) == 0)
 	{
 		$jsonResponse = array("key " . $rfid . " not found in db");
	}
 	else
 	{		
	 	$row = mysqli_fetch_assoc($result); 	
	 	
	 	$memberID = $row["cid"];
	 	$planPrice = $row["price"];
		
		$accountData = payment_accounts(array("cid" => $memberID));
		//{"2":{"credit":"2","code":"USD","value":5000}}
		
		$memberBalance = $accountData[$memberID]["value"] / 100;
		
		//if the current key owner's balance is 
		// greater than 2 months of dues then access is denied!
		// Unless thier plan price is zero then 0 balance == 0 price is OK.
		if ($memberBalance > ($planPrice * 2) && $memberBalance > 0)
		{
			$jsonResponse = array("member balance = " . $memberBalance);
		}
		else
		{
			$jsonResponse = array("True");
		}
	}
	
	return $jsonResponse;
}



// ------------------------------------------------------------------------------ 
// 
// Checkin Process and Hackerspace Status functions
//
// ------------------------------------------------------------------------------


// GetActiveMembersNames
// This funcion gets a list of names that are in the hackerspace, basically all users that are checked in.
function getActiveMembersNames() 
{

	global $con;

	$query = "SELECT firstName FROM contact WHERE active = '1'";

  	$result = mysqli_query($con, $query) 
		  or die(json_encode(array("getActiveMembersNames" => mysql_error())));
  	$array = array();

	$i=0;
	while($row = mysqli_fetch_array($result)) {
	  $name = $row['firstName'];
	  $array[$i] = $name . ', ';
	  $i++;
	}

	$var="";
	for ($item=0 ; $item<$i ; $item++)
	{
	    $var.=$array[$item];
	}
	return $var;
}

// getActiveMembersTotal
// Gets a number of total active users / checked in users
function getActiveMembersTotal() 
{

	global $con;

	$query = "SELECT COUNT(*) AS count FROM contact WHERE active = '1'";

	//then get the matching members
  	$result = mysqli_query($con, $query) 
		  or die(json_encode(array("getActiveMembersTotal" => mysql_error())));

	$row = mysqli_fetch_array($result);

	return $row['count'];
}

// Create a log in the logs table when a member does a check in
function createLog($contactId, $currentDate) 
{

	global $con;

	$query = "INSERT INTO checkin_logs (lid, cid, check_in, check_out) VALUES ('', '$contactId', '$currentDate', '0000-00-00 00:00:00')";

	if (!mysqli_query($con,$query)) {
		return mysqli_error($con);
	}else{
		return true;
	}		

}

// Update a log in the logs table
// Close the log when member is checked out
function updateLog($contactId, $currentDate, $contactLastCheckinTime) 
{

	global $con;

	$query = "UPDATE checkin_logs SET check_out='$currentDate', log_closed=1 WHERE cid='$contactId' AND check_in='$contactLastCheckinTime'";

	if (!mysqli_query($con,$query)) {
		return mysqli_error($con);
	}else{
		return true;
	}		

}

// Update Contact in contact table
// Set them active or non active, and update the last checkin and last checkout time.
function updateContactCheckinStatus($date, $userId, $active) 
{

	global $con;

	if ($active == 1) {
		$query = "UPDATE contact SET active=$active, last_checkin_time='$date' WHERE cid='$userId'";
	}else{
	 	$query = "UPDATE contact SET active=$active, last_checkout_time='$date' WHERE cid='$userId'";
	}

	if (!mysqli_query($con,$query)) {
		return mysqli_error($con);
	}else{
		return true;
	}		
}


//action=isUserCheckedIn&rfid=<scanned RFID>
//returns JSON string True if member is checked in, False if checked out
function isUserCheckedIn($rfid)
{
	global $con;
	
	$rfid = testInput($rfid);
	
	$query = "SELECT contact.cid, `key`.serial, contact.active, contact.last_checkin_time, contact.last_checkout_time
				FROM contact
				INNER JOIN `key`
				ON contact.cid=`key`.cid
				WHERE serial = '" . $rfid . "'";
				
	$result = mysqli_query($con, $query) 
		  or die(json_encode(array("isUserCheckedInERROR"=>mysqli_error($con))));
 
 	//if no rows returned then that key wasn't even found in the DB
 	if(mysqli_num_rows($result) == 0)
 	{
 		$jsonResponse = array("key " . $rfid . " not found in db");
	}
 	else
 	{		
	 	$row = mysqli_fetch_assoc($result); 	
	 	
	 	$checkinStatus = $row["active"];

	 	if ($checkinStatus == 0) {
	 		$jsonResponse = array("False");
	 	}else{
	 		$jsonResponse = array("True");
	 	}
	}
	
	return $jsonResponse;
}


//action=processCheckIn&rfid=<scanned RFID>
// Process the checkin or checkout process, checks user in out.
function processCheckIn($rfid)
{

	$errors = 0;
	$processCheckInMessage = "";

	$rfid = testInput($rfid);
	$date = date('Y-m-d H:i:s');

	if (getMemberInfoByRFID($rfid, 'k.serial')["serial"] != null) {

		if (getMemberInfoByRFID($rfid, "c.active")["active"] == 0) { // check if user is active

			if (!createLog(getMemberInfoByRFID($rfid, "c.cid")["cid"], $date)) { // create a log with the current date
			  $errors = 1;
			  $processCheckInMessage .= 'Could not create a new log in the database!';
			  die();
			}else{
				if (!updateContactCheckinStatus($date, getMemberInfoByRFID($rfid, "c.cid")["cid"], 1)) { // update user table, set active to 1 and insert last checkin time

					$errors = 1;
					$processCheckInMessage .= 'Could not update member status when checking in!';
			  		die();
				}else{
					$processCheckInMessage .= "Checkin successful!";
				}
			}
			
		}else{

			if (!updateContactCheckinStatus($date, getMemberInfoByRFID($rfid, "c.cid")["cid"], 0)) { // update user table, set active to 0 and insert last checkout time
			  $errors = 1;
			  $processCheckInMessage .= 'Could not update member status when checking out!';
			  die();
			}else{
				if (!updateLog(getMemberInfoByRFID($rfid, "c.cid")["cid"], $date, getMemberInfoByRFID($rfid, "c.last_checkin_time")["last_checkin_time"])) { // close log, insert checkout time (current date time)
					$errors = 1;
					$processCheckInMessage .= 'Could not close the log for user check out!';
			  		die();
				}else{
					$processCheckInMessage .= "Checkout successful!";
				}
			}

		}
	
	}else{
		$errors = 1;
		$processCheckInMessage .= "RFID key not found in the database!";
	}


	if ($errors == 1) {
		$processCheckInMessage = 'ERROR: ' . $processCheckInMessage; // in case there are errors, add 'ERROR: ' at the beginning of a status message.
		$response['hasErrors'] = $errors;
		$response['message'] = $processCheckInMessage;
	}else{
		$response['hasErrors'] = $errors;
		$response['message'] = $processCheckInMessage;
		$response['firstName'] = getMemberInfoByRFID($rfid, 'c.firstName')["firstName"];
		$response['lastName'] = getMemberInfoByRFID($rfid, 'c.lastName')["lastName"];
		$response['lastCheckInTime'] = getMemberInfoByRFID($rfid, 'c.last_checkin_time')["last_checkin_time"];
		$response['lastCheckOutTime'] = getMemberInfoByRFID($rfid, 'c.last_checkout_time')["last_checkout_time"];
	}

	return $response;

}


function hackerspaceStatus()
{
    $names = Array('Goddesses on Throne', 'Aliens', 'Nyan cats', 'Unicorns', 'Capacitors', 'Ghosts', 'Resistors', 'Astronauts','Code Knights','Serfs','Guardians','Haluca');

    if ((int)getActiveMembersTotal() == 1) {

    	$message = getActiveMembersTotal().' Hacker and '.rand(2, 5).' '.$names[array_rand($names)].' in the space, means that the hackerspace is now open!';

    }elseif((int)getActiveMembersTotal() > 1){

		$message = getActiveMembersTotal().' Hackers and '.rand(2, 5).' '.$names[array_rand($names)].' in the space, means that the hackerspace is now open!';

    }else{

    	$message = '0 Hackers and '.rand(2, 5).' '.$names[array_rand($names)].'  in the space, means that the hackerspace is now closed!';

    }


	$response['hackersInSpace'] = (int)getActiveMembersTotal();
	$response['message'] = $message;
	$response['memberNames'] = getActiveMembersNames();

	return $response;

}

//////////////////////////////////////
//other functions for service go here. 
// don't forget to add the action to the 
// $possible_url array below!!!!!
//You will then have to add the entry for
// the switch case in query.php as well.
//////////////////////////////////////

?>