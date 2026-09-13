import re

with open('backend/app/routers/tracking.py', 'r') as f:
    content = f.read()

models = '''
class SearchSuggestionsResponse(BaseModel):
    popularTerms: List[str]
    popularCategories: List[str]
    popularBrands: List[str]

class MostSearchedResponse(BaseModel):
    term: str
    count: int
    avgProductsFound: float

class ZeroResultSearchResponse(BaseModel):
    term: str
    count: int

class MostViewedResponse(BaseModel):
    productId: str
    productName: str
    count: int

class ReturningUserResponse(BaseModel):
    userId: str
    name: str
    email: str
    lastSeen: Optional[str] = None

class DropOffPointResponse(BaseModel):
    page: str
    count: int
    reasons: Dict[str, int]

class CartAbandonmentResponse(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    type: Optional[str] = None
    userId: Optional[str] = None
    sessionId: Optional[str] = None
    timestamp: Optional[str] = None
    cartItems: List[Any] = []
    cartValue: Optional[float] = 0.0
    
    model_config = ConfigDict(extra='allow', populate_by_name=True)

class MostAbandonedProductResponse(BaseModel):
    productId: str
    productName: str
    category: str
    abandonCount: int
    quantityAbandoned: int
    valueLost: float
'''

# Add Field, ConfigDict, Any to imports
content = re.sub(r'from pydantic import BaseModel', 'from pydantic import BaseModel, Field, ConfigDict', content)

# Insert models before @router.post("/beacon"...
content = content.replace('@router.post("/beacon"', models + '\n@router.post("/beacon"')

content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_recent_searches', 'response_model=List[str])\nasync def get_recent_searches')
content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_search_suggestions', 'response_model=SearchSuggestionsResponse)\nasync def get_search_suggestions')
content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_most_searched', 'response_model=List[MostSearchedResponse])\nasync def get_most_searched')
content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_zero_result_searches', 'response_model=List[ZeroResultSearchResponse])\nasync def get_zero_result_searches')
content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_most_viewed', 'response_model=List[MostViewedResponse])\nasync def get_most_viewed')
content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_returning_users', 'response_model=List[ReturningUserResponse])\nasync def get_returning_users')
content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_drop_off_points', 'response_model=List[DropOffPointResponse])\nasync def get_drop_off_points')
content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_cart_abandonments', 'response_model=List[CartAbandonmentResponse])\nasync def get_cart_abandonments')
content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_most_abandoned_products', 'response_model=List[MostAbandonedProductResponse])\nasync def get_most_abandoned_products')

with open('backend/app/routers/tracking.py', 'w') as f:
    f.write(content)
