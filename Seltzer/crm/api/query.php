<?php
////////////////////////////////
//This is the REST web service that will give back info from the Seltzer DB.
////////////////////////////////
//Altin Ukshini  altin.ukshini@gmail.com
//Created: Sep 20, 2015

// header("Content-Type:application/json");

include("functions.php"); // include functions

$possible_url = array(
  "getMemberInfoByRFID", 
  "getMemberLastPaymentTimestamp", 
  "getRFIDWhitelist", 
  "doorLockCheck", 
  "processCheckIn", 
  "hackerspaceStatus",
  "isUserCheckedIn"
);

if (isset($_GET["action"]) && in_array($_GET["action"], $possible_url))
{

  $value = "An error has occurred";

  switch ($_GET["action"])
	{
	  case "getMemberInfoByRFID":
		$value = getMemberInfoByRFID($_GET['rfid'], $_GET['fieldNames']);
		break;
	  case "getMemberLastPaymentTimestamp":
		$value = getMemberLastPaymentTimestamp($_GET['rfid']);
		break;
	  case "getRFIDWhitelist":
		$value = getRFIDWhitelist($_GET['fields']);
		break;
	  case "doorLockCheck":
		$value = doorLockCheck($_GET['rfid']);
		break;
	  case "processCheckIn":
		$value = processCheckIn($_GET['rfid']);
		break;
	  case "hackerspaceStatus":
		$value = hackerspaceStatus();
		break;
	  case "isUserCheckedIn":
		$value = isUserCheckedIn($_GET['rfid']);
		break;
	  case "get_app":
		if (isset($_GET["id"]))
		  $value = get_app_by_id($_GET["id"]);
		else
		  $value = "Missing argument";
		break;
	}

	//return JSON object as the response to client
	exit(json_encode($value));
}
else
{
  header("Location: "."http://www.google.com");
}
?>
