from sqlalchemy import create_engine, text

url_qa = "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjqadb"
url_uat = "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjuatdb"
create_stmt = """CREATE TABLE IF NOT EXISTS sj_system_settings (
  id          INT             NOT NULL AUTO_INCREMENT PRIMARY KEY,
  external_id VARCHAR(32)     NOT NULL,
  doc         LONGTEXT,
  created_at  DATETIME,
  updated_at  DATETIME,
  CONSTRAINT uq_sj_system_settings_external UNIQUE (external_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"""

for url in (url_qa, url_uat):
    with create_engine(url).begin() as conn:
        conn.execute(text(create_stmt))
        print("Created sj_system_settings")
