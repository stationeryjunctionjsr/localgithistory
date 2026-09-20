import re
with open('app/routers/analytics.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('from fastapi import APIRouter, Body, Depends, HTTPException, Query', 'from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request')

with open('app/routers/analytics.py', 'w', encoding='utf-8') as f:
    f.write(text)
