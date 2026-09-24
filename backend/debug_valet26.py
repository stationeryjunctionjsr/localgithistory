import re

with open('app/routers/orders.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('                })\n        )', '                }\n            })\n        )')
text = text.replace('                                })\n                        )', '                                }\n                            })\n                        )')

with open('app/routers/orders.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
