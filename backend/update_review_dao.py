with open('app/db/mysql_flat_daos.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Update __map_to_schema
old_map = '''            "rating": row.rating,
            "reviewText": row.review_text,
            "status": row.status,'''
new_map = '''            "rating": row.rating,
            "reviewText": row.review_text,
            "status": row.status,
            "userName": getattr(row, "user_name", None),
            "classification": getattr(row, "classification", None),'''
text = text.replace(old_map, new_map)

# Update create
old_create = '''        if data.reviewText is not None:
            cols.append("review_text")
            params["s_reviewText"] = data.reviewText

        if data.status is not None:
            cols.append("status")
            params["s_status"] = data.status'''
new_create = '''        if data.reviewText is not None:
            cols.append("review_text")
            params["s_reviewText"] = data.reviewText

        if data.status is not None:
            cols.append("status")
            params["s_status"] = data.status

        if getattr(data, "userName", None) is not None:
            cols.append("user_name")
            params["s_userName"] = data.userName

        if getattr(data, "classification", None) is not None:
            cols.append("classification")
            params["s_classification"] = data.classification'''
text = text.replace(old_create, new_create)

# Update update
old_update = '''        if update_data.reviewText is not None:
            updates.append("review_text = :s_reviewText")
            params["s_reviewText"] = update_data.reviewText

        if update_data.status is not None:
            updates.append("status = :s_status")
            params["s_status"] = update_data.status'''
new_update = '''        if update_data.reviewText is not None:
            updates.append("review_text = :s_reviewText")
            params["s_reviewText"] = update_data.reviewText

        if update_data.status is not None:
            updates.append("status = :s_status")
            params["s_status"] = update_data.status

        if getattr(update_data, "userName", None) is not None:
            updates.append("user_name = :s_userName")
            params["s_userName"] = update_data.userName

        if getattr(update_data, "classification", None) is not None:
            updates.append("classification = :s_classification")
            params["s_classification"] = update_data.classification'''
text = text.replace(old_update, new_update)

with open('app/db/mysql_flat_daos.py', 'w', encoding='utf-8') as f:
    f.write(text)
