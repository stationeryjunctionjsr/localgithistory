-- Add indices to speed up queries

-- sj_products indices for filtering
CREATE INDEX idx_products_brand ON sj_products (brand);
CREATE INDEX idx_products_category ON sj_products (category);
CREATE INDEX idx_products_sub_cat ON sj_products (sub_category);

-- sj_coupons indices for filtering (doc_store.py uses payload column for sj_coupons)
CREATE INDEX idx_coupons_json_isActive ON sj_coupons (JSON_VALUE(payload, '$.isActive'));
CREATE INDEX idx_coupons_json_typeDiscount ON sj_coupons (JSON_VALUE(payload, '$.typeOfDiscount'));
CREATE INDEX idx_coupons_json_method ON sj_coupons (JSON_VALUE(payload, '$.method'));

-- sj_orders uses OracleOrderDAO, so standard indices
-- actually let's skip sj_orders for now if we didn't check if it uses JSON
