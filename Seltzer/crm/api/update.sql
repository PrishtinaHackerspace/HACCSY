--
-- Table structure for table `contact`
--

ALTER TABLE `contact`
  ADD `active` int(11) DEFAULT '0',
  ADD `last_checkin_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  ADD `last_checkout_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00';


--
-- Table structure for table `checkin_logs`
--

CREATE TABLE IF NOT EXISTS `checkin_logs` (
  `lid` int(11) NOT NULL AUTO_INCREMENT,
  `cid` int(11) NOT NULL,
  `check_in` timestamp NULL DEFAULT NULL,
  `check_out` timestamp NULL DEFAULT NULL,
  `log_closed` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`lid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;
