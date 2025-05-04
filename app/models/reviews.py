from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.backend.db import Base


class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    comment = Column(String)
    comment_date = Column(DateTime(timezone=True))
    grade = Column(Integer)
    is_active = Column(Boolean, default=True)

    products = relationship('Product', back_populates='reviews')