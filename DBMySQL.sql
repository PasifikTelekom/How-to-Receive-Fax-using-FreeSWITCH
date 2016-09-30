-- ----------------------------
-- Table structure for `rss_faxes`
-- ----------------------------
DROP TABLE IF EXISTS `rss_faxes`;
CREATE TABLE `rss_faxes` (
  `id_fax` INT(8) NOT NULL AUTO_INCREMENT,
  `uuid` VARCHAR(255) NOT NULL,
  `caller_id` VARCHAR(255) NOT NULL,
  `remote_station` VARCHAR(255) NOT NULL,
  `local_station` VARCHAR(255) NOT NULL,
  `pages` VARCHAR(3) NOT NULL,
  `pages_total` VARCHAR(3) NOT NULL,
  `code` VARCHAR(255) NOT NULL,
  `date_received` datetime NOT NULL,
  PRIMARY KEY  (`id_fax`)
) ENGINE=MyISAM AUTO_INCREMENT=95 DEFAULT CHARSET=latin1;