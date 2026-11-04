CREATE DATABASE IF NOT EXISTS `kiraya_db`;
USE `kiraya_db`;

-- MySQL dump 10.13  Distrib 26.10.0, for macos27.0 (arm64)
--
-- Host: localhost    Database: kiraya_db
-- ------------------------------------------------------
-- Server version	9.7.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `accounts_emailotpchallenge`
--

DROP TABLE IF EXISTS `accounts_emailotpchallenge`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_emailotpchallenge` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `otp_hash` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `expires_at` datetime(6) NOT NULL,
  `attempts` int unsigned NOT NULL,
  `max_attempts` int unsigned NOT NULL,
  `is_consumed` tinyint(1) NOT NULL,
  `consumed_at` datetime(6) DEFAULT NULL,
  `ip_address` char(39) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_agent` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_emailotpchallenge_user_id_941c82f0_fk_auth_user_id` (`user_id`),
  KEY `accounts_emailotpchallenge_email_d6213b91` (`email`),
  KEY `accounts_emailotpchallenge_created_at_2d610cf7` (`created_at`),
  KEY `accounts_emailotpchallenge_expires_at_fae3c81c` (`expires_at`),
  KEY `accounts_emailotpchallenge_is_consumed_1679b1cd` (`is_consumed`),
  KEY `accounts_em_email_f4d9fa_idx` (`email`,`is_consumed`,`created_at` DESC),
  CONSTRAINT `accounts_emailotpchallenge_user_id_941c82f0_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `accounts_emailotpchallenge_chk_1` CHECK ((`attempts` >= 0)),
  CONSTRAINT `accounts_emailotpchallenge_chk_2` CHECK ((`max_attempts` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_emailotpchallenge`
--

LOCK TABLES `accounts_emailotpchallenge` WRITE;
/*!40000 ALTER TABLE `accounts_emailotpchallenge` DISABLE KEYS */;
INSERT INTO `accounts_emailotpchallenge` VALUES (3,'abhishekmewada6262@gmail.com','aac487cb537daebf2123863053abd8383d852af40b5085cadac666dd2dfe892b','2026-10-27 07:40:30.014173','2026-10-27 07:50:30.013923',3,5,1,'2026-10-27 07:41:39.795055','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36',7),(4,'shubham.desai147@gmail.com','a463a59c3901d7cc8263a9e40fa656cdb930ffb92f1d0e43f22bcd609a32a5f9','2026-10-27 08:08:05.138164','2026-10-27 08:18:05.137994',0,5,1,'2026-10-27 08:08:38.546055','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36',8),(5,'saloniberwal@gmail.com','715cf9978e92d098735572961c9ac86a8c7fb3c06c248982543c39a9b65a5145','2026-10-27 09:29:35.051510','2026-10-27 09:39:35.051373',0,5,1,'2026-10-27 09:29:59.284896','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36',9),(11,'pallaviberwal007@gmail.com','6e8280c6afff8bb776867465b71f2d125a3a0b0ff765866a12c9b0df4a201106','2026-10-27 14:32:07.865906','2026-10-27 14:42:07.865751',0,5,1,'2026-10-27 14:32:56.071799','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36',15),(12,'gouravberwal0001@gmail.com','766c35d3ebe63feb657d877463d9ff3fbc0953c80505de62200aea2e01f662db','2026-10-28 05:49:37.673712','2026-10-28 05:59:37.673504',0,5,1,'2026-10-28 05:50:27.719784','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36',16),(13,'siddharthgnigam@gmail.com','e3fffe8c79ce4ae077889e296f4ff73410faf11b79b00087cbd52e90fca7b2b4','2026-10-29 10:10:43.319544','2026-10-29 10:20:43.319379',0,5,0,NULL,'127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36',17),(14,'siddharthjinigam@gmail.com','742d916453479932f323a4cc9c08406b8ee44e72a563682e0afd64e1a3e828cc','2026-10-29 10:11:45.575451','2026-10-29 10:21:45.575337',0,5,1,'2026-10-29 10:12:52.834270','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36',18);
/*!40000 ALTER TABLE `accounts_emailotpchallenge` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_ownerauditlog`
--

DROP TABLE IF EXISTS `accounts_ownerauditlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_ownerauditlog` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `action` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `notes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip_address` char(39) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `owner_id` int NOT NULL,
  `performed_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_ownerauditlog_owner_id_9cc262a5_fk_auth_user_id` (`owner_id`),
  KEY `accounts_ownerauditlog_performed_by_id_42f88bba_fk_auth_user_id` (`performed_by_id`),
  KEY `accounts_ownerauditlog_action_bbd800e4` (`action`),
  KEY `accounts_ownerauditlog_created_at_bfa81b06` (`created_at`),
  CONSTRAINT `accounts_ownerauditlog_owner_id_9cc262a5_fk_auth_user_id` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `accounts_ownerauditlog_performed_by_id_42f88bba_fk_auth_user_id` FOREIGN KEY (`performed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_ownerauditlog`
--

LOCK TABLES `accounts_ownerauditlog` WRITE;
/*!40000 ALTER TABLE `accounts_ownerauditlog` DISABLE KEYS */;
INSERT INTO `accounts_ownerauditlog` VALUES (1,'REQUEST_SUBMITTED','Submitted verification request #1 for property \'Rosewood Hostel\'.','127.0.0.1','2026-10-27 09:31:22.365496',9,9),(2,'REVOKED','Rejected owner account / Revoked access. Reason: Electricity bill is blurred and property ownership title deed is missing.','127.0.0.1','2026-10-27 09:55:53.448060',2,1),(3,'REVOKED','Rejected owner account / Revoked access. Reason: Electricity bill is blurred and property ownership title deed is missing.','127.0.0.1','2026-10-27 09:57:35.244767',2,1),(4,'SUSPENDED','Put owner access on hold/suspended. Reason: Please upload an updated municipal property tax receipt for FY 2025-26.','127.0.0.1','2026-10-27 09:57:39.042173',2,1),(5,'REVOKED','Rejected owner account / Revoked access. Reason: Electricity bill is blurred and property ownership title deed is missing.','127.0.0.1','2026-10-27 09:58:40.108473',2,1),(6,'SUSPENDED','Put owner access on hold/suspended. Reason: Please upload an updated municipal property tax receipt for FY 2025-26.','127.0.0.1','2026-10-27 09:58:44.014242',2,1),(7,'APPROVED','Directly granted owner access by administrator.','127.0.0.1','2026-10-27 09:58:47.854008',2,1),(9,'APPROVED','Approved verification request #11 for property \'Pallavi\'s Property\'.','127.0.0.1','2026-10-27 14:39:59.417058',15,1),(10,'APPROVED','Approved verification request #12 for property \'test\'s Property\'.','127.0.0.1','2026-10-28 05:51:22.265077',16,1),(11,'APPROVED','Approved verification request #13 for property \'siddarthnigam\'s Property\'.','127.0.0.1','2026-10-29 10:13:50.019063',18,1);
/*!40000 ALTER TABLE `accounts_ownerauditlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_ownerprofile`
--

DROP TABLE IF EXISTS `accounts_ownerprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_ownerprofile` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `email_verified` tinyint(1) NOT NULL,
  `verified_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  `access_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `approval_status` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `approved_at` datetime(6) DEFAULT NULL,
  `approved_by_id` int DEFAULT NULL,
  `internal_notes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `owner_facing_message` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `revocation_reason` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `revoked_at` datetime(6) DEFAULT NULL,
  `suspended_at` datetime(6) DEFAULT NULL,
  `suspension_reason` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `accounts_ownerprofile_email_verified_d08338ca` (`email_verified`),
  KEY `accounts_ownerprofile_approved_by_id_cfec46ab_fk_auth_user_id` (`approved_by_id`),
  KEY `accounts_ownerprofile_access_status_44d67836` (`access_status`),
  KEY `accounts_ownerprofile_approval_status_ac4759a6` (`approval_status`),
  CONSTRAINT `accounts_ownerprofile_approved_by_id_cfec46ab_fk_auth_user_id` FOREIGN KEY (`approved_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `accounts_ownerprofile_user_id_7215f44d_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_ownerprofile`
--

LOCK TABLES `accounts_ownerprofile` WRITE;
/*!40000 ALTER TABLE `accounts_ownerprofile` DISABLE KEYS */;
INSERT INTO `accounts_ownerprofile` VALUES (1,1,'2026-10-27 06:26:03.063657','2026-10-27 06:26:03.068054','2026-10-27 06:26:03.068061',1,'ACTIVE','APPROVED',NULL,NULL,'','','',NULL,NULL,''),(2,1,'2026-10-27 06:26:03.063657','2026-10-27 06:26:03.070340','2026-10-27 09:58:47.852244',2,'ACTIVE','APPROVED','2026-10-27 09:58:47.852182',1,'','All documents verified and compliant.','Electricity bill is blurred and property ownership title deed is missing.','2026-10-27 09:58:40.098722','2026-10-27 09:58:44.012242','Please upload an updated municipal property tax receipt for FY 2025-26.'),(3,1,'2026-10-27 06:26:03.063657','2026-10-27 06:26:03.071619','2026-10-27 06:26:03.071623',3,'ACTIVE','APPROVED',NULL,NULL,'','','',NULL,NULL,''),(4,1,'2026-10-27 06:26:03.063657','2026-10-27 06:26:03.072358','2026-10-27 06:26:03.072361',4,'ACTIVE','APPROVED',NULL,NULL,'','','',NULL,NULL,''),(5,1,'2026-10-27 06:26:03.063657','2026-10-27 06:26:03.073078','2026-10-27 06:26:03.073082',5,'ACTIVE','APPROVED',NULL,NULL,'','','',NULL,NULL,''),(7,1,'2026-10-27 07:41:39.801751','2026-10-27 07:40:30.008931','2026-10-27 07:40:30.011182',7,'ACTIVE','APPROVED',NULL,NULL,'','','',NULL,NULL,''),(8,1,'2026-10-27 08:08:38.558384','2026-10-27 08:08:05.129962','2026-10-27 08:08:05.134788',8,'ACTIVE','APPROVED',NULL,NULL,'','','',NULL,NULL,''),(9,1,'2026-10-27 09:29:59.292507','2026-10-27 09:29:35.047985','2026-10-27 09:31:22.364179',9,'ACTIVE','PENDING',NULL,NULL,'','Your property verification request is under review.','',NULL,NULL,''),(15,1,'2026-10-27 14:32:56.085652','2026-10-27 14:32:07.855635','2026-10-27 14:39:59.415923',15,'ACTIVE','APPROVED','2026-10-27 14:39:59.415812',1,'Processed by gurjar','Your property verification has been approved.','',NULL,NULL,''),(16,1,'2026-10-28 05:50:27.739367','2026-10-28 05:49:37.662374','2026-10-28 05:51:22.263269',16,'ACTIVE','APPROVED','2026-10-28 05:51:22.263173',1,'Processed by gurjar','Your property verification has been approved.','',NULL,NULL,''),(17,0,NULL,'2026-10-29 10:10:43.303009','2026-10-29 10:10:43.303016',17,'ACTIVE','NOT_SUBMITTED',NULL,NULL,'','','',NULL,NULL,''),(18,1,'2026-10-29 10:12:52.841670','2026-10-29 10:11:45.570678','2026-10-29 10:13:50.017277',18,'ACTIVE','APPROVED','2026-10-29 10:13:50.017202',1,'Processed by gurjar','Your property verification has been approved.','',NULL,NULL,'');
/*!40000 ALTER TABLE `accounts_ownerprofile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_ownerverificationrequest`
--

DROP TABLE IF EXISTS `accounts_ownerverificationrequest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_ownerverificationrequest` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `property_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `address` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `city` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `state` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `postal_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `property_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `relationship` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ownership_proof` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `utility_bill` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `authorization_letter` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `notes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `submitted_at` datetime(6) NOT NULL,
  `reviewed_at` datetime(6) DEFAULT NULL,
  `owner_facing_message` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `internal_notes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `rejection_reason` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `owner_id` int NOT NULL,
  `reviewed_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_ownerverifi_reviewed_by_id_416a6312_fk_auth_user` (`reviewed_by_id`),
  KEY `accounts_ownerverificationrequest_status_c099a314` (`status`),
  KEY `accounts_ownerverificationrequest_submitted_at_c4d513b9` (`submitted_at`),
  KEY `accounts_ow_owner_i_1eaa84_idx` (`owner_id`,`status`,`submitted_at` DESC),
  CONSTRAINT `accounts_ownerverifi_owner_id_72ee9daf_fk_auth_user` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `accounts_ownerverifi_reviewed_by_id_416a6312_fk_auth_user` FOREIGN KEY (`reviewed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_ownerverificationrequest`
--

LOCK TABLES `accounts_ownerverificationrequest` WRITE;
/*!40000 ALTER TABLE `accounts_ownerverificationrequest` DISABLE KEYS */;
INSERT INTO `accounts_ownerverificationrequest` VALUES (1,'Rosewood Hostel','Chandigarh Group Of Colleges Jhanjeri','Mohali','Punjab','140307','HOSTEL','OWNER','verification_documents/b48ec40f79f544eba82ba18f3a47050c.pdf','','','','PENDING','2026-10-27 09:31:22.359308',NULL,'','','',9,NULL),(2,'kiraya_owner01\'s Property','Registered Owner Property','Indore','Madhya Pradesh','452001','BUILDING','OWNER','','','','','APPROVED','2026-10-27 09:40:02.106458','2026-10-27 09:58:47.853134','Your property verification request has been approved.','','Electricity bill is blurred and property ownership title deed is missing.',2,1),(3,'Gourav\'s Property','Registered Owner Property','Indore','Madhya Pradesh','452001','BUILDING','OWNER','','','','','APPROVED','2026-10-27 09:40:02.110743',NULL,'','','',3,NULL),(4,'gurjar1\'s Property','Registered Owner Property','Indore','Madhya Pradesh','452001','BUILDING','OWNER','','','','','APPROVED','2026-10-27 09:40:02.115247',NULL,'','','',4,NULL),(5,'mohit\'s Property','Registered Owner Property','Indore','Madhya Pradesh','452001','BUILDING','OWNER','','','','','APPROVED','2026-10-27 09:40:02.118547',NULL,'','','',5,NULL),(6,'Abhishek\'s Property','Registered Owner Property','Indore','Madhya Pradesh','452001','BUILDING','OWNER','','','','','APPROVED','2026-10-27 09:40:02.121311',NULL,'','','',7,NULL),(7,'Shubham\'s Property','Registered Owner Property','Indore','Madhya Pradesh','452001','BUILDING','OWNER','','','','','APPROVED','2026-10-27 09:40:02.123634',NULL,'','','',8,NULL),(11,'Pallavi\'s Property','Submitted via Owner Registration','Indore','Madhya Pradesh','452001','BUILDING','OWNER','','','','Automatically created upon email OTP verification.','APPROVED','2026-10-27 14:32:56.089187','2026-10-27 14:39:59.410139','Your property verification has been approved.','Processed by gurjar','',15,1),(12,'test\'s Property','Submitted via Owner Registration','Indore','Madhya Pradesh','452001','BUILDING','OWNER','','','','Automatically created upon email OTP verification.','APPROVED','2026-10-28 05:50:27.742483','2026-10-28 05:51:22.257069','Your property verification has been approved.','Processed by gurjar','',16,1),(13,'siddarthnigam\'s Property','Submitted via Owner Registration','Indore','Madhya Pradesh','452001','BUILDING','OWNER','','','','Automatically created upon email OTP verification.','APPROVED','2026-10-29 10:12:52.845643','2026-10-29 10:13:50.009155','Your property verification has been approved.','Processed by gurjar','',18,1);
/*!40000 ALTER TABLE `accounts_ownerverificationrequest` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=97 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',3,'add_permission'),(6,'Can change permission',3,'change_permission'),(7,'Can delete permission',3,'delete_permission'),(8,'Can view permission',3,'view_permission'),(9,'Can add group',2,'add_group'),(10,'Can change group',2,'change_group'),(11,'Can delete group',2,'delete_group'),(12,'Can view group',2,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add property',7,'add_property'),(26,'Can change property',7,'change_property'),(27,'Can delete property',7,'delete_property'),(28,'Can view property',7,'view_property'),(29,'Can add room',8,'add_room'),(30,'Can change room',8,'change_room'),(31,'Can delete room',8,'delete_room'),(32,'Can view room',8,'view_room'),(33,'Can add tenant',9,'add_tenant'),(34,'Can change tenant',9,'change_tenant'),(35,'Can delete tenant',9,'delete_tenant'),(36,'Can view tenant',9,'view_tenant'),(37,'Can add rental agreement',10,'add_rentalagreement'),(38,'Can change rental agreement',10,'change_rentalagreement'),(39,'Can delete rental agreement',10,'delete_rentalagreement'),(40,'Can view rental agreement',10,'view_rentalagreement'),(41,'Can add rent record',11,'add_rentrecord'),(42,'Can change rent record',11,'change_rentrecord'),(43,'Can delete rent record',11,'delete_rentrecord'),(44,'Can view rent record',11,'view_rentrecord'),(45,'Can add electricity meter',13,'add_electricitymeter'),(46,'Can change electricity meter',13,'change_electricitymeter'),(47,'Can delete electricity meter',13,'delete_electricitymeter'),(48,'Can view electricity meter',13,'view_electricitymeter'),(49,'Can add meter reading',14,'add_meterreading'),(50,'Can change meter reading',14,'change_meterreading'),(51,'Can delete meter reading',14,'delete_meterreading'),(52,'Can view meter reading',14,'view_meterreading'),(53,'Can add electricity bill',12,'add_electricitybill'),(54,'Can change electricity bill',12,'change_electricitybill'),(55,'Can delete electricity bill',12,'delete_electricitybill'),(56,'Can view electricity bill',12,'view_electricitybill'),(57,'Can add payment',15,'add_payment'),(58,'Can change payment',15,'change_payment'),(59,'Can delete payment',15,'delete_payment'),(60,'Can view payment',15,'view_payment'),(61,'Can add notification',16,'add_notification'),(62,'Can change notification',16,'change_notification'),(63,'Can delete notification',16,'delete_notification'),(64,'Can view notification',16,'view_notification'),(65,'Can add Workspace Settings',17,'add_workspacesettings'),(66,'Can change Workspace Settings',17,'change_workspacesettings'),(67,'Can delete Workspace Settings',17,'delete_workspacesettings'),(68,'Can view Workspace Settings',17,'view_workspacesettings'),(69,'Can add billing archive',18,'add_billingarchive'),(70,'Can change billing archive',18,'change_billingarchive'),(71,'Can delete billing archive',18,'delete_billingarchive'),(72,'Can view billing archive',18,'view_billingarchive'),(73,'Can add Email OTP Challenge',19,'add_emailotpchallenge'),(74,'Can change Email OTP Challenge',19,'change_emailotpchallenge'),(75,'Can delete Email OTP Challenge',19,'delete_emailotpchallenge'),(76,'Can view Email OTP Challenge',19,'view_emailotpchallenge'),(77,'Can add Owner Profile',20,'add_ownerprofile'),(78,'Can change Owner Profile',20,'change_ownerprofile'),(79,'Can delete Owner Profile',20,'delete_ownerprofile'),(80,'Can view Owner Profile',20,'view_ownerprofile'),(81,'Can add Owner Audit Log',21,'add_ownerauditlog'),(82,'Can change Owner Audit Log',21,'change_ownerauditlog'),(83,'Can delete Owner Audit Log',21,'delete_ownerauditlog'),(84,'Can view Owner Audit Log',21,'view_ownerauditlog'),(85,'Can add Owner Verification Request',22,'add_ownerverificationrequest'),(86,'Can change Owner Verification Request',22,'change_ownerverificationrequest'),(87,'Can delete Owner Verification Request',22,'delete_ownerverificationrequest'),(88,'Can view Owner Verification Request',22,'view_ownerverificationrequest'),(89,'Can add owner qr config',23,'add_ownerqrconfig'),(90,'Can change owner qr config',23,'change_ownerqrconfig'),(91,'Can delete owner qr config',23,'delete_ownerqrconfig'),(92,'Can view owner qr config',23,'view_ownerqrconfig'),(93,'Can add tenant qr assignment',24,'add_tenantqrassignment'),(94,'Can change tenant qr assignment',24,'change_tenantqrassignment'),(95,'Can delete tenant qr assignment',24,'delete_tenantqrassignment'),(96,'Can view tenant qr assignment',24,'view_tenantqrassignment');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `first_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$1500000$tbYlteYW709sx30Sjh2d7T$RNa6sx/ymrTCNXeqR47aQ/NmmbaBnWWhnDGtg/NpVFI=','2026-11-02 06:48:48.412066',1,'gurjar','Gourav','Gurjar','gouravberwal003@gmail.com',1,1,'2026-10-22 10:47:26.504330'),(2,'pbkdf2_sha256$1500000$DurE5Z64WuGIO85K7I4rPS$znMKrHHcDQiRg4E5UELa+D1OHZLYe8h5TRE9TCmP8o0=','2026-10-23 02:27:01.239805',0,'kiraya_owner01','','','owner01@example.com',0,1,'2026-10-23 01:55:37.269414'),(3,'pbkdf2_sha256$1200000$TupMjPStLme3YNwDXZM3k2$irIat7xCh15JSOaIC0j/WBtFatO4R+CyKD+pW5tHe2s=','2026-10-23 07:40:43.205388',0,'Gourav','','','gouravpc88@gmail.com',0,1,'2026-10-23 07:40:42.579400'),(4,'pbkdf2_sha256$1500000$QlubCFjWLqoxd4fgn3K6JY$z6jOc4w5ybrLn+jE2HMZmQ6ETYyCuU/yJEMkCKCIWdM=','2026-10-23 08:10:10.092658',0,'gurjar1','','','owner@example.com',0,1,'2026-10-23 08:10:09.695674'),(5,'pbkdf2_sha256$1500000$jPp1s5AVeUxXYIHBtVa7lW$Mixd/pp4OihbroiQ5GsBNBvyHTF+9YVC1Ep7Bn2L59Y=','2026-11-02 06:38:48.101063',0,'mohit','','','mohitgurjar8088@gmail.com',0,1,'2026-10-23 11:55:51.865050'),(7,'pbkdf2_sha256$1500000$0HF7exqLnB0YRLqIrWRqX7$JtzGrav9DDu+5naXnkb/De3XbWbZ/TUg+AACuPDO23U=','2026-10-27 08:06:44.299076',0,'Abhishek','','','abhishekmewada6262@gmail.com',0,1,'2026-10-27 07:40:29.643121'),(8,'pbkdf2_sha256$1500000$S0ZHNGCQGQaJsP9rqyOZ3q$pjAmKR5a4HpnjNudBU6cINzileID52Zz3oH6d+Rwxb8=','2026-10-27 08:08:38.563057',0,'Shubham','','','shubham.desai147@gmail.com',0,1,'2026-10-27 08:08:04.763659'),(9,'pbkdf2_sha256$1500000$luP32r8jdqeRwAdr9ZSJEv$N0T8PRD/VOpRVTY3AyBtNezqnhJ/d4QhsAtaIsy8sk0=','2026-10-27 09:29:59.295400',0,'Saloni','','','saloniberwal@gmail.com',0,1,'2026-10-27 09:29:34.688095'),(15,'pbkdf2_sha256$1500000$Lt134CN0mAO9PGjtNI0zB6$Z+9IzBvU74FRd+0EH2zK6gcaMK8NbV2/s0EYsrBNpJY=','2026-10-27 14:40:31.795158',0,'Pallavi','','','pallaviberwal007@gmail.com',0,1,'2026-10-27 14:32:07.488739'),(16,'pbkdf2_sha256$1500000$oPsd0ySi2tsfbmA3CRH7jn$3YxolhdJ1rcqbQc/tIAkbHFa0AVc0HN7IopxAIzzyRs=','2026-10-29 08:30:54.919697',0,'test','','','gouravberwal0001@gmail.com',0,1,'2026-10-28 05:49:37.291152'),(17,'pbkdf2_sha256$1500000$Pz5mc4eBOgvq44wubPQM1x$5OB6vbm5oxrBiIB0pTvJZ3xCB5NHJeowkXXE/3avtLg=',NULL,0,'Siddarth','','','siddharthgnigam@gmail.com',0,0,'2026-10-29 10:10:42.930854'),(18,'pbkdf2_sha256$1500000$E6GGBu4BolgsyQT4Vxb2Jz$++afuYbySk78rsUvUCPkEe6YNcBWmAE6GoxOdwC2Hig=','2026-11-02 12:29:55.210705',0,'siddarthnigam','','','siddharthjinigam@gmail.com',0,1,'2026-10-29 10:11:45.194182');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `billing_billingarchive`
--

DROP TABLE IF EXISTS `billing_billingarchive`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `billing_billingarchive` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `billing_month` date NOT NULL,
  `total_tenants` int unsigned NOT NULL,
  `total_billed` decimal(12,2) NOT NULL,
  `total_paid` decimal(12,2) NOT NULL,
  `total_balance` decimal(12,2) NOT NULL,
  `archived_at` datetime(6) NOT NULL,
  `snapshot_data` json NOT NULL,
  `notes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `owner_id` int NOT NULL,
  `property_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `billing_billingarchive_owner_id_a1b5e991_fk_auth_user_id` (`owner_id`),
  KEY `billing_billingarchi_property_id_83696f86_fk_propertie` (`property_id`),
  CONSTRAINT `billing_billingarchi_property_id_83696f86_fk_propertie` FOREIGN KEY (`property_id`) REFERENCES `properties_property` (`id`),
  CONSTRAINT `billing_billingarchive_owner_id_a1b5e991_fk_auth_user_id` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `billing_billingarchive_chk_1` CHECK ((`total_tenants` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `billing_billingarchive`
--

LOCK TABLES `billing_billingarchive` WRITE;
/*!40000 ALTER TABLE `billing_billingarchive` DISABLE KEYS */;
INSERT INTO `billing_billingarchive` VALUES (1,'2026-10-01',2,5001.00,1.00,5000.00,'2026-10-27 02:28:52.847420','[{\"balance\": \"5000.00\", \"room_id\": 1, \"due_date\": \"2026-10-05\", \"record_id\": 2, \"rent_paid\": \"0.00\", \"tenant_id\": 1, \"total_paid\": \"0.00\", \"property_id\": 1, \"rent_amount\": \"5000.00\", \"rent_status\": \"OVERDUE\", \"room_number\": \"1\", \"tenant_name\": \"Rahul Sharma\", \"meter_number\": \"MTR-1\", \"rent_balance\": \"5000.00\", \"tenant_phone\": \"9876543210\", \"total_billed\": \"5000.00\", \"billing_month\": \"2026-10-01\", \"property_name\": \"Sunrise Hostel\", \"rate_per_unit\": \"12.00\", \"units_consumed\": \"0.00\", \"current_reading\": \"0.00\", \"electricity_paid\": \"0.00\", \"previous_reading\": \"0.00\", \"electricity_amount\": \"0.00\", \"electricity_status\": \"N/A\"}, {\"balance\": \"0.00\", \"room_id\": 2, \"due_date\": \"2026-10-05\", \"record_id\": 3, \"rent_paid\": \"1.00\", \"tenant_id\": 6, \"total_paid\": \"1.00\", \"property_id\": 1, \"rent_amount\": \"1.00\", \"rent_status\": \"PAID\", \"room_number\": \"2\", \"tenant_name\": \"Gourav Berwal\", \"meter_number\": \"MTR-2\", \"rent_balance\": \"0.00\", \"tenant_phone\": \"6262593646\", \"total_billed\": \"1.00\", \"billing_month\": \"2026-10-01\", \"property_name\": \"Sunrise Hostel\", \"rate_per_unit\": \"12.00\", \"units_consumed\": \"0.00\", \"current_reading\": \"0.00\", \"electricity_paid\": \"0.00\", \"previous_reading\": \"0.00\", \"electricity_amount\": \"0.00\", \"electricity_status\": \"N/A\"}]','',1,NULL);
/*!40000 ALTER TABLE `billing_billingarchive` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `billing_ownerqrconfig`
--

DROP TABLE IF EXISTS `billing_ownerqrconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `billing_ownerqrconfig` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `label` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `payee_name` varchar(160) COLLATE utf8mb4_unicode_ci NOT NULL,
  `upi_id` varchar(160) COLLATE utf8mb4_unicode_ci NOT NULL,
  `qr_image_data_url` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `property_name` varchar(160) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `owner_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_owner_qr_profile_label` (`owner_id`,`label`),
  CONSTRAINT `billing_ownerqrconfig_owner_id_fb763f97_fk_auth_user_id` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `billing_ownerqrconfig`
--

LOCK TABLES `billing_ownerqrconfig` WRITE;
/*!40000 ALTER TABLE `billing_ownerqrconfig` DISABLE KEYS */;
INSERT INTO `billing_ownerqrconfig` VALUES (1,'Qr','Goldy','712882701@ybl','','','2026-10-28 11:13:37.490192','2026-10-28 11:13:37.490205',1);
/*!40000 ALTER TABLE `billing_ownerqrconfig` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `billing_rentrecord`
--

DROP TABLE IF EXISTS `billing_rentrecord`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `billing_rentrecord` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `billing_month` date NOT NULL,
  `rent_amount` decimal(10,2) NOT NULL,
  `due_date` date NOT NULL,
  `amount_paid` decimal(10,2) NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `notes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `agreement_id` bigint NOT NULL,
  `archived_at` datetime(6) DEFAULT NULL,
  `is_archived` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_rent_record_per_month` (`agreement_id`,`billing_month`),
  CONSTRAINT `billing_rentrecord_agreement_id_d73d86e6_fk_tenants_r` FOREIGN KEY (`agreement_id`) REFERENCES `tenants_rentalagreement` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `billing_rentrecord`
--

LOCK TABLES `billing_rentrecord` WRITE;
/*!40000 ALTER TABLE `billing_rentrecord` DISABLE KEYS */;
INSERT INTO `billing_rentrecord` VALUES (1,'2026-10-22',5000.00,'2026-10-27',5000.00,'PAID','uiuhqdwo','2026-10-22 13:26:16.060393','2026-10-27 13:47:19.032710',1,NULL,0),(2,'2026-10-01',5000.00,'2026-10-05',5000.00,'PAID','','2026-10-22 15:19:10.948038','2026-10-27 13:47:00.831115',1,'2026-10-27 02:28:52.819878',1),(3,'2026-10-01',1.00,'2026-10-05',1201.00,'PAID','Initial rent bill created upon tenant onboarding','2026-10-26 07:58:08.887907','2026-10-27 04:53:18.786293',3,'2026-10-27 02:28:52.819878',1),(4,'2026-10-01',10000.00,'2026-10-05',0.00,'PENDING','Initial rent bill created upon tenant onboarding','2026-10-28 05:57:24.749108','2026-10-29 05:57:59.244360',4,NULL,0),(5,'2026-10-01',2500.00,'2026-10-07',0.00,'PENDING','Initial rent bill created upon tenant onboarding','2026-10-29 15:00:35.232531','2026-10-29 15:02:46.957069',6,NULL,0),(6,'2026-10-01',2500.00,'2026-10-07',2500.00,'PAID','Initial rent bill created upon tenant onboarding','2026-10-29 15:01:33.564417','2026-10-29 15:02:48.137791',7,NULL,0);
/*!40000 ALTER TABLE `billing_rentrecord` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `billing_tenantqrassignment`
--

DROP TABLE IF EXISTS `billing_tenantqrassignment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `billing_tenantqrassignment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint unsigned NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `owner_id` int NOT NULL,
  `qr_config_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_owner_tenant_qr_assignment` (`owner_id`,`tenant_id`),
  KEY `billing_tenantqrassi_qr_config_id_1be754e1_fk_billing_o` (`qr_config_id`),
  CONSTRAINT `billing_tenantqrassi_qr_config_id_1be754e1_fk_billing_o` FOREIGN KEY (`qr_config_id`) REFERENCES `billing_ownerqrconfig` (`id`),
  CONSTRAINT `billing_tenantqrassignment_owner_id_f44a03af_fk_auth_user_id` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `billing_tenantqrassignment_chk_1` CHECK ((`tenant_id` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `billing_tenantqrassignment`
--

LOCK TABLES `billing_tenantqrassignment` WRITE;
/*!40000 ALTER TABLE `billing_tenantqrassignment` DISABLE KEYS */;
INSERT INTO `billing_tenantqrassignment` VALUES (1,1,'2026-10-28 11:13:37.640011','2026-10-28 11:13:37.640026',1,1);
/*!40000 ALTER TABLE `billing_tenantqrassignment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext COLLATE utf8mb4_unicode_ci,
  `object_repr` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2026-10-22 13:24:00.109605','1','Sunrise Hostel - Room 1',1,'[{\"added\": {}}]',8,1);
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `model` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (19,'accounts','emailotpchallenge'),(21,'accounts','ownerauditlog'),(20,'accounts','ownerprofile'),(22,'accounts','ownerverificationrequest'),(1,'admin','logentry'),(2,'auth','group'),(3,'auth','permission'),(4,'auth','user'),(18,'billing','billingarchive'),(23,'billing','ownerqrconfig'),(11,'billing','rentrecord'),(24,'billing','tenantqrassignment'),(5,'contenttypes','contenttype'),(12,'electricity','electricitybill'),(13,'electricity','electricitymeter'),(14,'electricity','meterreading'),(16,'notifications','notification'),(15,'payments','payment'),(7,'properties','property'),(8,'properties','room'),(17,'properties','workspacesettings'),(6,'sessions','session'),(10,'tenants','rentalagreement'),(9,'tenants','tenant');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-10-22 10:35:01.301470'),(2,'auth','0001_initial','2026-10-22 10:35:01.425923'),(3,'admin','0001_initial','2026-10-22 10:35:01.461534'),(4,'admin','0002_logentry_remove_auto_add','2026-10-22 10:35:01.464364'),(5,'admin','0003_logentry_add_action_flag_choices','2026-10-22 10:35:01.466674'),(6,'contenttypes','0002_remove_content_type_name','2026-10-22 10:35:01.491758'),(7,'auth','0002_alter_permission_name_max_length','2026-10-22 10:35:01.505894'),(8,'auth','0003_alter_user_email_max_length','2026-10-22 10:35:01.515725'),(9,'auth','0004_alter_user_username_opts','2026-10-22 10:35:01.518470'),(10,'auth','0005_alter_user_last_login_null','2026-10-22 10:35:01.528813'),(11,'auth','0006_require_contenttypes_0002','2026-10-22 10:35:01.529349'),(12,'auth','0007_alter_validators_add_error_messages','2026-10-22 10:35:01.531635'),(13,'auth','0008_alter_user_username_max_length','2026-10-22 10:35:01.545195'),(14,'auth','0009_alter_user_last_name_max_length','2026-10-22 10:35:01.558716'),(15,'auth','0010_alter_group_name_max_length','2026-10-22 10:35:01.567015'),(16,'auth','0011_update_proxy_permissions','2026-10-22 10:35:01.569949'),(17,'auth','0012_alter_user_first_name_max_length','2026-10-22 10:35:01.587129'),(18,'sessions','0001_initial','2026-10-22 10:35:01.596199'),(19,'properties','0001_initial','2026-10-22 10:39:19.146802'),(20,'properties','0002_room','2026-10-22 10:41:09.003845'),(21,'tenants','0001_initial','2026-10-22 10:44:44.801680'),(22,'tenants','0002_rentalagreement','2026-10-22 10:51:46.828167'),(23,'billing','0001_initial','2026-10-22 10:56:53.366357'),(24,'electricity','0001_initial','2026-10-22 11:03:55.638672'),(25,'payments','0001_initial','2026-10-22 11:10:42.930134'),(26,'billing','0002_alter_rentrecord_options','2026-10-22 15:18:10.159128'),(27,'notifications','0001_initial','2026-10-22 16:22:16.843129'),(28,'electricity','0002_unique_bill_reading','2026-10-23 05:09:46.322007'),(29,'properties','0003_property_owner','2026-10-23 05:09:46.444663'),(30,'tenants','0003_tenant_owner','2026-10-23 05:09:46.496117'),(31,'properties','0004_property_image','2026-10-25 04:45:32.795700'),(32,'properties','0005_workspacesettings','2026-10-25 08:25:53.417823'),(33,'billing','0003_rentrecord_archived_at_rentrecord_is_archived_and_more','2026-10-25 13:15:38.403438'),(34,'notifications','0002_notification_delivery_status_notification_is_sent_and_more','2026-10-25 13:21:31.348806'),(35,'tenants','0004_rentalagreement_deduction_amount_and_more','2026-10-27 03:43:09.609131'),(36,'accounts','0001_initial','2026-10-27 06:26:03.160909'),(37,'properties','0006_alter_property_property_type_alter_room_room_type','2026-10-27 07:22:30.409398'),(38,'accounts','0002_ownerprofile_access_status_and_more','2026-10-27 07:47:19.209797'),(39,'accounts','0003_alter_ownerverificationrequest_ownership_proof','2026-10-27 09:39:04.835850'),(40,'properties','0007_add_owner_display_name','2026-10-27 14:08:19.801855'),(41,'tenants','0005_tenant_emergency_contact_relationship_and_more','2026-10-27 14:08:30.469272'),(42,'billing','0004_ownerqrconfig_tenantqrassignment_and_more','2026-10-28 11:07:51.421110');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_data` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('3llqf1jnrmawp0n8oi7e2yrgdrciby4p','.eJxVjDkOwjAUBe_iGlleAH9T0ucM1l8MDiBbipMKcXcSKQW0b2beWyVc5pKWnqc0irooC-rwOxLyM9eNyAPrvWludZ5G0puid9r10CS_rrv7d1Cwl7U2UQDExiwEEk0EzyQOfTixAS_Os7-dOSBTjI4zgQWzBpmOGJgJ1ecLGs05Bw:1xNlfA:rHNXg6jLFdhB3cin5aoBcC0ZV8eOcNuQVODSmYd1Jlc','2026-11-16 06:37:00.840299'),('7f45b2afxage77ukaxk0ldaf4vksmgiy','.eJxVjDkOwjAUBe_iGlleAH9T0ucM1l8MDiBbipMKcXcSKQW0b2beWyVc5pKWnqc0irooC-rwOxLyM9eNyAPrvWludZ5G0puid9r10CS_rrv7d1Cwl7U2UQDExiwEEk0EzyQOfTixAS_Os7-dOSBTjI4zgQWzBpmOGJgJ1ecLGs05Bw:1xNm2H:4wkEPcgthwt84g4-EEfIFfgSBeL-qXu7W6GQN1Vlx9s','2026-11-16 07:00:53.526596'),('7keok5ln0h9oamw11fm3nhc2qvekeb2j','.eJxVjDkOwjAUBe_iGlleAH9T0ucM1l8MDiBbipMKcXcSKQW0b2beWyVc5pKWnqc0irooC-rwOxLyM9eNyAPrvWludZ5G0puid9r10CS_rrv7d1Cwl7U2UQDExiwEEk0EzyQOfTixAS_Os7-dOSBTjI4zgQWzBpmOGJgJ1ecLGs05Bw:1xNlzj:k2DZg3wnng73EQ6dFgi48425174BeBBUNa9hJkEfoLQ','2026-11-16 06:58:15.241977'),('7n0bcd396amdups97jxp680umt2g1t1v','.eJxVjDkOwjAUBe_iGlleAH9T0ucM1l8MDiBbipMKcXcSKQW0b2beWyVc5pKWnqc0irooC-rwOxLyM9eNyAPrvWludZ5G0puid9r10CS_rrv7d1Cwl7U2UQDExiwEEk0EzyQOfTixAS_Os7-dOSBTjI4zgQWzBpmOGJgJ1ecLGs05Bw:1xNm9Z:Fi7VLMkuw4-pwD0nACkgyJBauxfxSVr05ggZTlTvB2o','2026-11-16 07:08:25.882801'),('867wc6xtsb7ab983bm28itayf8cgjyf6','.eJxVjEEOwiAQRe_C2hBApoBL9z0DmWFAqoYmpV0Z765NutDtf-_9l4i4rTVuPS9xYnER2orT70iYHrnthO_YbrNMc1uXieSuyIN2Oc6cn9fD_Tuo2Ou3Ng7O4IaiwXpWWoFhSECD92SVDtaSKQDeAeYSjFY-WDQAyIyKSiji_QHJfjcc:1xLe0Z:aq2ATlF3xRm_3jKUv3FmuAHWFMWYYrJJ7IwIU2rLZ7Q','2026-11-10 10:02:19.325059'),('8gku17d8wzsc5wn2jdipzgkhq1glra57','.eJxVjDkOwjAUBe_iGlleAH9T0ucM1l8MDiBbipMKcXcSKQW0b2beWyVc5pKWnqc0irooC-rwOxLyM9eNyAPrvWludZ5G0puid9r10CS_rrv7d1Cwl7U2UQDExiwEEk0EzyQOfTixAS_Os7-dOSBTjI4zgQWzBpmOGJgJ1ecLGs05Bw:1xNlf6:KlyYCzasYwKStjGO1mr2GI-1qk99WP64dKQF5thDTSY','2026-11-16 06:36:56.419411'),('bl0vx1o2zd65z8vsj97sfvt5jy700qcv','.eJxVjL0OAiEQhN-F2hA4OH4s7X0GsrCrnBpIjrvK-O5CcoVOMcV8M_NmAfYth73RGhZkZybZ6TeLkJ5UBsAHlHvlqZZtXSIfFX7Qxq8V6XU5un8HGVrua5gnVOBoyKNwzqCcSWpQyXSUvEAZo5lAoI4Rb6Stkl6R7WaNQPb5AgYqOFs:1xNlqa:9Gd6F8dHvtiQbtSQ9jjGi-XLX0fjJGi1G7GVC-13E-0','2026-11-16 06:48:48.423593'),('cpqh1m0mgugty04o6gc40f3rdzljh0vk','.eJxVjEEOwiAQRe_C2pAOUqa4dO8ZyDAMUjU0Ke3KeHet6UK3773_nyrQupSwNpnDmNRJWXX4ZZH4LnUT6Ub1Omme6jKPUW-J3m3TlynJ47y3fweFWvmsnSXMxoLDjDExOLDd0DnjPbKRDBSpxyOTBztIH9MXCxJgtp4zq9cb1BY4Ew:1xKALq:g6DhDMQH6I_GmCmepBuLyzEwu8aqcnBeF2x40iH5Mlk','2026-11-06 08:10:10.102176'),('dmma6a2vafcnwjmv50lxkfy2cijhspij','.eJxVjDsOwjAQBe_iGln4b1PScwZrvbvgALKlOKkQd4dIKaB9M_NeIsO61LwOnvNE4iSUEYffsQA-uG2E7tBuXWJvyzwVuSlyp0NeOvHzvLt_BxVG_dbOYgpXKOxitFFxSuQ0BSJEo4JHPAZFli1riNr4VIpBcsb44nVInMT7AxJnOCI:1xLdzw:pvj3uaOi43c6DBhoOmklsvS5RDSF4RLpil_zoQyngKk','2026-11-10 10:01:40.169622'),('h72p0uc0lew1mvnjyf9wbzd93os1uufw','.eJxVjDkOwjAUBe_iGlleAH9T0ucM1l8MDiBbipMKcXcSKQW0b2beWyVc5pKWnqc0irooC-rwOxLyM9eNyAPrvWludZ5G0puid9r10CS_rrv7d1Cwl7U2UQDExiwEEk0EzyQOfTixAS_Os7-dOSBTjI4zgQWzBpmOGJgJ1ecLGs05Bw:1xNlq0:rJ6C58Cmw4gkKvuAz6AXotNgBxBhZRvQkxt2GM6Jm5A','2026-11-16 06:48:12.606082'),('i3ji0neuxmtlomcrnltoq3gmtt3ezm74','.eJxVjDkOwjAUBe_iGlleAH9T0ucM1l8MDiBbipMKcXcSKQW0b2beWyVc5pKWnqc0irooC-rwOxLyM9eNyAPrvWludZ5G0puid9r10CS_rrv7d1Cwl7U2UQDExiwEEk0EzyQOfTixAS_Os7-dOSBTjI4zgQWzBpmOGJgJ1ecLGs05Bw:1xNm9V:P3D2feo-qCyRC7vpBReiOA0VqvYWsrTP7UHwVFoz5ys','2026-11-16 07:08:21.214490'),('j2knbwoe8fzb6v27judoz8r1z5r3yvkd','.eJxVjDsOwjAQBe_iGlmO_6ak5wzWrndNAiiW4qRC3B0ipYD2zcx7iQzbOuat85InEmcxaHH6HRHKg-ed0B3mW5OlzesyodwVedAur434eTncv4MR-viti0UDRmMA52BwJkXvfMXIHpRXJbHnxAF1VYiWyBJXU7Xm5EMlm6J4fwASljio:1xLdzV:MHmbgArYxzozipw1-aYOsVR7hXUvdfFp1Kk70Jy8qHw','2026-11-10 10:01:13.526827'),('j4vwk23dpjbozeskfrzp023d4k8ftzi5','.eJxVjDkOwjAUBe_iGlleAH9T0ucM1l8MDiBbipMKcXcSKQW0b2beWyVc5pKWnqc0irooC-rwOxLyM9eNyAPrvWludZ5G0puid9r10CS_rrv7d1Cwl7U2UQDExiwEEk0EzyQOfTixAS_Os7-dOSBTjI4zgQWzBpmOGJgJ1ecLGs05Bw:1xNm9d:2AlVbUTCVx1qJiX3SG9zDvgKCu6fBsPXELI7BW_VA18','2026-11-16 07:08:29.395946'),('kbu9zcfwnmi4lr0vnknq9qcy7hxjd3i2','.eJxVjDkOwjAUBe_iGlleAH9T0ucM1l8MDiBbipMKcXcSKQW0b2beWyVc5pKWnqc0irooC-rwOxLyM9eNyAPrvWludZ5G0puid9r10CS_rrv7d1Cwl7U2UQDExiwEEk0EzyQOfTixAS_Os7-dOSBTjI4zgQWzBpmOGJgJ1ecLGs05Bw:1xNm9f:LJLa4QULyguAxNyjdw9bvM7EV-HSwjTIpbveTdxN05U','2026-11-16 07:08:31.281647'),('lu38ns6ks4e7woallq7ghnjz9s2ki15a','.eJxVjDkOwjAUBe_iGlleAH9T0ucM1l8MDiBbipMKcXcSKQW0b2beWyVc5pKWnqc0irooC-rwOxLyM9eNyAPrvWludZ5G0puid9r10CS_rrv7d1Cwl7U2UQDExiwEEk0EzyQOfTixAS_Os7-dOSBTjI4zgQWzBpmOGJgJ1ecLGs05Bw:1xNm9X:B6d6XaipaLyqpChJUE9EUSVTs7CGH5RBk6aUllj4-C0','2026-11-16 07:08:23.530765'),('n6pslzpv4ahth3pgbpq8kifpmwsu2wor','.eJxVjL0OAiEQhN-F2hA4OH4s7X0GsrCrnBpIjrvK-O5CcoVOMcV8M_NmAfYth73RGhZkZybZ6TeLkJ5UBsAHlHvlqZZtXSIfFX7Qxq8V6XU5un8HGVrua5gnVOBoyKNwzqCcSWpQyXSUvEAZo5lAoI4Rb6Stkl6R7WaNQPb5AgYqOFs:1xLBgH:Fh6I4YM6Wug_rPozTLQiloqDke4OoRUmfeiubO8z8E0','2026-11-09 03:47:29.022821'),('qhgmixj0q1bghwd62t53xe3274trcirq','.eJxVjDsOwjAQBe_iGlm28S-U9JzBWu9ucADZUpxUiLuTSCmgfTNv3iLBupS0dp7TROIinDj9bhnwyXUH9IB6bxJbXeYpy12RB-3y1ohf18P9CxToZXtbcjrqHFiD8eiYFTpjjcXIxutxcOzU4BE9sCH24QxjjrT1Q-SoPInPF-WoOGo:1xNlgu:2HlCffJ0jIX_GvPwH7RK603w10xaa2H0SuTi-7lSZhE','2026-11-16 06:38:48.113868'),('t3g0qr0pbj91j3tslb0huaz9ef835abf','.eJxVjDkOwjAUBe_iGlleAH9T0ucM1l8MDiBbipMKcXcSKQW0b2beWyVc5pKWnqc0irooC-rwOxLyM9eNyAPrvWludZ5G0puid9r10CS_rrv7d1Cwl7U2UQDExiwEEk0EzyQOfTixAS_Os7-dOSBTjI4zgQWzBpmOGJgJ1ecLGs05Bw:1xNlfk:6VLYXcS293zRZq7fE2qR4edNnUxqLzbbN-cJ2UWJmvE','2026-11-16 06:37:36.123107'),('tfsjg0e3anbslqihf0s8ouen9y443g5o','.eJxVjDkOwjAUBe_iGlleAH9T0ucM1l8MDiBbipMKcXcSKQW0b2beWyVc5pKWnqc0irooC-rwOxLyM9eNyAPrvWludZ5G0puid9r10CS_rrv7d1Cwl7U2UQDExiwEEk0EzyQOfTixAS_Os7-dOSBTjI4zgQWzBpmOGJgJ1ecLGs05Bw:1xNlgH:FuYtiyTHjbRIZZ6ebR17ZNJFSZSNzOIcTx_rv76-1x4','2026-11-16 06:38:09.811427'),('ubkyfcqk5qf29c56ed0wt7sqmuq937e2','.eJxVjL0OAiEQhN-F2hA4OH4s7X0GsrCrnBpIjrvK-O5CcoVOMcV8M_NmAfYth73RGhZkZybZ6TeLkJ5UBsAHlHvlqZZtXSIfFX7Qxq8V6XU5un8HGVrua5gnVOBoyKNwzqCcSWpQyXSUvEAZo5lAoI4Rb6Stkl6R7WaNQPb5AgYqOFs:1xKDi7:XwXVpXXWaRS9oweHqAUN0tngH-FcDaHbX_YPaZwLVp0','2026-11-06 11:45:23.656525'),('uipx3hpfj7x0qrkbvhl3boaynmmfxzdp','.eJxVjDsOwjAQRO_iGlnG8W8p6XMGa7Ne4wBypDipEHcHSylA0817My8Rcd9K3BuvcU7iIrQ4_XYT0oNrB-mO9bZIWuq2zpPsijxok-OS-Hk93L-Dgq30NYUAoBSQs8mjIocKh2x9zokxDA4T-2_OWgMEohycMcoHC8B-YCPeH_OfOAI:1xK4i5:6WKV8EqfChLQ45njNS8eVUnEZT5958eOp-qgNAndulg','2026-11-06 02:08:45.615162'),('vj5pug1kwnkdzvo0w9g54c7lxhyeynlv','.eJxVjDkOwjAUBe_iGlleAH9T0ucM1l8MDiBbipMKcXcSKQW0b2beWyVc5pKWnqc0irooC-rwOxLyM9eNyAPrvWludZ5G0puid9r10CS_rrv7d1Cwl7U2UQDExiwEEk0EzyQOfTixAS_Os7-dOSBTjI4zgQWzBpmOGJgJ1ecLGs05Bw:1xNm9Y:d00JjdxvMEdmg_RpzLUMUX5tRGUV8mriXxPpdOayPxQ','2026-11-16 07:08:24.577217'),('yd7mr6u6bkwxjv91xhrkbwq3mgjgl0df','.eJxVjDkOwjAUBe_iGlleAH9T0ucM1l8MDiBbipMKcXcSKQW0b2beWyVc5pKWnqc0irooC-rwOxLyM9eNyAPrvWludZ5G0puid9r10CS_rrv7d1Cwl7U2UQDExiwEEk0EzyQOfTixAS_Os7-dOSBTjI4zgQWzBpmOGJgJ1ecLGs05Bw:1xNm2L:eVBc798DBokkvXDi3xT5X7Ito9RZq7prb_raXeTPy0M','2026-11-16 07:00:57.607117'),('zs0qa9pdxv9mi5jqp5e2ej3qi2iezcmz','.eJxVjL0OAiEQhN-F2hA4OH4s7X0GsrCrnBpIjrvK-O5CcoVOMcV8M_NmAfYth73RGhZkZybZ6TeLkJ5UBsAHlHvlqZZtXSIfFX7Qxq8V6XU5un8HGVrua5gnVOBoyKNwzqCcSWpQyXSUvEAZo5lAoI4Rb6Stkl6R7WaNQPb5AgYqOFs:1xKtZc:uIxsEgDGbgmCb91fqo0rkDz7Bj5uojDE1bMAKrNfyXM','2026-11-08 08:27:24.000030');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `electricity_electricitybill`
--

DROP TABLE IF EXISTS `electricity_electricitybill`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `electricity_electricitybill` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `billing_month` date NOT NULL,
  `units_consumed` decimal(10,2) NOT NULL,
  `rate_per_unit` decimal(8,2) NOT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  `due_date` date NOT NULL,
  `amount_paid` decimal(10,2) NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `meter_id` bigint NOT NULL,
  `reading_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_electricity_bill_per_reading` (`reading_id`),
  KEY `electricity_electric_meter_id_16b69501_fk_electrici` (`meter_id`),
  CONSTRAINT `electricity_electric_meter_id_16b69501_fk_electrici` FOREIGN KEY (`meter_id`) REFERENCES `electricity_electricitymeter` (`id`),
  CONSTRAINT `electricity_electric_reading_id_5c49fe0d_fk_electrici` FOREIGN KEY (`reading_id`) REFERENCES `electricity_meterreading` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `electricity_electricitybill`
--

LOCK TABLES `electricity_electricitybill` WRITE;
/*!40000 ALTER TABLE `electricity_electricitybill` DISABLE KEYS */;
INSERT INTO `electricity_electricitybill` VALUES (1,'2026-10-22',100.00,12.00,1200.00,'2026-10-27',0.00,'PENDING','2026-10-22 13:28:08.826960','2026-10-22 13:28:08.826978',1,1),(2,'2026-10-01',10.00,12.00,120.00,'2026-10-05',0.00,'OVERDUE','2026-10-25 10:24:20.048854','2026-10-25 10:24:20.048861',2,2),(3,'2026-10-01',0.00,12.00,0.00,'2026-10-05',0.00,'OVERDUE','2026-10-26 14:05:35.492405','2026-10-26 14:05:35.492424',2,3),(4,'2026-10-01',1.00,12.00,12.00,'2026-10-05',12.00,'PAID','2026-10-27 10:55:38.161214','2026-10-27 13:47:09.631973',1,6),(5,'2026-10-01',88.00,8.00,704.00,'2026-10-05',0.00,'OVERDUE','2026-10-29 05:59:45.635205','2026-10-29 05:59:45.635215',4,7),(6,'2026-10-01',111.00,8.00,888.00,'2026-10-05',0.00,'OVERDUE','2026-10-29 08:15:33.376345','2026-10-29 08:15:33.376384',3,8),(7,'2026-10-01',19.00,12.00,228.00,'2026-10-07',0.00,'OVERDUE','2026-10-29 15:03:45.208862','2026-10-29 15:03:45.208873',5,9);
/*!40000 ALTER TABLE `electricity_electricitybill` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `electricity_electricitymeter`
--

DROP TABLE IF EXISTS `electricity_electricitymeter`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `electricity_electricitymeter` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `meter_number` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `installation_date` date NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `notes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `room_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `meter_number` (`meter_number`),
  KEY `electricity_electric_room_id_cad9d4a6_fk_propertie` (`room_id`),
  CONSTRAINT `electricity_electric_room_id_cad9d4a6_fk_propertie` FOREIGN KEY (`room_id`) REFERENCES `properties_room` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `electricity_electricitymeter`
--

LOCK TABLES `electricity_electricitymeter` WRITE;
/*!40000 ALTER TABLE `electricity_electricitymeter` DISABLE KEYS */;
INSERT INTO `electricity_electricitymeter` VALUES (1,'1','2026-10-22',1,'lhbjk','2026-10-22 13:26:43.934642','2026-10-22 13:26:43.934660',1),(2,'MTR-105','2026-10-25',1,'Auto-created during reading entry','2026-10-25 10:24:19.987182','2026-10-25 10:24:19.987197',4),(3,'122','2026-10-28',1,'Created with Room 101','2026-10-28 05:55:11.883348','2026-10-28 05:55:11.883362',5),(4,'MTR-102','2026-10-29',1,'Auto-created during reading entry','2026-10-29 05:59:45.574025','2026-10-29 05:59:45.574046',6),(5,'MTR-1','2026-10-29',1,'Auto-created during reading entry','2026-10-29 15:03:45.154735','2026-10-29 15:03:45.154756',7);
/*!40000 ALTER TABLE `electricity_electricitymeter` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `electricity_meterreading`
--

DROP TABLE IF EXISTS `electricity_meterreading`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `electricity_meterreading` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `reading_date` date NOT NULL,
  `previous_reading` decimal(12,2) NOT NULL,
  `current_reading` decimal(12,2) NOT NULL,
  `notes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `meter_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_meter_reading_per_date` (`meter_id`,`reading_date`),
  CONSTRAINT `electricity_meterrea_meter_id_8eb7b1a5_fk_electrici` FOREIGN KEY (`meter_id`) REFERENCES `electricity_electricitymeter` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `electricity_meterreading`
--

LOCK TABLES `electricity_meterreading` WRITE;
/*!40000 ALTER TABLE `electricity_meterreading` DISABLE KEYS */;
INSERT INTO `electricity_meterreading` VALUES (1,'2026-10-22',100.00,200.00,'jhwbf','2026-10-22 13:27:24.957399',1),(2,'2026-10-25',0.00,10.00,'','2026-10-25 10:24:20.028456',2),(3,'2026-10-26',10.00,10.00,'','2026-10-26 14:05:35.435219',2),(4,'2026-11-01',200.00,200.00,'Auto-rollover from October 2026 reading (200.00)','2026-10-27 02:28:52.857411',1),(5,'2026-11-01',10.00,10.00,'Auto-rollover from October 2026 reading (10.00)','2026-10-27 02:28:52.861102',2),(6,'2026-10-27',1.00,2.00,'','2026-10-27 10:55:38.125038',1),(7,'2026-10-29',100.00,188.00,'this wii be good','2026-10-29 05:59:45.605978',4),(8,'2026-10-29',12.00,123.00,'','2026-10-29 08:15:33.343426',3),(9,'2026-10-29',1.00,20.00,'','2026-10-29 15:03:45.181464',5);
/*!40000 ALTER TABLE `electricity_meterreading` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notifications_notification`
--

DROP TABLE IF EXISTS `notifications_notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications_notification` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `notification_type` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `message` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `due_date` date NOT NULL,
  `amount_due` decimal(10,2) NOT NULL,
  `is_read` tinyint(1) NOT NULL,
  `read_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `deduplication_key` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `electricity_bill_id` bigint DEFAULT NULL,
  `rent_record_id` bigint DEFAULT NULL,
  `tenant_id` bigint NOT NULL,
  `delivery_status` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_sent` tinyint(1) NOT NULL,
  `sent_at` datetime(6) DEFAULT NULL,
  `sent_via` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `deduplication_key` (`deduplication_key`),
  KEY `notifications_notifi_electricity_bill_id_70c655aa_fk_electrici` (`electricity_bill_id`),
  KEY `notifications_notifi_rent_record_id_38b734a1_fk_billing_r` (`rent_record_id`),
  KEY `notifications_notifi_tenant_id_156c9e0d_fk_tenants_t` (`tenant_id`),
  CONSTRAINT `notifications_notifi_electricity_bill_id_70c655aa_fk_electrici` FOREIGN KEY (`electricity_bill_id`) REFERENCES `electricity_electricitybill` (`id`),
  CONSTRAINT `notifications_notifi_rent_record_id_38b734a1_fk_billing_r` FOREIGN KEY (`rent_record_id`) REFERENCES `billing_rentrecord` (`id`),
  CONSTRAINT `notifications_notifi_tenant_id_156c9e0d_fk_tenants_t` FOREIGN KEY (`tenant_id`) REFERENCES `tenants_tenant` (`id`),
  CONSTRAINT `notification_has_exactly_one_bill` CHECK ((((`electricity_bill_id` is null) and (`rent_record_id` is not null)) or ((`electricity_bill_id` is not null) and (`rent_record_id` is null))))
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notifications_notification`
--

LOCK TABLES `notifications_notification` WRITE;
/*!40000 ALTER TABLE `notifications_notification` DISABLE KEYS */;
INSERT INTO `notifications_notification` VALUES (1,'RENT_OVERDUE','Rent Payment Overdue','Rahul Sharma, aapka rent overdue hai. Pending amount: Rs. 5000.00. Due date: 2026-10-05.','2026-10-05',5000.00,1,'2026-10-22 16:27:16.986938','2026-10-22 16:25:04.002971','1:rent:2:RENT_OVERDUE',NULL,2,1,'SENT',1,'2026-10-26 14:25:01.674951','WHATSAPP'),(2,'RENT_UPCOMING','Monthly Rent Bill (Oct 2026)','Rent bill for Room 1: Rs. 5000.00','2026-10-27',5000.00,1,'2026-10-26 14:28:45.153366','2026-10-26 09:26:08.022248','1:rent:1:RENT_UPCOMING',NULL,1,1,'SENT',1,'2026-10-26 14:25:01.671585','WHATSAPP'),(3,'RENT_OVERDUE','Monthly Rent Bill (Oct 2026)','Rent bill for Room 2: Rs. 1.00','2026-10-05',1.00,1,'2026-10-26 14:28:45.147086','2026-10-26 09:26:08.040549','6:rent:3:RENT_OVERDUE',NULL,3,6,'SENT',1,'2026-10-29 08:17:08.238613','SMS'),(4,'ELECTRICITY_UPCOMING','Electricity Bill Due Soon','Rahul Sharma, aapka electricity bill 2026-10-27 ko due hai. Pending amount: Rs. 1200.00.','2026-10-27',1200.00,1,'2026-10-26 14:28:45.145882','2026-10-26 14:13:20.603618','1:electricity:1:ELECTRICITY_UPCOMING',1,NULL,1,'SENT',1,'2026-10-26 14:25:01.651890','WHATSAPP'),(5,'ELECTRICITY_OVERDUE','Electricity Bill Overdue','Rahul Sharma, aapka electricity bill overdue hai. Pending amount: Rs. 12.00. Due date: 2026-10-05.','2026-10-05',12.00,1,'2026-10-27 10:56:14.321720','2026-10-27 10:55:38.230831','1:electricity:4:ELECTRICITY_OVERDUE',4,NULL,1,'PENDING',0,NULL,''),(6,'ELECTRICITY_OVERDUE','Electricity Bill Overdue','Rahul Sharma, aapka electricity bill overdue hai. Pending amount: Rs. 1200.00. Due date: 2026-10-27.','2026-10-27',1200.00,0,NULL,'2026-10-28 03:41:05.055584','1:electricity:1:ELECTRICITY_OVERDUE',1,NULL,1,'PENDING',0,NULL,''),(7,'RENT_OVERDUE','Rent Payment Overdue','Harsh, aapka rent overdue hai. Pending amount: Rs. 10000.00. Due date: 2026-10-05.','2026-10-05',10000.00,0,NULL,'2026-10-28 05:57:24.820646','7:rent:4:RENT_OVERDUE',NULL,4,7,'SENT',1,'2026-10-28 05:59:16.415389','BOTH'),(8,'ELECTRICITY_OVERDUE','Electricity Bill Overdue','Harsh, aapka electricity bill overdue hai. Pending amount: Rs. 704.00. Due date: 2026-10-05.','2026-10-05',704.00,0,NULL,'2026-10-29 05:59:45.740730','7:electricity:5:ELECTRICITY_OVERDUE',5,NULL,7,'SENT',1,'2026-10-29 08:30:58.778195','SMS'),(9,'RENT_OVERDUE','Rent Payment Overdue','Test 1, aapka rent overdue hai. Pending amount: Rs. 2500.00. Due date: 2026-10-07.','2026-10-07',2500.00,0,NULL,'2026-10-29 15:00:35.285102','9:rent:5:RENT_OVERDUE',NULL,5,9,'PENDING',0,NULL,''),(10,'RENT_OVERDUE','Rent Payment Overdue','Test 2, aapka rent overdue hai. Pending amount: Rs. 2500.00. Due date: 2026-10-07.','2026-10-07',2500.00,0,NULL,'2026-10-29 15:01:33.620267','10:rent:6:RENT_OVERDUE',NULL,6,10,'PENDING',0,NULL,''),(11,'ELECTRICITY_OVERDUE','Electricity Bill Overdue','Test 2, aapka electricity bill overdue hai. Pending amount: Rs. 228.00. Due date: 2026-10-07.','2026-10-07',228.00,0,NULL,'2026-10-29 15:03:45.299085','10:electricity:7:ELECTRICITY_OVERDUE',7,NULL,10,'PENDING',0,NULL,'');
/*!40000 ALTER TABLE `notifications_notification` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payments_payment`
--

DROP TABLE IF EXISTS `payments_payment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payments_payment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `amount` decimal(10,2) NOT NULL,
  `payment_date` datetime(6) NOT NULL,
  `payment_method` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `transaction_reference` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `notes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `agreement_id` bigint NOT NULL,
  `electricity_bill_id` bigint DEFAULT NULL,
  `rent_record_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `payments_payment_agreement_id_ef6994be_fk_tenants_r` (`agreement_id`),
  KEY `payments_payment_electricity_bill_id_0bf07635_fk_electrici` (`electricity_bill_id`),
  KEY `payments_payment_rent_record_id_dc29f96c_fk_billing_r` (`rent_record_id`),
  CONSTRAINT `payments_payment_agreement_id_ef6994be_fk_tenants_r` FOREIGN KEY (`agreement_id`) REFERENCES `tenants_rentalagreement` (`id`),
  CONSTRAINT `payments_payment_electricity_bill_id_0bf07635_fk_electrici` FOREIGN KEY (`electricity_bill_id`) REFERENCES `electricity_electricitybill` (`id`),
  CONSTRAINT `payments_payment_rent_record_id_dc29f96c_fk_billing_r` FOREIGN KEY (`rent_record_id`) REFERENCES `billing_rentrecord` (`id`),
  CONSTRAINT `payment_has_exactly_one_bill` CHECK ((((`electricity_bill_id` is null) and (`rent_record_id` is not null)) or ((`electricity_bill_id` is not null) and (`rent_record_id` is null))))
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payments_payment`
--

LOCK TABLES `payments_payment` WRITE;
/*!40000 ALTER TABLE `payments_payment` DISABLE KEYS */;
INSERT INTO `payments_payment` VALUES (1,6200.00,'2026-10-22 18:58:00.000000','CASH','PENDING','jhwbi','wnf','2026-10-22 13:30:52.705936',1,NULL,1),(2,6200.00,'2026-10-22 19:01:00.000000','CASH','COMPLETED','','wf','2026-10-22 13:31:40.529778',1,1,NULL),(3,1.00,'2026-10-26 13:14:33.242000','UPI','COMPLETED','TXN20473242','Rent payment','2026-10-26 13:14:33.286050',3,NULL,3),(4,5000.00,'2026-10-27 13:47:00.850822','UPI','COMPLETED','CONFIRM-AC172A3A','Marked Paid by Owner','2026-10-27 13:47:00.851280',1,NULL,2),(5,12.00,'2026-10-27 13:47:09.638143','UPI','COMPLETED','CONFIRM-ELEC-4BFD5D12','Marked Paid by Owner','2026-10-27 13:47:09.638458',1,4,NULL),(6,5000.00,'2026-10-27 13:47:19.038555','UPI','COMPLETED','CONFIRM-2533C533','Marked Paid by Owner','2026-10-27 13:47:19.038823',1,NULL,1),(10,2500.00,'2026-10-29 15:02:48.139936','UPI','COMPLETED','CONFIRM-D1105CF6','Marked Paid by Owner','2026-10-29 15:02:48.140178',7,NULL,6);
/*!40000 ALTER TABLE `payments_payment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `properties_property`
--

DROP TABLE IF EXISTS `properties_property`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `properties_property` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `property_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `address` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `city` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `state` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `pin_code` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `monthly_rent` decimal(10,2) NOT NULL,
  `security_deposit` decimal(10,2) NOT NULL,
  `rent_due_day` smallint unsigned NOT NULL,
  `electricity_rate` decimal(8,2) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `owner_id` int NOT NULL,
  `image` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `contact_number` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `owner_display_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `properties_property_owner_id_6700dc90_fk_auth_user_id` (`owner_id`),
  CONSTRAINT `properties_property_owner_id_6700dc90_fk_auth_user_id` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `properties_property_chk_1` CHECK ((`rent_due_day` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `properties_property`
--

LOCK TABLES `properties_property` WRITE;
/*!40000 ALTER TABLE `properties_property` DISABLE KEYS */;
INSERT INTO `properties_property` VALUES (1,'Sunrise Hostel','HOSTEL','MG Ro','Indore','M.P','452010',7000.00,5000.00,5,12.00,'2026-10-22 13:18:37.156204','2026-10-27 14:43:15.487935',1,'properties/main_hoWfAis.jpg','',''),(2,'Occupancy Test Property','BUILDING','Test Address','Indore','Madhya Pradesh','452001',0.00,0.00,5,0.00,'2026-10-22 15:06:38.145061','2026-10-26 07:46:03.485186',1,'properties/Gemini_Generated_Image_rjjaqmrjjaqmrjja_bSApJYX.png','',''),(3,'Palm Grove Residency','BUILDING','24, 8th Cross, Sector 2','Bengaluru','Karnataka','560102',12000.00,24000.00,5,8.00,'2026-10-23 07:42:14.975144','2026-10-23 07:42:14.975170',3,NULL,'',''),(4,'Test','APARTMENT','Ala Pura, Indore','Indore','Madhya Pradesh','452007',5000.00,2500.00,5,8.00,'2026-10-26 07:29:46.572073','2026-10-26 07:30:06.735437',5,'properties/Gemini_Generated_Image_rjjaqmrjjaqmrjja.png','',''),(5,'sky','COMMERCIAL','Gita Bhawan Rd, local','Indore','Madhya Pradesh','452001',8600.00,4000.00,5,8.00,'2026-10-26 07:31:23.137862','2026-10-26 07:32:35.448894',5,'','',''),(6,'Alphawizz','BUILDING','152, ratan lok colony, vijay nagar','Indore','Madhya Pradesh','452001',10000.00,12000.00,5,8.00,'2026-10-28 05:54:14.303077','2026-10-28 05:54:14.303101',16,'','7828238909','Dhamnesh99999999'),(7,'Nigam\'s Hostel','HOSTEL','Ala Pura, Ala Pura','Indore','Madhya Pradesh','452007',5000.00,5000.00,7,12.00,'2026-10-29 14:56:10.285401','2026-10-29 14:57:37.445394',18,'properties/agricultural-landscape.png','7828238909','Siddarth');
/*!40000 ALTER TABLE `properties_property` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `properties_room`
--

DROP TABLE IF EXISTS `properties_room`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `properties_room` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `room_number` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `floor` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `room_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `monthly_rent` decimal(10,2) NOT NULL,
  `security_deposit` decimal(10,2) NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `property_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_room_number_per_property` (`property_id`,`room_number`),
  CONSTRAINT `properties_room_property_id_e3dacca6_fk_properties_property_id` FOREIGN KEY (`property_id`) REFERENCES `properties_property` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `properties_room`
--

LOCK TABLES `properties_room` WRITE;
/*!40000 ALTER TABLE `properties_room` DISABLE KEYS */;
INSERT INTO `properties_room` VALUES (1,'1','2','SINGLE',5000.00,2999.84,'OCCUPIED','2026-10-22 13:24:00.107254','2026-10-27 05:23:14.402034',1),(2,'2','1','SINGLE',5000.00,2999.84,'VACANT','2026-10-22 13:37:11.685683','2026-10-26 10:49:53.931496',1),(3,'TEST-101','','SINGLE',5000.00,0.00,'MAINTENANCE','2026-10-22 15:06:38.151538','2026-10-22 15:10:52.650198',2),(4,'105','1','DOUBLE',7000.00,5000.00,'OCCUPIED','2026-10-25 05:54:59.274175','2026-10-25 05:54:59.274192',1),(5,'101','First floor','SINGLE',10000.00,12000.00,'VACANT','2026-10-28 05:55:11.845122','2026-10-29 08:14:45.320621',6),(6,'102','First floor','SINGLE',10000.00,12000.00,'OCCUPIED','2026-10-28 05:55:23.732542','2026-10-29 06:07:09.182711',6),(7,'1','Ground floor','DOUBLE',5000.00,5000.00,'OCCUPIED','2026-10-29 14:58:39.837301','2026-10-29 15:01:33.527365',7);
/*!40000 ALTER TABLE `properties_room` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tenants_rentalagreement`
--

DROP TABLE IF EXISTS `tenants_rentalagreement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tenants_rentalagreement` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `start_date` date NOT NULL,
  `end_date` date DEFAULT NULL,
  `monthly_rent` decimal(10,2) NOT NULL,
  `security_deposit` decimal(10,2) NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `notes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `room_id` bigint NOT NULL,
  `tenant_id` bigint NOT NULL,
  `deduction_amount` decimal(10,2) NOT NULL,
  `deduction_reason` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `deposit_paid_date` date DEFAULT NULL,
  `deposit_payment_method` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `deposit_refund_date` date DEFAULT NULL,
  `deposit_transaction_ref` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `handover_items` json NOT NULL,
  `handover_notes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `refund_amount` decimal(10,2) NOT NULL,
  `security_deposit_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tenants_rentalagreement_room_id_5ff96754_fk_properties_room_id` (`room_id`),
  KEY `tenants_rentalagreement_tenant_id_f4208fe1_fk_tenants_tenant_id` (`tenant_id`),
  CONSTRAINT `tenants_rentalagreement_room_id_5ff96754_fk_properties_room_id` FOREIGN KEY (`room_id`) REFERENCES `properties_room` (`id`),
  CONSTRAINT `tenants_rentalagreement_tenant_id_f4208fe1_fk_tenants_tenant_id` FOREIGN KEY (`tenant_id`) REFERENCES `tenants_tenant` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tenants_rentalagreement`
--

LOCK TABLES `tenants_rentalagreement` WRITE;
/*!40000 ALTER TABLE `tenants_rentalagreement` DISABLE KEYS */;
INSERT INTO `tenants_rentalagreement` VALUES (1,'2026-10-22',NULL,5000.00,2999.84,'ACTIVE','qjhdbqj','2026-10-22 13:25:21.426816','2026-10-27 05:23:14.399058',1,1,0.00,'','2026-10-27','UPI',NULL,'DEP-1-594368','[]','',0.00,'PAID'),(2,'2026-10-22',NULL,5000.00,5000.00,'COMPLETED','','2026-10-22 15:06:53.259699','2026-10-27 05:23:12.029656',3,2,0.00,'','2026-10-27','UPI',NULL,'DEP-2-592001','[]','',0.00,'PAID'),(3,'2026-10-26','2026-10-26',1.00,0.76,'COMPLETED','','2026-10-26 07:58:08.837043','2026-10-27 05:33:41.826219',2,6,0.00,'','2026-10-27','UPI',NULL,'DEP-6-221797','[]','',0.00,'PAID'),(4,'2026-10-28','2026-12-28',10000.00,12000.00,'ACTIVE','please maintain the property','2026-10-28 05:57:24.674810','2026-10-29 06:07:09.155009',6,7,0.00,'','2026-10-28','UPI',NULL,'DEP-7-220911','[]','',0.00,'PAID'),(5,'2026-10-29',NULL,10000.00,12000.00,'COMPLETED','','2026-10-29 08:14:45.283725','2026-10-29 08:14:45.283739',5,8,0.00,'',NULL,'UPI',NULL,'','[]','',0.00,'PENDING'),(6,'2026-10-01','2027-10-28',2500.00,2500.00,'ACTIVE','','2026-10-29 15:00:35.167618','2026-10-29 15:02:17.724460',7,9,0.00,'','2026-10-29','UPI',NULL,'DEP-9-137695','[]','',0.00,'PAID'),(7,'2026-10-29','2027-03-18',2500.00,2500.00,'ACTIVE','','2026-10-29 15:01:33.501436','2026-10-29 15:02:14.508790',7,10,0.00,'','2026-10-29','UPI',NULL,'DEP-10-134476','[]','',0.00,'PAID');
/*!40000 ALTER TABLE `tenants_rentalagreement` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tenants_tenant`
--

DROP TABLE IF EXISTS `tenants_tenant`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tenants_tenant` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `full_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(15) COLLATE utf8mb4_unicode_ci NOT NULL,
  `alternate_phone` varchar(15) COLLATE utf8mb4_unicode_ci NOT NULL,
  `date_of_birth` date DEFAULT NULL,
  `address` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `emergency_contact_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `emergency_contact_phone` varchar(15) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `owner_id` int DEFAULT NULL,
  `emergency_contact_relationship` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `occupation` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tenants_tenant_owner_id_d1114a4f_fk_auth_user_id` (`owner_id`),
  CONSTRAINT `tenants_tenant_owner_id_d1114a4f_fk_auth_user_id` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tenants_tenant`
--

LOCK TABLES `tenants_tenant` WRITE;
/*!40000 ALTER TABLE `tenants_tenant` DISABLE KEYS */;
INSERT INTO `tenants_tenant` VALUES (1,'Rahul Sharma','rahul@gmail.com','9876543210','1234567890','2024-01-30','qdbiqk','qdhb','685128691','2026-10-22 13:21:57.474469','2026-10-22 13:21:57.474527',1,'',''),(2,'Test Tenant','','9999999999','',NULL,'','','','2026-10-22 15:06:38.154533','2026-10-22 15:06:38.154541',1,'',''),(3,'Second Test Tenant','','8888888888','',NULL,'','','','2026-10-22 15:08:22.589865','2026-10-22 15:08:22.589924',NULL,'',''),(4,'Second Test Tenant','','8888888888','',NULL,'','','','2026-10-22 15:10:16.203463','2026-10-22 15:10:16.203584',NULL,'',''),(5,'Gourav Berwal','gouravberwal003@gmail.com','7654208927908','',NULL,'Chandigarh Group Of Colleges Jhanjeri','','','2026-10-25 08:06:11.659121','2026-10-25 08:06:11.659133',1,'',''),(6,'Gourav Berwal','gouravberwal003@gmail.com','6262593646','','2001-07-16','Chandigarh Group Of Colleges Jhanjeri','','','2026-10-26 07:58:08.800329','2026-10-26 09:35:10.859030',1,'',''),(7,'Harsh','harshvardhan.balphawizz@gmail.com','8109124210','964915147','2026-10-28','indore','','','2026-10-28 05:57:24.638772','2026-10-29 06:07:09.112323',16,'',''),(8,'Abhishek','abhi@gmail.com','6262593646','8233769189','2001-02-11','lashdbljanc','','','2026-10-29 08:12:49.948220','2026-10-29 08:14:45.248890',16,'',''),(9,'Test 1','gouravberwal0001@gmail.com','7828238909','','2002-01-11','Gita Bhawan Rd\nSouth Tukoganj','','','2026-10-29 15:00:35.135186','2026-10-29 15:00:35.135219',18,'',''),(10,'Test 2','gouravberwal0001@gmail.com','9516637166','','2001-08-11','Gita Bhawan Rd\nSouth Tukoganj','','','2026-10-29 15:01:33.471039','2026-10-29 15:01:33.471064',18,'','');
/*!40000 ALTER TABLE `tenants_tenant` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workspace_settings`
--

DROP TABLE IF EXISTS `workspace_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workspace_settings` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `data` json NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `owner_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `owner_id` (`owner_id`),
  CONSTRAINT `workspace_settings_owner_id_d57c3dc1_fk_auth_user_id` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workspace_settings`
--

LOCK TABLES `workspace_settings` WRITE;
/*!40000 ALTER TABLE `workspace_settings` DISABLE KEYS */;
INSERT INTO `workspace_settings` VALUES (1,'{\"email\": \"gouravberwal003@gmail.com\", \"mobile\": \"\", \"address\": \"Chandigarh Group Of Colleges Jhanjeri\", \"currency\": \"INR · Indian Rupee (₹)\", \"fullName\": \"Gourav Berwal\", \"language\": \"English (India)\", \"timezone\": \"Asia/Kolkata · IST (UTC+05:30)\", \"twoFactor\": false, \"dateFormat\": \"DD MMM YYYY\", \"defaultRate\": \"8.00\", \"financialYear\": \"April – March\", \"weeklySummary\": true, \"workspaceName\": \"Gurjar Space\", \"defaultDeposit\": \"2 months\' rent\", \"productUpdates\": false, \"defaultRentDueDay\": \"5th of each month\", \"whatsappReminders\": true, \"defaultReminderTiming\": \"3 days before due date\"}','2026-10-25 09:21:44.229574',1),(2,'{\"email\": \"\", \"mobile\": \"\", \"address\": \"\", \"currency\": \"INR · Indian Rupee (₹)\", \"fullName\": \"\", \"language\": \"English (India)\", \"timezone\": \"Asia/Kolkata · IST (UTC+05:30)\", \"twoFactor\": false, \"dateFormat\": \"DD MMM YYYY\", \"defaultRate\": \"8.00\", \"financialYear\": \"April – March\", \"weeklySummary\": true, \"workspaceName\": \"\", \"defaultDeposit\": \"2 months\' rent\", \"productUpdates\": false, \"defaultRentDueDay\": \"5th of each month\", \"whatsappReminders\": true, \"defaultReminderTiming\": \"3 days before due date\"}','2026-10-25 13:29:25.443013',5),(3,'{\"email\": \"\", \"mobile\": \"\", \"address\": \"\", \"currency\": \"INR · Indian Rupee (₹)\", \"fullName\": \"\", \"language\": \"English (India)\", \"timezone\": \"Asia/Kolkata · IST (UTC+05:30)\", \"twoFactor\": false, \"dateFormat\": \"DD MMM YYYY\", \"defaultRate\": \"8.00\", \"financialYear\": \"April – March\", \"weeklySummary\": true, \"workspaceName\": \"\", \"defaultDeposit\": \"2 months\' rent\", \"productUpdates\": false, \"defaultRentDueDay\": \"5th of each month\", \"whatsappReminders\": true, \"defaultReminderTiming\": \"3 days before due date\"}','2026-10-27 08:06:48.634956',7),(4,'{\"email\": \"\", \"mobile\": \"\", \"address\": \"\", \"currency\": \"INR · Indian Rupee (₹)\", \"fullName\": \"\", \"language\": \"English (India)\", \"timezone\": \"Asia/Kolkata · IST (UTC+05:30)\", \"twoFactor\": false, \"dateFormat\": \"DD MMM YYYY\", \"defaultRate\": \"8.00\", \"financialYear\": \"April – March\", \"weeklySummary\": true, \"workspaceName\": \"\", \"defaultDeposit\": \"2 months\' rent\", \"productUpdates\": false, \"defaultRentDueDay\": \"5th of each month\", \"whatsappReminders\": true, \"defaultReminderTiming\": \"3 days before due date\"}','2026-10-27 14:42:30.799009',15),(5,'{\"email\": \"\", \"mobile\": \"\", \"address\": \"\", \"currency\": \"INR · Indian Rupee (₹)\", \"fullName\": \"\", \"language\": \"English (India)\", \"timezone\": \"Asia/Kolkata · IST (UTC+05:30)\", \"twoFactor\": false, \"dateFormat\": \"DD MMM YYYY\", \"defaultRate\": \"8.00\", \"financialYear\": \"April – March\", \"weeklySummary\": true, \"workspaceName\": \"\", \"defaultDeposit\": \"2 months\' rent\", \"productUpdates\": false, \"defaultRentDueDay\": \"5th of each month\", \"whatsappReminders\": true, \"defaultReminderTiming\": \"3 days before due date\"}','2026-10-28 07:58:22.638318',16),(6,'{\"email\": \"\", \"mobile\": \"\", \"address\": \"\", \"currency\": \"INR · Indian Rupee (₹)\", \"fullName\": \"\", \"language\": \"English (India)\", \"timezone\": \"Asia/Kolkata · IST (UTC+05:30)\", \"qrConfigs\": [], \"twoFactor\": false, \"dateFormat\": \"DD MMM YYYY\", \"defaultRate\": \"8.00\", \"tenantQrMap\": {}, \"financialYear\": \"April – March\", \"weeklySummary\": true, \"workspaceName\": \"\", \"defaultDeposit\": \"2 months\' rent\", \"productUpdates\": false, \"defaultRentDueDay\": \"5th of each month\", \"whatsappReminders\": true, \"defaultReminderTiming\": \"3 days before due date\"}','2026-10-29 15:06:22.854146',18);
/*!40000 ALTER TABLE `workspace_settings` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-02 18:48:37
