import re

with open('schema.sql', 'r', encoding='utf-8') as f:
    text = f.read()

replacement_sql = '''CREATE TABLE sj_events (
  id int NOT NULL AUTO_INCREMENT,
  external_id varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  event_type varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  created_at datetime DEFAULT NULL,
  updated_at datetime DEFAULT NULL,
  	racking_id int DEFAULT NULL,
  session_id varchar(128) DEFAULT NULL,
  user_id varchar(128) DEFAULT NULL,
  ip_address varchar(128) DEFAULT NULL,
  os varchar(128) DEFAULT NULL,
  rowser varchar(128) DEFAULT NULL,
  campaign varchar(128) DEFAULT NULL,
  source varchar(128) DEFAULT NULL,
  product_id varchar(128) DEFAULT NULL,
  product_name varchar(255) DEFAULT NULL,
  quantity int DEFAULT NULL,
  query varchar(255) DEFAULT NULL,
  esults_count int DEFAULT NULL,
  eason varchar(255) DEFAULT NULL,
  page varchar(255) DEFAULT NULL,
  screen varchar(255) DEFAULT NULL,
  	est_run_id varchar(128) DEFAULT NULL,
  device_type varchar(64) DEFAULT NULL,
  device_os varchar(64) DEFAULT NULL,
  device_os_version varchar(64) DEFAULT NULL,
  device_model varchar(128) DEFAULT NULL,
  device_app_version varchar(128) DEFAULT NULL,'''

text = re.sub(r'CREATE TABLE sj_events \(\n  id int NOT NULL AUTO_INCREMENT,\n  external_id varchar\(32\) COLLATE utf8mb4_unicode_ci NOT NULL,\n  event_type varchar\(128\) COLLATE utf8mb4_unicode_ci DEFAULT NULL,\n  created_at datetime DEFAULT NULL,\n  updated_at datetime DEFAULT NULL,', replacement_sql, text)

with open('schema.sql', 'w', encoding='utf-8') as f:
    f.write(text)

