from fastapi import APIRouter, Depends, status, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import insert, select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func

from app.backend.db_depends import get_db
from app.schemas import CreateReview

from app.models.products import Product
from app.models.reviews import Review
from app.routers.auth import get_current_user

router = APIRouter(prefix='/reviews', tags=['reviews'])


async def get_db_authenticated(db: Annotated[AsyncSession, Depends(get_db)],
                               get_user: Annotated[dict, Depends(get_current_user)]):
    if all((not get_user.get('is_admin'), not get_user.get('is_customer'))):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not authorized to use this method'
        )

    return db


@router.get('/')
async def all_reviews(db: Annotated[AsyncSession, Depends(get_db)]):
    review = await db.scalars(select(Review).where(Review.is_active))
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no reviews'
        )

    return review.all()


@router.get('/{product_slug}')
async def products_reviews(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str):
    review = await db.scalars(select(Review).join(Review.products).where(Product.slug == product_slug))

    response = review.all()

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no product found'
        )

    return response


@router.post('/', status_code=status.HTTP_201_CREATED)
async def add_review(db: Annotated[AsyncSession, Depends(get_db_authenticated)],
                     new_review: CreateReview,
                     get_user: Annotated[dict, Depends(get_current_user)]):
    product = await db.scalar(select(Product).where(Product.id == new_review.product_id))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no product found'
        )

    await db.execute(insert(Review).values(comment=new_review.comment,
                                           comment_date=new_review.comment_date,
                                           grade=new_review.grade,
                                           product_id=product.id,
                                           user_id=get_user.get('id')))

    grade_avg = await db.scalar(select(func.round(func.avg(Review.grade), 2)).where(Review.product_id == product.id))
    product.rating = grade_avg

    await db.commit()

    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }


@router.delete('/{id_review}')
async def delete_reviews (db: Annotated[AsyncSession, Depends(get_db)],
                         get_user: Annotated[dict, Depends(get_current_user)],
                         id_review: int = Path(ge=1)):

    if not get_user.get('is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not authorized to use this method'
        )

    review = await db.scalar(select(Review).where(Review.id == id_review))

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no review found'
        )

    review.is_active = False
    await db.commit()

    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Review delete is successful'
    }
