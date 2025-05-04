from datetime import datetime

from pydantic import BaseModel, Field


class CreateProduct(BaseModel):
    name: str
    description: str
    price: int
    image_url: str
    stock: int
    category: int

class CreateCategory(BaseModel):
    name: str
    parent_id: int | None = None

class CreateUser(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str

class CreateReview(BaseModel):
    product_id: int
    comment: str
    comment_date: datetime
    grade: int = Field(..., ge = 1, le = 5, description='From 1 to 5')
