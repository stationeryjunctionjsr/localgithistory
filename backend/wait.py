import os

filepath = 'app/db/mysql_bundle_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the dict keys to snake_case because base DAO uses model_fields to extract values
text = text.replace('data.discountPercentage', 'data.discount_percentage')
text = text.replace('data_dict["discountPercentage"]', 'data_dict["discount_percentage"]')
text = text.replace('update_data.discountPercentage', 'update_data.discount_percentage')
text = text.replace('update_dict["discountPercentage"]', 'update_dict["discount_percentage"]')

text = text.replace('data.isActive', 'data.is_active')
text = text.replace('data_dict["isActive"]', 'data_dict["is_active"]')
text = text.replace('update_data.isActive', 'update_data.is_active')
text = text.replace('update_dict["isActive"]', 'update_dict["is_active"]')

text = text.replace('data.salesCount', 'data.sales_count')
text = text.replace('data_dict["salesCount"]', 'data_dict["sales_count"]')
text = text.replace('update_data.salesCount', 'update_data.sales_count')
text = text.replace('update_dict["salesCount"]', 'update_dict["sales_count"]')

# We no longer need the super() manual overrides if we use purely model_validate in BaseDAO, wait, MySQLBundleDAO passes data_dict to super().create() which calls self._doc_to_params(data, now).
# Since data is now a dict, _doc_to_params uses data.get().
# But wait, in MySQLFlatBaseDAO, _doc_to_params relies on scalar_map!
# Which we said maps api_key to db_column!
# If we change data_dict to use snake_case keys ("is_active", "sales_count"), but scalar_map is {"isActive": "is_active"}, then _doc_to_params will look for "isActive" in data_dict and FAIL!
