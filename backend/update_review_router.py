with open('app/routers/reviews.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('"comment": review_data.comment.strip(),', '"reviewText": review_data.comment.strip(),')

with open('app/routers/reviews.py', 'w', encoding='utf-8') as f:
    f.write(text)
