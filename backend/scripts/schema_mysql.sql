SET FOREIGN_KEY_CHECKS = 0;
SET NAMES utf8mb4;

CREATE TABLE `sj_about_us` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `version` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_published` tinyint(1) DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_activities` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `session_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `action` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `comments` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_guest` tinyint(1) NOT NULL DEFAULT '0',
  `user_agent` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `os` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `os_version` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `device_type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `app_version` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `device_model` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `locale` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ip` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_activities_external` (`external_id`),
  KEY `ix_sj_activities_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_activity_meta` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `meta_key` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `meta_value` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_activit` (`parent_id`),
  CONSTRAINT `fk_sj_activit` FOREIGN KEY (`parent_id`) REFERENCES `sj_activities` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_availability_requests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `product_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `product_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `pincode` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_banner_user_segments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `banner_id` int NOT NULL,
  `segment` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_banner_user_seg` (`banner_id`),
  CONSTRAINT `fk_banner_user_seg` FOREIGN KEY (`banner_id`) REFERENCES `sj_banners` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_banner_visibility_rules` (
  `id` int NOT NULL AUTO_INCREMENT,
  `banner_id` int NOT NULL,
  `rule` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_banner_vis_rule` (`banner_id`),
  CONSTRAINT `fk_banner_vis_rule` FOREIGN KEY (`banner_id`) REFERENCES `sj_banners` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_banners` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `image_url` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `link_url` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `display_order` int NOT NULL DEFAULT '0',
  `start_date` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `end_date` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `is_published` tinyint(1) NOT NULL DEFAULT '1',
  `target_audience` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `position` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_banners_external` (`external_id`),
  KEY `ix_sj_banners_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_brands` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `slug` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `image_url` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_brands_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_bundle_products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bundle_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `product_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `quantity` int DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_bundle_id` (`bundle_id`),
  CONSTRAINT `fk_bundle_id` FOREIGN KEY (`bundle_id`) REFERENCES `sj_bundles` (`external_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_bundles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `price` decimal(10,2) NOT NULL,
  `discount_percentage` decimal(5,2) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_cart_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cart_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `product_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `quantity` int NOT NULL,
  `sell_as_case` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `fk_cart_item_cart` (`cart_id`),
  CONSTRAINT `fk_cart_item_cart` FOREIGN KEY (`cart_id`) REFERENCES `sj_carts` (`external_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_carts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` int NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_carts_external` (`external_id`),
  KEY `ix_sj_carts_user` (`user_id`),
  CONSTRAINT `fk_sj_carts_user` FOREIGN KEY (`user_id`) REFERENCES `sj_users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_categories` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `category_tag` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `minimum_quantity` int NOT NULL DEFAULT '0',
  `show_in_mobile_homepage` tinyint(1) NOT NULL DEFAULT '1',
  `gst` decimal(5,2) NOT NULL DEFAULT '0.00',
  `is_returnable` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_categories_external` (`external_id`),
  KEY `ix_sj_categories_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_category_category_tags` (
  `id` int NOT NULL AUTO_INCREMENT,
  `category_id` int NOT NULL,
  `tag` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_cat_tag` (`category_id`),
  CONSTRAINT `fk_cat_tag` FOREIGN KEY (`category_id`) REFERENCES `sj_categories` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_category_images` (
  `id` int NOT NULL AUTO_INCREMENT,
  `category_id` int NOT NULL,
  `image_url` varchar(1024) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_cat_img` (`category_id`),
  CONSTRAINT `fk_cat_img` FOREIGN KEY (`category_id`) REFERENCES `sj_categories` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_category_sub_categories` (
  `id` int NOT NULL AUTO_INCREMENT,
  `category_id` int NOT NULL,
  `sub_category` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_cat_sub_cat` (`category_id`),
  CONSTRAINT `fk_cat_sub_cat` FOREIGN KEY (`category_id`) REFERENCES `sj_categories` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_category_tags` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_category_tags_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_coach_marks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `anchor_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `screen_name` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sequence_order` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_coach_marks_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_collection_pages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `page` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_collect` (`parent_id`),
  CONSTRAINT `fk_sj_collect` FOREIGN KEY (`parent_id`) REFERENCES `sj_collections` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_collection_products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `product_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_collection_products` (`parent_id`),
  CONSTRAINT `fk_sj_collection_products` FOREIGN KEY (`parent_id`) REFERENCES `sj_collections` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_collection_rules` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `rule` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_collection_rules` (`parent_id`),
  CONSTRAINT `fk_sj_collection_rules` FOREIGN KEY (`parent_id`) REFERENCES `sj_collections` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_collection_segments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `segment` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_collection_segments` (`parent_id`),
  CONSTRAINT `fk_sj_collection_segments` FOREIGN KEY (`parent_id`) REFERENCES `sj_collections` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_collections` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `image_url` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `display_order` int NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_collections_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_commission_settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `default_commission_pct` decimal(5,2) NOT NULL DEFAULT '5.00',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_commission_settings_tiers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `setting_id` int NOT NULL,
  `min_val` decimal(10,2) DEFAULT '0.00',
  `max_val` decimal(10,2) DEFAULT NULL,
  `commission_pct` decimal(5,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_comm_tier` (`setting_id`),
  CONSTRAINT `fk_comm_tier` FOREIGN KEY (`setting_id`) REFERENCES `sj_commission_settings` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_contact_addresses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `address` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_contact` (`parent_id`),
  CONSTRAINT `fk_sj_contact` FOREIGN KEY (`parent_id`) REFERENCES `sj_contacts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_contact_phones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `phone` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_contact_phones` (`parent_id`),
  CONSTRAINT `fk_sj_contact_phones` FOREIGN KEY (`parent_id`) REFERENCES `sj_contacts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_contacts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `display_order` int NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_contacts_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_coupons` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `discount_type` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `discount_value` decimal(18,2) DEFAULT NULL,
  `min_order_value` decimal(18,2) DEFAULT NULL,
  `max_uses` int DEFAULT NULL,
  `used_count` int NOT NULL DEFAULT '0',
  `start_date` datetime DEFAULT NULL,
  `end_date` datetime DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_coupons_external` (`external_id`),
  UNIQUE KEY `ix_sj_coupons_code` ((upper(`code`)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_customer_segment_users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `segment_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_segment_id` (`segment_id`),
  CONSTRAINT `fk_segment_id` FOREIGN KEY (`segment_id`) REFERENCES `sj_customer_segments` (`external_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_customer_segments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `min_avg_order_value` decimal(10,2) DEFAULT NULL,
  `max_avg_order_value` decimal(10,2) DEFAULT NULL,
  `start_date` datetime DEFAULT NULL,
  `end_date` datetime DEFAULT NULL,
  `min_order_freq` int DEFAULT NULL,
  `max_order_freq` int DEFAULT NULL,
  `state` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `district` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `app_user` tinyint(1) DEFAULT NULL,
  `behavior` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `role` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_system` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_delivery_charge_def_tiers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `min_order_value` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `max_order_value` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `charge` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_delivery_charge_def_ti` (`parent_id`),
  CONSTRAINT `fk_sj_delivery_charge_def_ti` FOREIGN KEY (`parent_id`) REFERENCES `sj_delivery_charge_defaults` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_delivery_charge_defaults` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `applicable_to_wholesaler` tinyint(1) NOT NULL DEFAULT '1',
  `applicable_to_retailer` tinyint(1) NOT NULL DEFAULT '1',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_dc_defaults_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_delivery_charge_tiers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `min_order_value` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `max_order_value` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `charge` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_deliver` (`parent_id`),
  CONSTRAINT `fk_sj_deliver` FOREIGN KEY (`parent_id`) REFERENCES `sj_delivery_charges` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_delivery_charges` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `location_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `pincode` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `state` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `city` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `district` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `apply_default_charge` tinyint(1) NOT NULL DEFAULT '0',
  `charge` decimal(18,2) DEFAULT NULL,
  `min_cart_value` decimal(18,2) DEFAULT NULL,
  `serviceable_for_customer` tinyint(1) NOT NULL DEFAULT '1',
  `serviceable_for_retailer` tinyint(1) NOT NULL DEFAULT '1',
  `serviceable_for_wholesaler` tinyint(1) NOT NULL DEFAULT '1',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `description` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_delivery_charges_external` (`external_id`),
  KEY `ix_sj_delivery_charges_pincode` (`pincode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_delivery_slot_pincodes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `pincode` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_delivery_slot_pincodes` (`parent_id`),
  CONSTRAINT `fk_sj_delivery_slot_pincodes` FOREIGN KEY (`parent_id`) REFERENCES `sj_delivery_slots` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_delivery_slot_times` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `start_time` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `end_time` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `capacity` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_delivery_slot_times` (`parent_id`),
  CONSTRAINT `fk_sj_delivery_slot_times` FOREIGN KEY (`parent_id`) REFERENCES `sj_delivery_slots` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_delivery_slots` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `segment` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `date` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_delivery_slots_external` (`external_id`),
  KEY `ix_sj_delivery_slots_date` (`date`),
  KEY `ix_sj_delivery_slots_segment` (`segment`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_delivery_zone_pincodes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `pincode` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_delivery_zone_pincodes` (`parent_id`),
  CONSTRAINT `fk_sj_delivery_zone_pincodes` FOREIGN KEY (`parent_id`) REFERENCES `sj_delivery_zones` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_delivery_zones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(1000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `default_capacity` int NOT NULL DEFAULT '10',
  `urgent_delivery_available` tinyint(1) NOT NULL DEFAULT '0',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_delivery_zones_external` (`external_id`),
  KEY `ix_sj_delivery_zones_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_device_keys` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `key_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `key_value` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_device_` (`parent_id`),
  CONSTRAINT `fk_sj_device_` FOREIGN KEY (`parent_id`) REFERENCES `sj_device_subscriptions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_device_sub_data` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `sub_key` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sub_val` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_device_sub_data` (`parent_id`),
  CONSTRAINT `fk_sj_device_sub_data` FOREIGN KEY (`parent_id`) REFERENCES `sj_device_subscriptions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_device_subscriptions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `endpoint` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `expo_token` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_device_subscriptions_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_event_payload` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `payload_key` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `payload_value` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_event_p` (`parent_id`),
  CONSTRAINT `fk_sj_event_p` FOREIGN KEY (`parent_id`) REFERENCES `sj_events` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_events` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `event_type` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_events_external` (`external_id`),
  KEY `ix_sj_events_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_faq_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `section_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `question` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `answer` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_faq_section_id` (`section_id`),
  CONSTRAINT `fk_faq_section_id` FOREIGN KEY (`section_id`) REFERENCES `sj_faq_sections` (`external_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_faq_sections` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `order_index` int DEFAULT '0',
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `icon` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT 'help-circle-outline',
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_feature_flags` (
  `id` int NOT NULL AUTO_INCREMENT,
  `flag_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL DEFAULT '1',
  `category` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_feature_flags_flag_id` (`flag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_google_reviews` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rating` decimal(3,1) DEFAULT NULL,
  `review_count` int DEFAULT NULL,
  `last_updated` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `method` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_google_reviews_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_notification_data` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `data_key` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `data_value` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_notific` (`parent_id`),
  CONSTRAINT `fk_sj_notific` FOREIGN KEY (`parent_id`) REFERENCES `sj_notifications` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `message` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_read` tinyint(1) NOT NULL DEFAULT '0',
  `is_acknowledged` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_notifications_external` (`external_id`),
  KEY `ix_sj_notifications_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_order_feedback` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `order_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `rating` int DEFAULT NULL,
  `comments` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `delivery_rating` int DEFAULT NULL,
  `delivery_comment` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `feedback_type` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_order_feedback_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_order_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `product_id` int NOT NULL,
  `quantity` int NOT NULL,
  `price` decimal(18,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_sj_order_items_order` (`order_id`),
  KEY `ix_sj_order_items_product` (`product_id`),
  CONSTRAINT `fk_oi_order` FOREIGN KEY (`order_id`) REFERENCES `sj_orders` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_oi_product` FOREIGN KEY (`product_id`) REFERENCES `sj_products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` int NOT NULL,
  `order_number` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `total` decimal(18,2) DEFAULT NULL,
  `subtotal` decimal(18,2) DEFAULT NULL,
  `tax` decimal(18,2) NOT NULL DEFAULT '0.00',
  `shipping` decimal(18,2) NOT NULL DEFAULT '0.00',
  `discount` decimal(18,2) NOT NULL DEFAULT '0.00',
  `order_type` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `payment_status` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `payment_method` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `upi_payment_screenshot` longtext COLLATE utf8mb4_unicode_ci,
  `notes` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `printed_bill` tinyint(1) NOT NULL DEFAULT '0',
  `assigned_valet` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `shipped_at` datetime DEFAULT NULL,
  `delivered_at` datetime DEFAULT NULL,
  `cod_payment_received` tinyint(1) NOT NULL DEFAULT '0',
  `cod_payment_received_at` datetime DEFAULT NULL,
  `decline_reason` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cancelled_at` datetime DEFAULT NULL,
  `cancelled_by` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `turnaround_hours` decimal(10,2) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `ship_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ship_street` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ship_city` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ship_state` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ship_pincode` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ship_phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bill_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bill_street` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bill_city` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bill_state` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bill_pincode` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bill_phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_orders_external` (`external_id`),
  UNIQUE KEY `uq_sj_orders_number` (`order_number`),
  KEY `ix_sj_orders_user` (`user_id`),
  KEY `ix_sj_orders_status` (`status`),
  KEY `ix_sj_orders_created` (`created_at`),
  CONSTRAINT `fk_sj_orders_user` FOREIGN KEY (`user_id`) REFERENCES `sj_users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_otp_send_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sent_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_sj_otp_send_log_phone` (`phone`),
  KEY `ix_sj_otp_send_log_sent` (`sent_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_otps` (
  `id` int NOT NULL AUTO_INCREMENT,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `device_key` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'default',
  `otp_code` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `verify_attempts` int NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL,
  `expires_at` datetime NOT NULL,
  `last_sent_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_sj_otps_phone` (`phone`),
  KEY `ix_sj_otps_expires` (`expires_at`),
  KEY `ix_sj_otps_phone_device` (`phone`,`device_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_payment_entries` (
  `id` int NOT NULL AUTO_INCREMENT,
  `payment_id` int NOT NULL,
  `entry_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `amount` decimal(18,2) DEFAULT '0.00',
  `payment_method` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `paid_at` datetime DEFAULT NULL,
  `image` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `verified` tinyint(1) DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_payment_ent` (`payment_id`),
  CONSTRAINT `fk_sj_payment_ent` FOREIGN KEY (`payment_id`) REFERENCES `sj_payments` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_payments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `order_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_id_formatted` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `customer_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `order_date` datetime DEFAULT NULL,
  `payment_method` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `amount_paid` decimal(18,2) DEFAULT '0.00',
  `amount_remaining` decimal(18,2) DEFAULT '0.00',
  `total_amount` decimal(18,2) DEFAULT '0.00',
  `payment_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_payments_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_pincode_searches` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `pincode` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `query` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_serviceable` tinyint(1) DEFAULT '0',
  `timestamp` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_privacy_policy` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `version` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `effective_date` date DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_product_attributes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_id` int NOT NULL,
  `attr_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_prod_attr` (`product_id`),
  CONSTRAINT `fk_prod_attr` FOREIGN KEY (`product_id`) REFERENCES `sj_products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_product_details` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_id` int NOT NULL,
  `detail_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `detail_value` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `fk_prod_det` (`product_id`),
  CONSTRAINT `fk_prod_det` FOREIGN KEY (`product_id`) REFERENCES `sj_products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_product_images` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_id` int NOT NULL,
  `image_url` varchar(1024) COLLATE utf8mb4_unicode_ci NOT NULL,
  `order_index` int DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `fk_prod_img` (`product_id`),
  CONSTRAINT `fk_prod_img` FOREIGN KEY (`product_id`) REFERENCES `sj_products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_product_notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `product_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_product_reviews` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `product_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rating` int NOT NULL,
  `review_text` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_product_seller_variants` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_seller_id` int NOT NULL,
  `variant_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_prod_sel_var` (`product_seller_id`),
  CONSTRAINT `fk_sj_prod_sel_var` FOREIGN KEY (`product_seller_id`) REFERENCES `sj_product_sellers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_product_sellers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Matches sj_products.external_id',
  `seller_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Matches sj_users.external_id',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `request_status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'approved',
  `stock` int NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_ps_product_seller` (`product_id`,`seller_id`),
  KEY `ix_ps_seller_active` (`seller_id`,`is_active`,`request_status`),
  KEY `ix_ps_product_id` (`product_id`),
  KEY `ix_ps_seller_id` (`seller_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_product_tags` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_id` int NOT NULL,
  `tag` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_prod_tag` (`product_id`),
  CONSTRAINT `fk_prod_tag` FOREIGN KEY (`product_id`) REFERENCES `sj_products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_product_variant_combinations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_id` int NOT NULL,
  `sku` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  `stock` int DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `fk_prod_var` (`product_id`),
  CONSTRAINT `fk_prod_var` FOREIGN KEY (`product_id`) REFERENCES `sj_products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_product_variant_options` (
  `id` int NOT NULL AUTO_INCREMENT,
  `combination_id` int NOT NULL,
  `attr_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `attr_value` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_prod_var_opt` (`combination_id`),
  CONSTRAINT `fk_prod_var_opt` FOREIGN KEY (`combination_id`) REFERENCES `sj_product_variant_combinations` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_product_videos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_id` int NOT NULL,
  `video_url` varchar(1024) COLLATE utf8mb4_unicode_ci NOT NULL,
  `order_index` int DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `fk_prod_vid` (`product_id`),
  CONSTRAINT `fk_prod_vid` FOREIGN KEY (`product_id`) REFERENCES `sj_products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci,
  `sku` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `category` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sub_category` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `brand` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `mrp` decimal(18,2) DEFAULT NULL,
  `mrp_per_case` decimal(18,2) DEFAULT NULL,
  `quantity_per_case` int DEFAULT NULL,
  `stock` int NOT NULL DEFAULT '0',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_products_external` (`external_id`),
  UNIQUE KEY `ix_sj_products_sku` (`sku`),
  KEY `ix_sj_products_active` (`is_active`),
  KEY `ix_sj_products_category` (`category`),
  KEY `ix_sj_products_stock` (`stock`),
  KEY `ix_sj_products_subcategory` (`sub_category`),
  KEY `ix_sj_products_mrp` (`mrp`),
  FULLTEXT KEY `ft_sj_products_search` (`name`,`brand`,`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_promo_strips` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `text` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_promo_strips_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_push_notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `message` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `link` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `image` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `scheduled_for` datetime DEFAULT NULL,
  `delivered_count` int NOT NULL DEFAULT '0',
  `read_count` int NOT NULL DEFAULT '0',
  `user_segment` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_behavior` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_by` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_push_notifications_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_referral_settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `segment` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `discount_type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `discount_value` decimal(18,2) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_referral_settings_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_return_request_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `product_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `quantity` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `reason` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_return_` (`parent_id`),
  CONSTRAINT `fk_sj_return_` FOREIGN KEY (`parent_id`) REFERENCES `sj_return_requests` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_return_requests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `return_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `order_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `payment_method` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `upi_payment_screenshot` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `notes` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `seller_id` varchar(64) DEFAULT NULL,
  `delivery_slot_id` varchar(64) DEFAULT NULL,
  `delivery_slot_config_id` varchar(64) DEFAULT NULL,
  `delivery_slot_date` varchar(32) DEFAULT NULL,
  `pending_valet_id` varchar(64) DEFAULT NULL,
  `valet_assigned_at` datetime DEFAULT NULL,
  `valet_cascade_count` int DEFAULT '0',
  `valet_accepted_at` datetime DEFAULT NULL,
  `valet_declined_at` datetime DEFAULT NULL,
  `valet_decline_reason` varchar(1000) DEFAULT NULL,
  `delivery_charge` float DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_return_requests_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_return_settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `return_days` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_return_settings_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_return_valet_declines` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `valet_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `reason` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_return_valet_declines` (`parent_id`),
  CONSTRAINT `fk_sj_return_valet_declines` FOREIGN KEY (`parent_id`) REFERENCES `sj_return_requests` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_review_classifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `review_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `confidence_score` decimal(5,4) DEFAULT NULL,
  `sentiment` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_saved_for_later` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `product_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `saved_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_saved_for_later_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_scheme_roles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `role` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_scheme_` (`parent_id`),
  CONSTRAINT `fk_sj_scheme_` FOREIGN KEY (`parent_id`) REFERENCES `sj_schemes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_schemes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `discount_type` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `discount_value` decimal(18,2) DEFAULT NULL,
  `min_order_value` decimal(18,2) DEFAULT NULL,
  `valid_from` datetime DEFAULT NULL,
  `valid_until` datetime DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `code` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_schemes_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_search_tag_brands` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `brand` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_search_tag_brands` (`parent_id`),
  CONSTRAINT `fk_sj_search_tag_brands` FOREIGN KEY (`parent_id`) REFERENCES `sj_search_tags` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_search_tag_categories` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `category` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_search_` (`parent_id`),
  CONSTRAINT `fk_sj_search_` FOREIGN KEY (`parent_id`) REFERENCES `sj_search_tags` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_search_tag_collections` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `collection` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_search_tag_collections` (`parent_id`),
  CONSTRAINT `fk_sj_search_tag_collections` FOREIGN KEY (`parent_id`) REFERENCES `sj_search_tags` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_search_tag_ex_products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `product_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_search_tag_ex_products` (`parent_id`),
  CONSTRAINT `fk_sj_search_tag_ex_products` FOREIGN KEY (`parent_id`) REFERENCES `sj_search_tags` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_search_tag_products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `product_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_search_tag_products` (`parent_id`),
  CONSTRAINT `fk_sj_search_tag_products` FOREIGN KEY (`parent_id`) REFERENCES `sj_search_tags` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_search_tag_subcats` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `sub_category` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_search_tag_subcats` (`parent_id`),
  CONSTRAINT `fk_sj_search_tag_subcats` FOREIGN KEY (`parent_id`) REFERENCES `sj_search_tags` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_search_tags` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tag_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_search_tags_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_seller_availability` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `seller_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT 'scheduled',
  `start_at` datetime DEFAULT NULL,
  `end_at` datetime DEFAULT NULL,
  `reason` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_by` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cancelled_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_seller_availability_external` (`external_id`),
  KEY `ix_sa_status_times` (`status`,`start_at`,`end_at`),
  KEY `ix_sa_seller_status` (`seller_id`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_seller_pincodes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `pincode` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `pincode_type` enum('serviceable','urgent','slot') COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_usr_pin` (`user_id`),
  CONSTRAINT `fk_usr_pin` FOREIGN KEY (`user_id`) REFERENCES `sj_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_seller_request_attachments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `request_id` int NOT NULL,
  `url` varchar(1024) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_req_att` (`request_id`),
  CONSTRAINT `fk_req_att` FOREIGN KEY (`request_id`) REFERENCES `sj_seller_requests` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_seller_request_responses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `request_id` int NOT NULL,
  `admin_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `response_text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_req_resp` (`request_id`),
  CONSTRAINT `fk_req_resp` FOREIGN KEY (`request_id`) REFERENCES `sj_seller_requests` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_seller_requests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `request_number` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `subject` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT 'general',
  `priority` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT 'medium',
  `status` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT 'open',
  `resolved_at` datetime DEFAULT NULL,
  `closed_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_seller_zones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `zone_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_usr_zone` (`user_id`),
  CONSTRAINT `fk_usr_zone` FOREIGN KEY (`user_id`) REFERENCES `sj_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_session_devices` (
  `id` int NOT NULL AUTO_INCREMENT,
  `session_id` int NOT NULL,
  `device_key` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `device_value` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_session_dev` (`session_id`),
  CONSTRAINT `fk_sj_session_dev` FOREIGN KEY (`session_id`) REFERENCES `sj_sessions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_sessions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` int NOT NULL,
  `refresh_token_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `last_active_at` datetime DEFAULT NULL,
  `revoked_at` datetime DEFAULT NULL,
  `revoked_reason` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_guest` tinyint(1) NOT NULL DEFAULT '0',
  `comments` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_sessions_external` (`external_id`),
  KEY `ix_sj_sessions_user` (`user_id`),
  KEY `ix_sj_sessions_status` (`status`),
  KEY `ix_sj_sessions_refresh` (`refresh_token_id`),
  CONSTRAINT `fk_sj_sessions_user` FOREIGN KEY (`user_id`) REFERENCES `sj_users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_stock_reservations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `product_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `quantity` int NOT NULL DEFAULT '1',
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'reserved',
  `expires_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_sub_order_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sub_order_id` int NOT NULL,
  `product_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL,
  `qty` int NOT NULL,
  `price` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `sub_order_id` (`sub_order_id`),
  CONSTRAINT `sj_sub_order_items_ibfk_1` FOREIGN KEY (`sub_order_id`) REFERENCES `sj_sub_orders` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_sub_order_variants` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sub_order_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `variant_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sub_ord_var` (`sub_order_id`),
  CONSTRAINT `fk_sub_ord_var` FOREIGN KEY (`sub_order_id`) REFERENCES `sj_sub_orders` (`external_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_sub_orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sub_order_number` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `seller_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `seller_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'pending',
  `payment_method` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `parent_order_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `parent_order_number` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `subtotal` decimal(12,2) NOT NULL DEFAULT '0.00',
  `tax` decimal(12,2) NOT NULL DEFAULT '0.00',
  `shipping` decimal(12,2) NOT NULL DEFAULT '0.00',
  `delivery_gst` decimal(12,2) NOT NULL DEFAULT '0.00',
  `discount` decimal(12,2) NOT NULL DEFAULT '0.00',
  `commission_status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'unrealized',
  `shipping_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `shipping_phone` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `shipping_line1` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `shipping_city` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `shipping_state` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `shipping_pincode` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `billing_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `billing_phone` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `billing_line1` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `billing_city` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `billing_state` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `billing_pincode` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `delivered_at` datetime DEFAULT NULL,
  `dispatched_at` datetime DEFAULT NULL,
  `cancelled_at` datetime DEFAULT NULL,
  `payment_status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'pending',
  `is_urgent_delivery` tinyint(1) NOT NULL DEFAULT '0',
  `delivery_slot_config_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `delivery_slot_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `delivery_slot_date` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `coupon_code` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `coupon_info_type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `coupon_info_value` decimal(12,2) DEFAULT NULL,
  `total` decimal(12,2) DEFAULT NULL,
  `order_type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_sub_orders_external` (`external_id`),
  KEY `ix_so_seller_status` (`seller_id`,`status`),
  KEY `ix_so_parent_order` (`parent_order_id`),
  KEY `ix_so_user_id` (`user_id`),
  KEY `ix_so_commission` (`commission_status`),
  KEY `ix_so_status` (`status`),
  KEY `ix_so_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_support_tickets` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ticket_number` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `company` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `subject` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `category` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `priority` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `assigned_to` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `resolved_at` datetime DEFAULT NULL,
  `closed_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_support_tickets_external` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_system_settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `maintenance_mode` tinyint(1) DEFAULT '0',
  `allow_signups` tinyint(1) DEFAULT '1',
  `max_upload_size_mb` int DEFAULT '10',
  `default_currency` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT 'INR',
  `timezone` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT 'Asia/Kolkata',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_ticket_attachments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `url` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_ticket_` (`parent_id`),
  CONSTRAINT `fk_sj_ticket_` FOREIGN KEY (`parent_id`) REFERENCES `sj_support_tickets` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_ticket_responses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL,
  `admin_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `message` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_ticket_responses` (`parent_id`),
  CONSTRAINT `fk_sj_ticket_responses` FOREIGN KEY (`parent_id`) REFERENCES `sj_support_tickets` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_tracking` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `event_type` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `session_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `event_timestamp` datetime DEFAULT NULL,
  `search_term` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `results_count` int DEFAULT NULL,
  `product_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `product_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `segment` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `page` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `reason` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `filter_type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `filter_value` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cart_value` decimal(18,2) DEFAULT NULL,
  `os` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `browser` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ip_address` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  is_returning tinyint(1) DEFAULT NULL,
  cart_items json DEFAULT NULL,
  source varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  campaign varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_tracking_external` (`external_id`),
  KEY `ix_sj_tracking_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_tracking_payload` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tracking_id` int NOT NULL,
  `payload_key` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `payload_value` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `fk_sj_tracking_pay` (`tracking_id`),
  CONSTRAINT `fk_sj_tracking_pay` FOREIGN KEY (`tracking_id`) REFERENCES `sj_tracking` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_tracking_products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tracking_id` int NOT NULL,
  `product_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_tracking_prod` (`tracking_id`),
  CONSTRAINT `fk_sj_tracking_prod` FOREIGN KEY (`tracking_id`) REFERENCES `sj_tracking` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_user_addresses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `is_primary` tinyint(1) DEFAULT '0',
  `street` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `city` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `state` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `pincode` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_usr_addr` (`user_id`),
  CONSTRAINT `fk_usr_addr` FOREIGN KEY (`user_id`) REFERENCES `sj_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id_formatted` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `role` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `company_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `approval_status` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_deactivated` tinyint(1) NOT NULL DEFAULT '0',
  `credit_limit` decimal(18,2) NOT NULL DEFAULT '0.00',
  `credit_used` decimal(18,2) NOT NULL DEFAULT '0.00',
  `payment_terms` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `assigned_salesperson` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_email_verified` tinyint(1) NOT NULL DEFAULT '0',
  `referral_code` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `is_seller_admin` tinyint(1) NOT NULL DEFAULT '0',
  `is_on_duty` tinyint(1) NOT NULL DEFAULT '0',
  `commission_override_pct` decimal(5,2) DEFAULT NULL,
  `allow_delivery_slots` tinyint(1) DEFAULT '0',
  `allow_urgent_delivery` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_users_external` (`external_id`),
  UNIQUE KEY `uq_sj_users_email` (`email`),
  UNIQUE KEY `uq_sj_users_phone` (`phone`),
  KEY `ix_sj_users_role` (`role`),
  KEY `ix_sj_users_referral` (`referral_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_valet_availability` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `date` date NOT NULL,
  `availability_type` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_valet_availability_slots` (
  `id` int NOT NULL AUTO_INCREMENT,
  `availability_id` int NOT NULL,
  `slot` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_valet_slot` (`availability_id`),
  CONSTRAINT `fk_valet_slot` FOREIGN KEY (`availability_id`) REFERENCES `sj_valet_availability` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_valet_availability_zones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `availability_id` int NOT NULL,
  `zone` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_valet_zone` (`availability_id`),
  CONSTRAINT `fk_valet_zone` FOREIGN KEY (`availability_id`) REFERENCES `sj_valet_availability` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_valet_payout_settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `delivery_charge_per_order` decimal(10,2) NOT NULL DEFAULT '0.00',
  `return_pickup_charge_per_order` decimal(10,2) NOT NULL DEFAULT '0.00',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_wishlist_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `wishlist_id` int NOT NULL,
  `product_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_sj_wishlist_item` (`wishlist_id`),
  CONSTRAINT `fk_sj_wishlist_item` FOREIGN KEY (`wishlist_id`) REFERENCES `sj_wishlists` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sj_wishlists` (
  `id` int NOT NULL AUTO_INCREMENT,
  `external_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` int NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sj_wishlists_external` (`external_id`),
  KEY `ix_sj_wishlists_user` (`user_id`),
  CONSTRAINT `fk_sj_wishlists_user` FOREIGN KEY (`user_id`) REFERENCES `sj_users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE sj_email_otp_send_log (
  id int NOT NULL AUTO_INCREMENT,
  email varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  sent_at datetime DEFAULT NULL,
  PRIMARY KEY (id),
  KEY ix_sj_email_otp_send_log_email (email),
  KEY ix_sj_email_otp_send_log_sent (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE sj_email_otps (
  id int NOT NULL AUTO_INCREMENT,
  email varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  device_key varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  otp_code varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  erify_attempts int DEFAULT '0',
  created_at datetime DEFAULT NULL,
  expires_at datetime DEFAULT NULL,
  last_sent_at datetime DEFAULT NULL,
  PRIMARY KEY (id),
  KEY ix_sj_email_otps_email (email),
  KEY ix_sj_email_otps_expires (expires_at),
  KEY ix_sj_email_otps_email_device (email,device_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Seed Payment Feature Flags
INSERT IGNORE INTO sj_feature_flags (flag_id, name, description, enabled, category, created_at, updated_at) VALUES 
('retail_enable_cod', 'Retail COD', 'Enable Cash on Delivery for Retail customers', 1, 'payments', NOW(), NOW()),
('retail_enable_upi', 'Retail UPI', 'Enable UPI payment for Retail customers', 1, 'payments', NOW(), NOW()),
('retail_enable_credit', 'Retail Credit', 'Enable Credit for Retail customers', 1, 'payments', NOW(), NOW()),
('wholesale_enable_cod', 'Wholesale COD', 'Enable Cash on Delivery for Wholesale customers', 1, 'payments', NOW(), NOW()),
('wholesale_enable_upi', 'Wholesale UPI', 'Enable UPI payment for Wholesale customers', 1, 'payments', NOW(), NOW()),
('wholesale_enable_credit', 'Wholesale Credit', 'Enable Credit orders for Wholesale customers', 1, 'payments', NOW(), NOW()),
('retail_enable_gst', 'Retail GST', 'Enable GST calculation for Retail customers', 1, 'payments', NOW(), NOW()),
('wholesale_enable_gst', 'Wholesale GST', 'Enable GST calculation for Wholesale customers', 1, 'payments', NOW(), NOW());

CREATE TABLE sj_return_valet_declines (
  id int NOT NULL AUTO_INCREMENT,
  
eturn_request_id varchar(64) NOT NULL,
  alet_id varchar(64) NOT NULL,
  
eason varchar(1000) DEFAULT NULL,
  PRIMARY KEY (id),
  KEY idx_ret_valet_decline (
eturn_request_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
