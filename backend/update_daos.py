with open('app/models/daos_flat.py', 'r', encoding='utf-8') as f:
    text = f.read()

create_str = """class ProductReviewsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    externalId: Optional[str] = Field(None, alias='externalId')
    productId: Optional[str] = None
    rating: Optional[int] = None
    reviewText: Optional[str] = None
    status: Optional[str] = None
    userId: Optional[str] = None
    userName: Optional[str] = Field(None, alias='userName')
    classification: Optional[str] = None"""

update_str = """class ProductReviewsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    externalId: Optional[str] = Field(None, alias='externalId')
    productId: Optional[str] = None
    rating: Optional[int] = None
    reviewText: Optional[str] = None
    status: Optional[str] = None
    userName: Optional[str] = Field(None, alias='userName')
    classification: Optional[str] = None"""

import re

# Replace ProductReviewsInternalCreate block
text = re.sub(
    r'class ProductReviewsInternalCreate\(BaseModel\):.*?userId: Optional\[str\] = None',
    create_str,
    text,
    flags=re.DOTALL
)

# Replace ProductReviewsInternalUpdate block
text = re.sub(
    r'class ProductReviewsInternalUpdate\(BaseModel\):.*?status: Optional\[str\] = None',
    update_str,
    text,
    flags=re.DOTALL
)

with open('app/models/daos_flat.py', 'w', encoding='utf-8') as f:
    f.write(text)
