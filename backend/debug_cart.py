filename = 'app/repositories/cart_repository.py'
with open(filename, 'r') as f:
    content = f.read()

content = content.replace(
    "async def createOrUpdate(self, user_id: str, items: List[Any]) -> Cart:",
    "async def createOrUpdate(self, user_id: str, items: List[Any]) -> Cart:\n        print(f'createOrUpdate called with user_id={user_id}')"
)

with open(filename, 'w') as f:
    f.write(content)
