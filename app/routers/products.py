from fastapi import APIRouter, Depends, status, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import insert, select, update, delete
from slugify import slugify

from app.backend.db_depends import get_db
from app.schemas import CreateProduct

from app.models.products import Product
from app.models.category import Category
from app.routers.auth import get_current_user
from backend.db import Base

router = APIRouter(prefix='/products', tags=['products'])

async def get_db_authenticated(db: Annotated[AsyncSession, Depends(get_db)],
                        get_user: Annotated[dict, Depends(get_current_user)]):

    if all((not get_user.get('is_admin'), not get_user.get('is_supplier'))):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not authorized to use this method'
        )

    return db


async def get_product(db: Annotated[AsyncSession, Depends(get_db)],
                      get_user: Annotated[dict, Depends(get_current_user)],
                      product_slug: str):

    product_edit = await db.scalar(select(Product).where(Product.slug == product_slug))

    if all((not get_user.get('id') == product_edit.supplier_id, not get_user.get('is_admin'))):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not authorized to use this method'
        )

    if product_edit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no product found'
        )

    return product_edit

@router.get('/')
async def all_reviews (db: Annotated[AsyncSession, Depends(get_db)]):
    products = await db.scalars(select(Product).where(Product.is_active, Product.stock > 0))
    if products is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no products'
        )

    return products.all()


@router.get('/{category_slug}')
async def product_by_category(db: Annotated[AsyncSession, Depends(get_db)], category_slug: str):
    category = await db.scalar(select(Category.id).where(Category.slug == category_slug))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no category found'
        )

    categories_and_subcategories = [category]

    subcategories = await db.scalars(select(Category.id).where(Category.parent_id == category))

    while True:
        categories = []
        for subcategory in subcategories.all():
            categories_and_subcategories.append(subcategory)
            categories.append(subcategory)
        if not categories:
            break
        subcategories = await db.scalars(select(Category.id).where(Category.parent_id.in_(categories)))

    products = await db.scalars(select(Product).where(Product.category_id.in_(categories_and_subcategories),
                                                      Product.is_active,
                                                      Product.stock > 0))

    return products.all()


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_product(db: Annotated[AsyncSession, Depends(get_db_authenticated)],
                         new_product: CreateProduct,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    category = await db.scalar(select(Category).where(Category.id == new_product.category))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no category found'
        )
    await db.execute(insert(Product).values(name=new_product.name,
                                            description=new_product.description,
                                            price=new_product.price,
                                            image_url=new_product.image_url,
                                            stock=new_product.stock,
                                            category_id=new_product.category,
                                            rating=0.0,
                                            slug=slugify(new_product.name),
                                            supplier_id=get_user.get('id')))
    await db.commit()
    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }


@router.get('/detail/{product_slug}')
async def product_detail(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str):
    product = await db.scalar(
        select(Product).where(Product.slug == product_slug, Product.is_active, Product.stock > 0))
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no product'
        )
    return product


@router.put('/{product_slug}')
async def update_product(db: Annotated[AsyncSession, Depends(get_db_authenticated)],
                         product_update: Annotated[Base, Depends(get_product)],
                         update_product_model: CreateProduct,):

    category = await db.scalar(select(Category).where(Category.id == update_product_model.category))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no category found'
        )
    product_update.name = update_product_model.name
    product_update.description = update_product_model.description
    product_update.price = update_product_model.price
    product_update.image_url = update_product_model.image_url
    product_update.stock = update_product_model.stock
    product_update.category_id = update_product_model.category
    product_update.slug = slugify(update_product_model.name)

    await db.commit()

    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product update is successful'
    }


@router.delete('/{product_slug}')
async def delete_product(db: Annotated[AsyncSession, Depends(get_db_authenticated)],
                         product_delete: Annotated[Base, Depends(get_product)]):

    product_delete.is_active = False
    await db.commit()

    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product delete is successful'
    }