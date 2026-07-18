-- SQL migration script to add missing indexes to sj_products table

CREATE INDEX ix_sj_products_lower_brand ON sj_products (LOWER(brand));
CREATE INDEX ix_sj_products_lower_category ON sj_products (LOWER(category));
CREATE INDEX ix_sj_products_lower_name ON sj_products (LOWER(name));
CREATE INDEX ix_sj_products_subcategory ON sj_products (sub_category);
CREATE INDEX ix_sj_products_mrp ON sj_products (mrp);
