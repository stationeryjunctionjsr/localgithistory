import re

with open('backend/app/routers/availability_requests.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('response_model=Dict[str, Any]', 'response_model=MessageResponse')
content = content.replace('from pydantic import BaseModel, Field', 'from pydantic import BaseModel, Field\nfrom app.models.schemas import MessageResponse')
with open('backend/app/routers/availability_requests.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('backend/app/routers/order_feedback.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('response_model=Dict[str, Any]', 'response_model=EligibleFeedbackResponse')
# inject EligibleFeedbackResponse
model = '''
class EligibleFeedbackResponse(BaseModel):
    eligibleOrderId: Optional[str] = None
'''
content = content.replace('from app.models.order_feedback import OrderFeedbackCreate', model + '\nfrom app.models.order_feedback import OrderFeedbackCreate')
with open('backend/app/routers/order_feedback.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('backend/app/routers/products.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('response_model=Dict[str, Any]', 'response_model=MessageResponse')
content = content.replace('response_model=List[Dict[str, Any]]', 'response_model=List[str]')
with open('backend/app/routers/products.py', 'w', encoding='utf-8') as f:
    f.write(content)

